import pytest
from datetime import datetime, timedelta
from starlette import status

@pytest.mark.asyncio
class TestAnalyticsAPIPositive:

    async def test_comments_daily_breakdown(self, client, user_admin_token, comments):
        # Set the authorization header for the administrator
        headers = {"Authorization": f"Bearer {user_admin_token}"}

        # Set the dates of the range
        date_from = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        response = client.get(
            f"/analytics/comments-daily-breakdown?date_from={date_from}&date_to={date_to}",
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Checking response structure and content
        response_data = response.json()
        assert isinstance(response_data, dict)

        # Check the number of comments and blocked comments for each day
        expected_data = {
            (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"): {"total_comments": 1, "blocked_comments": 0},
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"): {"total_comments": 2, "blocked_comments": 1},
            datetime.now().strftime("%Y-%m-%d"): {"total_comments": 1, "blocked_comments": 0},
        }

        for date, data in expected_data.items():
            assert response_data[date]["total_comments"] == data["total_comments"]
            assert response_data[date]["blocked_comments"] == data["blocked_comments"]

    async def test_comments_daily_breakdown_empty_data(self, client, user, user_admin_token):
        # Set the authorization header for the administrator
        headers = {"Authorization": f"Bearer {user_admin_token}"}

        # Set a range in which there are no comments
        date_from = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        date_to = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")

        response = client.get(
            f"/analytics/comments-daily-breakdown?date_from={date_from}&date_to={date_to}",
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Check that the data is empty
        response_data = response.json()

        assert isinstance(response_data, dict)
        assert len(response_data) == 3  # Проверяем количество дней в диапазоне

        for date in response_data:
            assert response_data[date]["total_comments"] == 0
            assert response_data[date]["blocked_comments"] == 0


@pytest.mark.asyncio
class TestAnalyticsAPINegative:
    async def test_missing_date_params(self, client, user_admin_token):
        headers = {"Authorization": f"Bearer {user_admin_token}"}

        response = client.get("/analytics/comments-daily-breakdown", headers=headers)
        assert response.status_code == 422
        assert "date_from" in response.json()["detail"][0]["loc"]
        assert "date_to" in response.json()["detail"][1]["loc"]

    async def test_invalid_date_format(self, client, user_admin_token):
        headers = {"Authorization": f"Bearer {user_admin_token}"}

        response = client.get("/analytics/comments-daily-breakdown?date_from=2024-11-31&date_to=2024-12-01", headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid date format. Use YYYY-MM-DD."

    async def test_start_date_greater_than_end_date(self, client, user_admin_token):
        headers = {"Authorization": f"Bearer {user_admin_token}"}

        response = client.get("/analytics/comments-daily-breakdown?date_from=2024-12-01&date_to=2024-11-05", headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"] == "date_from must be earlier than date_to."

    async def test_nonexistent_route(self, client):
        response = client.get("/analytics/nonexistent-endpoint")
        assert response.status_code == 404
        assert response.json()["detail"] == "Not Found"

    async def test_non_admin_user(self, client, another_user_token):
        headers = {"Authorization": f"Bearer {another_user_token}"}

        response = client.get("/analytics/comments-daily-breakdown?date_from=2024-11-08&date_to=2024-11-11", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to retrieve this info"

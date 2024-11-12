import pytest
from sqlalchemy import select
from starlette import status

from app.models import Comment


@pytest.mark.asyncio
class TestCommentsAPIPositive:
    @pytest.fixture(autouse=True)
    def setup(self, client, jwt_token, another_user_token):
        self.client = client
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
        self.another_user_headers = {"Authorization": f"Bearer {another_user_token}"}

    async def test_create_comment_positive(self, post):
        payload = {"content": "This is a test comment"}
        response = self.client.post(f"/comments/{post.id}/create", json=payload, headers=self.headers)

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["post_id"] == post.id

    async def test_get_all_comments_positive(self, post, comment):
        response = self.client.get(f"/comments/list/{post.id}", headers=self.headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["content"] == comment.content

    async def test_get_single_comment_positive(self, comment):
        response = self.client.get(f"/comments/{comment.id}", headers=self.headers)

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == comment.content
        assert data["id"] == comment.id

    async def test_update_comment_positive(self, comment):
        update_payload = {"content": "Updated test comment text"}

        response = self.client.put(f"/comments/{comment.id}", json=update_payload, headers=self.headers)

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated test comment text"

    async def test_delete_comment_positive(self, comment):
        response = self.client.delete(f"/comments/{comment.id}", headers=self.headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Comment deleted successfully"


@pytest.mark.asyncio
class TestCommentsAPINegative:
    @pytest.fixture(autouse=True)
    def setup(self, client, jwt_token, another_user_token, async_session):
        self.client = client
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
        self.another_user_headers = {"Authorization": f"Bearer {another_user_token}"}
        self.async_session = async_session

    async def test_create_comment_with_illegal_content(self, post):
        payload = {"content": "Stupid bastard"}
        response = self.client.post(f"/comments/{post.id}/create", json=payload, headers=self.headers)

        query = select(Comment).where(Comment.content == "Stupid bastard")
        result = await self.async_session.execute(query)
        comment_ = result.scalars().first()

        assert response.status_code == 400
        assert response.json()["detail"] == f"Content was blocked, reason - it contains inappropriate content: {comment_.block_reason}"

    async def test_create_comment_for_nonexistent_post(self):
        payload = {"content": "This is a test comment"}
        response = self.client.post("/comments/999/create", json=payload, headers=self.headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Post not found"

    async def test_get_nonexistent_comment(self):
        response = self.client.get("/comments/999", headers=self.headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Comment not found"

    async def test_update_comment_not_author(self, comment):
        update_payload = {"content": "Attempted update by another user"}

        response = self.client.put(f"/comments/{comment.id}", json=update_payload,
                                         headers=self.another_user_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Not authorized to update this comment"

    async def test_delete_comment_not_author(self, comment):
        response = self.client.delete(f"/comments/{comment.id}", headers=self.another_user_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Not authorized to delete this comment"

    async def test_create_comment_for_blocked_post(self, post):
        # Blocking the post
        post.is_blocked = True
        self.async_session.add(post)
        await self.async_session.commit()

        payload = {"content": "This comment should not be created"}
        response = self.client.post(f"/comments/{post.id}/create", json=payload, headers=self.headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "You cannot create a comment for blocked content."

    async def test_create_comment_for_blocked_parent_comment(self, comment):
        # Blocking parental comment
        comment.is_blocked = True
        self.async_session.add(comment)
        await self.async_session.commit()

        payload = {"content": "This is a reply to a blocked comment", "parent_id": comment.id}
        response = self.client.post(f"/comments/{comment.post_id}/create", json=payload, headers=self.headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "You cannot create a comment for blocked content."

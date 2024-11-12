import pytest


@pytest.mark.asyncio
class TestUsersPositive:
    @pytest.fixture(autouse=True)
    def setup(self, client, user, jwt_token):
        self.client = client
        self.user, self.token = user, jwt_token
        self.user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePassword123"
        }

    async def test_register_user(self):
        """Test successful user registration."""
        response = self.client.post("/users/register", json=self.user_data)

        assert response.status_code == 200
        assert response.json() == {"message": "User registered successfully"}

    async def test_login_user(self):
        """Test successful user login."""
        self.client.post("/users/register", json=self.user_data)

        payload = {
            "username": self.user_data.get("username"),
            "password": self.user_data.get("password")
        }
        response = self.client.post("/users/login", json=payload)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()


@pytest.mark.asyncio
class TestUsersNegative:
    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        self.client = client
        self.user = user
        self.userdata = {
            "username": "testuser2",
            "email": "test@email.com",
            "password": "SomePassword123"
        }

    async def test_register_user_duplicate_email(self):
        """Test registration with an existing username or email."""
        response = self.client.post("/users/register", json=self.userdata)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email or username already exists"

    async def test_register_user_duplicate_username(self):
        """Test registration with an existing username or email."""
        self.userdata["username"] = self.user.username
        response = self.client.post("/users/register", json=self.userdata)

        assert response.status_code == 400
        assert response.json()["detail"] == "Email or username already exists"

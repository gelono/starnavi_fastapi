import pytest
from sqlalchemy import select

from app.models import Post

@pytest.mark.asyncio
class TestPostsAPIPositive:
    @pytest.fixture(autouse=True)
    def setup(self, client, user, jwt_token):
        self.client = client
        self.user, self.token = user, jwt_token

    async def test_create_post_positive(self):
        payload = {"title": "New Post", "content": "This is a new post content."}
        headers = {"Authorization": f"Bearer {self.token}"}

        response = self.client.post("/posts/create/", json=payload, headers=headers)
        data = response.json()

        assert response.status_code == 201
        assert data['title'] == "New Post"
        assert data['content'] == "This is a new post content."

    async def test_list_posts_positive(self, post, blocked_post):
        headers = {"Authorization": f"Bearer {self.token}"}

        response = self.client.get("/posts/list", headers=headers)
        data = response.json()

        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) == 1

    async def test_get_single_post_positive(self, post):
        # Get post by ID
        response = self.client.get(f"/posts/{post.id}")
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == post.id

    async def test_update_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # Create a post
        create_response = self.client.post("/posts/create/",
                                           json={"title": "Simple title", "content": "Simple"},
                                           headers=headers)
        post_id = create_response.json()["id"]

        # Updating the post
        update_payload = {"title": "Updated Post", "content": "Updated text"}
        response = self.client.put(f"/posts/update/{post_id}", json=update_payload, headers=headers)
        data = response.json()

        assert response.status_code == 200
        assert data["title"] == "Updated Post"
        assert data["content"] == "Updated text"

    async def test_delete_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # Create a post
        create_response = self.client.post("/posts/create/",
                                           json={"title": "Simple title", "content": "Simple"},
                                           headers=headers)
        post_id = create_response.json()["id"]

        # Delete the post
        response = self.client.delete(f"/posts/delete/{post_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Post deleted successfully"


@pytest.mark.asyncio
class TestPostsAPINegative:
    @pytest.fixture(autouse=True)
    def setup(self, client, user, jwt_token, async_session):
        self.client = client
        self.user, self.token = user, jwt_token
        self.async_session = async_session

    async def test_create_post_without_authentication(self):
        payload = {"title": "New Post", "content": "This is a new post content."}

        # Trying to create a post without an authorization header
        response = self.client.post("/posts/create/", json=payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    async def test_create_post_with_illegal_content(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"title": "New Post", "content": "This is a new stupid bastard"}

        # Trying to create a post with inappropriate content
        response = self.client.post("/posts/create/", json=payload, headers=headers)

        query = select(Post).where(Post.content == "This is a new stupid bastard")
        result = await self.async_session.execute(query)
        post_ = result.scalars().first()

        assert response.status_code == 400
        assert response.json()["detail"] == f"Content was blocked, reason - it contains inappropriate content: {post_.block_reason}"

    async def test_create_post_with_invalid_data(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"title": "", "content": ""}  # Incorrect data

        # Trying to create a post with an empty title and content
        response = self.client.post("/posts/create/", json=payload, headers=headers)
        assert response.status_code == 422  # Unprocessable Entity
        assert response.json()["detail"] == "Title cannot be an empty string."

    async def test_list_posts_with_no_posts(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # Requesting a list of posts when there are no posts
        response = self.client.get("/posts/list", headers=headers)
        data = response.json()

        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_nonexistent_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # Trying to get a post that doesn't exist
        response = self.client.get("/posts/9999", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Post not found"

    async def test_update_post_not_authorized(self, post):
        # Trying to update a post without authorization
        update_payload = {"title": "Unauthorized Update", "content": "Unauthorized content"}
        response = self.client.put(f"/posts/update/{post.id}", json=update_payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    async def test_update_post_not_owner(self, post, another_user_token):
        headers = {"Authorization": f"Bearer {another_user_token}"}

        # Trying to update a post authored by another user
        update_payload = {"title": "Updated by Another User", "content": "Content"}
        response = self.client.put(f"/posts/update/{post.id}", json=update_payload, headers=headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to update this post"

    async def test_update_nonexistent_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        update_payload = {"title": "Nonexistent Post", "content": "Content"}

        # Trying to update a non-existent post
        response = self.client.put("/posts/update/9999", json=update_payload, headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Post not found"

    async def test_delete_post_not_owner(self, post, another_user_token):
        headers = {"Authorization": f"Bearer {another_user_token}"}

        # We are trying to delete a post authored by another user.
        response = self.client.delete(f"/posts/delete/{post.id}", headers=headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to delete this post"

    async def test_delete_nonexistent_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        # Trying to delete a non-existent post
        response = self.client.delete("/posts/delete/9999", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Post not found"

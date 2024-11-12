from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database.session import Base, get_db
from app.main import app
from app.models import User, Post, Comment
from jose import jwt

from settings import settings


DATABASE_URL = "sqlite+aiosqlite:///:memory:"


engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
def client(async_session) -> TestClient:
    def _get_db_override():
        return async_session

    app.dependency_overrides[get_db] = _get_db_override
    return TestClient(app)


@pytest.fixture
async def user(async_session: AsyncSession):
    user = User(username='testuser', email='test@email.com', hashed_password='testpass')
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def another_user(async_session: AsyncSession):
    another_user = User(username='anotheruser', email='anotheruser@email.com', hashed_password='anotherpass')
    async_session.add(another_user)
    await async_session.commit()
    await async_session.refresh(another_user)
    return another_user


def generate_jwt_token(user):
    token_payload = {
        'sub': user.username,
        'email': user.email,
        'hashed_password': user.hashed_password
    }
    return jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

@pytest.fixture
async def jwt_token(user):
    return generate_jwt_token(user)


@pytest.fixture
async def another_user_token(another_user):
    return generate_jwt_token(another_user)


@pytest.fixture
async def user_admin_token(user_admin):
    return generate_jwt_token(user_admin)


@pytest.fixture
def post(async_session, user):
    post = Post(id=1, author_id=user.id, title='This is title', content='This is text')
    async_session.add(post)
    async_session.commit()
    return post


@pytest.fixture
def blocked_post(async_session, user):
    post = Post(id=2, author_id=user.id, title='This is blocked title', content='This is fuck text', is_blocked=True)
    async_session.add(post)
    async_session.commit()
    return post


@pytest.fixture
async def comment(user, async_session, post):
    new_comment = Comment(
        id=1,
        author_id=user.id,
        content="Test comment text",
        post_id=post.id
    )
    async_session.add(new_comment)
    await async_session.commit()
    await async_session.refresh(new_comment)
    return new_comment


@pytest.fixture
async def user_admin(async_session):
    user = User(
        username="test_admin",
        email="test_admin@mail.com",
        hashed_password='adminpass',
        is_superuser=True
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def comments(async_session):
    today = datetime.now()
    comments = [
        Comment(content="Comment 1", created_at=today - timedelta(days=2), is_blocked=False),
        Comment(content="Comment 2", created_at=today - timedelta(days=1), is_blocked=True),
        Comment(content="Comment 3", created_at=today - timedelta(days=1), is_blocked=False),
        Comment(content="Comment 4", created_at=today, is_blocked=False),
    ]
    async_session.add_all(comments)
    await async_session.commit()
    return comments

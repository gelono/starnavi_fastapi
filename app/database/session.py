from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base, Session

async_connection = True

# Specify the database connection address
if async_connection:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/fastapi_posts"
else:
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost/fastapi_posts"

# Creating an engine for asynchronous connection
if async_connection:
    engine = create_async_engine(DATABASE_URL, echo=True)
else:
    engine = create_engine(DATABASE_URL, echo=True)


Base = declarative_base()

# Create a session factory to work with the database
if async_connection:
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
else:
    session_maker = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False
    )

# Method to get session
async def get_db():
    if async_connection:
        async with async_session_maker() as session:
            yield session
    else:
        with session_maker() as session:
            yield session

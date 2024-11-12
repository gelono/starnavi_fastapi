from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from datetime import datetime, timedelta
from app.database.session import get_db
from app.models import User
from app.schemas.schemas_users import RegisterSchema, Token, LoginSchema
from settings import settings


router = APIRouter(prefix="/users")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Generates a JWT access token with an optional expiration time.

    Args:
        data (dict): The payload data to encode into the token.
        expires_delta (timedelta | None): Optional expiration time for the token. If not provided,
                                          a default expiration time from settings is used.

    Returns:
        str: Encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/register", response_model=dict)
async def register(payload: RegisterSchema, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user by creating an account with a hashed password.

    Args:
        payload (RegisterSchema): Registration details including username, email, and password.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Success message upon successful registration.

    Raises:
        HTTPException: If the username or email already exists in the database.
    """
    # Creating a new user with password hashing via model method
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=User.hash_password(payload.password)
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email or username already exists")

    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    """
    Authenticates a user and generates access and refresh tokens upon successful login.

    Args:
        payload (LoginSchema): Login details including username and password.
        db (AsyncSession): Database session dependency.

    Returns:
        Token: JWT tokens (access and refresh) for authenticated sessions.

    Raises:
        HTTPException: If the username does not exist or the password is incorrect.
    """
    # Verifying user by name
    result = await db.execute(select(User).filter(User.username == payload.username))
    user = result.scalars().first()
    if not user or not user.verify_password(payload.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # JWT Token Generation
    access_token_expires = timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(days=7))

    return Token(access_token=access_token, refresh_token=refresh_token)

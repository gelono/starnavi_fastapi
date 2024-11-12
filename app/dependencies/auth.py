from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.session import get_db
from app.models import User
from settings import settings

# Specify the URL to receive the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Options for JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# Model for token data
class TokenData(BaseModel):
    username: str | None = None

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Retrieve the current authenticated user based on the provided JWT token.

    Args:
        token (str): The JWT access token obtained from the `oauth2_scheme` dependency.
        db (AsyncSession): Database session dependency for querying user data.

    Returns:
        User: The authenticated user instance if the token is valid and the user exists.

    Raises:
        HTTPException: If the token is invalid, expired, or does not contain a valid user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.username == token_data.username))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception

    return user

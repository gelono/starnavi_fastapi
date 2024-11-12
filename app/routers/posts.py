from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models import Post, User
from app.routers.tools import moderate_content, check_blocked_obj_content, create_new_post
from app.schemas.schemas_posts import PostOut, PostCreate, PostUpdate

router = APIRouter(prefix="/posts")


# Create Post
@router.post("/create", response_model=PostOut, status_code=201)
async def create_post(
        current_user: User = Depends(get_current_user),
        post_data: tuple[PostCreate, bool, str] = Depends(moderate_content),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new post.

    Args:
        current_user (User): The currently authenticated user, who will be set as the author of the post.
        post_data (tuple[PostCreate, bool, str]): A tuple containing:
            - The post creation data,
            - A boolean indicating if the content is blocked,
            - A string for the block reason, if applicable.
        db (AsyncSession): Database session dependency for executing the post creation.

    Returns:
        PostOut: The created post data serialized to the response model.

    Raises:
        HTTPException: If the post creation fails due to validation or integrity issues,
        appropriate HTTP status codes and messages are returned.
    """
    # Unpacking
    post, is_blocked, block_reason = post_data

    return await create_new_post(db, post, current_user, is_blocked, block_reason)


# List Posts
@router.get("/list", response_model=List[PostOut])
async def list_posts(db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of all unblocked posts.

    Args:
        db (AsyncSession): Database session dependency for executing the query.

    Returns:
        List[PostOut]: A list of posts that are not blocked, serialized to the response model.
    """
    query = select(Post).where(Post.is_blocked == False)
    result = await db.execute(query)
    posts = result.scalars().all()

    return posts


# Get Single Post
@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a single post by its ID.

    Args:
        post_id (int): The ID of the post to retrieve.
        db (AsyncSession): Database session dependency for executing the query.

    Returns:
        PostOut: The requested post data serialized to the response model.

    Raises:
        HTTPException: If the post is not found, a 404 HTTP exception is raised.
    """
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


# Update Post
@router.put("/update/{post_id}", response_model=PostOut)
async def update_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        post_data_tuple: tuple[PostUpdate, bool, str] = Depends(moderate_content),
        db: AsyncSession = Depends(get_db)
):
    """
    Update an existing post with new data.

    Args:
        post_id (int): The ID of the post to update.
        current_user (User): The currently authenticated user, used to verify author permissions.
        post_data_tuple (tuple[PostUpdate, bool, str]): Contains the updated post data, a blocked status flag, and a block reason.
        db (AsyncSession): Database session dependency for executing queries.

    Returns:
        PostOut: The updated post data serialized to the response model.

    Raises:
        HTTPException: If the post is not found, the user is not authorized, or there is a validation error, appropriate HTTP exceptions are raised.
    """
    # Fetch the post by id
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()

    # Check if post exists
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Check if the current user is the author of the post
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

    # Unpack post data tuple
    post_data, is_blocked, block_reason = post_data_tuple

    # Update post
    try:
        post.is_blocked = is_blocked
        post.block_reason = block_reason
        for key, value in post_data.dict(exclude_unset=True).items():
            setattr(post, key, value)

        db.add(post)
        await db.commit()
        await db.refresh(post)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return check_blocked_obj_content(post)


@router.delete("/delete/{post_id}", response_model=dict)
async def delete_post(
        post_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific post by its ID.

    Args:
        post_id (int): The ID of the post to delete.
        current_user (User): The currently authenticated user, used to verify permissions.
        db (AsyncSession): Database session dependency for executing queries.

    Returns:
        dict: A success message indicating that the post was deleted.

    Raises:
        HTTPException: If the post is not found, or the user is not authorized to delete it.
    """
    # Fetch the post by id
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()

    # Check if post exists
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Check if the current user is the author or an admin
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    # Delete the post
    await db.delete(post)
    await db.commit()

    return {"message": "Post deleted successfully"}

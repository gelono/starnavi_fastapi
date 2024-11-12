from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai_tools import moderate_content_with_ai
from app.models import Post, Comment, User
from app.schemas.schemas_comments import CommentCreate
from app.schemas.schemas_posts import PostCreate
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from app.tasks import send_auto_reply


async def moderate_content(data: PostCreate | CommentCreate):
    """Checking content for inappropriate content."""
    if hasattr(data, 'title'):
        is_blocked, block_reason = moderate_content_with_ai(data.title)
        if is_blocked:
            return data, is_blocked, block_reason

    is_blocked, block_reason = moderate_content_with_ai(data.content)

    return data, is_blocked, block_reason


def check_post_blocked(post: Post):
    """Check if a post is blocked and raise an HTTP 403 exception if it is."""
    if post.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a comment for blocked content."
        )


async def check_parent_comment_blocked(parent_id: int, db: AsyncSession):
    """Check if a parent comment is blocked and raise an exception if it is."""
    # Get parent comment
    result = await db.execute(select(Comment).filter(Comment.id == parent_id))
    parent_comment = result.scalars().first()

    # If comment wasn't found
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found."
        )

    # If comment is blocked
    if parent_comment.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a comment for blocked content."
        )


async def create_new_comment(db: AsyncSession, comment: CommentCreate, post_id: int, current_user: User,
         is_blocked: bool, block_reason: str):
    """
    Create a new comment for a specified post, setting block status and reason if applicable.

    Args:
        db (AsyncSession): Database session for executing queries.
        comment (CommentCreate): Data for creating the comment.
        post_id (int): ID of the post to associate with the comment.
        current_user (User): User creating the comment.
        is_blocked (bool): Indicates if the comment should be blocked.
        block_reason (str): Reason for blocking the comment, if applicable.

    Returns:
        Comment | JSONResponse: The created comment, or a JSON response if the content is blocked.

    Raises:
        HTTPException: If there is an error during comment creation.
    """
    # Create and add the new comment
    new_comment = Comment(
        content=comment.content,
        post_id=post_id,
        parent_id=comment.parent_id,
        author_id=current_user.id,
        is_blocked=is_blocked,
        block_reason=block_reason
    )
    try:
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return check_blocked_obj_content(new_comment)


def check_blocked_obj_content(obj: Post | Comment):
    """Check if an object (post or comment) is blocked and return an appropriate response."""
    # Check if content is blocked
    if obj.is_blocked:
        return JSONResponse(
            content={"detail": f"Content was blocked, reason - it contains inappropriate content: {obj.block_reason}"},
            status_code=400
        )

    return obj


async def create_new_post(db: AsyncSession, post: PostCreate, current_user: User, is_blocked: bool, block_reason: str):
    """
    Create a new post, setting block status and reason if necessary.

    Args:
        db (AsyncSession): Database session for executing queries.
        post (PostCreate): Data for creating the post.
        current_user (User): User creating the post.
        is_blocked (bool): Indicates if the post should be blocked.
        block_reason (str): Reason for blocking the post, if applicable.

    Returns:
        Post | JSONResponse: The created post, or a JSON response if the content is blocked.

    Raises:
        HTTPException: If there is an error during post creation.
    """
    # Post creating
    try:
        new_post = Post(**post.dict(), author_id=current_user.id, is_blocked=is_blocked, block_reason=block_reason)
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return check_blocked_obj_content(new_post)


def schedule_auto_reply_if_enabled(post: Post, comment: Comment):
    """Schedule an automatic reply to a comment if auto-reply is enabled on the post."""
    if post.auto_reply_enabled and not comment.is_blocked:
        send_auto_reply.apply_async(
            args=[post.id, comment.id],
            countdown=post.reply_delay * 10
        )

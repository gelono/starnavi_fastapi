from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Comment, Post, User
from app.routers.tools import moderate_content, check_post_blocked, check_parent_comment_blocked, create_new_comment, \
    check_blocked_obj_content, schedule_auto_reply_if_enabled
from app.schemas.schemas_comments import CommentCreate, CommentUpdate, CommentOut
from app.dependencies.auth import get_current_user
from app.database.session import get_db

router = APIRouter(prefix="/comments")


# Create Comment
@router.post("/{post_id}/create", response_model=CommentOut, status_code=201)
async def create_comment(
        post_id: int,
        current_user: User = Depends(get_current_user),
        comment_data: tuple[CommentCreate, bool, str] = Depends(moderate_content),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new comment for a given post, with optional moderation and automated reply functionality.

    Args:
        post_id (int): ID of the post to which the comment is being added.
        current_user (User): The user making the comment, retrieved from authentication.
        comment_data (tuple): A tuple containing the comment details, blocked status, and block reason,
                              obtained from the `moderate_content` dependency.
        db (AsyncSession): Database session dependency for performing operations on the post and comment.

    Returns:
        CommentOut: The created comment as an output model if successful.

    Raises:
        HTTPException: If the specified post is not found or if the content is blocked.
    """
    # Check if the post exists
    post = await db.execute(select(Post).where(Post.id == post_id))
    post = post.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Unpacking
    comment, is_blocked, block_reason = comment_data

    # Check blocked parent content
    check_post_blocked(post)
    if comment.parent_id:
        await check_parent_comment_blocked(comment.parent_id, db)

    # Comment create
    new_comment = await create_new_comment(db, comment, post_id, current_user, is_blocked, block_reason)

    # Auto_reply
    if not is_blocked:
        schedule_auto_reply_if_enabled(post, new_comment)

    return new_comment


# Get All Comments
@router.get("/list/{post_id}", response_model=list[CommentOut])
async def get_all_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve all comments for a specified post.

    Args:
        post_id (int): ID of the post for which comments are being retrieved.
        db (AsyncSession): Database session dependency for executing the query.

    Returns:
        list[CommentOut]: A list of comments associated with the specified post,
                          returned as output models.
    """
    result = await db.execute(select(Comment).where(Comment.post_id == post_id))
    comments = result.scalars().all()

    return comments


# Get Comment by ID
@router.get("/{comment_id}", response_model=CommentOut)
async def get_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific comment by its ID.

    Args:
        comment_id (int): ID of the comment to be retrieved.
        db (AsyncSession): Database session dependency for executing the query.

    Returns:
        CommentOut: The comment with the specified ID, returned as an output model.

    Raises:
        HTTPException: If the comment is not found, returns a 404 status code with
                       an error message.
    """
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    return comment


# Update Comment
@router.put("/{comment_id}", response_model=CommentOut)
async def update_comment(
        comment_id: int,
        current_user: User = Depends(get_current_user),
        updated_comment_data: tuple[CommentUpdate, bool, str] = Depends(moderate_content),
        db: AsyncSession = Depends(get_db)
):
    """
    Update the content of an existing comment by its ID.

    Args:
        comment_id (int): ID of the comment to be updated.
        current_user (User): The currently authenticated user, used to verify authorization.
        updated_comment_data (tuple[CommentUpdate, bool, str]): A tuple containing the new comment content,
            blocked status, and block reason after content moderation.
        db (AsyncSession): Database session dependency for executing the query and updates.

    Returns:
        CommentOut: The updated comment object, with possible modifications based on block status.

    Raises:
        HTTPException:
            - If the comment is not found, returns a 404 status code with an error message.
            - If the current user is not the author of the comment, returns a 403 status code
              indicating lack of authorization.
    """
    # Unpacking
    updated_comment, is_blocked, block_reason = updated_comment_data

    # Fetch the comment by id
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Check if the user is the author
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this comment")

    # Update the content
    comment.content = updated_comment.content
    comment.is_blocked = is_blocked
    comment.block_reason = block_reason
    await db.commit()
    await db.refresh(comment)

    return check_blocked_obj_content(comment)


# Delete Comment
@router.delete("/{comment_id}", response_model=dict)
async def delete_comment(
        comment_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Delete a comment by its ID.

    Args:
        comment_id (int): ID of the comment to be deleted.
        current_user (User): The currently authenticated user, used to verify authorization.
        db (AsyncSession): Database session dependency for executing the query and deletion.

    Returns:
        dict: A message indicating successful deletion of the comment.

    Raises:
        HTTPException:
            - If the comment is not found, returns a 404 status code with an error message.
            - If the current user is neither the author of the comment nor an admin, returns a 403 status
              code indicating lack of authorization.
    """
    # Fetch the comment by id
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Check if the user is the author or an admin
    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    # Delete the comment
    await db.delete(comment)
    await db.commit()

    return {"message": "Comment deleted successfully"}

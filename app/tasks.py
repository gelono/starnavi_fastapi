from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound
import asyncio

from app.ai_tools import generate_relevant_reply
from app.celery import app
from app.database.session import async_session_maker
from app.models import Post, Comment


@app.task
def send_auto_reply(post_id: int, comment_id: int):
    """
    Sends an automatic reply to a comment on a post by invoking an asynchronous task.

    This function acts as a Celery task and is used to send an automated response to a comment on a post.
    It runs asynchronously in the background to ensure that the reply is generated and saved to the database.

    Args:
        post_id (int): The ID of the post to which the comment is associated.
        comment_id (int): The ID of the comment for which the reply should be generated.

    Returns:
        None: The function does not return anything; it performs the task of sending the auto-reply.

    Notes:
        - This function schedules the asynchronous reply generation task using `asyncio.run`.
        - It requires the use of the `_send_auto_reply_async` function to handle the actual logic.
    """
    asyncio.run(_send_auto_reply_async(post_id, comment_id))

async def _send_auto_reply_async(post_id: int, comment_id: int):
    """
    Asynchronously generates and saves an auto-generated reply to a comment on a post.

    This function retrieves the post and comment from the database, generates a relevant response using AI,
    and then creates a new comment as a reply to the original comment. It commits the new reply comment to
    the database.

    Args:
        post_id (int): The ID of the post associated with the comment.
        comment_id (int): The ID of the comment for which the reply should be generated.

    Returns:
        None: This function does not return anything; it performs database operations to create a reply comment.

    Raises:
        NoResultFound: If either the post or comment is not found in the database.

    Notes:
        - This function depends on the `generate_relevant_reply` function to create a meaningful reply based
          on the content of the post and the comment.
        - The function handles the database operations asynchronously using `async_session_maker` and
          ensures that any errors during the process (such as missing post or comment) are handled gracefully.
    """
    async with async_session_maker() as db:
        try:
            # Receiving a post and comment
            post = (await db.execute(select(Post).filter(Post.id == post_id))).scalar_one()
            comment = (await db.execute(select(Comment).filter(Comment.id == comment_id))).scalar_one()

            # Generating a response
            reply_content = generate_relevant_reply(post, comment)

            # Creating a reply comment
            reply_comment = Comment(
                author_id=post.author_id,
                post_id=post.id,
                content=reply_content,
                parent_id=comment.id
            )
            db.add(reply_comment)
            await db.commit()
            print(f"Auto reply has been created: {reply_comment.content}")

        except NoResultFound:
            await db.rollback()
            print("Post or Comment not found")

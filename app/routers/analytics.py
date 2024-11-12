from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import Dict

from app.dependencies.auth import get_current_user
from app.models import Comment, User
from app.database.session import get_db

router = APIRouter(prefix="/analytics")


def validate_dates(date_from: str, date_to: str):
    """Validate date parameters and parse them to datetime objects."""
    try:
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="date_from must be earlier than date_to.")

    return start_date, end_date


def get_date_range(start_date: datetime, end_date: datetime):
    """Generate a list of dates from start_date to end_date."""
    return [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]


async def get_comments_data(start_date: datetime, end_date: datetime, db: AsyncSession):
    """Retrieve aggregated comments data for the specified date range."""
    results = await db.execute(
        select(
            func.date(Comment.created_at).label("created_date"),
            func.count(Comment.id).label("total_comments"),
            func.count(case((Comment.is_blocked == True, 1))).label("blocked_comments")
        )
        .where(func.date(Comment.created_at).between(start_date, end_date))
        .group_by("created_date")
        .order_by("created_date")
    )
    return results.all()


def build_analytics_dict(date_range, comments_data):
    """Build a dictionary to store the analytics data."""
    analytics = {date.strftime("%Y-%m-%d"): {"total_comments": 0, "blocked_comments": 0} for date in date_range}

    for entry in comments_data:
        if isinstance(entry.created_date, str):
            date = entry.created_date
        else:
            date = entry.created_date.strftime("%Y-%m-%d")
        analytics[date]["total_comments"] = entry.total_comments
        analytics[date]["blocked_comments"] = entry.blocked_comments

    return analytics


@router.get("/comments-daily-breakdown", response_model=Dict[str, Dict[str, int]])
async def comments_daily_breakdown(
        current_user: User = Depends(get_current_user),
        date_from: str = Query(..., description="Start date for analysis in YYYY-MM-DD format"),
        date_to: str = Query(..., description="End date for analysis in YYYY-MM-DD format"),
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a daily breakdown of comments within a specified date range.

    This endpoint accepts two query parameters, `date_from` and `date_to`,
    representing the start and end dates for the analysis. It validates these
    dates and retrieves comments created within the specified range.
    The response contains a JSON object with daily statistics.
    """
    # Check if the user is the author or an admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to retrieve this info")

    # Validate dates
    start_date, end_date = validate_dates(date_from, date_to)

    # Generate date range
    date_range = get_date_range(start_date, end_date)

    # Retrieve and aggregate comments data
    comments_data = await get_comments_data(start_date, end_date, db)

    # Build analytics dictionary
    analytics = build_analytics_dict(date_range, comments_data)

    return analytics

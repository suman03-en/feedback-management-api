"""
Business logic utilities for feedback management system.
This module handles core business operations separate from HTTP views.
"""

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from guardian.shortcuts import get_objects_for_user
from .models import Feedback, FeedbackResponse, Category


def get_user_feedbacks(user, with_superuser=True):
    """
    Retrieve all feedbacks accessible to a user based on permissions.

    Args:
        user: Django User instance
        with_superuser: Include superuser permissions (default: True)

    Returns:
        QuerySet of accessible Feedback objects
    """
    return get_objects_for_user(
        user,
        "feedback.view_feedback",
        klass=Feedback,
        with_superuser=with_superuser,
        accept_global_perms=False,
    )


def calculate_status_breakdown(feedbacks):
    """
    Calculate feedback distribution by status.

    Args:
        feedbacks: QuerySet of Feedback objects

    Returns:
        Dictionary with status breakdown
    """
    return {
        "pending": feedbacks.filter(status="pending").count(),
        "reviewed": feedbacks.filter(status="reviewed").count(),
        "resolved": feedbacks.filter(status="resolved").count(),
        "stats": list(
            feedbacks.values("status").annotate(count=Count("id")).order_by("status")
        ),
    }


def calculate_priority_breakdown(feedbacks):
    """
    Calculate feedback distribution by priority.

    Args:
        feedbacks: QuerySet of Feedback objects

    Returns:
        Dictionary with priority breakdown
    """
    return {
        "low": feedbacks.filter(priority="low").count(),
        "medium": feedbacks.filter(priority="medium").count(),
        "high": feedbacks.filter(priority="high").count(),
        "stats": list(
            feedbacks.values("priority")
            .annotate(count=Count("id"))
            .order_by("priority")
        ),
    }


def calculate_category_breakdown(feedbacks, limit=5):
    """
    Calculate top categories by feedback count.

    Args:
        feedbacks: QuerySet of Feedback objects
        limit: Maximum number of categories to return

    Returns:
        List of category statistics
    """
    return list(
        feedbacks.values("category__name")
        .annotate(count=Count("id"))
        .filter(category__isnull=False)
        .order_by("-count")[:limit]
    )


def calculate_department_breakdown(feedbacks):
    """
    Calculate feedback distribution by department.

    Args:
        feedbacks: QuerySet of Feedback objects

    Returns:
        List of department statistics
    """
    return list(
        feedbacks.prefetch_related("to_departments")
        .values("to_departments__name")
        .annotate(count=Count("id", distinct=True))
        .filter(to_departments__isnull=False)
        .order_by("-count")
    )


def calculate_response_statistics(feedbacks):
    """
    Calculate response-related statistics.

    Args:
        feedbacks: QuerySet of Feedback objects

    Returns:
        Dictionary with response statistics
    """
    total_feedback = feedbacks.count()
    total_responses = FeedbackResponse.objects.filter(feedback__in=feedbacks).count()
    resolved_count = feedbacks.filter(status="resolved").count()

    return {
        "total_responses": total_responses,
        "resolved_count": resolved_count,
        "unresolved_count": total_feedback - resolved_count,
        "response_rate": round((total_responses / max(total_feedback, 1)) * 100, 1),
    }


def calculate_recent_activity(feedbacks, days=7):
    """
    Calculate recent feedback activity.

    Args:
        feedbacks: QuerySet of Feedback objects
        days: Number of days to look back

    Returns:
        Dictionary with recent activity data
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    recent_count = feedbacks.filter(created_at__gte=cutoff_date).count()

    # Calculate feedback per day
    feedback_per_day = []
    for i in range(days - 1, -1, -1):
        date = timezone.now() - timedelta(days=i)
        count = feedbacks.filter(created_at__date=date.date()).count()
        feedback_per_day.append({"date": date.strftime("%a"), "count": count})

    return {
        "recent_count": recent_count,
        "feedback_per_day": feedback_per_day,
    }


def calculate_average_response_time(feedbacks, sample_size=20):
    """
    Calculate average response time from feedback to first response.

    Args:
        feedbacks: QuerySet of Feedback objects
        sample_size: Number of feedbacks to sample for calculation

    Returns:
        Average response time in hours
    """
    feedbacks_with_responses = feedbacks.filter(responses__isnull=False).distinct()

    if not feedbacks_with_responses.exists():
        return 0

    total_time = timedelta()
    count = 0

    for feedback in feedbacks_with_responses[:sample_size]:
        response = feedback.responses.first()
        if response:
            delta = response.created_at - feedback.created_at
            total_time += delta
            count += 1

    if count == 0:
        return 0

    avg_hours = (total_time.total_seconds() / count) / 3600
    return round(avg_hours, 1)


def get_analytics_data(user):
    """
    Comprehensive function to gather all analytics data for a user.

    Args:
        user: Django User instance

    Returns:
        Dictionary with complete analytics data
    """
    feedbacks = get_user_feedbacks(user)
    total_feedback = feedbacks.count()

    analytics_data = {
        "total_feedback": total_feedback,
        "status": calculate_status_breakdown(feedbacks),
        "priority": calculate_priority_breakdown(feedbacks),
        "categories": calculate_category_breakdown(feedbacks),
        "departments": calculate_department_breakdown(feedbacks),
        "responses": calculate_response_statistics(feedbacks),
        "recent_activity": calculate_recent_activity(feedbacks),
        "avg_response_time": calculate_average_response_time(feedbacks),
    }

    return analytics_data

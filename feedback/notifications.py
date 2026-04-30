"""
Notification service for feedback management system.
Handles email notifications and in-app notifications for feedback events.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from typing import List, Optional
import logging

from .models import Feedback, FeedbackResponse, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class to handle all notification logic."""

    @staticmethod
    def create_notification(
        recipient,
        notification_type: str,
        title: str,
        message: str,
        feedback: Optional[Feedback] = None,
        response: Optional[FeedbackResponse] = None,
        send_email: bool = False,
    ) -> Notification:

        """
        Create an in-app notification and optionally send email.

        Args:
            recipient: User to notify
            notification_type: Type of notification (feedback_submitted, assigned, etc.)
            title: Notification title
            message: Notification message
            feedback: Optional related feedback object
            response: Optional related response object
            send_email: Whether to send email notification

        Returns:
            Created Notification object
        """
        with transaction.atomic():
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                feedback=feedback,
                response=response,
            )
            # Push via Channels if available
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{recipient.id}",
                        {
                            "type": "notify",
                            "notification": {
                                "id": notification.id,
                                "type": notification.notification_type,
                                "title": notification.title,
                                "message": notification.message,
                                "created_at": notification.created_at.isoformat(),
                                "is_read": notification.is_read,
                            },
                        },
                    )
            except Exception:
                # Channels not configured – ignore, fallback to polling/SSE
                pass

            if send_email:
                NotificationService.send_email_notification(
                    recipient=recipient,
                    subject=title,
                    message=message,
                    notification_type=notification_type,
                )

            return notification


    @staticmethod
    def send_email_notification(
        recipient,
        subject: str,
        message: str,
        notification_type: str,
    ) -> bool:
        """
        Send email notification to a user.

        Args:
            recipient: User to email
            subject: Email subject
            message: Email body
            notification_type: Type of notification for logging

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not recipient.email:
            logger.warning(f"Cannot send {notification_type} email: user {recipient} has no email")
            return False

        try:
            send_mail(
                subject=f"[FeedbackFlow] {subject}",
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@feedbackflow.com'),
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            logger.info(f"Sent {notification_type} email to {recipient.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send {notification_type} email to {recipient.email}: {str(e)}")
            return False

    @staticmethod
    def notify_feedback_submitted(feedback: Feedback) -> List[Notification]:
        """
        Notify when new feedback is submitted.
        - Notify creator (confirmation)
        - Notify department managers
        """
        notifications = []

        # Notify creator
        title = "Feedback Submitted Successfully"
        message = (
            f"Your feedback '{feedback.title or 'Untitled'}' has been submitted successfully. "
            f"We'll review it and get back to you soon.\n\n"
            f"Status: {feedback.get_status_display()}\n"
            f"Priority: {feedback.get_priority_display()}\n"
            f"Submitted: {feedback.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

        notif = NotificationService.create_notification(
            recipient=feedback.creator,
            notification_type="feedback_submitted",
            title=title,
            message=message,
            feedback=feedback,
        )
        notifications.append(notif)

        # Notify department managers
        for department in feedback.to_departments.all():
            for manager in department.managers.all():
                if manager != feedback.creator:
                    title = f"New Feedback Assigned to {department.name}"
                    message = (
                        f"A new feedback item has been routed to your department ({department.name}).\n\n"
                        f"Title: {feedback.title or 'Untitled'}\n"
                        f"From: {feedback.creator.name}\n"
                        f"Priority: {feedback.get_priority_display()}\n"
                        f"Status: {feedback.get_status_display()}\n\n"
                        f"Please review and assign to a responder."
                    )

                    notif = NotificationService.create_notification(
                        recipient=manager,
                        notification_type="feedback_submitted",
                        title=title,
                        message=message,
                        feedback=feedback,
                    )
                    notifications.append(notif)

        return notifications

    @staticmethod
    def notify_feedback_assigned(feedback: Feedback, responder) -> Notification:
        """
        Notify when feedback is assigned to a responder.
        """
        title = f"Feedback Assigned to You"
        message = (
            f"You have been assigned to handle the following feedback:\n\n"
            f"Title: {feedback.title or 'Untitled'}\n"
            f"From: {feedback.creator.name}\n"
            f"Priority: {feedback.get_priority_display()}\n"
            f"Status: {feedback.get_status_display()}\n"
            f"Submitted: {feedback.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Please review and respond as soon as possible."
        )

        return NotificationService.create_notification(
            recipient=responder,
            notification_type="feedback_assigned",
            title=title,
            message=message,
            feedback=feedback,
        )

    @staticmethod
    def notify_response_created(response: FeedbackResponse) -> List[Notification]:
        """
        Notify when a response is created.
        - Notify feedback creator
        - Notify other responders on the feedback
        """
        notifications = []
        feedback = response.feedback

        # Notify creator (if not the responder)
        responders = list(response.responder.all())
        responder_names = ", ".join([r.name for r in responders])

        if feedback.creator not in responders:
            title = f"New Response on Your Feedback"
            message = (
                f"Your feedback '{feedback.title or 'Untitled'}' has received a response.\n\n"
                f"Response from: {responder_names}\n"
                f"Status updated to: {feedback.get_status_display()}\n\n"
                f"You can view the full response by logging into the system."
            )

            notif = NotificationService.create_notification(
                recipient=feedback.creator,
                notification_type="response_created",
                title=title,
                message=message,
                feedback=feedback,
                response=response,
            )
            notifications.append(notif)

        # Notify other department managers (optional - for awareness)
        for department in feedback.to_departments.all():
            for manager in department.managers.all():
                if manager not in responders and manager != feedback.creator:
                    title = f"Response Added to Feedback"
                    message = (
                        f"A response has been added to feedback in your department.\n\n"
                        f"Title: {feedback.title or 'Untitled'}\n"
                        f"Responded by: {responder_names}\n"
                        f"Status: {feedback.get_status_display()}"
                    )

                    notif = NotificationService.create_notification(
                        recipient=manager,
                        notification_type="response_created",
                        title=title,
                        message=message,
                        feedback=feedback,
                        response=response,
                    )
                    notifications.append(notif)

        return notifications

    @staticmethod
    def notify_feedback_resolved(feedback: Feedback, resolver) -> List[Notification]:
        """
        Notify when feedback is resolved.
        - Notify creator
        - Notify department managers
        """
        notifications = []

        # Notify creator
        title = f"Feedback Resolved"
        message = (
            f"Your feedback '{feedback.title or 'Untitled'}' has been resolved.\n\n"
            f"Resolved by: {resolver.name}\n"
            f"Resolved at: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"We hope the resolution meets your expectations. "
            f"You can view the full resolution by logging into the system."
        )

        notif = NotificationService.create_notification(
            recipient=feedback.creator,
            notification_type="feedback_resolved",
            title=title,
            message=message,
            feedback=feedback,
        )
        notifications.append(notif)

        # Notify department managers
        for department in feedback.to_departments.all():
            for manager in department.managers.all():
                if manager != resolver:
                    title = f"Feedback Resolved in {department.name}"
                    message = (
                        f"A feedback item in your department has been resolved.\n\n"
                        f"Title: {feedback.title or 'Untitled'}\n"
                        f"Resolved by: {resolver.name}\n"
                        f"Status: {feedback.get_status_display()}"
                    )

                    notif = NotificationService.create_notification(
                        recipient=manager,
                        notification_type="feedback_resolved",
                        title=title,
                        message=message,
                        feedback=feedback,
                    )
                    notifications.append(notif)

        return notifications

    @staticmethod
    def notify_escalation(feedback: Feedback, reason: str = "") -> List[Notification]:
        """
        Notify when feedback is escalated (overdue, high priority, etc.).
        """
        notifications = []

        # Notify feedback admin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(is_superuser=True) | User.objects.filter(groups__name="Feedback Admin")

        for admin in admins.distinct():
            title = f"Feedback Escalation Alert"
            message = (
                f"A feedback item requires immediate attention.\n\n"
                f"Title: {feedback.title or 'Untitled'}\n"
                f"From: {feedback.creator.name}\n"
                f"Priority: {feedback.get_priority_display()}\n"
                f"Status: {feedback.get_status_display()}\n"
                f"Submitted: {feedback.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"Reason: {reason or 'Requires attention'}\n\n"
                f"Please review and take appropriate action."
            )

            notif = NotificationService.create_notification(
                recipient=admin,
                notification_type="escalation",
                title=title,
                message=message,
                feedback=feedback,
            )
            notifications.append(notif)

        return notifications

    @staticmethod
    def mark_as_read(notification_id: int, user) -> bool:
        """
        Mark a notification as read for a user.

        Args:
            notification_id: ID of the notification
            user: User marking the notification as read

        Returns:
            True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user) -> int:
        """
        Mark all unread notifications as read for a user.

        Args:
            user: User to mark notifications for

        Returns:
            Number of notifications marked as read
        """
        now = timezone.now()
        count = Notification.objects.filter(
            recipient=user, is_read=False
        ).update(is_read=True, read_at=now)
        return count

    @staticmethod
    def get_unread_count(user) -> int:
        """
        Get the count of unread notifications for a user.
        """
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def get_recent_notifications(user, limit: int = 10):
        """
        Get recent notifications for a user.
        """
        return Notification.objects.filter(
            recipient=user
        ).select_related("feedback", "response").order_by("-created_at")[:limit]

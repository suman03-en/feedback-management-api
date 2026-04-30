"""
Signal handlers that trigger notification creation for feedback related events.
"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings

from .models import Feedback, FeedbackResponse, FeedbackResponderRecord, Notification
from .notifications import NotificationService

# ---------------------------------------------------------------------------
# Feedback creation
# ---------------------------------------------------------------------------
@receiver(post_save, sender=Feedback)
def feedback_created_handler(sender, instance, created, **kwargs):
    """Create notifications when a new Feedback is submitted.
    The service also notifies department managers.
    """
    if created:
        NotificationService.notify_feedback_submitted(instance)

# ---------------------------------------------------------------------------
# Feedback assignment to responder (many‑to‑many through FeedbackResponderRecord)
# ---------------------------------------------------------------------------
@receiver(post_save, sender=FeedbackResponderRecord)
def feedback_assigned_handler(sender, instance, created, **kwargs):
    """Notify a responder when they are assigned to a feedback.
    ``FeedbackResponderRecord`` is created by ``Feedback.assign_to_responder``.
    """
    if created:
        NotificationService.notify_feedback_assigned(
            feedback=instance.feedback,
            responder=instance.responder,
        )

# ---------------------------------------------------------------------------
# Response creation – many‑to‑many responder field may be set after save.
# We use ``m2m_changed`` to fire after responders are added.
# ---------------------------------------------------------------------------
@receiver(post_save, sender=FeedbackResponse)
def feedback_response_created_handler(sender, instance, created, **kwargs):
    """When a ``FeedbackResponse`` object is first saved, the responders may not yet be attached.
    The ``m2m_changed`` signal will handle the final notification once the relation is set.
    """
    # No action here – wait for m2m_changed where ``post_add`` signals responders set.
    pass

@receiver(m2m_changed, sender=FeedbackResponse.responder.through)
def feedback_response_responder_added(sender, instance, action, reverse, pk_set, **kwargs):
    """After responders are attached to a ``FeedbackResponse`` we fire notifications.
    ``instance`` is the ``FeedbackResponse`` object.
    """
    if action == "post_add":
        # Ensure the response is persisted before notifying.
        NotificationService.notify_response_created(instance)

# ---------------------------------------------------------------------------
# Feedback resolution – assumed to be indicated by changing ``status`` to "resolved".
# ---------------------------------------------------------------------------
@receiver(post_save, sender=Feedback)
def feedback_status_change_handler(sender, instance, **kwargs):
    """Detect transition to ``resolved`` status and send notifications.
    We compare the instance's current status with the value stored in the DB before the save.
    """
    if not instance.pk:
        return  # New object – handled by ``feedback_created_handler``
    # Fetch previous status from DB (avoid extra query if unchanged)
    try:
        previous = sender.objects.only("status").get(pk=instance.pk)
    except sender.DoesNotExist:
        previous = None
    if previous and previous.status != instance.status and instance.status == "resolved":
        # Resolve performed by the user who made the request; we cannot get the user here,
        # so we use ``instance.creator`` as a fallback – the view that changes status will
        # pass the resolver via ``instance._resolver`` if set.
        resolver = getattr(instance, "_resolver", instance.creator)
        NotificationService.notify_feedback_resolved(instance, resolver)

# ---------------------------------------------------------------------------
# Escalation – a custom signal could be emitted elsewhere; here we provide a helper.
# ---------------------------------------------------------------------------
from django.dispatch import Signal
escalation_signal = Signal()

@receiver(escalation_signal)
def feedback_escalation_handler(sender, feedback, reason="", **kwargs):
    NotificationService.notify_escalation(feedback, reason)


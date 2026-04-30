"""Template tags for notification dropdown.
Usage in any template (e.g., base.html):
{% load notification_tags %}
{% notification_dropdown %}
{% unread_notification_count as unread_count %}
"""

from django import template
from django.utils import timezone
from ..models import Notification
import json

register = template.Library()

@register.inclusion_tag('feedback/notifications_dropdown.html', takes_context=True)
def notification_dropdown(context):
    user = context['request'].user
    if not user.is_authenticated:
        return {'unread_count': 0, 'recent_notifications': []}
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    recent_notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:10]
    # Ensure CSRF token for AJAX
    context.update({
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'csrf_token': context.get('csrf_token'),
    })
    return context

@register.simple_tag(takes_context=True)
def unread_notification_count(context):
    user = context.get('request').user
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, is_read=False).count()


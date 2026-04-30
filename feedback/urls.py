from django.urls import path
from .views import (
    FeedbackListView,
    FeedbackDetailView,
    FeedbackCreateView,
    FeedbackDeleteView,
    FeedbackResponseCreateView,
    FeedbackResponseEditView,
    FeedbackResponseDeleteView,
    FeedbackResponseListView,
    FeedbackResponseAssignView,
    DepartmentCreateView,
    AnalyticsView,
    CategoryCreateView,
    NotificationListView,
    MarkNotificationReadView,
    NotificationSSEView,
)

urlpatterns = [
    path("", FeedbackListView.as_view(), name="feedback_list"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("<uuid:pk>/", FeedbackDetailView.as_view(), name="feedback_detail"),
    path("create/", FeedbackCreateView.as_view(), name="feedback_create"),
    path("<uuid:pk>/delete/", FeedbackDeleteView.as_view(), name="feedback_delete"),
    # feedback reponse urls
    path(
        "<uuid:pk>/response/create/",
        FeedbackResponseCreateView.as_view(),
        name="feedback_response_create",
    ),
    path(
        "response/<uuid:pk>/edit/",
        FeedbackResponseEditView.as_view(),
        name="feedback_response_edit",
    ),
    path(
        "<uuid:pk>/responses/",
        FeedbackResponseListView.as_view(),
        name="feedback_response_list",
    ),
    path(
        "response/<uuid:pk>/delete/",
        FeedbackResponseDeleteView.as_view(),
        name="feedback_response_delete",
    ),
    path(
        "<uuid:pk>/assign/",
        FeedbackResponseAssignView.as_view(),
        name="feedback_responder_assign",
    ),
    # additional url for department create view
    path(
        "department/create/",
        DepartmentCreateView.as_view(),
        name="department_create",
    ),
    path(
        "category/create/",
        CategoryCreateView.as_view(),
        name="category_create",
    ),
    # notification URLs
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/mark/<int:pk>/', MarkNotificationReadView.as_view(), name='notification_mark_read'),
    path('notifications/sse/', NotificationSSEView.as_view(), name='notifications_sse'),


]

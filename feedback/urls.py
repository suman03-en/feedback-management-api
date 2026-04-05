from django.urls import path
from .views import (
    FeedbackListView,
    FeedbackDetailView,
    FeedbackCreateView,
    FeedbackDeleteView,
    FeedbackResponseCreateView,
    FeedbackResponseListView,
)

urlpatterns = [
    path("", FeedbackListView.as_view(), name="feedback_list"),
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
        "<uuid:pk>/responses/",
        FeedbackResponseListView.as_view(),
        name="feedback_response_list",
    ),
]

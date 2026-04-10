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
    FeedbackResponseAssignView
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

]

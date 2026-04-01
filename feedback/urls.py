from django.urls import path
from .views import FeedbackListView, FeedbackDetailView, FeedbackCreateView

urlpatterns = [
    path('', FeedbackListView.as_view(), name='feedback_list'),
    path('<uuid:pk>/', FeedbackDetailView.as_view(), name='feedback_detail'),
    path('create/', FeedbackCreateView.as_view(), name='feedback_create'),
]
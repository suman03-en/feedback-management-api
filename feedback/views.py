from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.urls import reverse_lazy
from .models import Feedback
from .forms import FeedbackForm
from datetime import datetime


class FeedbackListView(ListView):
    model = Feedback
    template_name = "feedback/feedback_list.html"
    context_object_name = "feedbacks"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = "Suman"
        return context

    def get_queryset(self):
        return Feedback.objects.order_by("-created_at")


class FeedbackDetailView(DetailView):
    model = Feedback
    template_name = "feedback/feedback_detail.html"
    context_object_name = "feedback"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class FeedbackCreateView(CreateView):
    model = Feedback
    template_name = "feedback/feedback_form.html"
    form_class = FeedbackForm

class FeedbackDeleteView(DeleteView):
    model = Feedback
    template_name = "feedback/feedback_confirm_delete.html"
    success_url = reverse_lazy('feedback_list')
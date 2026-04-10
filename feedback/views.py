from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from .models import (
    Feedback,
    FeedbackResponse,
    FeedbackResponderRecord,
)
from .forms import (
    FeedbackForm,
    FeedbackResponseForm,
    FeedbackResponseAssignForm,
)
from .mixins import FeedbackMixin


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
    success_url = reverse_lazy("feedback_list")


class FeedbackResponseCreateView(LoginRequiredMixin, CreateView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_form.html"
    form_class = FeedbackResponseForm
    success_url = reverse_lazy("feedback_list")

    def get_feedback(self):
        """Helper method to retrieve the associated feedback based on the URL parameter."""
        return Feedback.objects.get(id=self.kwargs.get("pk"))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.feedback = self.get_feedback()
        is_assigned = FeedbackResponderRecord.objects.filter(
            feedback=self.feedback,
            responder=request.user,
        ).exists()
        if not is_assigned:
            raise PermissionDenied("You are not assigned to this feedback.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback"] = self.feedback
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.feedback
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["responder"].queryset = (
            form.fields["responder"]
            .queryset.filter(responder_records__feedback=self.feedback)
            .distinct()
        )
        return form


class FeedbackResponseListView(FeedbackMixin, ListView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_list.html"
    context_object_name = "responses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback"] = self.get_feedback()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.get_feedback()
        return kwargs

    def get_queryset(self):
        feedback_id = self.kwargs.get("pk")
        return FeedbackResponse.objects.filter(feedback__id=feedback_id).order_by(
            "-created_at"
        )


class FeedbackResponseEditView(UpdateView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_form.html"
    form_class = FeedbackResponseForm
    pk_url_kwarg = "pk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.object.feedback
        return kwargs

    def get_success_url(self):
        return reverse("feedback_response_list", kwargs={"pk": self.object.feedback.pk})


class FeedbackResponseDeleteView(DeleteView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_confirm_delete.html"
    success_url = reverse_lazy("feedback_list")


class FeedbackResponseAssignView(View):
    form_class = FeedbackResponseAssignForm
    template_name = "feedback/feedback_assign_form.html"

    def get(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        form = self.form_class()
        return render(
            request,
            self.template_name,
            {"form": form, "feedback": feedback},
        )

    def post(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        form = self.form_class(request.POST)
        if form.is_valid():
            responder = form.cleaned_data["responder"]
            feedback.assign_to_responder(responder)
            return redirect("feedback_response_list", pk=feedback.pk)

        return render(
            request,
            self.template_name,
            {"form": form, "feedback": feedback},
        )

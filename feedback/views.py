from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.urls import reverse_lazy, reverse

from guardian.shortcuts import get_objects_for_user, assign_perm # type: ignore

from .models import (
    Feedback,
    FeedbackResponse,
    FeedbackResponderRecord,
    Department,
)
from .forms import (
    FeedbackForm,
    FeedbackResponseForm,
    FeedbackResponseAssignForm,
)
from .mixins import FeedbackMixin
from .permissions import (
    assign_department_permissions,
    assign_owner_perms,
    assign_permission_creator_of_feedback_to_response,
)   


class FeedbackListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/feedback_list.html"
    context_object_name = "feedbacks"
    permission_required = ["feedback.view_feedback"]

    def get_queryset(self):
        return get_objects_for_user(
            self.request.user,
            "feedback.view_feedback",
            klass=Feedback,
            with_superuser=True,
            accept_global_perms=False,
        )
    
    def get(self, request, *args, **kwargs):
        if not request.user.has_perm("feedback.view_feedback"):
            raise PermissionDenied("You do not have permission to view feedback.")

        return super().get(request, *args, **kwargs)
    


class FeedbackDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Feedback
    template_name = "feedback/feedback_detail.html"
    context_object_name = "feedback"
    permission_required = ["feedback.view_feedback"]

    def get_object(self, queryset=None): 
        obj = super().get_object(queryset)
        if not self.request.user.has_perm("feedback.view_feedback", obj):
            raise PermissionDenied
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #if user is superuser or has assign permission, show the assign form
        context["can_assign_feedback"] = self.request.user.has_perm("feedback.assign_feedback")
        if context["can_assign_feedback"]:
            context["assign_form"] = FeedbackResponseAssignForm()
        return context


class FeedbackCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Feedback
    template_name = "feedback/feedback_form.html"
    form_class = FeedbackForm
    permission_required = ["feedback.add_feedback"]

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.email = self.request.user.email
        response = super().form_valid(form)

        # Assign [view, change, delete] permissions to the creator for this feedback
        assign_owner_perms(self.request.user, self.object)

        # Assign view permissions to the managers and auditors of the routed departments
        assign_department_permissions(feedback=self.object)

        return response
    
        
class FeedbackDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Feedback
    template_name = "feedback/feedback_confirm_delete.html"
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.delete_feedback"]


    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not self.request.user.has_perm("feedback.delete_feedback", obj):
            raise PermissionDenied

        return obj
    

class FeedbackResponseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_form.html"
    form_class = FeedbackResponseForm
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.add_feedbackresponse"]

    feedback = None

    def get_feedback(self):
        """Helper method to retrieve the associated feedback based on the URL parameter."""
        try:
            self.feedback = Feedback.objects.get(id=self.kwargs.get("pk"))
        except Feedback.DoesNotExist:
            raise Http404("Feedback not found")

    def dispatch(self, request, *args, **kwargs):
        #load the feedback object before processing the request, so it's available for permission checks and form initialization
        self.get_feedback()
        return super().dispatch(request, *args, **kwargs)  

    def get_context_data(self, **kwargs):
        # Context for template, include the feedback object for display
        context = super().get_context_data(**kwargs)
        context["feedback"] = self.feedback
        return context

    def get_form_kwargs(self):
        # Pass context to form
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.feedback
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.responder.add(self.request.user)

        assign_owner_perms(self.request.user, self.object)
        assign_department_permissions(response==self.object)
        assign_permission_creator_of_feedback_to_response(self.object, self.feedback)

        return response
    

class FeedbackResponseListView(LoginRequiredMixin, PermissionRequiredMixin, FeedbackMixin, ListView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_list.html"
    context_object_name = "responses"
    permission_required = ["feedback.view_feedbackresponse"]

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


class FeedbackResponseEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_form.html"
    form_class = FeedbackResponseForm
    pk_url_kwarg = "pk"
    permission_required = ["feedback.change_feedbackresponse"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.object.feedback
        return kwargs

    def get_success_url(self):
        return reverse("feedback_response_list", kwargs={"pk": self.object.feedback.pk})


class FeedbackResponseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_confirm_delete.html"
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.delete_feedbackresponse"]


class FeedbackResponseAssignView(LoginRequiredMixin, PermissionRequiredMixin, View):
    form_class = FeedbackResponseAssignForm
    template_name = "feedback/feedback_assign_form.html"
    permission_required = ["feedback.assign_feedback"]

    def _get_feedback(self):
        self.feedback = get_object_or_404(Feedback, pk=self.kwargs.get("pk"))

    def dispatch(self, request, *args, **kwargs):
        # Ensure the feedback is loaded before checking permissions
        self._get_feedback()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        form = self.form_class(feedback=self.feedback, assigner=request.user)
        return render(
            request,
            self.template_name,
            {"form": form, "feedback": self.feedback},
        )

    def post(self, request, pk):
        form = self.form_class(
            request.POST,
        )
        if form.is_valid():
            responder = form.cleaned_data["responder"]
            try:
                self.feedback.assign_to_responder(responder)
            except ValueError as e:
                form.add_error(None, str(e))
                return render(
                    request,
                    self.template_name,
                    {"form": form, "feedback": self.feedback},
                )
            return redirect("feedback_response_list", pk=self.feedback.pk)

        return render(
            request,
            self.template_name,
            {"form": form, "feedback": self.feedback},
        )


# additinal view to add the department , only allowed to superuser and staff user
class DepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Department
    template_name = "feedback/department_form.html"
    fields = ["name", "description"]
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.add_department"]

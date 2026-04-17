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
    get_feedback_queryset_for_user, sync_feedback_view_permissions,
    assign_owner_perms,
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
        self.assign_department_permissions(self.object)

        return response
    
    def assign_department_permissions(self, feedback):
        # get all routed departments for this feedback
        departments = feedback.to_departments.all()

        for department in departments:
            #assign view permission to the managers of  the routed departments
            for manager in department.managers.all():
                assign_perm("feedback.view_feedback", manager, feedback)

            #assign view permission to the auditors of  the routed departments
            for auditor in department.auditors.all():
                assign_perm("feedback.view_feedback", auditor, feedback)
        


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
    

#left to refactor to use object level permission check

class FeedbackResponseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_form.html"
    form_class = FeedbackResponseForm
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.add_feedbackresponse"]

    def get_feedback(self):
        """Helper method to retrieve the associated feedback based on the URL parameter."""
        return Feedback.objects.get(id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback"] = self.feedback
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.feedback
        return kwargs

    def form_valid(self, form):
        self.object = form.save(responder=self.request.user)
        return redirect(self.get_success_url())


class FeedbackResponseListView(LoginRequiredMixin, FeedbackMixin, ListView):
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


class FeedbackResponseEditView(LoginRequiredMixin, UpdateView):
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


class FeedbackResponseDeleteView(LoginRequiredMixin, DeleteView):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_confirm_delete.html"
    success_url = reverse_lazy("feedback_list")


class FeedbackResponseAssignView(LoginRequiredMixin,PermissionRequiredMixin, View):
    form_class = FeedbackResponseAssignForm
    template_name = "feedback/feedback_assign_form.html"
    permission_required = "feedback.assign_feedback"

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
            self.feedback.assign_to_responder(responder)
            sync_feedback_view_permissions(self.feedback)
            return redirect("feedback_response_list", pk=self.feedback.pk)

        return render(
            request,
            self.template_name,
            {"form": form, "feedback": self.feedback},
        )


# additinal view to add the department , only allowed to superuser and staff user
class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    template_name = "feedback/department_form.html"
    fields = ["name", "description"]
    success_url = reverse_lazy("feedback_list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.is_staff):
            raise PermissionDenied("You do not have permission to add a department.")
        return super().dispatch(request, *args, **kwargs)

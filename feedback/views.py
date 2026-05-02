from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count

from guardian.shortcuts import get_objects_for_user, assign_perm  # type: ignore

from .models import (
    Feedback,
    FeedbackResponse,
    FeedbackResponderRecord,
    Department,
    Category,
)
from .forms import (
    FeedbackForm,
    FeedbackResponseForm,
    FeedbackResponseAssignForm,
    DepartmentForm,
    CategoryForm,
)
from .mixins import FeedbackMixin
from .permissions import (
    assign_department_permissions,
    assign_owner_perms,
    assign_permission_creator_of_feedback_to_response,
)
from .utils import (
    get_analytics_data,
)


class FeedbackListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/feedback_list.html"
    context_object_name = "feedbacks"
    permission_required = ["feedback.view_feedback"]
    paginate_by = 6

    def get_queryset(self):
        queryset = get_objects_for_user(
            self.request.user,
            "feedback.view_feedback",
            klass=Feedback,
            with_superuser=True,
            accept_global_perms=False,
        )

        search_term = self.request.GET.get("q", "").strip()
        selected_status = self.request.GET.get("status", "")
        selected_priority = self.request.GET.get("priority", "")
        selected_category = self.request.GET.get("category", "")

        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term)
                | Q(message__icontains=search_term)
                | Q(creator__name__icontains=search_term)
            )

        if selected_status in dict(Feedback.status_choices):
            queryset = queryset.filter(status=selected_status)

        if selected_priority in dict(Feedback.PRIORITY_CHOICES):
            queryset = queryset.filter(priority=selected_priority)

        if selected_category:
            queryset = queryset.filter(category__id=selected_category)

        return (
            queryset.select_related("creator", "category")
            .prefetch_related("to_departments")
            .order_by("-created_at")
        )

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm("feedback.view_feedback"):
            raise PermissionDenied("You do not have permission to view feedback.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_term"] = self.request.GET.get("q", "").strip()
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_priority"] = self.request.GET.get("priority", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["status_choices"] = Feedback.status_choices
        context["priority_choices"] = Feedback.PRIORITY_CHOICES
        context["category_choices"] = Category.objects.order_by("name")
        context["total_feedback_count"] = self.get_queryset().count()
        return context


class AnalyticsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "feedback/analytics.html"
    permission_required = ["feedback.view_feedback"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get comprehensive analytics data from business logic
        analytics = get_analytics_data(self.request.user)

        # Flatten analytics data into context
        context["total_feedback"] = analytics["total_feedback"]
        context["status_stats"] = analytics["status"]["stats"]
        context["status_pending"] = analytics["status"]["pending"]
        context["status_reviewed"] = analytics["status"]["reviewed"]
        context["status_resolved"] = analytics["status"]["resolved"]

        context["priority_stats"] = analytics["priority"]["stats"]
        context["priority_low"] = analytics["priority"]["low"]
        context["priority_medium"] = analytics["priority"]["medium"]
        context["priority_high"] = analytics["priority"]["high"]

        context["category_stats"] = analytics["categories"]
        context["department_stats"] = analytics["departments"]

        context["total_responses"] = analytics["responses"]["total_responses"]
        context["resolved_count"] = analytics["responses"]["resolved_count"]
        context["unresolved_count"] = analytics["responses"]["unresolved_count"]
        context["response_rate"] = analytics["responses"]["response_rate"]

        context["recent_feedback_count"] = analytics["recent_activity"]["recent_count"]
        context["feedback_per_day"] = analytics["recent_activity"]["feedback_per_day"]
        context["avg_response_time"] = analytics["avg_response_time"]

        return context


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
        context["assign_form"] = FeedbackResponseAssignForm()
        context["response_count"] = self.object.responses.count()
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

        messages.success(
            self.request,
            f"Feedback '{self.object.title or 'Untitled'}' created successfully!",
        )
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

    def delete(self, request, *args, **kwargs):
        feedback_title = self.get_object().title or "Untitled"
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Feedback '{feedback_title}' deleted successfully!")
        return response


class FeedbackResponseCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
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
        # load the feedback object before processing the request, so it's available for permission checks and form initialization
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
        assign_department_permissions(response=self.object)
        assign_permission_creator_of_feedback_to_response(self.object, self.feedback)

        messages.success(self.request, "Response created successfully!")
        return response


class FeedbackResponseListView(
    LoginRequiredMixin, PermissionRequiredMixin, FeedbackMixin, ListView
):
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

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.has_perm("feedback.change_feedbackresponse", obj):
            raise PermissionDenied
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feedback"] = self.object.feedback
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Response updated successfully!")
        return reverse("feedback_response_list", kwargs={"pk": self.object.feedback.pk})


class FeedbackResponseDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = FeedbackResponse
    template_name = "feedback/feedback_response_confirm_delete.html"
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.delete_feedbackresponse"]

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.has_perm("feedback.delete_feedbackresponse", obj):
            raise PermissionDenied
        return obj

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Response deleted successfully!")
        return response


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
                _, created = self.feedback.assign_to_responder(responder)
                if created:
                    assign_perm("feedback.view_feedback", responder, self.feedback)
                    messages.success(
                        request, f"Feedback assigned to {responder.name} successfully!"
                    )
            except ValueError as e:
                form.add_error(None, str(e))
                return render(
                    request,
                    self.template_name,
                    {"form": form, "feedback": self.feedback},
                )
            return redirect("feedback_response_list", pk=pk)
        return render(
            request,
            self.template_name,
            {"form": form, "feedback": self.feedback},
        )


# Notification list and mark‑as‑read views
from django.views.generic import ListView, View
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Notification


class NotificationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List recent notifications for the logged‑in user.
    Returns JSON when ``?format=json`` is present, otherwise renders
    ``feedback/notifications_list.html``.
    """

    model = Notification
    template_name = "feedback/notifications_list.html"
    context_object_name = "notifications"
    permission_required = ["feedback.view_feedback"]
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by(
            "-created_at"
        )

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get("format") == "json":
            data = [
                {
                    "id": n.id,
                    "type": n.notification_type,
                    "title": n.title,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in context["notifications"]
            ]
            return JsonResponse({"notifications": data})
        return super().render_to_response(context, **response_kwargs)


class MarkNotificationReadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Mark a single notification as read (AJAX)."""

    permission_required = ["feedback.view_feedback"]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Invalid notification"}, status=400
            )
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return JsonResponse({"success": True, "status": "ok"})


# ---------------------------------------------------------------------------
# Server‑Sent Events endpoint for real‑time notifications
# ---------------------------------------------------------------------------
from django.http import StreamingHttpResponse
import time


class NotificationSSEView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Stream new notifications to the client using Server‑Sent Events.
    The client should open an EventSource to ``/feedback/notifications/sse/``.
    Events are sent as ``data: <json>\n\n`` where the JSON contains the
    notification fields.
    """

    permission_required = ["feedback.view_feedback"]

    def get(self, request):
        # Simple implementation: poll the DB every 5 seconds for new notifications.
        # In production you might use a more efficient approach (Redis pub/sub, etc.).
        last_id = request.GET.get("last_id")
        try:
            last_id = int(last_id) if last_id else 0
        except ValueError:
            last_id = 0

        def event_stream():
            while True:
                new_notifications = Notification.objects.filter(
                    recipient=request.user, id__gt=last_id
                ).order_by("id")
                for notif in new_notifications:
                    payload = {
                        "id": notif.id,
                        "type": notif.notification_type,
                        "title": notif.title,
                        "message": notif.message,
                        "is_read": notif.is_read,
                        "created_at": notif.created_at.isoformat(),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    last_id = notif.id
                time.sleep(5)

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        return response


class DepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Department
    template_name = "feedback/department_form.html"
    form_class = DepartmentForm
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.add_department"]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Department '{self.object.name}' created successfully!"
        )
        return response


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    template_name = "feedback/category_form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("feedback_list")
    permission_required = ["feedback.add_category"]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Category '{self.object.name}' created successfully!"
        )
        return response


# Existing views continue below …

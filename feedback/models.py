import uuid
from django.db import models
from django.urls import reverse
from django.conf import settings


class Feedback(models.Model):
    """Model representing user feedback."""

    status_choices = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=status_choices, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    to_departments = models.ManyToManyField(
        "Department", through="FeedbackDepartment", related_name="feedbacks"
    )
    is_anonymous = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse("feedback_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} - {self.message[:20]}..."

    def assign_to_responder(self, responder):
        """Assign this feedback to a responder."""
        record, created = FeedbackResponderRecord.objects.get_or_create(
            feedback=self, responder=responder
        )
        return record, created


class Department(models.Model):
    """Model representing a department."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class FeedbackDepartment(models.Model):
    """Model representing the relationship between feedback and departments.
    This indicate that feedback is given to a specific department for review and action.
    """

    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="feedback_departments"
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="department_feedbacks"
    )

    def __str__(self):
        return f"{self.feedback.name} - {self.department.name}"


class FeedbackResponderRecord(models.Model):
    """Model representing the assignment of a feedback to a responder."""

    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="feedback_responder_records"
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="responder_records",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["feedback", "responder"],
                name="unique_feedback_responder_assignment",
            )
        ]

    def __str__(self):
        return f"{self.feedback} assigned to {self.responder}"


class FeedbackResponse(models.Model):
    """Model representing a response to feedback."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="responses"
    )
    responder = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="feedback_responses"
    )

    responder_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.feedback.name} by {', '.join(str(user) for user in self.responder.all())}"

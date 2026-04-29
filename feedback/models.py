import uuid
from django.db import models
from django.urls import reverse
from django.conf import settings
from .permissions import assign_many_perms


class Feedback(models.Model):
    """Model representing user feedback."""

    status_choices = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_feedbacks",
    )
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    title = models.CharField(max_length=200, blank=True)
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
    )
    status = models.CharField(max_length=20, choices=status_choices, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    to_departments = models.ManyToManyField(
        "Department", through="FeedbackDepartment", related_name="feedbacks"
    )

    def get_absolute_url(self):
        return reverse("feedback_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.creator} - {self.message[:20]}..."

    def assign_to_responder(self, responder):
        """Assign this feedback to a responder."""
        if not responder.groups.filter(name="Responder").exists():
            raise ValueError(
                "User must be in the 'Feedback Responders' group to be assigned as a responder."
            )

        record, created = FeedbackResponderRecord.objects.get_or_create(
            feedback=self, responder=responder
        )
        return record, created

    class Meta:
        permissions = [
            ("assign_feedback", "Can assign feedback to responders"),
            ("revoke_responder", "Can revoke responder assignment from feedback"),
        ]


class Department(models.Model):
    """Model representing a department."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="managed_departments", blank=True
    )
    auditors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="audited_departments", blank=True
    )

    def __str__(self):
        return self.name


class Category(models.Model):
    """Optional category for feedback items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

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
        return f"{self.feedback.creator} - {self.department.name}"


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
        return f"Response to {self.feedback.creator} by {', '.join(str(user) for user in self.responder.all())}"

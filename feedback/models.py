import uuid
from django.db import models
from django.urls import reverse


class Feedback(models.Model):
    """Model representing user feedback."""

    status_choices = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=status_choices, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    to_departments = models.ManyToManyField(
        "Department", through="FeedbackDepartment", related_name="feedbacks"
    )

    def get_absolute_url(self):
        return reverse("feedback_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} - {self.message[:20]}..."


class Department(models.Model):
    """Model representing a department."""

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


class FeedbackResponse(models.Model):
    """Model representing a response to feedback."""

    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="responses"
    )
    responder_name = models.CharField(max_length=100)
    responder_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.feedback.name} by {self.responder_name}"

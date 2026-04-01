import uuid
from django.db import models
from django.urls import reverse

class Feedback(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("feedback_detail", kwargs={"pk": self.pk})
    

    def __str__(self):
        return f"{self.name} - {self.message[:20]}..."

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        exclude = ['status', 'created_at']

    def save(self, commit = ...):
        self.instance.status = 'reviewed'
        return super().save(commit)
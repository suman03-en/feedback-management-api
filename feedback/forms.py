from django import forms
from .models import Feedback, FeedbackResponse

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        exclude = ['status', 'created_at']

    def save(self, commit = ...):
        self.instance.status = 'reviewed'
        return super().save(commit)
    
class FeedbackResponseForm(forms.ModelForm):
    class Meta:
        model = FeedbackResponse
        fields = ['responder_name', 'responder_message']
    
    def __init__(self, *args, feedback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback = feedback

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.feedback = self.feedback
        instance.feedback.status = 'resolved'
        instance.feedback.save()
        if commit:
            instance.save()
        return instance

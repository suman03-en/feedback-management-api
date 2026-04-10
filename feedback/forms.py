from django import forms
from .models import Feedback, FeedbackResponse, Department
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()

class FeedbackForm(forms.ModelForm):

    class Meta:
        model = Feedback
        exclude = [
            "status",
            "created_at",
        ]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_anonymous"):
            cleaned_data["name"] = "Anonymous"
            cleaned_data["email"] = ""
        return cleaned_data

    def save(self, commit=...):
        self.instance.status = "pending"
        return super().save(commit)


class FeedbackResponseForm(forms.ModelForm):
    resolve = forms.BooleanField(required=False, label="Mark feedback as resolved")

    class Meta:
        model = FeedbackResponse
        fields = ["responder", "responder_message"]

    def __init__(self, *args, feedback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback = feedback

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.feedback = self.feedback

        if self.cleaned_data.get("resolve"):
            instance.feedback.status = "resolved"
        else:
            instance.feedback.status = "reviewed"

        instance.feedback.save()

        if commit:
            instance.save()
        return instance
    

class FeedbackResponseAssignForm(forms.Form):
    """Form for assigning feedback to a responder."""
    responder = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True), label="Assign to")
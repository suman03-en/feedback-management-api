from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Department, Feedback, FeedbackResponse, Category

# Get the User model
User = get_user_model()


class FeedbackForm(forms.ModelForm):

    to_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        required=False,
        label="Route to departments",
        widget=forms.SelectMultiple(attrs={"size": 5}),
    )

    class Meta:
        model = Feedback
        fields = ["title", "priority", "category", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["to_departments"].queryset = Department.objects.order_by("name")
        self.fields["title"].widget.attrs.update({"placeholder": "Short summary"})
        self.fields["message"].widget = forms.Textarea(attrs={"rows": 7})
        self.fields["category"].required = False
        self.fields["to_departments"].help_text = (
            "Pick one or more departments so the right team receives visibility."
        )

        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                # If existing classes exist, don't overwrite them completely if we want to preserve, but here we can just set it
                field.widget.attrs['class'] = 'form-select'

    def save(self, commit=True):
        departments = self.cleaned_data.get("to_departments", [])
        self.instance.status = "pending"
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            instance.to_departments.set(departments)
        else:
            self._pending_departments = departments
        return instance

    def save_m2m(self):
        super().save_m2m()
        pending_departments = getattr(self, "_pending_departments", None)
        if pending_departments is not None and self.instance.pk:
            self.instance.to_departments.set(pending_departments)


class FeedbackResponseForm(forms.ModelForm):
    resolve = forms.BooleanField(required=False, label="Mark feedback as resolved")

    class Meta:
        model = FeedbackResponse
        fields = ["responder_message"]

    def __init__(self, *args, feedback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback = feedback

        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'

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

    responder = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_active=True, groups__name="Responder"
        ).distinct(),
        label="Assign to",
    )

    def __init__(self, *args, feedback=None, assigner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback = feedback
        self.assigner = assigner

        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 4})
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'

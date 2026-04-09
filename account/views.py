from django.views import View
from django.shortcuts import render, redirect, HttpResponse
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth import authenticate, login

class UserRegisterView(View):
    form_class = UserRegistrationForm
    template_name = "account/register.html"

    def get_form(self, *args, **kwargs):
        return self.form_class(*args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": self.get_form()})

    def post(self, request):
        form = self.get_form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("User registered successfully")
        return render(request, self.template_name, {"form": form})
    
class UserLoginView(View):
    form_class = UserLoginForm
    template_name = "account/login.html"

    def get_form(self, *args, **kwargs):
        return self.form_class(*args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": self.get_form()})
    
    def post(self, request):
        form = self.get_form(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)
                return HttpResponse(f"User {email} logged in successfully")
            else:
                form.add_error(None, "Invalid email or password")
        return render(request, self.template_name, {"form": form})

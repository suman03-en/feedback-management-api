from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

class UserRegisterView(View):
    def get(self, request):
        return render(request, "account/register.html", {"form": UserCreationForm()})
    
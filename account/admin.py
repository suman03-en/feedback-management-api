from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "department", "is_staff", "is_superuser")
    search_fields = ("email", "name", "department")
    readonly_fields = ("password",)
        

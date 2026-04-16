from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


def promote_to_department_manager(modeladmin, request, queryset):
    if not request.user.is_superuser:
        modeladmin.message_user(request, "You do not have permission to perform this action.", level="error")
        return
    
    errors = []

    for user in queryset:
        try:
            user.promote_to_department_manager(by_user=request.user)
        except PermissionError as e:
            errors.append(f"User {user.email}: {str(e)}")
    if errors:
        modeladmin.message_user(request, "Some users could not be promoted:\n" + "\n".join(errors), level="error")
    else:
        modeladmin.message_user(request, "Selected users have been promoted to department manager.")



@admin.register(User)       
class UserAdmin(UserAdmin):
    list_display = ("email", "name", "department", "is_staff", "is_superuser")
    search_fields = ("email", "name", "department")
    ordering = ("email",)

    # override the default fieldsets to include department and remove username since we are using email as the unique identifier . check User model for more details
    fieldsets = (
    (None, {"fields": ("email", "password")}),
    (_("Personal info"), {"fields": ("name", "department")}),
    (
        _("Permissions"),
        {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        },
    ),
    (_("Important dates"), {"fields": ("last_login", "date_joined")}),
)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )

    actions = [promote_to_department_manager]



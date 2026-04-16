from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser
from feedback.models import Department
from django.contrib.auth.models import Group

class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("User must have an email address"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    first_name = last_name = username = None
    name = models.CharField(max_length=100)
    email = models.EmailField(_("email address"), unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="users", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def promote_to_staff(self, by_user):
        """Promote a user to staff status. Only superusers can perform this action."""
        if not by_user.is_superuser:
            raise PermissionError("Only superusers can promote users to staff.")
        self.is_staff = True
        self.save(update_fields=["is_staff"])

    def promote_to_department_manager(self, by_user):
        """Promote a user to department manager. Only superusers can perform this action."""
        if not by_user.is_superuser:
            raise PermissionError("Only superusers can promote users to department manager.")
        if self.department is None:
            raise ValueError("User must be assigned to a department before being promoted to department manager.")
        
        self.department.managers.add(self)
        # add user to department manager group for permissions
        department_manager_group, _ = Group.objects.get_or_create(name="Department Manager")
        # check if user is already in the group to avoid duplicates
        if not self.groups.filter(name="Department Manager").exists():
            department_manager_group.user_set.add(self)
            


    def promote_to_auditor(self, by_user):
        """Promote a user to auditor. Only superusers can perform this action."""
        if not by_user.is_superuser:
            raise PermissionError("Only superusers can promote users to auditor.")
        if self.department is None:
            raise ValueError("User must be assigned to a department before being promoted to auditor.")
        
        self.department.auditors.add(self)

    def __str__(self):
        return self.name

    def get_full_name(self):
        return self.name

    def get_email(self):
        return self.email

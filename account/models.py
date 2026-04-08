from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser


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
    department = models.CharField(max_length=100)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "department"]

    objects = UserManager()

    def promote_to_staff(self, by_user):
        """Promote a user to staff status. Only superusers can perform this action."""
        if not by_user.is_superuser:
            raise PermissionError("Only superusers can promote users to staff.")
        self.is_staff = True
        self.save(update_fields=["is_staff"])

    def __str__(self):
        return self.name

    def get_full_name(self):
        return self.name

    def get_email(self):
        return self.email

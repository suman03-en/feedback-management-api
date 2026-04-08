from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    department = models.CharField(max_length=100)
    is_superadmin = models.BooleanField(default=False)

    def promote_to_staff(self, by_user):
        """Promote a user to staff status. Only superadmins can perform this action."""
        if not by_user.is_superadmin:
            raise PermissionError("Only superadmins can promote users to staff.")
        self.is_staff = True
        self.save(update_fields=["is_staff"])
    

    def __str__(self):
        return self.username

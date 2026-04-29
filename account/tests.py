from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from feedback.models import Department

User = get_user_model()


class AccountFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            name="Support", description="Support team"
        )

    def test_register_assigns_employee_group(self):
        response = self.client.post(
            reverse("user_register"),
            {
                "email": "new.user@example.com",
                "name": "New User",
                "department": self.department.pk,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        user = User.objects.get(email="new.user@example.com")
        employee_group = Group.objects.get(name="Employee")

        self.assertRedirects(response, reverse("user_login"))
        self.assertTrue(user.groups.filter(pk=employee_group.pk).exists())

    def test_login_redirects_to_feedback_queue(self):
        user = User.objects.create_user(
            email="login.user@example.com",
            name="Login User",
            password="StrongPass123!",
        )
        user.user_permissions.add(
            Permission.objects.get(
                codename="view_feedback", content_type__app_label="feedback"
            )
        )

        response = self.client.post(
            reverse("user_login"),
            {
                "email": "login.user@example.com",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("feedback_list"))
        self.assertEqual(int(self.client.session.get("_auth_user_id")), user.pk)

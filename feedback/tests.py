from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from guardian.shortcuts import assign_perm

from .models import (
    Category,
    Department,
    Feedback,
    FeedbackResponse,
    FeedbackResponderRecord,
)
from .permissions import assign_owner_perms

User = get_user_model()


def permission_for(codename):
    return Permission.objects.get(codename=codename, content_type__app_label="feedback")


class FeedbackWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="Operations", description="Ops")
        cls.category = Category.objects.create(name="Facilities")

        cls.creator = User.objects.create_user(
            email="creator@example.com",
            name="Creator",
            password="testpass123",
        )
        cls.manager = User.objects.create_user(
            email="manager@example.com",
            name="Manager",
            password="testpass123",
        )
        cls.responder = User.objects.create_user(
            email="responder@example.com",
            name="Responder",
            password="testpass123",
        )

        cls.department.managers.add(cls.manager)
        responder_group, _ = Group.objects.get_or_create(name="Responder")
        cls.responder.groups.add(responder_group)

        for user, codename in [
            (cls.creator, "add_feedback"),
            (cls.creator, "view_feedback"),
            (cls.manager, "view_feedback"),
            (cls.manager, "assign_feedback"),
            (cls.manager, "view_feedbackresponse"),
            (cls.responder, "add_feedbackresponse"),
            (cls.responder, "view_feedbackresponse"),
            (cls.responder, "change_feedbackresponse"),
            (cls.responder, "view_feedback"),
        ]:
            user.user_permissions.add(permission_for(codename))

    def create_feedback(self, title, message, priority="medium", category=None):
        feedback = Feedback.objects.create(
            creator=self.creator,
            email=self.creator.email,
            title=title,
            message=message,
            priority=priority,
            category=category,
        )
        feedback.to_departments.add(self.department)
        assign_owner_perms(self.creator, feedback)
        assign_perm("feedback.view_feedback", self.creator, feedback)
        return feedback

    def test_queue_filters_and_paginates(self):
        first = self.create_feedback(
            "Printer jam", "Printer on floor 2 is jammed.", "high", self.category
        )
        second = self.create_feedback("Water leak", "Leak near the storage room.")

        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("feedback_list"),
            {
                "q": "Printer",
                "status": "pending",
                "priority": "high",
                "category": str(self.category.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first.title)
        self.assertNotContains(response, second.title)
        self.assertEqual(len(response.context["feedbacks"]), 1)

    def test_feedback_create_routes_departments(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("feedback_create"),
            {
                "title": "Broken desk",
                "priority": "high",
                "category": self.category.pk,
                "message": "The desk in meeting room 4 is broken.",
                "to_departments": [self.department.pk],
            },
        )

        feedback = Feedback.objects.get(title="Broken desk")
        self.assertRedirects(
            response, reverse("feedback_detail", kwargs={"pk": feedback.pk})
        )
        self.assertEqual(feedback.status, "pending")
        self.assertEqual(list(feedback.to_departments.all()), [self.department])
        self.assertTrue(self.manager.has_perm("feedback.view_feedback", feedback))

    def test_assigning_responder_creates_record(self):
        feedback = self.create_feedback("Projector issue", "Projector is flickering.")

        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("feedback_responder_assign", kwargs={"pk": feedback.pk}),
            {"responder": self.responder.pk},
        )

        self.assertRedirects(
            response, reverse("feedback_response_list", kwargs={"pk": feedback.pk})
        )
        self.assertTrue(
            FeedbackResponderRecord.objects.filter(
                feedback=feedback,
                responder=self.responder,
            ).exists()
        )
        self.assertTrue(self.responder.has_perm("feedback.view_feedback", feedback))

    def test_response_creation_updates_status_and_permissions(self):
        feedback = self.create_feedback(
            "Wi-Fi issue", "Wi-Fi is dropping on the second floor."
        )

        self.client.force_login(self.responder)
        response = self.client.post(
            reverse("feedback_response_create", kwargs={"pk": feedback.pk}),
            {
                "responder_message": "IT has reset the access point and the connection is stable.",
                "resolve": "on",
            },
        )

        feedback.refresh_from_db()
        self.assertRedirects(response, reverse("feedback_list"))
        self.assertEqual(feedback.status, "resolved")

        reply = FeedbackResponse.objects.get(feedback=feedback)
        self.assertTrue(reply.responder.filter(pk=self.responder.pk).exists())
        self.assertTrue(self.creator.has_perm("feedback.view_feedbackresponse", reply))

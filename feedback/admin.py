from django.contrib import admin
from .models import Feedback, FeedbackResponse, Department, FeedbackResponderRecord


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("creator", "email", "message", "created_at")
    search_fields = ("creator", "email", "message")
    list_filter = ("created_at",)


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ("feedback", "responder_message", "created_at")
    search_fields = ("responder__name", "responder_message")
    list_filter = ("created_at",)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


class FeedbackResponderRecordAdmin(admin.ModelAdmin):
    list_display = ("feedback", "responder", "assigned_at")
    search_fields = ("feedback__message", "responder__name")
    list_filter = ("assigned_at",)

# register your models here
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(FeedbackResponderRecord, FeedbackResponderRecordAdmin)

from django.contrib import admin
from .models import Feedback, FeedbackResponse, Department


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "message", "created_at")
    search_fields = ("name", "email", "message")
    list_filter = ("created_at",)


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ("feedback", "responder_message", "created_at")
    search_fields = ("responder__name", "responder_message")
    list_filter = ("created_at",)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


# register your models here
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)
admin.site.register(Department, DepartmentAdmin)

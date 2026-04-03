from django.contrib import admin
from .models import Feedback, FeedbackResponse


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "message", "created_at")
    search_fields = ("name", "email", "message")
    list_filter = ("created_at",)


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ("feedback", "responder_name", "responder_message", "created_at")
    search_fields = ("responder_name", "responder_message")
    list_filter = ("created_at",)


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)

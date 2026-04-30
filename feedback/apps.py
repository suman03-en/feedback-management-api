from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    name = 'feedback'

    def ready(self):
        # Import signal handlers so they are registered when the app loads
        from . import signals  # noqa: F401


from django.apps import AppConfig


class CultureConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.culture"
    label = "culture"
    verbose_name = "Culture (manifestations et référentiels)"

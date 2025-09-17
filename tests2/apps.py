from django.apps import AppConfig


class Tests2Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests2"
    verbose_name = "2 Тестовое задание"

    def ready(self):
        pass

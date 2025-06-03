from django.apps import AppConfig


class GymConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gym'
    verbose_name = 'باشگاه'

    def ready(self):
        import gym.signals  # Import signals module

from django.apps import AppConfig


class HotelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotel'
    
    def ready(self):
        # import the module to register admin report URLs
        try:
            from .admin.reports import get_admin_urls  # noqa: F401
        except Exception:
            pass
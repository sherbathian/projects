from django.contrib import admin

# ensure admin report URLs are registered
try:
    # import the module that performs admin.site.get_urls = get_admin_urls(...)
    from .reports import get_admin_urls  # noqa: F401
except Exception:
    # keep admin usable even if reports import fails
    pass


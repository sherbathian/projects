from django.contrib import admin        

# ensure admin report URLs are registered
try:
    # import the module that performs admin.site.get_urls = get_admin_urls(...)
    from .admin.reports import get_admin_urls  # noqa: F401
except Exception:
    # keep admin usable even if reports import fails
    pass

admin.site.site_header = "Project Admin"
admin.site.site_title = "Project Admin"
admin.site.index_title = "Welcome to the Project Admin"   
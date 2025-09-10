from django.contrib import admin
from project.models import Party

# Admin for Party
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email', 'phone')

admin.site.site_header = "Project Admin"
admin.site.site_title = "Project Admin"
admin.site.index_title = "Welcome to the Project Admin"   
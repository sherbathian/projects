from django.contrib import admin
from hotel.models import Partner



@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'created_at')
    search_fields = ('name', 'contact')
    ordering = ('name',)
    
    
    
admin.site.site_header = "Hotel Admin"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Welcome to the Hotel Admin"   
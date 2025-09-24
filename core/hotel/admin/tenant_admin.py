from django.contrib import admin
from hotel.models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'created_at')
    search_fields = ('name', 'contact')
    ordering = ('name',)
    
    
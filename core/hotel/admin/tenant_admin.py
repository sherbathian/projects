from django.contrib import admin
from hotel.models import Tenant
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class TenantResource(resources.ModelResource):
    
    class Meta:
        fields = ('id', 'name', 'cnic', 'contact', 'detail',)
        exclude = ('created_at')
        model = Tenant
    

@admin.register(Tenant)
class TenantAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = TenantResource
    list_display = ('name', 'cnic', 'contact', 'created_at', 'detail')
    search_fields = ('name', 'cnic', 'contact')
    ordering = ('name',)
    
    
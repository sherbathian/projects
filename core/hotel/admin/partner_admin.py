from django.contrib import admin
from hotel.models import Partner, PartnerPayment
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class PartnerResource(resources.ModelResource):
    
    class Meta:
        fields = ('id', 'name', 'cnic', 'contact','share_percentage', 'detail',)
        exclude = ('created_at')
        model = Partner

@admin.register(Partner)
class PartnerAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = PartnerResource
    list_display = ('name', 'cnic', 'contact',  'share_percentage', 'detail',)
    search_fields = ('name', 'contact')
    ordering = ('name',)
    
    
    
@admin.register(PartnerPayment)
class PartnerPaymentAdmin(admin.ModelAdmin):
    list_display = ('partner__name', 'partner__cnic', 'partner__contact',  'amount', 'payment_date','comments')
    search_fields = ('partner__name', 'partner__cnic', 'partner__contact')
    ordering = ('-payment_date',)   
    
    
admin.site.site_header = "Hotel Admin"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Welcome to the Hotel Admin"   



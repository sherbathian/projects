import csv
import io
from django.contrib import admin, messages
from django.db.models import Sum
from django.http import HttpResponse
from project.models import Saddqah
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class SaddqahResource(resources.ModelResource):

    class Meta:
        fields = ('party__name', 'amount', 'name', 'category', 'transaction_date')
        model = Saddqah


# Admin for Saddqah with export functionality
@admin.register(Saddqah)
class SaddqahAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = SaddqahResource
    list_display = ('party', 'amount', 'name', 'category', 'transaction_date')
    list_filter = ('party', 'category', 'transaction_date')
    search_fields = ('party__name', 'name')
    ordering = ('-transaction_date',)
    change_list_template = 'admin/project/saddqah/change_list.html'
    actions = ['export_as_csv', 'export_as_pdf']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(total_amount=Sum('amount'))
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response

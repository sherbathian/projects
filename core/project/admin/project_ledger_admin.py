from django.contrib import admin
from project.models import ProjectLedger
from django.db.models import Sum
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class ProjectLedgerResource(resources.ModelResource):
    class Meta:
        fields = ('project__name', 'paid_amount', 'received_amount', 'transaction_date', 'comments')
        model = ProjectLedger

# Admin for ProjectLedger with total amount display
@admin.register(ProjectLedger)
class ProjectLedgerAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ProjectLedgerResource
    list_display = ('project', 'paid_amount', 'received_amount', 'transaction_date', 'comments')
    list_filter = ('project', 'transaction_date')
    change_list_template = 'admin/project/projectledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            response.context_data['title'] = 'Project Ledgers'
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_received=Sum('received_amount'),
                    total_paid=Sum('paid_amount'),
                )
                response.context_data['total_received'] = totals.get('total_received') or 0
                response.context_data['total_paid'] = totals.get('total_paid') or 0
        except Exception:
            response.context_data.setdefault('total_received', 0)
            response.context_data.setdefault('total_paid', 0)
        return response

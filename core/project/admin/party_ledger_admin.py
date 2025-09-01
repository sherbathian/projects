from django.contrib import admin
from django.db.models import Sum
from project.models import PartyLedger
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class PartyLedgerResource(resources.ModelResource):

    class Meta:
        fields = ('paid_by__name', 'received_by__name', 'amount', 'transaction_date', 'comments')
        model = PartyLedger


# Admin for PartyLedger with total amount display
@admin.register(PartyLedger)
class PartyLedgerAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = PartyLedgerResource
    list_display = ('paid_by', 'received_by', 'amount', 'transaction_date', 'comments')
    list_filter = ('paid_by', 'received_by', 'transaction_date')
    change_list_template = 'admin/project/partyledger/change_list.html'
    rows_per_page = 20
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_amount=Sum('amount'),
                )
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response

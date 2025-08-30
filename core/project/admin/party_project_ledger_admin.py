from django.contrib import admin
from django.db.models import Sum
from project.models import PartyProjectLedger

# Admin for PartyProjectLedger with total amount display
@admin.register(PartyProjectLedger)
class PartyProjectLedgerAdmin(admin.ModelAdmin):
    list_display = ('party', 'project', 'paid_amount', 'received_amount', 'withdrawn_amount', 'transaction_date', 'comments')
    list_filter = ('party', 'project', 'transaction_date')
    list_per_page = 20
   
    change_list_template = 'admin/project/partyprojectledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        """Inject total received/paid for the current changelist queryset into the template context."""
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_received=Sum('received_amount'),
                    total_paid=Sum('paid_amount'),
                    total_withdrawn=Sum('withdrawn_amount'),
                )
                response.context_data['total_received'] = totals.get('total_received') or 0
                response.context_data['total_paid'] = totals.get('total_paid') or 0
                response.context_data['total_withdrawn'] = totals.get('total_withdrawn') or 0
        except Exception:
            response.context_data.setdefault('total_received', 0)
            response.context_data.setdefault('total_paid', 0)
            response.context_data.setdefault('total_withdrawn', 0)
        return response

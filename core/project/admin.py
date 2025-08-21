from django.contrib import admin
from django.db.models import Sum
from .models import Project, Party, ProjectParty, ProjectLedger, PartyProjectLedger
from .models import PartyLedger, Saddqah
from django.db.models import Sum

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'budget')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email', 'phone')
    
@admin.register(ProjectParty)
class ProjectPartyAdmin(admin.ModelAdmin):
    list_display = ('project', 'party', 'share')
    list_filter = ('project', 'party')

@admin.register(ProjectLedger)
class ProjectLedgerAdmin(admin.ModelAdmin):
    list_display = ('project', 'paid_amount', 'received_amount', 'transaction_date', 'comments')
    list_filter = ('project', 'transaction_date')
    change_list_template = 'admin/project/partyprojectledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data.get('cl')
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

@admin.register(PartyProjectLedger)
class PartyProjectLedgerAdmin(admin.ModelAdmin):
    list_display = ('party', 'project', 'paid_amount', 'received_amount', 'transaction_date')
    list_filter = ('party', 'project', 'transaction_date')
    change_list_template = 'admin/project/partyprojectledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        """Inject total received amount for the current changelist queryset into the template context."""
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_received=Sum('received_amount'),
                    total_paid=Sum('paid_amount'),
                )
                response.context_data['total_received'] = totals.get('total_received') or 0
                response.context_data['total_paid'] = totals.get('total_paid') or 0
        except Exception:
            # keep admin stable if aggregation fails
            response.context_data.setdefault('total_received', 0)
            response.context_data.setdefault('total_paid', 0)
        return response


@admin.register(PartyLedger)
class PartyLedgerAdmin(admin.ModelAdmin):
    list_display = ('paid_by', 'received_by', 'amount', 'transaction_date')
    list_filter = ('paid_by', 'received_by', 'transaction_date')
    change_list_template = 'admin/project/partyledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
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

@admin.register(Saddqah)
class SaddqahAdmin(admin.ModelAdmin):
    list_display = ('party', 'amount', 'name', 'category', 'transaction_date')
    list_filter = ('party', 'category', 'transaction_date')
    search_fields = ('party__name', 'name')
    ordering = ('-transaction_date',)
    change_list_template = 'admin/project/saddqah/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
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
from django.contrib import admin
from django.db.models import Sum
from .models import Project, Party, ProjectParty, ProjectLedger, PartyProjectLedger
from .models import PartyLedger, Saddqah
from django.db.models import Sum
import datetime
from django.template.response import TemplateResponse
from django.urls import path


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

# Custom admin view for Saddqah reports
class SaddqahReportAdminView:
    @staticmethod
    def dashboard_view(request):
        year = int(request.GET.get('year', datetime.datetime.now().year))
        saddqah_data = (
            Saddqah.objects.filter(transaction_date__year=year)
            .values('transaction_date__month')
            .annotate(total=Sum('amount'))
            .order_by('transaction_date__month')
        )
        months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
        saddqah_amounts = [0]*12
        for entry in saddqah_data:
            saddqah_amounts[entry['transaction_date__month']-1] = float(entry['total'])
        years = Saddqah.objects.dates('transaction_date', 'year').distinct()
        context = dict(
            admin.site.each_context(request),
            months=months,
            saddqah_amounts=saddqah_amounts,
            selected_year=year,
            years=[y.year for y in years],
        )
        return TemplateResponse(request, "admin/project/saddqah/report.html", context)
# Add dashboard URL to admin
def get_admin_urls(urls):
    def get_urls():
        my_urls = [
            path('dashboard/', admin.site.admin_view(SaddqahReportAdminView.dashboard_view), name='saddqah_dashboard'),
        ]
        return my_urls + urls()
    return get_urls

admin.site.get_urls = get_admin_urls(admin.site.get_urls)

# Custom admin view for Project Ledger reports
class ProjectLedgerReportAdminView:
    @staticmethod
    def dashboard_view(request):
        year = int(request.GET.get('year', datetime.datetime.now().year))
        ledger_data = (
            ProjectLedger.objects.filter(transaction_date__year=year)
            .values('transaction_date__month')
            .annotate(total_received=Sum('received_amount'), total_paid=Sum('paid_amount'))
            .order_by('transaction_date__month')
        )
        months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
        received_amounts = [0]*12
        paid_amounts = [0]*12
        for entry in ledger_data:
            received_amounts[entry['transaction_date__month']-1] = float(entry['total_received'] or 0)
            paid_amounts[entry['transaction_date__month']-1] = float(entry['total_paid'] or 0)
        years = ProjectLedger.objects.dates('transaction_date', 'year').distinct()
        context = dict(
            admin.site.each_context(request),
            months=months,
            received_amounts=received_amounts,
            paid_amounts=paid_amounts,
            selected_year=year,
            years=[y.year for y in years],
        )
        return TemplateResponse(request, "admin/project/ledger_dashboard.html", context)


# class SaddqahReportAdminView:
#     @staticmethod
#     def dashboard_view(request):
#         year = int(request.GET.get('year', datetime.datetime.now().year))
#         saddqah_data = (
#             Saddqah.objects.filter(transaction_date__year=year)
#             .values('transaction_date__month')
#             .annotate(total=Sum('amount'))
#             .order_by('transaction_date__month')
#         )
#         received_data = (
#             ProjectLedger.objects.filter(transaction_date__year=year)
#             .values('transaction_date__month')
#             .annotate(total=Sum('received_amount'))
#             .order_by('transaction_date__month')
#         )
#         months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
#         saddqah_amounts = [0]*12
#         received_amounts = [0]*12
#         for entry in saddqah_data:
#             saddqah_amounts[entry['transaction_date__month']-1] = float(entry['total'])
#         for entry in received_data:
#             received_amounts[entry['transaction_date__month']-1] = float(entry['total'])
#         years = Saddqah.objects.dates('transaction_date', 'year').distinct()
#         context = dict(
#             admin.site.each_context(request),
#             months=months,
#             saddqah_amounts=saddqah_amounts,
#             received_amounts=received_amounts,
#             selected_year=year,
#             years=[y.year for y in years],
#         )
#         return TemplateResponse(request, "admin/saddqah/project/dashboard.html", context)

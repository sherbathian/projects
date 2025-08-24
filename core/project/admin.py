from django.contrib import admin
from django.db.models import Sum
from .models import (
    Project, Party, ProjectParty, ProjectLedger, PartyProjectLedger,
    PartyLedger, Saddqah
)
import datetime
from django.template.response import TemplateResponse
from django.urls import path
from django.http import HttpResponse
from django.contrib import messages
import csv
import io


# Admin for Project
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'budget')
    list_filter = ('status',)
    search_fields = ('name', 'description')

# Admin for Party
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email', 'phone')

# Admin for ProjectParty
@admin.register(ProjectParty)
class ProjectPartyAdmin(admin.ModelAdmin):
    list_display = ('project', 'party', 'share')
    list_filter = ('project', 'party')

# Admin for ProjectLedger with total amount display
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

# Admin for PartyProjectLedger with total amount display
@admin.register(PartyProjectLedger)
class PartyProjectLedgerAdmin(admin.ModelAdmin):
    list_display = ('party', 'project', 'paid_amount', 'received_amount', 'transaction_date')
    list_filter = ('party', 'project', 'transaction_date')
    change_list_template = 'admin/project/partyprojectledger/change_list.html'

    def changelist_view(self, request, extra_context=None):
        """Inject total received/paid for the current changelist queryset into the template context."""
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

# Admin for PartyLedger with total amount display
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

# Admin for Saddqah with export functionality
@admin.register(Saddqah)
class SaddqahAdmin(admin.ModelAdmin):
    list_display = ('party', 'amount', 'name', 'category', 'transaction_date')
    list_filter = ('party', 'category', 'transaction_date')
    search_fields = ('party__name', 'name')
    ordering = ('-transaction_date',)
    change_list_template = 'admin/project/saddqah/change_list.html'
    actions = ['export_as_csv', 'export_as_pdf']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(total_amount=Sum('amount'))
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response

    def export_as_csv(self, request, queryset):
        """Admin action: export selected Saddqah records as CSV."""
        if not queryset.exists():
            messages.warning(request, "No records selected for export.")
            return None
        f = io.StringIO()
        writer = csv.writer(f)
        header = ['ID', 'Party', 'Name', 'Category', 'Amount', 'Transaction Date']
        writer.writerow(header)
        for obj in queryset.select_related('party'):
            writer.writerow([
                obj.pk,
                getattr(obj.party, 'name', ''),
                obj.name or '',
                obj.category or '',
                str(obj.amount),
                obj.transaction_date.isoformat() if getattr(obj, 'transaction_date', None) else ''
            ])
        f.seek(0)
        resp = HttpResponse(f.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="saddqah_export.csv"'
        return resp
    export_as_csv.short_description = "Export selected Saddqah as CSV"

    def export_as_pdf(self, request, queryset):
        """Admin action: export selected Saddqah records as a simple PDF table.
        Requires reportlab: pip install reportlab
        """
        if not queryset.exists():
            messages.warning(request, "No records selected for export.")
            return None
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messages.error(request, "reportlab is required to export PDF. Install with: pip install reportlab")
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title = Paragraph("Saddqah Export", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [['ID', 'Party', 'Name', 'Category', 'Amount', 'Transaction Date']]
        for obj in queryset.select_related('party'):
            data.append([
                str(obj.pk),
                getattr(obj.party, 'name', ''),
                obj.name or '',
                obj.category or '',
                str(obj.amount),
                obj.transaction_date.isoformat() if getattr(obj, 'transaction_date', None) else ''
            ])

        table = Table(data, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (4,1), (4,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="saddqah_export.pdf"'
        return resp
    export_as_pdf.short_description = "Export selected Saddqah as PDF"

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
            saddqah_amounts[entry['transaction_date__month']-1] = float(entry.get('total') or 0)
        years = Saddqah.objects.dates('transaction_date', 'year').distinct()
        context = dict(
            admin.site.each_context(request),
            months=months,
            saddqah_amounts=saddqah_amounts,
            selected_year=year,
            years=[y.year for y in years],
        )
        return TemplateResponse(request, "admin/project/saddqah/report.html", context)

# Add dashboard URL to admin (wrap original get_urls safely)
# def get_admin_urls(original_get_urls):
#     def get_urls():
#         my_urls = [
#             path('dashboard/', admin.site.admin_view(SaddqahReportAdminView.dashboard_view), name='saddqah_dashboard'),
#         ]
#         return my_urls + original_get_urls()
#     return get_urls

# admin.site.get_urls = get_admin_urls(admin.site.get_urls)

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
            received_amounts[entry['transaction_date__month']-1] = float(entry.get('total_received') or 0)
            paid_amounts[entry['transaction_date__month']-1] = float(entry.get('total_paid') or 0)
        years = ProjectLedger.objects.dates('transaction_date', 'year').distinct()
        context = dict(
            admin.site.each_context(request),
            months=months,
            received_amounts=received_amounts,
            paid_amounts=paid_amounts,
            selected_year=year,
            years=[y.year for y in years],
        )
        return TemplateResponse(request, "admin/project/projectledger/report.html", context)

# Add dashboard URL to admin (wrap original get_urls safely)
def get_admin_urls(original_get_urls):
    def get_urls():
        my_urls = [
            path('report/saddqah/', admin.site.admin_view(SaddqahReportAdminView.dashboard_view), name='saddqah_report'),
            path('report/project-ledger/', admin.site.admin_view(ProjectLedgerReportAdminView.dashboard_view), name='project_ledger_report'),
        ]
        return my_urls + original_get_urls()
    return get_urls

admin.site.get_urls = get_admin_urls(admin.site.get_urls)

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

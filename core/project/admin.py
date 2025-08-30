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

# Admin for PartyLedger with total amount display
@admin.register(PartyLedger)
class PartyLedgerAdmin(admin.ModelAdmin):
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


# Custom admin view for Project Ledger reports
class ProjectLedgerReportAdminView:
    @staticmethod
    def dashboard_view(request):
        # filters
        project_param = request.GET.get('project', 'any')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')

        base_qs = ProjectLedger.objects.all()
        if project_param != 'any':
            try:
                base_qs = base_qs.filter(project_id=int(project_param))
            except ValueError:
                pass
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except ValueError:
                pass

        # detect whether transaction_date is DateTimeField to use __date lookup
        try:
            field_type = ProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(transaction_date__gte=sd)
        except Exception:
            pass

        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(transaction_date__lte=ed)
        except Exception:
            pass

        # aggregate by year+month
        ledger_data = (
            base_qs
            .values('transaction_date__year', 'transaction_date__month')
            .annotate(
                total_received=Sum('received_amount'),
                total_paid=Sum('paid_amount'),
            )
            .order_by('transaction_date__year', 'transaction_date__month')
        )

        rows = []
        total_received = total_paid = total_balance = 0.0
        for entry in ledger_data:
            y = entry['transaction_date__year']
            m = entry['transaction_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            rec = float(entry.get('total_received') or 0)
            paid = float(entry.get('total_paid') or 0)
            balance = rec - paid
            rows.append({
                'year': y,
                'month': month_name,
                'received': rec,
                'paid': paid,
                'balance': balance,
            })
            total_received += rec
            total_paid += paid
            total_balance += balance

        # dropdowns
        projects = Project.objects.order_by('name')
        years_qs = ProjectLedger.objects.dates('transaction_date', 'year').distinct()
        years = [y.year for y in years_qs]

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            total_received_all=total_received,
            total_paid_all=total_paid,
            total_balance_all=total_balance,
            projects=projects,
            years=years,
            selected_project=str(project_param),
            selected_year=str(year_param),
            start_date=start_date,
            end_date=end_date,
        )
        return TemplateResponse(request, "admin/project/projectledger/report.html", context)

    @staticmethod
    def export_pdf(request):
        """Export aggregated ProjectLedger rows (filtered) as PDF."""
        project_param = request.GET.get('project', 'any')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')

        base_qs = ProjectLedger.objects.all()
        if project_param != 'any':
            try:
                base_qs = base_qs.filter(project_id=int(project_param))
            except ValueError:
                pass
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except ValueError:
                pass

        try:
            field_type = ProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(transaction_date__gte=sd)
        except Exception:
            pass
        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(transaction_date__lte=ed)
        except Exception:
            pass

        ledger_data = (
            base_qs
            .values('transaction_date__year', 'transaction_date__month')
            .annotate(
                total_received=Sum('received_amount'),
                total_paid=Sum('paid_amount'),
            )
            .order_by('transaction_date__year', 'transaction_date__month')
        )

        rows = []
        total_received = total_paid = total_balance = 0.0
        for entry in ledger_data:
            y = entry['transaction_date__year']
            m = entry['transaction_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            rec = float(entry.get('total_received') or 0)
            paid = float(entry.get('total_paid') or 0)
            balance = rec - paid
            rows.append([str(y), month_name, f"{rec:.2f}", f"{paid:.2f}", f"{balance:.2f}"])
            total_received += rec
            total_paid += paid
            total_balance += balance

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messages.error(request, "reportlab is required to export PDF. Install with: pip install reportlab")
            return HttpResponse("reportlab required", status=400)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title = Paragraph("Project Ledger Export", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [['Year', 'Month', 'Received', 'Paid', 'Balance']]
        data.extend(rows)
        data.append(['', 'Totals:', f"{total_received:.2f}", f"{total_paid:.2f}", f"{total_balance:.2f}"])

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[60, 120, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="project_ledger_export.pdf"'
        return resp
# ...existing code...

# Add dashboard URL to admin (wrap original get_urls safely)
def get_admin_urls(original_get_urls):
    def get_urls():
        my_urls = [
            path('report/saddqah/', admin.site.admin_view(SaddqahReportAdminView.dashboard_view), name='saddqah_report'),
            path('report/project-ledger/', admin.site.admin_view(ProjectLedgerReportAdminView.dashboard_view), name='project_ledger_report'),
            path('report/project-ledger/export_pdf/', admin.site.admin_view(ProjectLedgerReportAdminView.export_pdf), name='project_ledger_export_pdf'),
            path('report/party-project-ledger/', admin.site.admin_view(PartyProjectLedgerReportAdminView.dashboard_view), name='party_project_ledger_report'),
            # export endpoint for party project ledger (uses same filters as the dashboard view)
            path('report/party-project-ledger/export_pdf/', admin.site.admin_view(PartyProjectLedgerReportAdminView.export_pdf), name='party_project_ledger_export_pdf'),
        ]
        return my_urls + original_get_urls()
    return get_urls

admin.site.get_urls = get_admin_urls(admin.site.get_urls)


# Custom admin view for Party Project Ledger reports
class PartyProjectLedgerReportAdminView:
    @staticmethod
    def dashboard_view(request):
        # read filters (use 'any' as the sentinel)
        year_param = request.GET.get('year', 'any')
        project_param = request.GET.get('project', 'any')
        party_param = request.GET.get('party', 'any')
        start_date = request.GET.get('start_date', '')  # expected YYYY-MM-DD or empty
        end_date = request.GET.get('end_date', '')      # expected YYYY-MM-DD or empty

        base_qs = PartyProjectLedger.objects.all()
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except ValueError:
                pass
        if project_param != 'any':
            try:
                base_qs = base_qs.filter(project_id=int(project_param))
            except ValueError:
                pass
        if party_param != 'any':
            try:
                base_qs = base_qs.filter(party_id=int(party_param))
            except ValueError:
                pass

        # apply start/end date filters if provided (expecting YYYY-MM-DD)
        # use __date lookup for DateTimeField, direct compare for DateField
        try:
            field_type = PartyProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True  # conservative default

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(transaction_date__gte=sd)
        except Exception:
            pass
        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(transaction_date__lte=ed)
        except Exception:
            pass

        # aggregate by year+month so we can list Year + Month rows
        ledger_data = (
            base_qs
            .values('transaction_date__year', 'transaction_date__month')
            .annotate(
                total_received=Sum('received_amount'),
                total_paid=Sum('paid_amount'),
                total_withdrawn=Sum('withdrawn_amount'),
            )
            .order_by('transaction_date__year', 'transaction_date__month')
        )

        rows = []
        total_received = total_paid = total_withdrawn = total_balance = 0.0
        for entry in ledger_data:
            y = entry['transaction_date__year']
            m = entry['transaction_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            rec = float(entry.get('total_received') or 0)
            paid = float(entry.get('total_paid') or 0)
            withdrawn = float(entry.get('total_withdrawn') or 0)
            balance = rec - withdrawn
            rows.append({
                'year': y,
                'month': month_name,
                'received': rec,
                'paid': paid,
                'withdrawn': withdrawn,
                'balance': balance,
            })
            total_received += rec
            total_paid += paid
            total_withdrawn += withdrawn
            total_balance += balance

        # values for dropdowns
        projects = Project.objects.order_by('name')
        parties = Party.objects.order_by('name')

        years_qs = PartyProjectLedger.objects.dates('transaction_date', 'year').distinct()
        years = [y.year for y in years_qs]

        # resolve selected names (for heading and PDF)
        selected_project_name = "Any"
        if project_param != 'any':
            try:
                selected_project_name = Project.objects.get(pk=int(project_param)).name
            except Exception:
                selected_project_name = "Unknown"

        selected_party_name = "Any"
        if party_param != 'any':
            try:
                selected_party_name = Party.objects.get(pk=int(party_param)).name
            except Exception:
                selected_party_name = "Unknown"

        selected_year_label = str(year_param) if year_param != 'any' else "Any"

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            total_received_all=total_received,
            total_paid_all=total_paid,
            total_withdrawn_all=total_withdrawn,
            total_balance_all=total_balance,
            selected_year=str(year_param),
            selected_project=str(project_param),
            selected_party=str(party_param),
            years=years,
            projects=projects,
            parties=parties,
            start_date=start_date,
            end_date=end_date,
            # new context items for display
            selected_project_name=selected_project_name,
            selected_party_name=selected_party_name,
            selected_year_label=selected_year_label,
        )
        return TemplateResponse(request, "admin/project/partyprojectledger/report.html", context)

    @staticmethod
    def export_pdf(request):
        """Export the currently filtered report rows as a simple PDF."""
        # Reuse same filtering logic as dashboard_view
        year_param = request.GET.get('year', 'any')
        project_param = request.GET.get('project', 'any')
        party_param = request.GET.get('party', 'any')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        base_qs = PartyProjectLedger.objects.all()
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except ValueError:
                pass
        if project_param != 'any':
            try:
                base_qs = base_qs.filter(project_id=int(project_param))
            except ValueError:
                pass
        if party_param != 'any':
            try:
                base_qs = base_qs.filter(party_id=int(party_param))
            except ValueError:
                pass

        # apply start/end date filters if provided (expecting YYYY-MM-DD)
        # use __date lookup for DateTimeField, direct compare for DateField
        try:
            field_type = PartyProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True  # conservative default

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(transaction_date__gte=sd)
        except Exception:
            pass
        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(transaction_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(transaction_date__lte=ed)
        except Exception:
            pass

        ledger_data = (
            base_qs
            .values('transaction_date__year', 'transaction_date__month')
            .annotate(
                total_received=Sum('received_amount'),
                total_paid=Sum('paid_amount'),
                total_withdrawn=Sum('withdrawn_amount'),
            )
            .order_by('transaction_date__year', 'transaction_date__month')
        )

        rows = []
        total_received = total_paid = total_withdrawn = total_balance = 0.0
        for entry in ledger_data:
            y = entry['transaction_date__year']
            m = entry['transaction_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            rec = float(entry.get('total_received') or 0)
            paid = float(entry.get('total_paid') or 0)
            withdrawn = float(entry.get('total_withdrawn') or 0)
            balance = rec - withdrawn
            rows.append([str(y), month_name, f"{rec:.2f}", f"{paid:.2f}", f"{withdrawn:.2f}", f"{balance:.2f}"])
            total_received += rec
            total_paid += paid
            total_withdrawn += withdrawn
            total_balance += balance

        # resolve selected names for PDF header
        selected_project_name = "Any"
        if project_param != 'any':
            try:
                selected_project_name = Project.objects.get(pk=int(project_param)).name
            except Exception:
                selected_project_name = "Unknown"

        selected_party_name = "Any"
        if party_param != 'any':
            try:
                selected_party_name = Party.objects.get(pk=int(party_param)).name
            except Exception:
                selected_party_name = "Unknown"

        selected_year_label = str(year_param) if year_param != 'any' else "Any"

        # build PDF
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            messages.error(request, "reportlab is required to export PDF. Install with: pip install reportlab")
            return HttpResponse("reportlab required", status=400)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title = Paragraph("Party Project Ledger Export", styles['Title'])
        elements.append(title)

        # add filter summary
        filter_line = f"Project: {selected_project_name}    Party: {selected_party_name}    Year: {selected_year_label}"
        if start_date or end_date:
            filter_line += "    Date Range: "
            filter_line += f"{start_date or 'Any'} - {end_date or 'Any'}"
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(filter_line, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [['Year', 'Month', 'Received', 'Paid', 'Withdrawn', 'Balance']]
        data.extend(rows)
        # totals row
        data.append(['', 'Totals:', f"{total_received:.2f}", f"{total_paid:.2f}", f"{total_withdrawn:.2f}", f"{total_balance:.2f}"])

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[60, 100, 80, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        # include project/party/year in filename (basic safe fallback)
        safe_project = selected_project_name.replace(' ', '_') if selected_project_name else 'Any'
        safe_party = selected_party_name.replace(' ', '_') if selected_party_name else 'Any'
        filename = f"party_project_ledger_{safe_project}_{safe_party}_{selected_year_label}.pdf"
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp

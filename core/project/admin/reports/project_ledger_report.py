from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
import datetime
from django.http import HttpResponse
from django.contrib import messages
import io
from project.models import ProjectLedger, Project


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



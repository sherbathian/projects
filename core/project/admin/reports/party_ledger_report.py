from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.contrib import messages
import datetime
import io
import json

from project.models import PartyLedger, Party  # adjust if your model names differ


class PartyLedgerReportAdminView:
    @staticmethod
    def dashboard_view(request):
        # filters
        year_param = request.GET.get('year', 'any')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        base_qs = PartyLedger.objects.all()
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except Exception:
                pass

        # detect whether transaction_date is DateTimeField to use __date lookup
        try:
            field_type = PartyLedger._meta.get_field('transaction_date').get_internal_type()
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

        # aggregate by paid_by & received_by
        aggregated = (
            base_qs
            .values('paid_by__name', 'received_by__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')
        )

        rows = []
        total_amount_all = 0.0
        for entry in aggregated:
            payer = entry.get('paid_by__name') or 'Unknown'
            receiver = entry.get('received_by__name') or 'Unknown'
            amt = float(entry.get('total_amount') or 0)
            rows.append({'paid_by': payer, 'received_by': receiver, 'amount': amt})
            total_amount_all += amt

        # years dropdown
        years_qs = PartyLedger.objects.dates('transaction_date', 'year').distinct()
        years = [y.year for y in years_qs]

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            rows_json=json.dumps(rows),
            total_amount_all=total_amount_all,
            years=years,
            selected_year=str(year_param),
            start_date=start_date,
            end_date=end_date,
        )
        return TemplateResponse(request, "admin/project/partyledger/report.html", context)

    @staticmethod
    def export_pdf(request):
        # same filtering logic as dashboard_view
        year_param = request.GET.get('year', 'any')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        base_qs = PartyLedger.objects.all()
        if year_param != 'any':
            try:
                base_qs = base_qs.filter(transaction_date__year=int(year_param))
            except Exception:
                pass

        try:
            field_type = PartyLedger._meta.get_field('transaction_date').get_internal_type()
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

        aggregated = (
            base_qs
            .values('paid_by__name', 'received_by__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')
        )

        rows = []
        total_amount_all = 0.0
        for entry in aggregated:
            payer = entry.get('paid_by__name') or 'Unknown'
            receiver = entry.get('received_by__name') or 'Unknown'
            amt = float(entry.get('total_amount') or 0)
            rows.append([payer, receiver, f"{amt:.2f}"])
            total_amount_all += amt

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
        elements.append(Paragraph("Party Ledger - Paid by / Received by", styles['Title']))
        elements.append(Spacer(1, 6))
        filter_line = f"Year: {year_param if year_param!='any' else 'Any'}"
        if start_date or end_date:
            filter_line += f"    Date Range: {start_date or 'Any'} - {end_date or 'Any'}"
        elements.append(Paragraph(filter_line, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [['Paid by', 'Received by', 'Total Amount']]
        data.extend(rows)

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[160, 160, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="party_ledger_paid_received.pdf"'
        return resp
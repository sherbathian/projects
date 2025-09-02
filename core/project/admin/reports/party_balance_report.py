from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.contrib import messages
import datetime
import io
import json

from project.models import PartyProjectLedger, Party


class PartyBalanceReportAdminView:
    @staticmethod
    def dashboard_view(request):
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        base_qs = PartyProjectLedger.objects.all()

        # detect field type (DateField vs DateTimeField)
        try:
            field_type = PartyProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = False

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

        agg = (
            base_qs
            .values('party__id', 'party__name')
            .annotate(
                total_received=Sum('received_amount'),
                total_withdrawn=Sum('withdrawn_amount'),
            )
            .order_by('party__name')
        )

        rows = []
        total_received_all = total_withdrawn_all = total_balance_all = 0.0
        for e in agg:
            name = e.get('party__name') or 'Unknown'
            rec = float(e.get('total_received') or 0)
            wdr = float(e.get('total_withdrawn') or 0)
            bal = rec - wdr
            rows.append({'party_name': name, 'received': rec, 'withdrawn': wdr, 'balance': bal})
            total_received_all += rec
            total_withdrawn_all += wdr
            total_balance_all += bal

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            rows_json=json.dumps(rows),
            total_received_all=total_received_all,
            total_withdrawn_all=total_withdrawn_all,
            total_balance_all=total_balance_all,
            start_date=start_date,
            end_date=end_date,
        )
        return TemplateResponse(request, "admin/project/party_balance/report.html", context)

    @staticmethod
    def export_pdf(request):
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        base_qs = PartyProjectLedger.objects.all()

        try:
            field_type = PartyProjectLedger._meta.get_field('transaction_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = False

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

        agg = (
            base_qs
            .values('party__name')
            .annotate(
                total_received=Sum('received_amount'),
                total_withdrawn=Sum('withdrawn_amount'),
            )
            .order_by('party__name')
        )

        rows = []
        total_received_all = total_withdrawn_all = total_balance_all = 0.0
        for e in agg:
            name = e.get('party__name') or 'Unknown'
            rec = float(e.get('total_received') or 0)
            wdr = float(e.get('total_withdrawn') or 0)
            bal = rec - wdr
            rows.append([name, f"{rec:.2f}", f"{wdr:.2f}", f"{bal:.2f}"])
            total_received_all += rec
            total_withdrawn_all += wdr
            total_balance_all += bal

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
        elements.append(Paragraph("Party Balances", styles['Title']))
        elements.append(Spacer(1, 6))
        if start_date or end_date:
            elements.append(Paragraph(f"Date range: {start_date or 'Any'} - {end_date or 'Any'}", styles['Normal']))
            elements.append(Spacer(1, 12))

        data = [['Party', 'Total Received', 'Total Withdrawn', 'Balance']]
        data.extend(rows)
        data.append(['Totals:', f"{total_received_all:.2f}", f"{total_withdrawn_all:.2f}", f"{total_balance_all:.2f}"])

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[200, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="party_balances.pdf"'
        return resp
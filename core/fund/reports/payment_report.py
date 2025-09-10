from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
import datetime
from fund.models import Payment
from django.http import HttpResponse
from django.contrib import messages
import io

# Custom admin view for Payment reports
class PaymentReportAdminView:
    @staticmethod
    def dashboard_view(request):
        # Filters
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')
        needy_param = request.GET.get('needy', 'any')

        base_qs = Payment.objects.all()

        if year_param != 'any':
            try:
                base_qs = base_qs.filter(payment_date__year=int(year_param))
            except ValueError:
                pass

        if needy_param != 'any':
            try:
                base_qs = base_qs.filter(needy_id=int(needy_param))
            except ValueError:
                pass

        # detect field type for payment_date
        try:
            field_type = Payment._meta.get_field('payment_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(payment_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(payment_date__gte=sd)
        except Exception:
            pass

        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(payment_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(payment_date__lte=ed)
        except Exception:
            pass

        # aggregate by year+month
        ledger_data = (
            base_qs
            .values('payment_date__year', 'payment_date__month')
            .annotate(
                total_amount=Sum('amount'),
            )
            .order_by('payment_date__year', 'payment_date__month')
        )

        rows = []
        total_amount = 0.0
        for entry in ledger_data:
            y = entry['payment_date__year']
            m = entry['payment_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            amount = float(entry.get('total_amount') or 0)
            rows.append({
                'year': y,
                'month': month_name,
                'amount': amount,
            })
            total_amount += amount

        # needy dropdown values (from related needy names if available)
        needies = []
        try:
            needies_qs = Payment.objects.values('needy__id', 'needy__name').distinct().order_by('needy__name')
            for n in needies_qs:
                nid = n.get('needy__id')
                nname = n.get('needy__name') or 'Unknown'
                if nid:
                    needies.append({'id': nid, 'name': nname})
        except Exception:
            needies = []

        # resolve selected needy name for display
        selected_needy_name = "Any"
        if needy_param != 'any':
            try:
                sel = Payment.objects.filter(needy_id=int(needy_param)).values_list('needy__name', flat=True).first()
                selected_needy_name = sel or "Unknown"
            except Exception:
                selected_needy_name = "Unknown"

        # dropdowns for years
        years_qs = Payment.objects.dates('payment_date', 'year').distinct()
        years = [y.year for y in years_qs]

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            years=years,
            total_amount=total_amount,
            selected_year=str(year_param),
            start_date=start_date,
            end_date=end_date,
            needies=needies,
            selected_needy=str(needy_param),
            selected_needy_name=selected_needy_name,
        )
        return TemplateResponse(request, "admin/payment/report.html", context)

    @staticmethod
    def export_pdf(request):
        """Export aggregated Payment rows (filtered) as PDF."""
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')
        needy_param = request.GET.get('needy', 'any')

        base_qs = Payment.objects.all()

        if year_param != 'any':
            try:
                base_qs = base_qs.filter(payment_date__year=int(year_param))
            except ValueError:
                pass

        if needy_param != 'any':
            try:
                base_qs = base_qs.filter(needy_id=int(needy_param))
            except ValueError:
                pass

        try:
            field_type = Payment._meta.get_field('payment_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(payment_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(payment_date__gte=sd)
        except Exception:
            pass
        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(payment_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(payment_date__lte=ed)
        except Exception:
            pass

        ledger_data = (
            base_qs
            .values('payment_date__year', 'payment_date__month')
            .annotate(
                total_amount=Sum('amount'),
            )
            .order_by('payment_date__year', 'payment_date__month')
        )

        rows = []
        total_amount = 0.0
        for entry in ledger_data:
            y = entry['payment_date__year']
            m = entry['payment_date__month']
            month_name = datetime.date(2000, m, 1).strftime('%B')
            rec = float(entry.get('total_amount') or 0)
            rows.append([str(y), month_name, f"{rec:.2f}"])
            total_amount += rec

        # resolve selected needy name for PDF header/filename
        selected_needy_name = "Any"
        if needy_param != 'any':
            try:
                sel = Payment.objects.filter(needy_id=int(needy_param)).values_list('needy__name', flat=True).first()
                selected_needy_name = sel or "Unknown"
            except Exception:
                selected_needy_name = "Unknown"

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
        title = Paragraph("Payment Export", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # add filter summary (include needy)
        filter_line = f"Year: {year_param if year_param!='any' else 'Any'}"
        filter_line += f"    Needy: {selected_needy_name}"
        if start_date or end_date:
            filter_line += f"    Date Range: {start_date or 'Any'} - {end_date or 'Any'}"
        elements.append(Paragraph(filter_line, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [['Year', 'Month', 'Amount']]
        data.extend(rows)
        data.append(['', 'Totals:', f"{total_amount:.2f}"])

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[60, 120, 120])
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
        safe_needy = selected_needy_name.replace(' ', '_') if selected_needy_name else 'Any'
        resp['Content-Disposition'] = 'attachment; filename="payment_export.pdf"'
        return resp



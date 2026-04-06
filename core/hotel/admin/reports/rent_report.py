from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
import datetime
from hotel.models import ShopRent, Shop
from django.http import HttpResponse
from django.contrib import messages
import io

# Custom admin view for Rent reports
class RentReportAdminView:
    @staticmethod
    def dashboard_view(request):
        # Filters
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')
        location_param = request.GET.get('location', 'any')

        base_qs = ShopRent.objects.select_related('shop')

        if year_param != 'any':
            try:
                base_qs = base_qs.filter(rent_date__year=int(year_param))
            except ValueError:
                pass

        if location_param != 'any':
            base_qs = base_qs.filter(shop__location=location_param)

        # detect field type for rent_date
        try:
            field_type = ShopRent._meta.get_field('rent_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(rent_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(rent_date__gte=sd)
        except Exception:
            pass

        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(rent_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(rent_date__lte=ed)
        except Exception:
            pass

        # aggregate by location and month
        ledger_data = (
            base_qs
            .values('shop__location', 'rent_date__year', 'rent_date__month')
            .annotate(
                total_amount=Sum('final_amount'),
            )
            .order_by('shop__location', 'rent_date__year', 'rent_date__month')
        )

        rows = []
        total_amount = 0.0
        for entry in ledger_data:
            location = entry['shop__location']
            location_display = dict(Shop.LOCATION_CHOICES).get(location, location)
            year = entry['rent_date__year']
            month = entry['rent_date__month']
            month_name = datetime.date(2000, month, 1).strftime('%B')
            amount = float(entry.get('total_amount') or 0)
            rows.append({
                'location': location_display,
                'year': year,
                'month': month_name,
                'amount': amount,
            })
            total_amount += amount

       

        # dropdowns for years and locations
        years_qs = ShopRent.objects.dates('rent_date', 'year').distinct()
        years = [y.year for y in years_qs]
        locations = Shop.LOCATION_CHOICES

        context = dict(
            admin.site.each_context(request),
            rows=rows,
            years=years,
            locations=locations,
            total_amount=total_amount,
            selected_year=str(year_param),
            selected_location=location_param,
            start_date=start_date,
            end_date=end_date,
        )
        return TemplateResponse(request, "admin/hotel/report.html", context)

    @staticmethod
    def export_pdf(request):
        """Export aggregated ShopRent rows (filtered) as PDF."""
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        year_param = request.GET.get('year', 'any')
        location_param = request.GET.get('location', 'any')

        base_qs = ShopRent.objects.select_related('shop')

        if year_param != 'any':
            try:
                base_qs = base_qs.filter(rent_date__year=int(year_param))
            except ValueError:
                pass

        if location_param != 'any':
            base_qs = base_qs.filter(shop__location=location_param)

        try:
            field_type = ShopRent._meta.get_field('rent_date').get_internal_type()
            is_datetime = field_type == 'DateTimeField'
        except Exception:
            is_datetime = True

        try:
            if start_date:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(rent_date__date__gte=sd)
                else:
                    base_qs = base_qs.filter(rent_date__gte=sd)
        except Exception:
            pass
        try:
            if end_date:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                if is_datetime:
                    base_qs = base_qs.filter(rent_date__date__lte=ed)
                else:
                    base_qs = base_qs.filter(rent_date__lte=ed)
        except Exception:
            pass

        ledger_data = (
            base_qs
            .values('shop__location', 'rent_date__year', 'rent_date__month')
            .annotate(
                total_amount=Sum('final_amount'),
            )
            .order_by('shop__location', 'rent_date__year', 'rent_date__month')
        )

        rows = []
        total_amount = 0.0
        for entry in ledger_data:
            location = entry['shop__location']
            location_display = dict(Shop.LOCATION_CHOICES).get(location, location)
            year = entry['rent_date__year']
            month = entry['rent_date__month']
            month_name = datetime.date(2000, month, 1).strftime('%B')
            rec = float(entry.get('total_amount') or 0)
            rows.append([location_display, str(year), month_name, f"{rec:.2f}"])
            total_amount += rec

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
        title = Paragraph("Rent Export", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # add filter summary
        filter_line = f"Year: {year_param if year_param!='any' else 'Any'}"
        if location_param != 'any':
            location_display = dict(Shop.LOCATION_CHOICES).get(location_param, location_param)
            filter_line += f"    Location: {location_display}"
        if start_date or end_date:
            filter_line += f"    Date Range: {start_date or 'Any'} - {end_date or 'Any'}"
        elements.append(Paragraph(filter_line, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [['Location', 'Year', 'Month', 'Amount']]
        data.extend(rows)
        data.append(['', '', 'Totals:', f"{total_amount:.2f}"])

        table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[120, 60, 80, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (2,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="rent_export.pdf"'
        return resp



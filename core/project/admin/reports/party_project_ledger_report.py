from django.contrib import admin, messages
from django.db.models import Sum
from django.http import HttpResponse
from django.template.response import TemplateResponse
import datetime
import io
from project.models import PartyProjectLedger, Project, Party

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
import csv
import io
from django.contrib import admin, messages
from django.db.models import Sum
from django.http import HttpResponse
from project.models import Saddqah


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

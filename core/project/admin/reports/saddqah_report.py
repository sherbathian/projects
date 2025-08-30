from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
import datetime
from project.models import Saddqah

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



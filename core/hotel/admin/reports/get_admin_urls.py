from django.urls import path
from django.contrib import admin
from hotel.admin.reports.rent_report import RentReportAdminView

def get_admin_urls(original_get_urls):
    def get_urls():
        my_urls = [
            path('report/rent/', admin.site.admin_view(RentReportAdminView.dashboard_view), name='rent_report'),
            path('report/rent/export_pdf/', admin.site.admin_view(RentReportAdminView.export_pdf), name='rent_report_export_pdf'),
        ]
        return my_urls + original_get_urls()
    return get_urls
admin.site.get_urls = get_admin_urls(admin.site.get_urls)
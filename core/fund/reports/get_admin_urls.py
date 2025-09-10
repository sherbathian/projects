from django.urls import path
from django.contrib import admin
from fund.reports.bank_report import BankReportAdminView
from fund.reports.payment_report import PaymentReportAdminView

def get_admin_urls(original_get_urls):
    def get_urls():
        my_urls = [
            path('report/bank/', admin.site.admin_view(BankReportAdminView.dashboard_view), name='bank_report'),
            path('report/bank/export_pdf/', admin.site.admin_view(BankReportAdminView.export_pdf), name='bank_report_export_pdf'),
            path('report/payment/', admin.site.admin_view(PaymentReportAdminView.dashboard_view), name='payment_report'),
            path('report/payment/export_pdf/', admin.site.admin_view(PaymentReportAdminView.export_pdf), name='payment_report_export_pdf'),
        ]
        return my_urls + original_get_urls()
    return get_urls
admin.site.get_urls = get_admin_urls(admin.site.get_urls)
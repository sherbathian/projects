from django.urls import path
from django.contrib import admin
from project.admin.reports.saddqah_report import SaddqahReportAdminView
from project.admin.reports.party_project_ledger_report import PartyProjectLedgerReportAdminView
from project.admin.reports.project_ledger_report import ProjectLedgerReportAdminView
from project.admin.reports.party_ledger_report import PartyLedgerReportAdminView
from project.admin.reports.party_balance_report import PartyBalanceReportAdminView

# Add dashboard URL to admin (wrap original get_urls safely)
def get_admin_urls(original_get_urls):
    def get_urls():
        my_urls = [
            path('report/saddqah/', admin.site.admin_view(SaddqahReportAdminView.dashboard_view), name='saddqah_report'),
            path('report/saddqah/export_pdf/', admin.site.admin_view(SaddqahReportAdminView.export_pdf), name='saddqah_report_export_pdf'),
            path('report/party-project-ledger/', admin.site.admin_view(PartyProjectLedgerReportAdminView.dashboard_view), name='party_project_ledger_report'),
            path('report/party-project-ledger/export_pdf/', admin.site.admin_view(PartyProjectLedgerReportAdminView.export_pdf), name='party_project_ledger_export_pdf'),
            path('report/project-ledger/', admin.site.admin_view(ProjectLedgerReportAdminView.dashboard_view), name='project_ledger_report'),
            path('report/project-ledger/export_pdf/', admin.site.admin_view(ProjectLedgerReportAdminView.export_pdf), name='project_ledger_export_pdf'),
            path('report/party-ledger/', admin.site.admin_view(PartyLedgerReportAdminView.dashboard_view), name='party_ledger_report'),
            path('report/party-ledger/export_pdf/', admin.site.admin_view(PartyLedgerReportAdminView.export_pdf), name='party_ledger_report_export_pdf'),
            path('report/party-balance/', admin.site.admin_view(PartyBalanceReportAdminView.dashboard_view), name='party_balance_report'),
            path('report/party-balance/export_pdf/', admin.site.admin_view(PartyBalanceReportAdminView.export_pdf), name='party_balance_report_export_pdf'),
        ]
        return my_urls + original_get_urls()
    return get_urls
admin.site.get_urls = get_admin_urls(admin.site.get_urls)
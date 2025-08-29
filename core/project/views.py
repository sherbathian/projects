from django.shortcuts import render
from .models import ProjectLedger, PartyProjectLedger, Saddqah

def dashboard(request):
    # Fetch data for the dashboard
    saddqah_data = Saddqah.objects.all()
    project_ledgers = ProjectLedger.objects.all()
    party_project_ledgers = PartyProjectLedger.objects.all()

    # Process data to get amounts per month, paid and received amounts
    # This is a placeholder for the actual data processing logic
    saddqah_amounts = sum(saddqah.amount for saddqah in saddqah_data)
    project_paid = sum(ledger.paid_amount for ledger in project_ledgers)
    project_received = sum(ledger.received_amount for ledger in project_ledgers)
    party_paid = sum(ledger.paid_amount for ledger in party_project_ledgers)
    party_received = sum(ledger.received_amount for ledger in party_project_ledgers)

    context = {
        'saddqah_amounts': saddqah_amounts,
        'project_paid': project_paid,
        'project_received': project_received,
        'party_paid': party_paid,
        'party_received': party_received,
    }

    return render(request, 'admin/dashboard/dashboard.html', context)



def report_view(request):
    # Fetch data for the report
    project_ledgers = ProjectLedger.objects.all()
    party_project_ledgers = PartyProjectLedger.objects.all()

    context = {
        'project_ledgers': project_ledgers,
        'party_project_ledgers': party_project_ledgers,
    }

    return render(request, 'admin/project/partyprojectledger/report.html', context)
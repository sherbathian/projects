from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal, ROUND_DOWN


## Project Model
class Project(models.Model):
    STATUS_CHOICES = [
        ('rented', 'Rented'),
        ('investment', 'Investment'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rented')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Projects'
        verbose_name = 'Project'


## Party Model
class Party(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Parties'
        verbose_name = 'Party'
    


## ProjectParty Model
class ProjectParty(models.Model):
    project = models.ForeignKey(Project, related_name='parties', on_delete=models.CASCADE)
    party = models.ForeignKey(Party, related_name='projects', on_delete=models.CASCADE)
    share = models.SmallIntegerField(default=0)  # Share percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.party.name} - {self.project.name} ({self.share}%)"
    
    class Meta:
        ordering = ['project', 'party']
        verbose_name_plural = 'Project Parties'
        verbose_name = 'Project Party'
        unique_together = ('project', 'party')


## ProjectLedger Model
class ProjectLedger(models.Model):
    project = models.ForeignKey(Project, related_name='ledgerPrject', on_delete=models.CASCADE)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    transaction_date = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.paid_amount} - {self.received_amount} on {self.transaction_date}"

    class Meta:
        ordering = ['project', 'transaction_date']
        verbose_name_plural = 'Project Ledgers'
        verbose_name = 'Project Ledger'


@receiver(post_save, sender=ProjectLedger)
def create_party_project_ledgers(sender, instance, created, **kwargs):
    """
    When a ProjectLedger is created with a received_amount, split that amount
    among the parties of the project according to their share and create
    PartyProjectLedger entries for each party.

    Behavior:
    - Runs only on create (not on update) to avoid duplicates.
    - If no received_amount or no project parties, does nothing.
    """
    if not created:
        return

    if not instance.received_amount:
        return

    # Safeguard: fetch project parties
    project_parties = instance.project.parties.all()
    if not project_parties.exists():
        return

    # Use a DB transaction to ensure all-or-nothing
    with transaction.atomic():
        total_received = Decimal(instance.received_amount)
        # Create PartyProjectLedger for each party proportional to share
        for pp in project_parties:
            try:
                share_pct = Decimal(pp.share or 0)
            except Exception:
                share_pct = Decimal(0)

            amount = (total_received * share_pct / Decimal(100)).quantize(Decimal('.01'), rounding=ROUND_DOWN)

            # Create ledger entry for the party
            PartyProjectLedger.objects.create(
                party=pp.party,
                project=instance.project,
                received_amount=amount,
                transaction_date=instance.transaction_date or None,
                comments=f"Auto split from ProjectLedger {instance.id}"
            )
        

## PartyProjectLedger Model
class PartyProjectLedger(models.Model):
    party = models.ForeignKey(Party, related_name='ledger', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='ledger', on_delete=models.CASCADE)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    withdrawn_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(blank=True, null=True)
    transaction_date = models.DateField()
    
    def __str__(self):
        return f"{self.party.name} - {self.project.name} ({self.transaction_date})"
    
    class Meta:
        ordering = ['party', 'project', 'transaction_date']
        verbose_name_plural = 'Party Project Ledgers'
        verbose_name = 'Party Project Ledger'

## PartyLedger Model
class PartyLedger(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, related_name='payments_made')
    received_by = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    transaction_date = models.DateField()
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.paid_by.name} to {self.received_by.name} - {self.amount} on {self.transaction_date}"    
    
    class Meta:
        ordering = ['transaction_date']
        verbose_name_plural = 'Party Ledgers'
        verbose_name = 'Party Ledger'


## Saddqah Model
class Saddqah(models.Model):
    
    CATEGORY_CHOICES = [
        ('relative', 'Relative'),
        ('cousin', 'Cousin'),
         ('bathian', 'Bathian'),
    ]
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    party = models.ForeignKey(Party, related_name='saddqahs', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    transaction_date = models.DateField()
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.party.name} -  ({self.amount})"
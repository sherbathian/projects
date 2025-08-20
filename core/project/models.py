from django.db import models


## Project Model
class Project(models.Model):
    STATUS_CHOICES = [
        ('rented', 'Rented'),
        ('investment', 'Investment'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rented')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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

## ProjectParty Model
class ProjectParty(models.Model):
    project = models.ForeignKey(Project, related_name='parties', on_delete=models.CASCADE)
    party = models.ForeignKey(Party, related_name='projects', on_delete=models.CASCADE)
    share = models.SmallIntegerField(default=0)  # Share percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.party.name} - {self.project.name} ({self.share}%)"

## PartyProjectLedger Model
class PartyProjectLedger(models.Model):
    party = models.ForeignKey(Party, related_name='ledger', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='ledger', on_delete=models.CASCADE)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(blank=True, null=True)
    transaction_date = models.DateField()
    
    def __str__(self):
        return f"{self.party.name} - {self.project.name} ({self.transaction_date})"
    
class PartyLedger(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, related_name='payments_made')
    received_by = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    transaction_date = models.DateField()
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.party.name} - {self.amount} on {self.transaction_date}"    

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
        return f"{self.party.name} - {self.project.name} ({self.amount})"
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

## Needy Model
class Needy(models.Model):
    CATEGORY_CHOICES = [
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
        ('byneed', 'By Need'),
    ]
    LOCATION_CHOICES = [
        ('bathian', 'Bathian'),
        ('relative', 'Relative'),
    ]
    NEEDTYPE_CHOICES = [
        ('windows', 'Windows'),
        ('hardship', 'Hardship'),
        ('sickness', 'Sickness'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='bathian')
    needtype = models.CharField(max_length=20, choices=NEEDTYPE_CHOICES, default='windows')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='monthly')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    detail = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Needy'
        verbose_name = 'Needy' 
        
        
## Payment Model     
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    needy = models.ForeignKey(Needy, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    year = models.PositiveIntegerField(editable=False)
    month = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')

    def save(self, *args, **kwargs):
        if self.payment_date:
            self.year = self.payment_date.year
            self.month = self.payment_date.month
        super().save(*args, **kwargs)
    
    def get_month_name(self):
        import calendar
        return calendar.month_name[self.month] if self.month else ""
    
    def __str__(self):
        return f"{self.needy.name} - {self.amount} ({self.payment_date})"
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name_plural = 'Payments'
        verbose_name = 'Payment'
        
        
## Bank Model
class Bank(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_made')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    date = models.DateField()
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Bank: {self.amount} paid by {self.paid_by} received by {self.received_by} on {self.date}"
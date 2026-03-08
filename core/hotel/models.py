from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date

User = get_user_model()

class Partner(models.Model):
    name = models.CharField(max_length=255)
    cnic = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=100, unique=True)
    share_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Partners'
        verbose_name = 'Partner'

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    cnic = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=100, unique=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Tenants'
        verbose_name = 'Tenant'

class Shop(models.Model):
    STATUS_CHOICES = [
        ('rent', 'Rent'),
        ('sold', 'Sold'),
        ('empty', 'Empty'),
    ]
    shop_no = models.CharField(max_length=10)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='empty')
    sold_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.shop_no

    class Meta:
        ordering = ['shop_no']
        verbose_name_plural = 'Shops'
        verbose_name = 'Shop'

    def get_balance(self):
        """
        Return total outstanding balance for this shop:
        total rents (use final_amount when present else amount) - total payments
        """
        total_final = self.rents.filter(final_amount__isnull=False).aggregate(total=Sum('final_amount'))['total'] or Decimal('0')
        total_amounts = self.rents.filter(final_amount__isnull=True).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_rents = (total_final or Decimal('0')) + (total_amounts or Decimal('0'))

        total_payments = self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return (total_rents or Decimal('0')) - (total_payments or Decimal('0'))

class ShopDetail(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='details')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    # partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_amount = models.DecimalField(max_digits=10, decimal_places=2)
    increment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    detail = models.TextField(blank=True)

    def __str__(self):
        return f"{self.shop.shop_no} - {self.tenant.name}"

    class Meta:
        verbose_name_plural = 'Shop Details'
        verbose_name = 'Shop Detail'
    
class ShopRent(models.Model):
   
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='rents')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_increment = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_percentage = models.BooleanField(default=False)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)
    rent_date = models.DateField()
    year = models.PositiveIntegerField(editable=False)
    month = models.PositiveIntegerField(editable=False)

    def save(self, *args, **kwargs):
        if self.rent_date:
            self.year = self.rent_date.year
            self.month = self.rent_date.month
        
        if self.amount and self.discount:
            if self.is_percentage:
                discount_amount = (self.amount * self.discount) / 100
            else:
                discount_amount = self.discount
            self.final_amount = self.amount - discount_amount
            
        super().save(*args, **kwargs)
    
    def get_month_name(self):
        import calendar
        return calendar.month_name[self.month] if self.month else ""
    
    def __str__(self):
        return f"{self.amount} ({self.rent_date})"

    class Meta:
        ordering = ['-rent_date']
        verbose_name_plural = 'Shop Rents'
        verbose_name = 'Shop Rent'

class ShopPayment(models.Model):

    PAYMENTTYPE_CHOICES = [
        ('rent', 'Rent'),
        ('security', 'Security'),
        ('installment', 'Installment'),
    ]
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENTTYPE_CHOICES, default='rent')
    payment_date = models.DateField()
    year = models.PositiveIntegerField(editable=False)
    month = models.PositiveIntegerField(editable=False)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.payment_date:
            self.year = self.payment_date.year
            self.month = self.payment_date.month
        super().save(*args, **kwargs)
    
    def get_month_name(self):
        import calendar
        return calendar.month_name[self.month] if self.month else ""
    
    def __str__(self):
        return f"{self.amount} ({self.payment_date})"
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name_plural = 'Shop Payments'
        verbose_name = 'Shop Payment'

class Expense(models.Model):
    
    TYPE_CHOICES = [
        ('salary', 'Salary'),
        ('electric', 'Electric'),
        ('water', 'Water'),
        ('registry', 'Registry'),
        ('other', 'Other'),
    ]
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    year = models.PositiveIntegerField(editable=False)
    month = models.PositiveIntegerField(editable=False)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.expense_date:
            self.year = self.expense_date.year
            self.month = self.expense_date.month
        super().save(*args, **kwargs)
    
    def get_month_name(self):
        import calendar
        return calendar.month_name[self.month] if self.month else ""
    
    def __str__(self):
        return f"{self.amount} ({self.expense_date})"
    
    class Meta:
        ordering = ['-expense_date']
        verbose_name_plural = 'Expenses'
        verbose_name = 'Expense'
    

class PartnerPayment(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    year = models.PositiveIntegerField(editable=False)
    month = models.PositiveIntegerField(editable=False)
    comments = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.payment_date:
            self.year = self.payment_date.year
            self.month = self.payment_date.month
        super().save(*args, **kwargs)
    
    def get_month_name(self):
        import calendar
        return calendar.month_name[self.month] if self.month else ""

    def __str__(self):
        return f"{self.partner.name} - {self.amount} ({self.payment_date})"
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name_plural = 'Partner Payments'
        verbose_name = 'Partner Payment'


def current_year():
    return date.today().year

def current_month():
    return date.today().month
        
class Bank(models.Model):
    year = models.PositiveIntegerField(default=current_year, editable=False)
    month = models.PositiveIntegerField(default=current_month, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    expense = models.DecimalField(max_digits=12, decimal_places=2)
    distribute = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # def get_month_name(self):
    #     import calendar
    #     return calendar.month_name[self.month] if self.month else ""
    
    def __str__(self):
        # Ensure we always return a string (was returning an int)
        # Prefer a readable label; fall back to the default object repr if needed.
        try:
            return str(self.year) if getattr(self, 'year', None) is not None else super().__str__()
        except Exception:
            return super().__str__()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Banks'
        verbose_name = 'Bank'
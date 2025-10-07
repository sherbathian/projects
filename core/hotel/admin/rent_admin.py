from django.contrib import admin
from hotel.models import ShopRent

@admin.register(ShopRent)
class ShopRentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'amount', 'is_increment', 'discount', 'is_percentage', 'final_amount', 'rent_date', 'year', 'month')
    list_filter = ( 'month', 'year')
    # search_fields = ('shop__shop_no')
    ordering = ('-rent_date',)
    fields = ('shop', 'amount',  'discount', 'is_percentage',  'rent_date')
    
    def save(self, *args, **kwargs):
        if self.amount and self.discount:
            if self.is_percentage:
                discount_amount = (self.amount * self.discount) / 100
            else:
                discount_amount = self.discount
            self.final_amount = self.amount - discount_amount
        super().save(*args, **kwargs)
    
    
    
    

from django.contrib import admin
from hotel.models import ShopRent, ShopPayment

@admin.register(ShopRent)
class ShopRentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'rent_date', 'amount', 'discount',  'final_amount','is_percentage',)
    list_filter = ('month', 'year')
    ordering = ('-rent_date',)
    fields = ('shop', 'amount',  'discount', 'is_percentage',  'rent_date')

@admin.register(ShopPayment)
class ShopPaymentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'payment_date', 'amount', 'year', 'month', 'balance_after_payment')
    list_filter = ('month', 'year')
    ordering = ('-payment_date',)
    fields = ('shop', 'amount', 'payment_type', 'payment_date', 'comments')

    def balance_after_payment(self, obj):
        # show remaining balance for the shop after this payment (current totals)
        bal = obj.shop.get_balance() if obj and obj.shop else None
        return f"{bal:.2f}" if bal is not None else ""
    balance_after_payment.short_description = 'Balance'






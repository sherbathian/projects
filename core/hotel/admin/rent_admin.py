from django.contrib import admin
from hotel.models import ShopRent, ShopPayment

class MonthNameListFilter(admin.SimpleListFilter):
    title = 'Month'
    parameter_name = 'month'
    template = 'admin/select_filter.html'  # Use select box for filter

    def lookups(self, request, model_admin):
        import calendar
        return [(i, calendar.month_name[i]) for i in range(1, 13)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(month=int(self.value()))
        return queryset

class PaymentYearListFilter(admin.SimpleListFilter):
    title = 'Year'
    parameter_name = 'year'
    template = 'admin/select_filter.html'  # Use select box

    def lookups(self, request, model_admin):
        years = ShopPayment.objects.values_list('year', flat=True).distinct().order_by('-year')
        return [(year, year) for year in years if year]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=int(self.value()))
        return queryset

class RentYearListFilter(admin.SimpleListFilter):
    title = 'Year'
    parameter_name = 'year'
    template = 'admin/select_filter.html'  # Use select box

    def lookups(self, request, model_admin):
        years = ShopRent.objects.values_list('year', flat=True).distinct().order_by('-year')
        return [(year, year) for year in years if year]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=int(self.value()))
        return queryset

@admin.register(ShopRent)
class ShopRentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'rent_date', 'amount', 'discount',  'final_amount','is_percentage',)
    list_filter = (MonthNameListFilter, RentYearListFilter)
    search_fields = ('shop__shop_no',)
    ordering = ('-rent_date',)
    fields = ('shop', 'amount',  'discount', 'is_percentage',  'rent_date')

@admin.register(ShopPayment)
class ShopPaymentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'payment_date', 'amount', 'balance_after_payment')
    list_filter = (MonthNameListFilter, PaymentYearListFilter)
    search_fields = ('shop__shop_no',)
    ordering = ('-payment_date',)
    fields = ('shop', 'amount', 'payment_type', 'payment_date', 'comments')

    def balance_after_payment(self, obj):
        # show remaining balance for the shop after this payment (current totals)
        bal = obj.shop.get_balance() if obj and obj.shop else None
        return f"{bal:.2f}" if bal is not None else ""
    balance_after_payment.short_description = 'Balance'






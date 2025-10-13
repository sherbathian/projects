from django.contrib import admin
from hotel.models import Expense

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

class YearListFilter(admin.SimpleListFilter):
    title = 'Year'
    parameter_name = 'year'
    template = 'admin/select_filter.html'  # Use select box

    def lookups(self, request, model_admin):
        years = Expense.objects.values_list('year', flat=True).distinct().order_by('-year')
        return [(year, year) for year in years if year]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=int(self.value()))
        return queryset


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('shop', 'type', 'amount', 'expense_date', 'comments')
    search_fields = ('shop__shop_no',)
    ordering = ('-expense_date',)
    list_filter = (MonthNameListFilter, YearListFilter)
    fields = ('shop', 'type', 'amount',   'expense_date', 'comments')
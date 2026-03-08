from django.contrib import admin
from django.db.models import Sum
from decimal import Decimal
from hotel.models import Bank


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
        years = Bank.objects.values_list('year', flat=True).distinct().order_by('-year')
        return [(y, str(y)) for y in years if y]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=int(self.value()))
        return queryset


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'total', 'expense', 'distribute', 'balance', 'created_at')
    list_filter = (MonthNameListFilter, YearListFilter)

    # Show labels (readonly callables) for computed values, and editable distribute.
    # Order: total (label), expense (label), balance (label), final (label), distribute (editable)
    fields = ('display_total', 'display_expense', 'display_balance', 'display_final', 'distribute')
    readonly_fields = ('display_total', 'display_expense', 'display_balance', 'display_final')

    # --- helpers ---------------------------------------------------------
    def _get_bank_cutoff_date(self, last_bank):
        if not last_bank:
            return None
        for name in ('created_at', 'rent_date', 'date', 'paid_at', 'transaction_date'):
            if hasattr(last_bank, name):
                return getattr(last_bank, name)
        return None

    def _date_field_for_model(self, model_cls):
        candidates = ('created_at', 'rent_date', 'date', 'paid_at', 'transaction_date')
        for f in model_cls._meta.fields:
            if getattr(f, 'name', None) in candidates:
                return f.name
        return None

    def _sum_qs(self, qs, *fields):
        for f in fields:
            agg = qs.aggregate(s=Sum(f))
            val = agg.get('s')
            if val is not None:
                # ensure Decimal
                return Decimal(str(val))
        return Decimal('0')

    def _compute_totals_and_prev_balance(self, last_bank):
        """
        Returns (total, expense, prev_balance) where:
         - total = sum ShopRent.final_amount or ShopRent.amount for records after cutoff (if cutoff available)
         - expense = sum Expense.amount for records after cutoff (if cutoff available)
         - prev_balance = last_bank.balance or 0
        """
        try:
            from hotel.models import ShopRent, Expense
        except Exception:
            ShopRent = None
            Expense = None

        cutoff = self._get_bank_cutoff_date(last_bank)

        total = Decimal('0')
        if ShopRent is not None:
            date_field = self._date_field_for_model(ShopRent)
            if cutoff and date_field:
                qs = ShopRent.objects.filter(**{f"{date_field}__gt": cutoff})
            else:
                qs = ShopRent.objects.all()
            total = self._sum_qs(qs,  'amount')

        expense = Decimal('0')
        if Expense is not None:
            date_field = self._date_field_for_model(Expense)
            if cutoff and date_field:
                qs = Expense.objects.filter(**{f"{date_field}__gt": cutoff})
            else:
                qs = Expense.objects.all()
            expense = self._sum_qs(qs, 'amount')

        prev_balance = Decimal(str(last_bank.balance)) if last_bank and getattr(last_bank, 'balance', None) is not None else Decimal('0')
        return total, expense, prev_balance

    # --- display callables used as readonly_fields -----------------------
    def display_total(self, obj):
        last_bank = Bank.objects.order_by('-created_at').first()
        total, _, _ = self._compute_totals_and_prev_balance(last_bank)
        return f"{total:.2f}"
    display_total.short_description = 'Total (auto)'

    def display_expense(self, obj):
        last_bank = Bank.objects.order_by('-created_at').first()
        _, expense, _ = self._compute_totals_and_prev_balance(last_bank)
        return f"{expense:.2f}"
    display_expense.short_description = 'Expense (auto)'

    def display_balance(self, obj):
        # show previous bank balance (if adding) or the instance's balance (if editing)
        if obj and getattr(obj, 'balance', None) is not None:
            try:
                return f"{Decimal(str(obj.balance)):.2f}"
            except Exception:
                return str(obj.balance)
        last_bank = Bank.objects.order_by('-created_at').first()
        _, _, prev_balance = self._compute_totals_and_prev_balance(last_bank)
        return f"{prev_balance:.2f}"
    display_balance.short_description = 'Balance (auto)'

    def display_final(self, obj):
        # prefer model value if editing and present
        if obj and getattr(obj, 'final', None) not in (None, ''):
            try:
                return f"{Decimal(str(obj.final)):.2f}"
            except Exception:
                return str(obj.final)
        last_bank = Bank.objects.order_by('-created_at').first()
        total, expense, prev_balance = self._compute_totals_and_prev_balance(last_bank)
        final_val = total + prev_balance - expense
        return f"{final_val:.2f}"
    display_final.short_description = 'Final (auto)'

    # --- form initial / save hooks --------------------------------------
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request) or {}
        last_bank = Bank.objects.order_by('-created_at').first()
        total, expense, prev_balance = self._compute_totals_and_prev_balance(last_bank)
        final = total + prev_balance - expense

        # set distribute default; actual numeric fields are written in save_model
        initial.update({
            'distribute': Decimal('0'),
        })
        # still provide numeric values for the model fields (not shown) so form.cleaned_data may contain them
        initial.update({
            'total': total,
            'expense': expense,
            'balance': prev_balance,
            'final': final,
        })
        return initial

    def save_model(self, request, obj, form, change):
        # compute totals from last bank and override/store to model fields automatically
        last_bank = Bank.objects.order_by('-created_at').first()
        total, expense, _ = self._compute_totals_and_prev_balance(last_bank)

        # set computed totals if not provided or to ensure server-side correctness
        try:
            obj.total = total
            obj.expense = expense
        except Exception:
            pass

        # compute final if not provided
        prev_balance = Decimal(str(last_bank.balance)) if last_bank and getattr(last_bank, 'balance', None) is not None else Decimal('0')
        if getattr(obj, 'final', None) in (None, ''):
            obj.final = total + prev_balance - expense
        else:
            # ensure Decimal
            obj.final = Decimal(str(obj.final))

        # compute balance as final - distribute (as requested)
        distribute = Decimal(getattr(obj, 'distribute', 0) or 0)
        obj.balance = (obj.final - distribute)

        super().save_model(request, obj, form, change)
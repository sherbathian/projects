from django.contrib import admin
from .models import Needy, Payment, Bank
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from django.db.models import Sum
from django.contrib import messages
import datetime
from django.template.response import TemplateResponse
from django import forms
from django.urls import path
from django.shortcuts import render, redirect


try:
    # import the module that performs admin.site.get_urls = get_admin_urls(...)
    from .reports import get_admin_urls  # noqa: F401
except Exception:
    # keep admin usable even if reports import fails
    pass

# Admin for Party

class NeedyResource(resources.ModelResource):

    class Meta:
        fields = ('name', 'amount', 'location', 'needtype', 'category', 'status', 'detail')
        model = Needy
        
@admin.register(Needy)
class NeedyAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ('name', 'amount', 'location', 'needtype', 'category', 'status', 'detail')
    list_filter = ('location', 'needtype', 'category', 'status')
    search_fields = ('name', 'detail')
    list_editable = ('status',)
    ordering = ('-id',)
    list_per_page = 20
    
    change_list_template = 'admin/needy/change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_amount=Sum('amount'),
                )
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response

class PaymentResource(resources.ModelResource):

    class Meta:
        fields = ('needy__name', 'amount', 'payment_date', 'year', 'month', 'status')
        model = Payment
        
class GeneratePaymentsForm(forms.Form):
    month = forms.ChoiceField(
        choices=[(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        label="Month"
    )
    year = forms.IntegerField(
        initial=datetime.datetime.now().year,
        label="Year"
    )

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
        years = Payment.objects.values_list('year', flat=True).distinct().order_by('-year')
        return [(year, year) for year in years if year]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=int(self.value()))
        return queryset

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ('needy', 'amount', 'payment_date', 'status')
    list_filter = ( 'status', 'payment_date', YearListFilter, MonthNameListFilter)
    search_fields = ('needy__name',)
    ordering = ('-payment_date', 'year', 'month',)   
    list_editable = ('status',)
    list_per_page = 20
    actions = ['mark_as_paid', 'mark_as_pending']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f"{updated} payment(s) marked as paid.")
    mark_as_paid.short_description = "Mark selected payments as Paid"

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f"{updated} payment(s) marked as pending.")
    mark_as_pending.short_description = "Mark selected payments as Pending"
    
    def needy(self, obj):
        return obj.needy.name
    needy.short_description = 'Needy'
    
    change_list_template = 'admin/payment/change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['generate_payments_url'] = 'generate_monthly_payments/'
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_amount=Sum('amount'),
                )
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate_monthly_payments/', self.admin_site.admin_view(self.generate_monthly_payments), name='generate_monthly_payments'),
        ]
        return custom_urls + urls
    
    def generate_monthly_payments(self, request):
        if request.method == 'POST':
            form = GeneratePaymentsForm(request.POST)
            if form.is_valid():
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])

                # If the 'confirm' flag is in the POST data, it's the confirmation step.
                if 'confirm' in request.POST:
                    payment_date = datetime.date(year, month, 1)
                    needies = Needy.objects.filter(status='active', category='monthly')
                    created_count = 0
                    for needyer in needies:
                        # Double-check existence to be safe and avoid duplicates
                        if not Payment.objects.filter(needy=needyer, year=year, month=month).exists():
                            Payment.objects.create(
                                needy=needyer,
                                amount=needyer.amount,
                                payment_date=payment_date,
                                year=year,
                                month=month,
                                status='pending'
                            )
                            created_count += 1
                    messages.success(request, f"{created_count} payments were successfully generated for {payment_date.strftime('%B %Y')}.")
                    return redirect('admin:fund_payment_changelist')

                # Otherwise, it's the first submission. Show the confirmation page.
                else:
                    active_monthly_needyers = Needy.objects.filter(status='active', category='monthly')
                    existing_payment_needy_ids = set(Payment.objects.filter(
                        year=year,
                        month=month,
                        needy__in=active_monthly_needyers
                    ).values_list('needy_id', flat=True))

                    needyers_to_pay = [s for s in active_monthly_needyers if s.id not in existing_payment_needy_ids]
                    needyers_with_existing_payment = [s for s in active_monthly_needyers if s.id in existing_payment_needy_ids]

                    context = dict(
                        self.admin_site.each_context(request),
                        month=month,
                        month_name=datetime.date(2000, month, 1).strftime('%B'),
                        year=year,
                        needyers_to_pay=needyers_to_pay,
                        needyers_with_existing_payment=needyers_with_existing_payment,
                        opts=self.model._meta, # For breadcrumbs
                    )
                    return render(request, "admin/payment/generate_monthly_payments_confirm.html", context)
        else:
            form = GeneratePaymentsForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            opts=self.model._meta, # For breadcrumbs
        )
        return render(request, "admin/payment/generate_monthly_payments.html", context)

class BankResource(resources.ModelResource):

    class Meta:
        fields = ('amount', 'paid_by', 'received_by', 'date', 'comments')
        model = Bank
        
@admin.register(Bank)
class BankAdmin(ImportExportModelAdmin, ExportActionMixin):
    list_display = ('amount', 'paid_by', 'received_by', 'date', 'comments')
    list_filter = ('date',)
    search_fields = ('comments',)
    ordering = ('-date',)
    def paid_by(self, obj):
        return obj.paid_by.name if obj.paid_by else ''
    paid_by.short_description = 'Paid By' 

    change_list_template = 'admin/needy/change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, 'context_data') or response.context_data is None:
            return response
        try:
            cl = response.context_data.get('cl')
            if cl is not None:
                qs = cl.queryset
                totals = qs.aggregate(
                    total_amount=Sum('amount'),
                )
                response.context_data['total_amount'] = totals.get('total_amount') or 0
        except Exception:
            response.context_data.setdefault('total_amount', 0)
        return response
  
  # ensure admin report URLs are registered


admin.site.site_header = "Donation Admin"
admin.site.site_title = "Donation Admin"
admin.site.index_title = "Welcome to the Donation Admin"    
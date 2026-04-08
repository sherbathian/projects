from django.contrib import admin
from django.contrib.admin import helpers
from hotel.models import Shop, ShopDetail, ShopRent, Tenant
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export.widgets import ForeignKeyWidget
from import_export import fields
from django.urls import path, reverse
from django import forms
from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
import calendar
from datetime import date
from decimal import Decimal
from django.shortcuts import redirect
# from django.db.models import Sum

class ShopResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        # accept user passed from admin and keep it for use during import
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save_instance(self, instance, *args, **kwargs):
        # set added_by from the authenticated user performing the import if not set
        if getattr(self, 'user', None) and not getattr(instance, 'added_by', None):
            instance.added_by = self.user
        # forward all args/kwargs (e.g. file_name) to the parent implementation
        return super().save_instance(instance, *args, **kwargs)

    class Meta:
        exclude = ('id',)
        import_id_fields = ('shop_no',)
        skip_unchanged = True
        fields = ('location', 'shop_no', 'status', 'amount', 'created_at')
        model = Shop

@admin.register(Shop)
class ShopAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ShopResource
    list_display = ('location', 'shop_no', 'status', 'sold_amount', 'balance', 'created_at')
    list_filter = ('location', 'status', 'created_at')
    search_fields = ('shop_no', 'detail')
    ordering = ('shop_no',)
    fields = ('location', 'shop_no', 'status', 'sold_amount', 'detail')
    actions = ['bulk_update_location']
    list_editable = ['location']
    list_display_links = ['shop_no']

    def get_resource_kwargs(self, request, *args, **kwargs):
        # pass the current user into the resource so imports can set added_by
        return {'user': request.user}

    def save_model(self, request, obj, form, change):
        # set added_by to the currently logged-in user on create (or if not set)
        if not change or not getattr(obj, 'added_by', None):
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def balance(self, obj):
        bal = obj.get_balance()
        return f"{bal:.2f}"
    balance.short_description = 'Balance'
    
    # change_list_template = 'admin/change_list.html'
    
    # def changelist_view(self, request, extra_context=None):
    #     response = super().changelist_view(request, extra_context=extra_context)
    #     if not hasattr(response, 'context_data') or response.context_data is None:
    #         return response
    #     try:
    #         cl = response.context_data.get('cl')
    #         if cl is not None:
    #             qs = cl.queryset
    #             totals = qs.aggregate(
    #                 total_balance=Sum('balance'),
    #             )
    #             response.context_data['total_balance'] = totals.get('total_balance') or 0
    #     except Exception:
    #         response.context_data.setdefault('total_balance', 0)
    #     return response

    def bulk_update_location(self, request, queryset):
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        return redirect(reverse('admin:hotel_shop_bulk_update_location') + '?ids=' + ','.join(selected))
    bulk_update_location.short_description = "Update location of selected shops"

    class LocationForm(forms.Form):
        location = forms.ChoiceField(choices=Shop.LOCATION_CHOICES)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('bulk-update-location/', self.admin_site.admin_view(self.bulk_update_location_view), name='hotel_shop_bulk_update_location'),
        ]
        return custom + urls

    def bulk_update_location_view(self, request):
        ids = [i for i in request.GET.get('ids', '').split(',') if i]
        if not ids:
            messages.error(request, 'No shops selected.')
            return redirect('admin:hotel_shop_changelist')
        shops = Shop.objects.filter(id__in=ids)
        if request.method == 'POST':
            form = self.LocationForm(request.POST)
            if form.is_valid():
                new_location = form.cleaned_data['location']
                count = shops.update(location=new_location)
                messages.success(request, f'Updated location for {count} shops.')
                return redirect('admin:hotel_shop_changelist')
        else:
            form = self.LocationForm()
        context = dict(
            self.admin_site.each_context(request),
            shops=shops,
            form=form,
            title='Bulk update location',
        )
        return TemplateResponse(request, 'admin/hotel/shop/bulk_update_location.html', context)

class ShopListFilter(admin.SimpleListFilter):
    title = 'Shop'
    parameter_name = 'shop'
    template = 'admin/select_filter.html'  # Use select box

    def lookups(self, request, model_admin):
        shops = set(ShopDetail.objects.values_list('shop__id', 'shop__shop_no'))
        return [(shop_id, shop_no) for shop_id, shop_no in shops if shop_id]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(shop__id=self.value())
        return queryset

class TenantListFilter(admin.SimpleListFilter):
    title = 'Tenant'
    parameter_name = 'tenant'
    template = 'admin/select_filter.html'  # Use select box

    def lookups(self, request, model_admin):
        tenants = set(ShopDetail.objects.values_list('tenant__id', 'tenant__name'))
        return [(tenant_id, name) for tenant_id, name in tenants if tenant_id]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tenant__id=self.value())
        return queryset

class ShopDetailResource(resources.ModelResource):
    
    shop = fields.Field(
        column_name='shop',
        attribute='shop',
        widget=ForeignKeyWidget(Shop, field='shop_no'))
    
    tenant = fields.Field(
        column_name='tenant',
        attribute='tenant',
        widget=ForeignKeyWidget(Tenant, field='cnic'))
    
    class Meta:
        # exclude = ('id', 'shop_id', 'tenant_id')
        # import_id_fields = ('shop__shop_no', 'tenant__cnic')
        # skip_unchanged = True
        fields = ('id', 'shop', 'tenant', 'rent_amount', 'security_amount', 'increment', 'start_date', 'detail') 
        model = ShopDetail
    
@admin.register(ShopDetail)
class ShopDetailAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ShopDetailResource
    change_list_template = "admin/hotel/shopdetail/change_list.html"
    list_display = ('shop', 'tenant', 'rent_amount', 'security_amount', 'increment', 'start_date', 'detail')
    # make the right-side filters render as dropdowns showing only related values
    list_filter = (ShopListFilter, TenantListFilter)
    search_fields = ('shop__shop_no', 'tenant__name')
    ordering = ('-id',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # restrict the shop dropdown on add/edit to shops with status == 'rent'
        if db_field.name == 'shop':
            qs = Shop.objects.filter(status='rent')
            # when editing, include the Shop already linked to this ShopDetail even if its status changed
            try:
                obj_id = request.resolver_match.kwargs.get('object_id')
                if obj_id:
                    sd = ShopDetail.objects.filter(pk=obj_id).select_related('shop').first()
                    if sd and sd.shop:
                        qs = qs | Shop.objects.filter(pk=sd.shop.pk)
            except Exception:
                # fallback: ignore resolver issues and use the rent queryset
                pass
            kwargs['queryset'] = qs.distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Only set initial values for new instances (when obj is None)
        if obj is None:
            form.base_fields['start_date'].initial = date.today()
            form.base_fields['increment'].initial = 10
        return form

    # --- bulk create rents admin view ------------------------------------------------
    class BulkRentForm(forms.Form):
        month = forms.ChoiceField(choices=[(i, calendar.month_name[i]) for i in range(1, 13)])
        year = forms.ChoiceField()

        def __init__(self, *args, **kwargs):
            current_year = date.today().year
            current_month = date.today().month
            years = [(y, str(y)) for y in range(current_year - 2, current_year + 6)]
            super().__init__(*args, **kwargs)
            self.fields['year'].choices = years
            # set defaults to current month/year
            self.fields['year'].initial = current_year
            self.fields['month'].initial = current_month

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('bulk-create-rents/', self.admin_site.admin_view(self.bulk_create_rents), name='hotel_shopdetail_bulk_create_rents'),
        ]
        return custom + urls

    def bulk_create_rents(self, request):
        if request.method == 'POST':
            form = self.BulkRentForm(request.POST)
            if form.is_valid():
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])
                created = 0
                skipped = 0
                shop_details = ShopDetail.objects.filter(shop__status='rent').select_related('shop').distinct()
                with transaction.atomic():
                    for sd in shop_details:
                        # skip if rent record already exists for that shop/year/month
                        exists = ShopRent.objects.filter(shop=sd.shop, year=year, month=month).exists()
                        if exists:
                            skipped += 1
                            continue
                        # apply annual increment (add ShopDetail.increment to base rent)
                        started_at = sd.start_date
                        now = date.today()
                        months_diff = (now.year - started_at.year) * 12 + (now.month - started_at.month)
                        # compute full years since start (annual increment)
                        years = months_diff // 12 if months_diff > 0 else 0
                        amount = sd.rent_amount or Decimal('0')
                        increment = sd.increment or Decimal('0')
                        if years > 0 and increment > 0:
                            increment = increment / 100 * sd.rent_amount
                            amount += increment * years
                            is_increment = True
                        else:
                            is_increment = False
                        final_amount = amount
                        rent_date = date(year, month, 1)
                        ShopRent.objects.create(
                            shop=sd.shop,
                            amount=amount,
                            is_increment=bool(is_increment),
                            discount=0,
                            is_percentage=False,
                            final_amount=final_amount,  # model save will compute year/month; final_amount remains None until save logic runs if any
                            rent_date=rent_date
                        )
                        created += 1
                messages.success(request, f'Created {created} rents, skipped {skipped} already-existing.')
                # Redirect back to changelist
                return TemplateResponse(request, 'admin/hotel/shopdetail/bulk_create_result.html', {'created': created, 'skipped': skipped})
        else:
            form = self.BulkRentForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title='Bulk create rents for all "rent" shops',
        )
        return TemplateResponse(request, 'admin/hotel/shopdetail/bulk_create_form.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_create_url'] = reverse('admin:hotel_shopdetail_bulk_create_rents')
        return super().changelist_view(request, extra_context=extra_context)

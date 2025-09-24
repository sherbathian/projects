from django.contrib import admin
from hotel.models import Shop, ShopDetail
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

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
        fields = ('shop_no', 'status', 'amount', 'created_at')
        model = Shop

@admin.register(Shop)
class ShopAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ShopResource
    list_display = ('shop_no', 'status', 'amount', 'added_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('shop_no', 'detail', 'added_by__username')
    ordering = ('shop_no',)
    fields = ('shop_no', 'status', 'amount', 'detail')

    def get_resource_kwargs(self, request, *args, **kwargs):
        # pass the current user into the resource so imports can set added_by
        return {'user': request.user}

    def save_model(self, request, obj, form, change):
        # set added_by to the currently logged-in user on create (or if not set)
        if not change or not getattr(obj, 'added_by', None):
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

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

    class Meta:
        exclude = ('id',)
        import_id_fields = ('shop__shop_no', 'tenant__name')
        skip_unchanged = True
        fields = ('shop__shop_no', 'tenant__name', 'rent_amount', 'security_amount', 'increment', 'detail') 
        model = ShopDetail
    
@admin.register(ShopDetail)
class ShopDetailAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ShopDetailResource
    list_display = ('shop', 'tenant', 'rent_amount', 'security_amount')
    # make the right-side filters render as dropdowns showing only related values
    list_filter = (ShopListFilter, TenantListFilter)
    search_fields = ('shop__shop_no', 'tenant__name')
    ordering = ('-id',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # restrict the shop dropdown on add/edit to shops with status == 'rent'
        if db_field.name == 'shop':
            kwargs['queryset'] = Shop.objects.filter(status='rent')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

from django.contrib import admin
from .models import Restaurant, UserRestaurant, Employee, Plan, Printer, Table, PrintJob

# Register your models here.

class UserRestaurantInline(admin.TabularInline):
    model = UserRestaurant
    extra = 0
    show_change_link = True

class EmployeeInline(admin.StackedInline):
    model = Employee
    extra = 0
    show_change_link = True


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    inlines = [UserRestaurantInline, EmployeeInline]
    readonly_fields = ('token',)
    search_fields = ('name', 'slug', 'token')
    list_display = ('name','token')
    fieldsets = (
        ('Restaurante', {
            'fields': ('name', 'email', 'phone', 'token', 'owner'),
            'classes': ('wide', 'extrapretty')
        }),
        ('Endereço', {
            'fields': ('postal_code', 'address', 'address_number', 'neighborhood', 'city', 'state', 'complement'),
            'classes': ('collapse', 'extrapretty')
        }),
        ("Configurações", {
            'fields': ('is_active', 'trial_ends'),
            'classes': ('collapse', 'extrapretty')
        }),
        ('Gorjeta', {
            'fields': ('default_tip_value', 'tip_aplyed_by_default', 'tip_type'),
            'classes': ('collapse', 'extrapretty')
        }),
        ('Caixa', {
            'fields': ('cashier_default_initial_value',),
            'classes': ('collapse', 'extrapretty')
        }),
    )

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'is_admin', 'restaurant')
    search_fields = ('name', 'code')
    list_display = ('name', 'code', 'restaurant', 'is_active', 'is_admin')
    fieldsets = (
        ('', {
            'fields': ('restaurant','name', 'code', 'neighborhood', 'cep'),
            'classes': ('wide', 'extrapretty')
        }),
        ('Financeiro', {
            'fields': ('sallary', 'payment_day', 'office'),
            'classes': ('collapse', 'extrapretty')
        }),
        ('Permissões', {
            'fields': ('is_admin', 'is_active', 'can_delete_item', 'can_delete_bill', 'can_transfer_order', 'can_change_payment', 'can_open_cashier', 'can_close_cashier'),
            'classes': ('collapse', 'extrapretty')
        }),
    )
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    pass

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    list_filter = ('is_active', 'restaurant')
    search_fields = ('name', )

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    pass

@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'printer', 'created', 'status', 'restaurant')
    list_filter = ('printer', 'status', 'created', 'restaurant')
    search_fields = ('id', 'printer__name', 'restaurant__name')
    date_hierarchy = 'created'
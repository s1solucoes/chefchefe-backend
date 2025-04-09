from django.contrib import admin
from .models import Restaurant, UserRestaurant, Employee, UserPermissions, Plan, Printer
from django.utils.translation import gettext_lazy as _

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
        (_('Restaurant'), {
            'fields': ('name', 'email', 'phone', 'token'),
            'classes': ('wide', 'extrapretty')
        }),
        (_('Address'), {
            'fields': ('postal_code', 'address', 'address_number', 'neighborhood', 'city', 'state', 'complement'),
            'classes': ('collapse', 'extrapretty')
        }),
        (_('Settings'), {
            'fields': ('is_active', 'trial_ends_at'),
            'classes': ('collapse', 'extrapretty')
        }),
        (_('Tips'), {
            'fields': ('default_tip_value', 'tip_aplyed_by_default', 'tip_type'),
            'classes': ('collapse', 'extrapretty')
        }),
        (_('Cashier'), {
            'fields': ('cashier_default_initial_value', 'order_last_sequencial_number'),
            'classes': ('collapse', 'extrapretty')
        }),
    )

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'is_admin', 'restaurant')
    search_fields = ('name', 'code')
    list_display = ('name', 'code', 'restaurant', 'is_active', 'is_admin')
    fieldsets = (
        (_('Info'), {
            'fields': ('restaurant','name', 'code', 'neighborhood', 'cep'),
            'classes': ('wide', 'extrapretty')
        }),
        (_('Financial'), {
            'fields': ('sallary', 'payment_day', 'office'),
            'classes': ('collapse', 'extrapretty')
        }),
        (_('Permissions'), {
            'fields': ('is_admin', 'is_active', 'can_delete_item', 'can_delete_bill', 'can_transfer_order', 'can_change_payment', 'can_open_cashier'),
            'classes': ('collapse', 'extrapretty')
        }),
    )

@admin.register(UserPermissions)
class UserPermissionsAdmin(admin.ModelAdmin):
    pass

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    pass

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    list_filter = ('is_active', 'restaurant')
    search_fields = ('name', )
from django.contrib import admin
from .models import Cashier, PaymentMethod, Sale, Transaction


@admin.register(Cashier)
class CashierAdmin(admin.ModelAdmin):
    list_display = ('identification', 'is_open', 'created', 'restaurant')
    list_filter = ('is_open', 'restaurant')
    date_hierarchy = 'created'
    search_fields = ('identification', 'restaurant__name')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'description', 'position', 'restaurant')
    list_filter = ('restaurant',)
    search_fields = ('method', 'description', 'restaurant__name')

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    show_change_link = True

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass
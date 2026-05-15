from django.contrib import admin
from .models import Cashier, PaymentMethod, Sale, Transaction


@admin.register(Cashier)
class CashierAdmin(admin.ModelAdmin):
    list_display = ('identification', 'is_open', 'created', 'restaurant')
    list_filter = ('is_open', 'restaurant')
    date_hierarchy = 'created'
    search_fields = ('identification', 'restaurant__name')

    actions = ['set_stats_url']

    def set_stats_url(self, request, queryset):
        for cashier in queryset:
            stats_url = f'http://192.168.46.21:8001/api/relatorio/?cashier_id={cashier.id}'
            cashier.stats_url = stats_url
            cashier.save()


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
    list_display = ('payment_method', 'sale', 'amount', 'status', 'created')
    list_filter = ('payment_method', 'status', 'created')
    search_fields = ('sale__code',)
from django.contrib import admin
from .models import Category, Product, ComplementGroup, Complement, Bill, Order, OrderComplement, BillGroup
# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    list_filter = ('is_active', 'restaurant')
    search_fields = ('name', 'restaurant')

class ProductComplementGroupInline(admin.TabularInline):
    model = ComplementGroup
    extra = 0
    show_change_link = True
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductComplementGroupInline]
    list_display = ('name', 'category', 'price', 'restaurant', 'position', 'printer')
    list_filter = ('category', 'restaurant', 'printer', 'is_active')
    search_fields = ('name', 'code')

class ComplementInline(admin.TabularInline):
    model = Complement
    extra = 0


@admin.register(ComplementGroup)
class ComplementGroupAdmin(admin.ModelAdmin):
    inlines = [ComplementInline]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    search_fields = ('number', 'identification', 'restaurant__name')

class OrderComplementInline(admin.TabularInline):
    model = OrderComplement
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderComplementInline]
    autocomplete_fields = ('bill', 'product', 'canceled_by', 'launched_by')
    list_display = ('number', 'product', 'quantity', 'total_price', 'status', 'bill', 'launched_by', 'canceled_by')
    list_filter = ('status', 'restaurant')
    list_display_links = ('number', 'product')
    readonly_fields = ('number', 'restaurant', 'id', 'created', 'modified')
    search_fields = ('product__name', 'number__exact')
    fieldsets = (
        ('', {
            'fields': ('restaurant','number', 'status', 'bill', 'product', 'product_name', 'quantity', 'unit_price', 'complements_price', 'total_price', 'notes', 'complements_details'),
            'classes': ('wide', 'extrapretty')
        }),
        ('Pessoas', {
            'fields': ('launched_by', 'launched_by_name', 'canceled_by', 'canceled_by_name'),
            'classes': ('collapse', 'extrapretty')
        }),
         ('Datas', {
            'fields': ('status_changed', 'created', 'modified'),
            'classes': ('collapse', 'extrapretty')
        }),
        ( 'Meta', {
            'fields': ('id', 'is_active', 'is_deleted'),
            'classes': ('collapse', 'extrapretty')
        }),
    )


@admin.register(BillGroup)
class BillGroupAdmin(admin.ModelAdmin):
    pass
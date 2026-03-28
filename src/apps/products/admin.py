from django.contrib import admin
from .models import Category, Product, ComplementGroup, Complement, Bill
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
    pass
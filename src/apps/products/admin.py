from django.contrib import admin
from .models import Category, Product, ComplementGroup, Complement, ProductComplementGroup, Bill
# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    list_filter = ('is_active', 'restaurant')
    search_fields = ('name', 'restaurant')

class ProductComplementGroupInline(admin.TabularInline):
    model = ProductComplementGroup
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductComplementGroupInline]
    list_display = ('name', 'category', 'price', 'restaurant', 'position', 'printer')
    list_filter = ('category', 'restaurant', 'printer', 'is_active')
    search_fields = ('name', 'code')


@admin.register(ComplementGroup)
class ComplementGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('complements',)

@admin.register(Complement)
class ComplementAdmin(admin.ModelAdmin):
    pass

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    pass
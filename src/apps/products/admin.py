from django.contrib import admin
from .models import Category, ProductBase, Product, ComplementGroup, Complement, ProductComplementGroup
# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    list_filter = ('is_active', 'restaurant')
    search_fields = ('name', 'restaurant')

@admin.register(ProductBase)
class ProductBaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_public', 'created_by')
    list_filter = ('is_active', 'is_public', 'category', 'created_by')
    search_fields = ('name', )


class ProductComplementGroupInline(admin.TabularInline):
    model = ProductComplementGroup
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductComplementGroupInline]
    list_display = ('name', 'category', 'price', 'restaurant', 'order', 'printer')
    list_filter = ('category', 'restaurant', 'printer', 'is_active')
    search_fields = ('name', 'code')


@admin.register(ComplementGroup)
class ComplementGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(Complement)
class ComplementAdmin(admin.ModelAdmin):
    pass
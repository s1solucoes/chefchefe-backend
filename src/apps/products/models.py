from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel, SoftDeletableModel
from django.utils.translation import gettext_lazy as _

from apps.restaurant.models import Restaurant, Printer

class BaseModel(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Category(BaseModel):
    name = models.CharField(_('name'), max_length=255)
    order = models.PositiveIntegerField(_('order'), default=0)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products_categories')

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name

class Complement(BaseModel):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, default='')
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=0.00)

    max = models.PositiveIntegerField(_('max'), default=1)
    min = models.PositiveIntegerField(_('min'), default=0)

    tag = models.CharField(_('tag'), max_length=255, blank=True, default='')

    order = models.PositiveIntegerField(_('order'), default=0)

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='complements')

    class Meta:
        verbose_name = _('complement')
        verbose_name_plural = _('complements')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name +' | ' + self.tag + ' | ' + str(self.price)

ComplementGroupRules = models.TextChoices('ComplementGroupRules', 'HIGH SUM MEDIAN')
class ComplementGroup(BaseModel):
    name = models.CharField(_('name'), max_length=255)
    tag = models.CharField(_('tag'), max_length=255, blank=True, default='')
    order = models.PositiveIntegerField(_('order'), default=0)
    rule = models.CharField(_('rule'), max_length=10, choices=ComplementGroupRules.choices, default=ComplementGroupRules.SUM)
    min = models.PositiveIntegerField(_('min'), default=0)
    max = models.PositiveIntegerField(_('max'), default=1)

    complements = models.ManyToManyField(Complement, related_name='complement_groups')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='complement_groups')

    class Meta:
        verbose_name = _('complement group')
        verbose_name_plural = _('complement groups')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name + ' | ' + self.tag + ' | ' + self.restaurant.name



ProductSellType = models.TextChoices('ProductSellType', 'UN KG')
class Product(TimeStampedModel, UUIDModel, SoftDeletableModel):
    name = models.CharField(_('name'), max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(_('description'), blank=True, default='')
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    code = models.CharField(_('code'), max_length=255, blank=True, default='')
    is_active = models.BooleanField(_('is active'), default=True)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products')
    sell_type = models.CharField(_('sell type'), max_length=10, choices=ProductSellType.choices, default=ProductSellType.UN)
    order = models.PositiveIntegerField(_('order'), default=0)



    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name

class ProductComplementGroup(UUIDModel, TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='complement_groups')
    complement_group = models.ForeignKey(ComplementGroup, on_delete=models.CASCADE, related_name='products')
    order = models.PositiveIntegerField(_('order'), default=0)

    class Meta:
        verbose_name = _('product complement group')
        verbose_name_plural = _('product complement groups')
        ordering = ['order']

    def __str__(self):
        return self.product.name + ' | ' + self.complement_group.name




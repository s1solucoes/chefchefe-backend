from decimal import Decimal

from django.db import models, transaction
from model_utils.models import TimeStampedModel, UUIDModel
from model_utils.fields import MonitorField
from apps.restaurant.models import Restaurant, Printer, Table, Employee, NumberIdCounter
from apps.financial.models import Sale

from django.utils import timezone

class BaseModel(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Category(BaseModel):
    name = models.CharField('nome', max_length=255)
    position = models.PositiveIntegerField('ordem', default=0)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products_categories')

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        ordering = ['position', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name
class ProductSellType(models.TextChoices):
    UN = 'UN', 'Unidade'
    KG = 'KG', 'Quilo'
class Product(BaseModel):
    name = models.CharField('nome', max_length=255)
    slug = models.SlugField('slug', max_length=255, blank=True, default='', db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    description = models.TextField('descrição', blank=True, default='')
    price = models.DecimalField('preço', max_digits=10, decimal_places=2)
    code = models.CharField('código', max_length=255, blank=True, default='', db_index=True)
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    sell_type = models.CharField('tipo de venda', max_length=10, choices=ProductSellType.choices, default=ProductSellType.UN)
    position = models.PositiveIntegerField('ordem', default=0)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products')


    class Meta:
        verbose_name = 'produto'
        verbose_name_plural = 'produtos'
        ordering = ['position', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name
class ComplementGroupRules(models.TextChoices):
    HIGH = 'HIGH', 'Maior'
    SUM = 'SUM', 'Soma'
    MEDIAN = 'MEDIAN', 'Mediana'

class ComplementGroup(BaseModel):
    name = models.CharField('nome', max_length=255)
    tag = models.CharField('tag', max_length=255, blank=True, default='')
    position = models.PositiveIntegerField('ordem', default=0)
    rule = models.CharField('regra', max_length=10, choices=ComplementGroupRules.choices, default=ComplementGroupRules.SUM)
    min = models.PositiveIntegerField('mínimo', default=0)
    max = models.PositiveIntegerField('máximo', default=1)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='complement_groups')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='complement_groups')

    class Meta:
        verbose_name = 'grupo de complementos'
        verbose_name_plural = 'grupos de complementos'
        ordering = ['position', 'name']

    def __str__(self):
        return self.name + ' | ' + self.tag + ' | ' + self.restaurant.name
class Complement(BaseModel):
    name = models.CharField('nome', max_length=255)
    description = models.TextField('descrição', blank=True, default='')
    price = models.DecimalField('preço', max_digits=10, decimal_places=2, default=0.00)

    max = models.PositiveIntegerField('max', default=1)
    min = models.PositiveIntegerField('min', default=0)

    tag = models.CharField('tag', max_length=255, blank=True, default='')

    position = models.PositiveIntegerField('ordem', default=0)

    complement_group = models.ForeignKey(ComplementGroup, on_delete=models.CASCADE, related_name='complements')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='complements')

    class Meta:
        verbose_name = 'complemento'
        verbose_name_plural = 'complementos'
        ordering = ['position', 'name']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name +' | ' + self.tag + ' | ' + str(self.price)

class Bill(BaseModel):
    number = models.PositiveIntegerField('número', default=0)
    identification = models.CharField('identificação', max_length=255, blank=True, default='')
    table=models.ForeignKey(Table, on_delete=models.SET_NULL, related_name='bills', null=True, blank=True)
    is_open = models.BooleanField('aberta', default=True)
    opened_at = models.DateTimeField('aberta em', null=True, blank=True)
    closed_at = models.DateTimeField('fechada em', null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='bills')

    opened_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='bills_opened', null=True, blank=True)
    opened_by_name = models.CharField('aberta por', max_length=255, blank=True, default='')

    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, related_name='bills', null=True, blank=True)

    class Meta:
        verbose_name = 'comanda'
        verbose_name_plural = 'comandas'
        ordering = ['-opened_at']

    def __str__(self):
        return f'Comanda {self.number} - {self.identification} - {self.restaurant.name}'
    
    def save(self, *args, **kwargs):
        if not self.opened_by_name and self.opened_by:
            self.opened_by_name = self.opened_by.name
        if self.is_open and not self.opened_at:
            self.opened_at = timezone.now()
        if not self.is_open and not self.closed_at and self.opened_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    


class BillGroup(BaseModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='bill_groups')
    bills = models.ManyToManyField(Bill, related_name='bill_groups', blank=True)

    def __str__(self):
        return f'Grupo de Comandas - {self.restaurant.name} - {self.created.strftime("%Y-%m-%d %H:%M:%S")}'

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendente'
    IN_PROGRESS = 'IN_PROGRESS', 'Em preparo'
    READY = 'READY', 'Pronto'
    DELIVERED = 'DELIVERED', 'Entregue'
    CANCELED = 'CANCELED', 'Cancelado'

class Order(BaseModel):
    number = models.PositiveIntegerField('número', default=0)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orders')
    product_name = models.CharField('nome do produto', max_length=255)
    notes = models.TextField('observações', blank=True, default='')
    status = models.CharField('status', max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    status_changed = MonitorField(monitor='status', blank=True, null=True, verbose_name='status changed')
    
    complements_price = models.DecimalField('preço dos complementos', max_digits=10, decimal_places=2, default=0.00)
    unit_price = models.DecimalField('preço unitário', max_digits=10, decimal_places=2, default=0.00)
    quantity = models.DecimalField('quantidade', max_digits=11, decimal_places=3, default=1)
    total_price = models.DecimalField('preço total', max_digits=10, decimal_places=2, default=0.00)

    canceled_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='orders_canceled', null=True, blank=True)
    canceled_by_name = models.CharField('cancelada por', max_length=255, blank=True, default='')
    cancel_notes = models.TextField('observações de cancelamento', blank=True, default='')

    launched_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='orders_launched', null=True, blank=True)
    launched_by_name = models.CharField('lançada por', max_length=255, blank=True, default='')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')

    complements_details = models.JSONField('detalhes dos complementos', blank=True, null=True)
    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-created']

    def __str__(self):
        return f'#{self.number}'
    
    def calculate_complements_price(self):
        self.complements_price = sum([complement.total_price for complement in self.complements.all()])
        self.save()
        
    def calculate_total_price(self):
        self.total_price = self.quantity * (self.unit_price + Decimal(self.complements_price))
        return self.save()
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.number == 0:
            self.number = NumberIdCounter.get_next(self.restaurant, 'order_number')
        if self.product:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.unit_price or self.unit_price == 0:
                self.unit_price = self.product.price
        if self.launched_by and not self.launched_by_name:
            self.launched_by_name = self.launched_by.name
        if self.canceled_by and not self.canceled_by_name:
            self.canceled_by_name = self.canceled_by.name
        return super().save(*args, **kwargs)
    
class OrderComplement(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='complements')
    complement = models.ForeignKey(Complement, on_delete=models.PROTECT, related_name='order_complements')
    complement_name = models.CharField('nome do complemento', max_length=255)
    quantity = models.DecimalField('quantidade', max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField('preço unitário', max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField('preço total', max_digits=10, decimal_places=2)
    class Meta:
        verbose_name = 'complemento do pedido'
        verbose_name_plural = 'complementos dos pedidos'
        ordering = ['-created']

    def __str__(self):
        return f'{self.complement_name} - {self.order}'
    
    def save(self, *args, **kwargs):
        if self.complement:
            if not self.complement_name:
                self.complement_name = self.complement.name
            if not self.unit_price or self.unit_price == 0:
                self.unit_price = self.complement.price
        if not self.total_price or self.total_price == 0:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    


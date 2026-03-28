from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel
from localflavor.br.models import BRCPFField, BRCNPJField
from phonenumber_field.modelfields import PhoneNumberField
from apps.crm.models import Customer
from model_utils.fields import MonitorField
from apps.restaurant.models import Employee, Restaurant
# Create your models here.

class BaseModel(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Cashier(BaseModel):
    identification = models.CharField('identificação', max_length=255)
    is_open = models.BooleanField('aberto', default=False)
    closed_at = models.DateTimeField('fechado em', null=True, blank=True)
    initial_value = models.DecimalField('valor inicial', max_digits=10, decimal_places=2, default=0.00)

    opened_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='cashiers_opened', null=True, blank=True)
    opened_by_name = models.CharField('aberto por', max_length=255, blank=True, default='')
    closed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='cashiers_closed', null=True, blank=True)
    closed_by_name = models.CharField('fechado por', max_length=255, blank=True, default='')

    final_value = models.DecimalField('valor final', max_digits=10, decimal_places=2, default=0.00)

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='cashiers')

    class Meta:
        verbose_name = 'caixa'
        verbose_name_plural = 'caixas'
        ordering = ['-created']

class MethodsChoices(models.TextChoices):
    CREDIT_CARD = 'CREDIT_CARD', 'Cartão de Crédito'
    DEBIT_CARD = 'DEBIT_CARD', 'Cartão de Débito'
    PIX = 'PIX', 'PIX'
    CASH = 'CASH', 'Dinheiro'
    OTHER = 'OTHER', 'Outro'

class PaymentMethod(BaseModel):
    method = models.CharField('método', max_length=20, choices=MethodsChoices.choices, default=MethodsChoices.CASH)
    description = models.CharField('descrição', max_length=255, blank=True, default='')
    postition = models.PositiveIntegerField('ordem', default=0)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='payment_methods')

    class Meta:
        verbose_name = 'método de pagamento'
        verbose_name_plural = 'métodos de pagamento'
        ordering = ['postition', 'method']

    def __str__(self):
        return f'{self.method} {self.description}' if self.method != MethodsChoices.OTHER else f'{self.description}'
    

class DiscountMethodChoices(models.TextChoices):
    PERCENTAGE = 'PERCENTAGE', 'Porcentagem'
    VALUE = 'VALUE', 'Valor'
    VALUE_VARIABLE = 'VALUE_VARIABLE', 'Valor Variável'
    PERCENTAGE_VARIABLE = 'PERCENTAGE_VARIABLE', 'Porcentagem Variável'

class DiscountCode(BaseModel):
    code = models.CharField('código', max_length=50, unique=True)
    method = models.CharField('método', max_length=20, choices=DiscountMethodChoices.choices, default=DiscountMethodChoices.VALUE)
    min_value = models.DecimalField('valor mínimo', max_digits=10, decimal_places=2, default=0.00)
    max_value = models.DecimalField('valor máximo', max_digits=10, decimal_places=2, default=0.00)
    
    users_allowed = models.ManyToManyField(Employee, related_name='discount_codes_allowed', blank=True, help_text='Funcionários que podem usar este código de desconto. Se vazio, todos os funcionários podem usar.')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='discount_codes')

    class Meta:
        verbose_name = 'código de desconto'
        verbose_name_plural = 'códigos de desconto'
        ordering = ['code']

    def __str__(self):
        return self.code


class SalesStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pendente'
    COMPLETED = 'COMPLETED', 'Concluída'
    CANCELED = 'CANCELED', 'Cancelada'

class Sale(BaseModel):
    cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE, related_name='sales')
    status = models.CharField('status', max_length=20, choices=SalesStatusChoices.choices, default=SalesStatusChoices.PENDING)
    status_changed = MonitorField('status changed', monitor='status', null=True, blank=True)

    subtotal = models.DecimalField('subtotal', max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField('desconto', max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField('total', max_digits=10, decimal_places=2, default=0.00)

    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, related_name='sales', null=True, blank=True)
    discount_code_code = models.CharField('código do desconto', max_length=50, blank=True, default='')
    discount_used_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='sales_with_discount_used', null=True, blank=True)
    discount_used_by_name = models.CharField('desconto usado por', max_length=255, blank=True, default='')

    client = models.ForeignKey(Customer, on_delete=models.SET_NULL, related_name='sales', null=True, blank=True)
    client_name = models.CharField('nome do cliente', max_length=255, blank=True, default=None, null=True)
    client_cpf = BRCPFField('cpf do cliente', blank=True, default=None, null=True)
    client_cnpj = BRCNPJField('cnpj do cliente', blank=True, default=None, null=True)
    client_phone = PhoneNumberField('telefone do cliente', blank=True, default=None, null=True, region='BR')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='sales')

    tip_value = models.DecimalField('valor da gorjeta', max_digits=10, decimal_places=2, default=0.00)
    tip_percentage = models.DecimalField('porcentagem da gorjeta', max_digits=5, decimal_places=2, default=0.00)

    canceled_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='sales_canceled', null=True, blank=True)
    canceled_by_name = models.CharField('cancelado por', max_length=255, blank=True, default='')

    description = models.TextField('descrição', blank=True, default='')

    class Meta:
        verbose_name = 'venda'
        verbose_name_plural = 'vendas'
        ordering = ['-created']


    
class Transaction(BaseModel):
    description = models.CharField('descrição', max_length=255, blank=True, default='')
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, related_name='transactions', null=True, blank=True)
    cashier = models.ForeignKey(Cashier, on_delete=models.SET_NULL, related_name='transactions', null=True, blank=True)

    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, related_name='transactions', null=True, blank=True)
    method_description = models.CharField('descrição do método', max_length=255, blank=True, default='')

    received_value = models.DecimalField('valor recebido', max_digits=10, decimal_places=2, default=0.00)
    exchange = models.DecimalField('troco', max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField('total', max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField('status', max_length=20, choices=SalesStatusChoices.choices, default=SalesStatusChoices.PENDING)
    status_changed = MonitorField('status changed', monitor='status', null=True, blank=True)

    canceled_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='transactions_canceled', null=True, blank=True)
    canceled_by_name = models.CharField('cancelado por', max_length=255, blank=True, default='')

    notes = models.TextField('observações', blank=True, default='')

    class Meta:
        verbose_name = 'transação'
        verbose_name_plural = 'transações'
        ordering = ['-created']



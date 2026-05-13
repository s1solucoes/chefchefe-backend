from django.db import models, transaction
from model_utils.models import TimeStampedModel, UUIDModel
from model_utils.fields import MonitorField
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.br.models import BRPostalCodeField, BRStateField
from apps.user.models import User
from django.db.models import F
import random
import string

class BaseModel(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

def generate_token():
    return ''.join(random.choices(string.ascii_uppercase, k=4)) + ''.join(random.choices(string.digits, k=4))

class TipTypes(models.TextChoices):
    PERCENTAGE = 'percentage', 'Porcentagem'
    Value = 'value', 'Valor'

class BillingTypes(models.TextChoices):
    BOLETO = 'BOLETO', 'Boleto'
    CREDIT_CARD = "CREDIT_CARD", 'Cartão de Crédito'
    PIX = "PIX", "PIX"

class CicleTypes(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Mensal'
    YEARLY = 'YEARLY', 'Anual'

class StatusChoices(models.TextChoices):
    TESTING = 'TESTING', 'Teste'
    ACTIVE = 'ACTIVE', 'Ativo'
    BLOCKED = 'BLOCKED', 'Bloqueado'
    CANCELLED = 'CANCELLED', 'Cancelado'


class Plan(BaseModel):
    title = models.CharField('título', max_length=255)
    cicle = models.CharField('ciclo', choices=CicleTypes.choices, default=CicleTypes.MONTHLY, max_length=11)
    value = models.DecimalField('valor', max_digits=10, decimal_places=2, default=0.0)
    listed = models.BooleanField('listado', default=True)
    is_active = models.BooleanField('ativo', default=True)
    days_trial = models.PositiveIntegerField('dias de teste', default=0)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['-created']

    def __str__(self):
        return self.title

class Restaurant(BaseModel):
    name = models.CharField('nome', max_length=255)
    email = models.EmailField('email', max_length=255, blank=True, default='')
    phone = PhoneNumberField('telefone', region='BR', blank=True, default='')
    owner = models.ForeignKey(User, verbose_name='proprietário', on_delete=models.CASCADE, related_name='restaurants')

    postal_code = BRPostalCodeField('cep', blank=True, default='')
    address = models.CharField('endereço', max_length=255, blank=True, default='')
    address_number = models.CharField('número', max_length=10, blank=True, default='')
    neighborhood = models.CharField('bairro', max_length=255, blank=True, default='')
    city = models.CharField('cidade', max_length=255, blank=True, default='')
    state = BRStateField('estado', blank=True, default='')
    complement = models.CharField('complemento', max_length=255, blank=True, default='')

    token = models.CharField('token', max_length=8, default=generate_token, db_index=True, unique=True)

    default_tip_value = models.DecimalField('valor padrão da gorjeta', max_digits=10, decimal_places=2, default=10.0)
    tip_aplyed_by_default = models.BooleanField('gorjeta aplicada por padrão', default=False)
    tip_type = models.CharField('tipo da gorjeta', choices=TipTypes.choices, default=TipTypes.PERCENTAGE, max_length=10)

    cashier_default_initial_value = models.DecimalField('valor inicial padrão do caixa', max_digits=10, decimal_places=2, default=0.0)

    status = models.CharField('status', choices=StatusChoices.choices, default=StatusChoices.TESTING, max_length=10)
    status_changed = MonitorField(monitor='status')
    trial_ends = models.DateField('fim do período de teste', blank=True, null=True)

    billing_type = models.CharField('tipo de cobrança', choices=BillingTypes.choices, default=BillingTypes.CREDIT_CARD, max_length=11)
    plan = models.ForeignKey(Plan, verbose_name='plano', on_delete=models.CASCADE, related_name='restaurants', blank=True, null=True)
    plan_value = models.DecimalField('valor do plano', max_digits=10, decimal_places=2, default=0.0)
    plan_cicle = models.CharField('ciclo do plano', choices=CicleTypes.choices, default=CicleTypes.MONTHLY, max_length=11)
    plan_start_date = models.DateTimeField('data de início do plano', blank=True, null=True)

    def get_next_order_group_code(self):
        try:
            cashier = self.cashiers.get(is_open=True)
            return cashier.get_next_order_group_code()
        except self.cashiers.model.DoesNotExist:
            raise ValueError('Não é possível gerar o código do grupo de pedidos porque não há caixa aberto para este restaurante.')

    class Meta:
        verbose_name = 'restaurante'
        verbose_name_plural = 'restaurantes'
        ordering = ['-created']

    def __str__(self):
        return self.name


class NumberIdCounter(models.Model):
    name = models.SlugField('name', max_length=255)
    value = models.PositiveIntegerField('value', default=0)
    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurant', on_delete=models.CASCADE, related_name='number_id_counters')

    class Meta:
        verbose_name = 'Ultimo ID'
        verbose_name_plural = 'Ultimos IDs'
        unique_together = ['name', 'restaurant']

    def __str__(self):
        return self.name + ' - ' + str(self.value)
    
    @classmethod
    def get_next(cls, restaurant, name):
        with transaction.atomic():
            counter, _ = cls.objects.select_for_update().get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={'value': 0}
            )

            counter.value = F('value') + 1
            counter.save()
            counter.refresh_from_db()

            return counter.value

class RoleTypes(models.TextChoices):
    OWNER = 'OWNER', 'Proprietário'
    MANAGER = 'MANAGER', 'Gerente'
    USER = 'USER', 'Usuário'

class UserRestaurant(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_restaurants')
    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurante', on_delete=models.CASCADE, related_name='user_restaurants')
    role = models.CharField('cargo', choices=RoleTypes.choices, default=RoleTypes.USER, max_length=10)
    class Meta:
        verbose_name = 'usuário do restaurante'
        verbose_name_plural = 'usuários do restaurante'
        ordering = ['-created']
        unique_together = ['user', 'restaurant']

    def __str__(self):
        return f'{self.user} - {self.restaurant}'
    
class Employee(BaseModel):
    code = models.CharField('código', max_length=20)
    name = models.CharField('nome', max_length=255)

    is_admin = models.BooleanField('é administrador', default=False)
    can_delete_item = models.BooleanField('pode excluir item', default=False)
    can_delete_bill = models.BooleanField('pode excluir comanda', default=False)
    can_transfer_order = models.BooleanField('pode transferir pedido', default=False)
    can_change_payment = models.BooleanField('pode alterar pagamento', default=False)
    can_open_cashier = models.BooleanField('pode abrir caixa', default=False)
    can_close_cashier = models.BooleanField('pode fechar caixa', default=False)

    office = models.CharField('cargo', max_length=255, blank=True, default='')
    sallary = models.DecimalField('salário', max_digits=10, decimal_places=2, default=0.0)
    payment_day = models.PositiveIntegerField('dia de pagamento', default=0)

    neighborhood = models.CharField('bairro', max_length=255, blank=True, default='')
    cep = BRPostalCodeField('cep', blank=True, default='')

    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurante', on_delete=models.CASCADE, related_name='employees')

    class Meta:
        verbose_name = 'funcionário'
        verbose_name_plural = 'funcionários'
        ordering = ['-created']
        unique_together = ['code', 'restaurant']

    def __str__(self):
        return f'{self.name} - {self.restaurant}'
    
class Printer(BaseModel):
    name = models.CharField('nome', max_length=255)
    font_size = models.PositiveIntegerField('tamanho da fonte', default=12)
    title_font_size = models.PositiveIntegerField('tamanho da fonte do título', default=16)
    paper_size = models.PositiveBigIntegerField('tamanho do papel', default=80, help_text="mm")
    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurante', on_delete=models.CASCADE, related_name='printers')

    class Meta:
        verbose_name = 'impressora'
        verbose_name_plural = 'impressoras'
        ordering = ['-created']
        unique_together = ['name', 'restaurant']

    def __str__(self):
        return self.name + ' - ' + self.restaurant.name
    
class Table(BaseModel):
    number = models.PositiveIntegerField('número')
    title = models.CharField('título', max_length=255, blank=True, default='')
    capacity = models.PositiveIntegerField('capacidade', default=2)
    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurante', on_delete=models.CASCADE, related_name='tables')

    class Meta:
        verbose_name = 'mesa'
        verbose_name_plural = 'mesas'
        ordering = ['number']
        unique_together = ['number', 'restaurant']

    def __str__(self):
        return f'Mesa {self.number} - {self.restaurant.name}'
    

class PrintJob(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        SENT = 'SENT', 'Enviado'
        ERROR = 'ERROR', 'Erro'
    printer = models.ForeignKey(Printer, verbose_name='impressora', on_delete=models.CASCADE, related_name='print_jobs')
    payload = models.JSONField('payload')
    status = models.CharField('status', choices=StatusChoices.choices, default=StatusChoices.PENDING, max_length=10)
    restaurant = models.ForeignKey(Restaurant, verbose_name='restaurante', on_delete=models.CASCADE, related_name='print_jobs')
    class Meta:
        verbose_name = 'tarefa de impressão'
        verbose_name_plural = 'tarefas de impressão'
        ordering = ['-created']

    def __str__(self):
        return f'Tarefa de impressão {self.id} - {self.printer.name} - {self.restaurant.name}'






from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel, StatusModel
from model_utils.fields import MonitorField
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.br.models import BRPostalCodeField, BRStateField
from apps.user.models import User
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
    PERCENTAGE = 'percentage', _('Percentage')
    Value = 'value', _('Value')

class BillingTypes(models.TextChoices):
    BOLETO = 'BOLETO', _('Boleto')
    CREDIT_CARD = "CREDIT_CARD", _('Credit Card')
    PIX = "PIX", _("PIX")

class CicleTypes(models.TextChoices):
    MONTHLY = 'MONTHLY', _('Monthly')
    YEARLY = 'YEARLY', _('Yearly')

class StatusChoices(models.TextChoices):
    TESTING = 'TESTING', _('Testing')
    ACTIVE = 'ACTIVE', _('Active')
    BLOCKED = 'BLOCKED', _('Blocked')
    CANCELLED = 'CANCELLED', _('Cancelled')


class Plan(TimeStampedModel, UUIDModel):
    title = models.CharField(_('title'), max_length=255)
    cicle = models.CharField(_('cicle'), choices=CicleTypes.choices, default=CicleTypes.MONTHLY, max_length=11)
    value = models.DecimalField(_('value'), max_digits=10, decimal_places=2, default=0.0)
    listed = models.BooleanField(_('listed'), default=True)
    is_active = models.BooleanField(_('is active'), default=True)
    days_trial = models.PositiveIntegerField(_('days trial'), default=0)

    class Meta:
        verbose_name = _('plan')
        verbose_name_plural = _('plans')
        ordering = ['-created']

    def __str__(self):
        return self.title

class Restaurant(BaseModel, StatusModel):
    name = models.CharField(_('name'), max_length=255)
    email = models.EmailField(_('email'), max_length=255, blank=True, default='')
    phone = PhoneNumberField(_('phone'), region='BR', blank=True, default='')

    postal_code = BRPostalCodeField(_('postal code'), blank=True, default='')
    address = models.CharField(_('address'), max_length=255, blank=True, default='')
    address_number = models.CharField(_('address number'), max_length=10, blank=True, default='')
    neighborhood = models.CharField(_('neighborhood'), max_length=255, blank=True, default='')
    city = models.CharField(_('city'), max_length=255, blank=True, default='')
    state = BRStateField(_('state'), blank=True, default='')
    complement = models.CharField(_('complement'), max_length=255, blank=True, default='')

    token = models.CharField(_('token'), max_length=8, default=generate_token, db_index=True, unique=True)

    default_tip_value = models.DecimalField(_('default tip value'), max_digits=10, decimal_places=2, default=10.0)
    tip_aplyed_by_default = models.BooleanField(_('tip aplied by default'), default=False)
    tip_type = models.CharField(_('tip type'), choices=TipTypes.choices, default=TipTypes.PERCENTAGE, max_length=10)

    cashier_default_initial_value = models.DecimalField(_('cashier default initial value'), max_digits=10, decimal_places=2, default=0.0)
    order_last_sequencial_number = models.PositiveIntegerField(_('order last sequencial number'), default=0)

    STATUS = StatusChoices.choices
    trial_ends_at = models.DateField(_('trial ends at'), blank=True, null=True)

    billing_type = models.CharField(_('billing type'), choices=BillingTypes.choices, default=BillingTypes.CREDIT_CARD, max_length=11)
    plan = models.ForeignKey(Plan, verbose_name=_('plan'), on_delete=models.CASCADE, related_name='restaurants', blank=True, null=True)
    plan_value = models.DecimalField(_('plan value'), max_digits=10, decimal_places=2, default=0.0)
    plan_cicle = models.CharField(_('plan cicle'), choices=CicleTypes.choices, default=CicleTypes.MONTHLY, max_length=11)
    plan_start_date = models.DateTimeField(_('plan start date'), blank=True, null=True)

    def get_next_order_group_code(self):
        try:
            cashier = self.cashiers.get(is_open=True)
            return cashier.get_next_order_group_code()
        except self.cashiers.model.DoesNotExist:
            raise ValueError(_('There is no open cashier for this restaurant'))

    class Meta:
        verbose_name = _('restaurant')
        verbose_name_plural = _('restaurants')
        ordering = ['-created']

    def __str__(self):
        return self.name
    
    def get_next_order_group_number(self):
        self.order_last_sequencial_number += 1
        self.save()
        return self.order_last_sequencial_number


class PermissionsMethods(models.TextChoices):
    CREATE = 'CREATE', _('Create')
    READ = 'READ', _('Read')
    UPDATE = 'UPDATE', _('Update')
    DELETE = 'DELETE', _('Delete')

class UserPermissions(BaseModel):
    permission = models.CharField(_('permission'), max_length=255, unique=True)
    method = models.CharField(_('method'), choices=PermissionsMethods.choices, default=PermissionsMethods.READ, max_length=10)

    class Meta:
        verbose_name = _('user permission')
        verbose_name_plural = _('users permissions')
        ordering = ['permission']

    def __str__(self):
        return self.permission + ' | ' + self.method
    
class RoleTypes(models.TextChoices):
    OWNER = 'OWNER', _('Owner')
    MANAGER = 'MANAGER', _('Manager')
    USER = 'USER', _('User')

class UserRestaurant(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_restaurants')
    restaurant = models.ForeignKey(Restaurant, verbose_name=_('restaurant'), on_delete=models.CASCADE, related_name='user_restaurants')
    role = models.CharField(_('role'), choices=RoleTypes.choices, default=RoleTypes.USER, max_length=10)
    permission = models.ManyToManyField(UserPermissions, verbose_name=_('permissions'), blank=True)

    class Meta:
        verbose_name = _('user restaurant')
        verbose_name_plural = _('users restaurants')
        ordering = ['-created']
        unique_together = ['user', 'restaurant']

    def __str__(self):
        return f'{self.user} - {self.restaurant}'
    
class Employee(TimeStampedModel, UUIDModel):
    code = models.CharField(_('code'), max_length=20)
    name = models.CharField(_('name'), max_length=255)
    
    is_active = models.BooleanField(_('is active'), default=True)
    is_admin = models.BooleanField(_('is admin'), default=False)
    can_delete_item = models.BooleanField(_('can delete item'), default=False)
    can_delete_bill = models.BooleanField(_('can delete bill'), default=False)
    can_transfer_order = models.BooleanField(_('can transfer order'), default=False)
    can_change_payment = models.BooleanField(_('can change payment'), default=False)
    can_open_cashier = models.BooleanField(_('can open cashier'), default=False)
    can_login_on_desktop = models.BooleanField(_('can login on desktop'), default=False)

    office = models.CharField(_('office'), max_length=255, blank=True, default='')
    sallary = models.DecimalField(_('sallary'), max_digits=10, decimal_places=2, default=0.0)
    payment_day = models.PositiveIntegerField(_('payment day'), default=0)

    neighborhood = models.CharField(_('neighborhood'), max_length=255, blank=True, default='')
    cep = BRPostalCodeField(_('cep'), blank=True, default='')

    restaurant = models.ForeignKey(Restaurant, verbose_name=_('restaurant'), on_delete=models.CASCADE, related_name='employees')

    class Meta:
        verbose_name = _('employee')
        verbose_name_plural = _('employees')
        ordering = ['-created']
        unique_together = ['code', 'restaurant']

    def __str__(self):
        return f'{self.name} - {self.restaurant}'
    
class Printer(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(_('is active'), default=True)
    name = models.CharField(_( 'name'), max_length=255)
    font_size = models.PositiveIntegerField(_('font size'), default=12)
    title_font_size = models.PositiveIntegerField(_('title font size'), default=16)
    paper_size = models.PositiveBigIntegerField(_('paper size'), default=80, help_text="mm")
    restaurant = models.ForeignKey(Restaurant, verbose_name=_('restaurant'), on_delete=models.CASCADE, related_name='printers')

    class Meta:
        verbose_name = _('printer')
        verbose_name_plural = _('printers')
        ordering = ['-created']
        unique_together = ['name', 'restaurant']

    def __str__(self):
        return self.name + ' - ' + self.restaurant.name
    







from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel
from apps.restaurant.models import Restaurant
from localflavor.br.models import BRCPFField, BRCNPJField
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class BaseModel(TimeStampedModel, UUIDModel):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Customer(BaseModel):
    name = models.CharField('nome', max_length=255)
    cpf = BRCPFField('cpf', blank=True, default=None, null=True)
    cnpj = BRCNPJField('cnpj', blank=True, default='', null=True)
    phone = PhoneNumberField('telefone', blank=True, default=None, null=True, region='BR')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='customers')

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['-created']

    def __str__(self):
        return self.name + ' | ' + self.restaurant.name

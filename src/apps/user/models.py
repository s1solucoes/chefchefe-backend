from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from model_utils.models import TimeStampedModel, UUIDModel
from model_utils.fields import MonitorField

class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel, UUIDModel):
    email = models.EmailField(_('email address'), unique=True)
    phone = PhoneNumberField(_('phone'), region='BR')
    verified_email = models.BooleanField(_('verified email'), default=False)
    verified_email_at = MonitorField(monitor='verified_email')
    verified_phone = models.BooleanField(_('verified phone'), default=False)
    verified_phone_at = MonitorField(monitor='verified_phone')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()
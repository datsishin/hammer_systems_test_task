import random
import string

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# from referral_system.settings import AUTH_USER_MODEL


def generate_referral_code():
    return ''.join((random.sample(string.ascii_lowercase + string.digits, 6)))


class User(models.Model):
    phone_number = models.CharField(unique=True, max_length=11, blank=False, null=False)
    invite_code = models.CharField(max_length=6, blank=True, null=True)
    ref_code = models.CharField(max_length=6,
                                blank=False,
                                null=False,
                                editable=False,
                                unique=True,
                                default=generate_referral_code)
    email = models.EmailField(unique=True, blank=False, null=False)
    secret_code = models.CharField(max_length=4, blank=True, null=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']
    is_anonymous = False
    is_authenticated = True
    is_active = True

    def __str__(self):
        return self.phone_number


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Referral(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    referral = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral')

    def __str__(self):
        return self.user.phone_number

    class Meta:
        unique_together = ['user', 'referral']

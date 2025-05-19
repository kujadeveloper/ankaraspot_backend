from django.db import models
from django.conf import settings
from decimal import Decimal

class Balance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)

    def __str__(self):
        username = self.user.username if self.user else 'No user'
        amount = format(self.amount or Decimal('0.00'), '.2f')
        return f"{username} - {amount}"

class Transaction(models.Model):
    balance = models.ForeignKey(Balance, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user = self.balance.user.username if self.balance and self.balance.user else 'No user'
        amount = self.amount or 0.00
        time = self.timestamp or 'No timestamp'
        return f"{user} - {amount} - {time}"
from rest_framework import serializers
from .models import Balance, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'timestamp', 'description']

class BalanceSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Balance
        fields = ['user', 'amount', 'transactions']

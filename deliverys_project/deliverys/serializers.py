from rest_framework import serializers
from .models import Поставки

class DeliverysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Поставки
        fields = ('id', 'order_id', 'amount_dol', 'amount_rub', 'delivery')
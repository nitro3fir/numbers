from .models import Поставки
from .serializers import DeliverysSerializer
from rest_framework import generics

class DeliverysListCreate(generics.ListCreateAPIView):
    queryset = Поставки.objects.all().order_by("id")
    serializer_class = DeliverysSerializer
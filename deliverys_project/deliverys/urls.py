from django.urls import path
from . import views

urlpatterns = [
    path('api/deliverys/', views.DeliverysListCreate.as_view()),
]
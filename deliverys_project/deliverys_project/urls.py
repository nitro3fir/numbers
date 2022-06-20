from django.urls import path, include

urlpatterns = [
    path('', include('deliverys.urls')),
    path('', include('frontend.urls'))
]
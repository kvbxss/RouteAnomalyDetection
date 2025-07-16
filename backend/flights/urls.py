from django.urls import path
from .views import flight_anomalies

urlpatterns = [
    path('flights/<str:flight_id>/', flight_anomalies)
]
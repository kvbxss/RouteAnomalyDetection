from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlightViewSet, AnomalyDetectionViewSet, DataSourceViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'flights', FlightViewSet)
router.register(r'anomalies', AnomalyDetectionViewSet)
router.register(r'data-sources', DataSourceViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
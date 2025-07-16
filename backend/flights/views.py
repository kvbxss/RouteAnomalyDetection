from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Flight, AnomalyDetection, DataSource
from .serializers import FlightSerializer, AnomalyDetectionSerializer, DataSourceSerializer


class FlightViewSet(viewsets.ModelViewSet):
    """ViewSet for Flight model with full CRUD operations"""
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['origin', 'destination', 'aircraft_id']
    search_fields = ['flight_id', 'aircraft_id', 'origin', 'destination']
    ordering_fields = ['timestamp', 'altitude', 'speed']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Custom queryset with optional filtering"""
        queryset = Flight.objects.all()
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset

    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        """Get all anomalies for a specific flight"""
        flight = self.get_object()
        anomalies = flight.anomaly_detections.all()
        serializer = AnomalyDetectionSerializer(anomalies, many=True)
        return Response(serializer.data)


class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for AnomalyDetection model"""
    queryset = AnomalyDetection.objects.all()
    serializer_class = AnomalyDetectionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['anomaly_type', 'is_reviewed', 'is_false_positive']
    search_fields = ['flight__flight_id', 'flight__aircraft_id']
    ordering_fields = ['detected_at', 'confidence_score']
    ordering = ['-detected_at']

    def get_queryset(self):
        """Custom queryset with filtering options"""
        queryset = AnomalyDetection.objects.select_related('flight')
        
        # Filter by confidence score range
        min_confidence = self.request.query_params.get('min_confidence')
        max_confidence = self.request.query_params.get('max_confidence')
        
        if min_confidence:
            queryset = queryset.filter(confidence_score__gte=float(min_confidence))
        if max_confidence:
            queryset = queryset.filter(confidence_score__lte=float(max_confidence))
            
        # Filter by high confidence anomalies
        high_confidence_only = self.request.query_params.get('high_confidence_only')
        if high_confidence_only and high_confidence_only.lower() == 'true':
            queryset = queryset.filter(confidence_score__gt=0.8)
            
        return queryset

    @action(detail=False, methods=['get'])
    def needs_review(self, request):
        """Get anomalies that need human review"""
        anomalies = self.get_queryset().filter(
            is_reviewed=False,
            confidence_score__gt=0.8
        )
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        """Mark an anomaly as reviewed"""
        anomaly = self.get_object()
        anomaly.is_reviewed = True
        anomaly.reviewer_notes = request.data.get('notes', '')
        anomaly.is_false_positive = request.data.get('is_false_positive', False)
        anomaly.save()
        
        serializer = self.get_serializer(anomaly)
        return Response(serializer.data)


class DataSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for DataSource model"""
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'last_ingestion']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get data sources that are overdue for ingestion"""
        overdue_sources = [source for source in self.get_queryset() if source.is_overdue]
        serializer = self.get_serializer(overdue_sources, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def trigger_ingestion(self, request, pk=None):
        """Manually trigger data ingestion for a source"""
        source = self.get_object()
        # This would trigger the actual ingestion process
        # For now, just return success message
        return Response({
            'message': f'Ingestion triggered for {source.name}',
            'source_id': source.id
        })

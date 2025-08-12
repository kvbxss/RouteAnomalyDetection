from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
import logging
from .models import Flight, AnomalyDetection, DataSource
from .serializers import FlightSerializer, AnomalyDetectionSerializer, DataSourceSerializer
from .utils import FlightDataIngestion, CSVDataParser
from .ml_pipeline import AnomalyDetectionModel, AnomalyDetectionPipeline

logger = logging.getLogger(__name__)


class FlightViewSet(viewsets.ModelViewSet):
    """ViewSet for Flight model with full CRUD operations"""
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['origin', 'destination', 'aircraft_id']
    search_fields = ['flight_id', 'aircraft_id', 'origin', 'destination']
    ordering_fields = ['timestamp', 'altitude', 'speed']
    ordering = ['-timestamp']
    parser_classes = [MultiPartParser, FileUploadParser]

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

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser], permission_classes=[AllowAny])
    def upload_csv(self, request):
        """
        Upload and process CSV file containing flight data
        
        Expected file format: CSV with headers including lat/latitude, lon/longitude, etc.
        """
        try:
            # Validate file upload
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided. Please upload a CSV file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            uploaded_file = request.FILES['file']
            
            # Validate file type
            if not uploaded_file.name.lower().endswith('.csv'):
                return Response(
                    {'error': 'Invalid file type. Only CSV files are supported.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (limit to 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if uploaded_file.size > max_size:
                return Response(
                    {'error': f'File too large. Maximum size is {max_size // (1024*1024)}MB.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Read file content
            try:
                file_content = uploaded_file.read().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Try with different encoding
                    uploaded_file.seek(0)
                    file_content = uploaded_file.read().decode('latin-1')
                except UnicodeDecodeError:
                    return Response(
                        {'error': 'Unable to decode file. Please ensure it is a valid CSV file with UTF-8 or Latin-1 encoding.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Log upload attempt
            logger.info(f"CSV upload started: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Create or get data source for CSV uploads
            data_source, created = DataSource.objects.get_or_create(
                name=f"CSV Upload - {uploaded_file.name}",
                defaults={
                    'source_type': 'csv_upload',
                    'is_active': True
                }
            )
            
            # Process the CSV data
            ingestion = FlightDataIngestion(data_source)
            result = ingestion.ingest_csv_data(file_content, uploaded_file.name)
            
            # Prepare response
            response_data = {
                'success': result['success'],
                'filename': uploaded_file.name,
                'file_size_bytes': uploaded_file.size,
                'processed_count': result['processed_count'],
                'error_count': result['error_count'],
                'warning_count': result['warning_count'],
                'processing_time_seconds': result['processing_time_seconds'],
                'created_flights': result['created_flights']
            }
            
            # Include errors and warnings if present
            if result['errors']:
                response_data['errors'] = result['errors']
            if result['warnings']:
                response_data['warnings'] = result['warnings']
            
            # Determine response status
            if result['success']:
                response_status = status.HTTP_201_CREATED
                logger.info(f"CSV upload successful: {uploaded_file.name} - {result['processed_count']} flights created")
            else:
                response_status = status.HTTP_400_BAD_REQUEST
                logger.error(f"CSV upload failed: {uploaded_file.name} - {result['error_count']} errors")
            
            return Response(response_data, status=response_status)
            
        except Exception as e:
            error_msg = f"Unexpected error during CSV upload: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser], permission_classes=[AllowAny])
    def validate_csv(self, request):
        """
        Validate CSV file format without processing the data
        
        This endpoint allows users to check if their CSV file is valid before uploading
        """
        try:
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided. Please upload a CSV file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            uploaded_file = request.FILES['file']
            
            # Basic file validation
            if not uploaded_file.name.lower().endswith('.csv'):
                return Response(
                    {'error': 'Invalid file type. Only CSV files are supported.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Read file content
            try:
                file_content = uploaded_file.read().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    file_content = uploaded_file.read().decode('latin-1')
                except UnicodeDecodeError:
                    return Response(
                        {'error': 'Unable to decode file. Please ensure it is a valid CSV file.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate file format
            ingestion = FlightDataIngestion()
            validation_result = ingestion.validate_file_format(file_content, uploaded_file.name)
            
            response_data = {
                'filename': uploaded_file.name,
                'file_size_bytes': uploaded_file.size,
                'valid': validation_result['valid'],
                'file_type': validation_result['file_type'],
                'estimated_rows': validation_result['estimated_rows'],
                'detected_headers': validation_result['detected_headers']
            }
            
            if validation_result['errors']:
                response_data['errors'] = validation_result['errors']
            if validation_result['warnings']:
                response_data['warnings'] = validation_result['warnings']
            
            response_status = status.HTTP_200_OK if validation_result['valid'] else status.HTTP_400_BAD_REQUEST
            
            return Response(response_data, status=response_status)
            
        except Exception as e:
            error_msg = f"Error during CSV validation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get anomaly detection statistics"""
        total_anomalies = self.get_queryset().count()
        high_confidence = self.get_queryset().filter(confidence_score__gt=0.8).count()
        reviewed = self.get_queryset().filter(is_reviewed=True).count()
        false_positives = self.get_queryset().filter(is_false_positive=True).count()
        
        # Anomaly types breakdown
        anomaly_types = {}
        for choice in AnomalyDetection.ANOMALY_TYPES:
            type_key = choice[0]
            count = self.get_queryset().filter(anomaly_type=type_key).count()
            anomaly_types[type_key] = count
        
        stats = {
            'total_anomalies': total_anomalies,
            'high_confidence_anomalies': high_confidence,
            'reviewed_anomalies': reviewed,
            'false_positives': false_positives,
            'pending_review': total_anomalies - reviewed,
            'anomaly_types': anomaly_types,
            'confidence_distribution': {
                'low': self.get_queryset().filter(confidence_score__lt=0.5).count(),
                'medium': self.get_queryset().filter(confidence_score__gte=0.5, confidence_score__lt=0.8).count(),
                'high': self.get_queryset().filter(confidence_score__gte=0.8).count(),
            }
        }
        
        return Response(stats)

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
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def train_model(self, request):
        """Train the anomaly detection model"""
        try:
            contamination = float(request.data.get('contamination', 0.1))
            flight_limit = request.data.get('flight_limit')
            
            logger.info(f"Starting ML model training with contamination={contamination}")
            
            # Initialize model
            model = AnomalyDetectionModel(contamination=contamination)
            
            # Prepare training data
            flights_queryset = Flight.objects.all()
            if flight_limit:
                flights_queryset = flights_queryset[:int(flight_limit)]
            
            # Train model
            training_results = model.train(flights_queryset)
            
            if training_results['success']:
                # Optionally save the model
                if request.data.get('save_model', False):
                    model_path = model.save_model()
                    training_results['model_saved_to'] = model_path
                
                logger.info(f"Model training completed successfully: {training_results['training_samples']} samples")
                return Response(training_results, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Model training failed: {training_results.get('error')}")
                return Response(training_results, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            error_msg = f"Model training error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def detect_anomalies(self, request):
        """Run anomaly detection on flights"""
        try:
            flight_ids = request.data.get('flight_ids', [])
            retrain_model = request.data.get('retrain', False)
            
            logger.info(f"Starting anomaly detection for {len(flight_ids) if flight_ids else 'all'} flights")
            
            # Initialize pipeline
            pipeline = AnomalyDetectionPipeline()
            
            if flight_ids:
                # Process specific flights
                results = pipeline.process_flight_batch(flight_ids)
            else:
                # Run full pipeline
                results = pipeline.run_full_pipeline(retrain=retrain_model)
            
            if results['success']:
                logger.info(f"Anomaly detection completed: {results.get('total_anomalies_detected', results.get('anomalies_detected', 0))} anomalies detected")
                return Response(results, status=status.HTTP_200_OK)
            else:
                logger.error(f"Anomaly detection failed: {results.get('error', 'Unknown error')}")
                return Response(results, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            error_msg = f"Anomaly detection error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

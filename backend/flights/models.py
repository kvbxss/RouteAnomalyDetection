from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Flight(models.Model):
    """
    Model representing flight data from ADS-B sources.
    Stores comprehensive flight information including route, aircraft details, and telemetry.
    """
    flight_id = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique identifier for the flight"
    )
    aircraft_id = models.CharField(
        max_length=20,
        help_text="Aircraft registration or identifier"
    )
    timestamp = models.DateTimeField(
        help_text="Timestamp of the flight data point"
    )
    latitude = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitude coordinate in decimal degrees"
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitude coordinate in decimal degrees"
    )
    altitude = models.IntegerField(
        help_text="Altitude in feet"
    )
    speed = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Ground speed in knots"
    )
    heading = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(360.0)],
        help_text="Aircraft heading in degrees (0-360)"
    )
    origin = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Origin airport code (ICAO/IATA)"
    )
    destination = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Destination airport code (ICAO/IATA)"
    )
    route_points = models.JSONField(
        default=list,
        help_text="Array of route coordinates as [lat, lng] pairs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['flight_id']),
            models.Index(fields=['aircraft_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['origin', 'destination']),
        ]
        permissions = [
            ('can_manage_flight_data', 'Can manage flight data uploads and processing'),
            ('can_run_ml_operations', 'Can run machine learning operations'),
        ]

    def __str__(self):
        return f"Flight {self.flight_id} - {self.aircraft_id}"

    @property
    def duration_minutes(self):
        """Calculate flight duration if route points are available"""
        if len(self.route_points) < 2:
            return None
        # This would need actual timestamp data in route_points for accurate calculation
        return None

    @property
    def distance_km(self):
        """Calculate approximate flight distance from route points"""
        if len(self.route_points) < 2:
            return None
        # Simple haversine distance calculation would go here
        return None


class AnomalyDetection(models.Model):
    """
    Model representing anomaly detection results for flights.
    Stores ML model predictions and confidence scores.
    """
    
    ANOMALY_TYPES = [
        ('route_deviation', 'Route Deviation'),
        ('speed_anomaly', 'Speed Anomaly'),
        ('altitude_anomaly', 'Altitude Anomaly'),
        ('temporal_anomaly', 'Temporal Pattern Anomaly'),
        ('combined', 'Combined Anomaly'),
    ]

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='anomaly_detections',
        help_text="Associated flight record"
    )
    anomaly_type = models.CharField(
        max_length=50,
        choices=ANOMALY_TYPES,
        help_text="Type of anomaly detected"
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="ML model confidence score (0.0 to 1.0)"
    )
    detected_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when anomaly was detected"
    )
    ml_model_version = models.CharField(
        max_length=20,
        help_text="Version of the ML model used for detection"
    )
    anomaly_details = models.JSONField(
        default=dict,
        help_text="Additional details about the anomaly (features, thresholds, etc.)"
    )
    is_reviewed = models.BooleanField(
        default=False,
        help_text="Whether this anomaly has been reviewed by a human"
    )
    reviewer_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from human reviewer"
    )
    is_false_positive = models.BooleanField(
        default=False,
        help_text="Marked as false positive after review"
    )

    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['anomaly_type']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['detected_at']),
            models.Index(fields=['is_reviewed']),
        ]

    def __str__(self):
        return f"Anomaly: {self.anomaly_type} for {self.flight.flight_id} (confidence: {self.confidence_score:.2f})"

    @property
    def is_high_confidence(self):
        """Check if this is a high confidence anomaly (>0.8)"""
        return self.confidence_score > 0.8

    @property
    def needs_review(self):
        """Check if this anomaly needs human review"""
        return not self.is_reviewed and self.is_high_confidence


class DataSource(models.Model):
    """
    Model for tracking data sources and ingestion configuration.
    """
    
    SOURCE_TYPES = [
        ('csv_upload', 'CSV File Upload'),
        ('api_endpoint', 'API Endpoint'),
        ('real_time_feed', 'Real-time Data Feed'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the data source"
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES,
        help_text="Type of data source"
    )
    endpoint_url = models.URLField(
        blank=True,
        null=True,
        help_text="API endpoint URL (if applicable)"
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="API key for authentication (if required)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this data source is currently active"
    )
    last_ingestion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of last successful data ingestion"
    )
    ingestion_frequency_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1)],
        help_text="How often to ingest data (in minutes)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.source_type})"

    @property
    def is_overdue(self):
        """Check if data ingestion is overdue based on frequency"""
        if not self.last_ingestion:
            return True
        
        expected_next = self.last_ingestion + timezone.timedelta(
            minutes=self.ingestion_frequency_minutes
        )
        return timezone.now() > expected_next

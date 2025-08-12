from rest_framework import serializers
from .models import Flight, AnomalyDetection, DataSource


class FlightSerializer(serializers.ModelSerializer):
    """Serializer for Flight model with comprehensive validation"""
    duration_minutes = serializers.ReadOnlyField()
    distance_km = serializers.ReadOnlyField()
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_id', 'aircraft_id', 'timestamp', 
            'latitude', 'longitude', 'altitude', 'speed', 'heading',
            'origin', 'destination', 'route_points', 
            'created_at', 'updated_at', 'duration_minutes', 'distance_km'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_minutes', 'distance_km']

    def validate_flight_id(self, value):
        """Validate flight ID format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Flight ID cannot be empty")
        if len(value) > 50:
            raise serializers.ValidationError("Flight ID cannot exceed 50 characters")
        return value.strip().upper()

    def validate_aircraft_id(self, value):
        """Validate aircraft ID format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Aircraft ID cannot be empty")
        if len(value) > 20:
            raise serializers.ValidationError("Aircraft ID cannot exceed 20 characters")
        return value.strip().upper()

    def validate_latitude(self, value):
        """Validate latitude coordinate"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Latitude must be a number")
        if not -90.0 <= value <= 90.0:
            raise serializers.ValidationError("Latitude must be between -90 and 90 degrees")
        return float(value)

    def validate_longitude(self, value):
        """Validate longitude coordinate"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Longitude must be a number")
        if not -180.0 <= value <= 180.0:
            raise serializers.ValidationError("Longitude must be between -180 and 180 degrees")
        return float(value)

    def validate_altitude(self, value):
        """Validate altitude value"""
        if not isinstance(value, int):
            raise serializers.ValidationError("Altitude must be an integer")
        if value < -1000:  # Below sea level limit
            raise serializers.ValidationError("Altitude cannot be below -1000 feet")
        if value > 60000:  # Commercial aviation ceiling
            raise serializers.ValidationError("Altitude cannot exceed 60,000 feet")
        return value

    def validate_speed(self, value):
        """Validate speed value"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Speed must be a number")
        if value < 0:
            raise serializers.ValidationError("Speed cannot be negative")
        if value > 1000:  # Reasonable upper limit for commercial aircraft
            raise serializers.ValidationError("Speed cannot exceed 1000 knots")
        return float(value)

    def validate_heading(self, value):
        """Validate heading value"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Heading must be a number")
        if not 0.0 <= value <= 360.0:
            raise serializers.ValidationError("Heading must be between 0 and 360 degrees")
        return float(value)

    def validate_origin(self, value):
        """Validate origin airport code"""
        if value and len(value.strip()) > 0:
            value = value.strip().upper()
            if len(value) < 3 or len(value) > 4:
                raise serializers.ValidationError("Airport code must be 3-4 characters")
            if not value.isalpha():
                raise serializers.ValidationError("Airport code must contain only letters")
        return value

    def validate_destination(self, value):
        """Validate destination airport code"""
        if value and len(value.strip()) > 0:
            value = value.strip().upper()
            if len(value) < 3 or len(value) > 4:
                raise serializers.ValidationError("Airport code must be 3-4 characters")
            if not value.isalpha():
                raise serializers.ValidationError("Airport code must contain only letters")
        return value

    def validate_route_points(self, value):
        """Validate route_points format and coordinates"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Route points must be a list")
        
        if len(value) > 1000:  # Reasonable limit for route points
            raise serializers.ValidationError("Too many route points (maximum 1000)")
        
        for i, point in enumerate(value):
            if not isinstance(point, list) or len(point) != 2:
                raise serializers.ValidationError(
                    f"Route point {i+1} must be a [latitude, longitude] pair"
                )
            try:
                lat, lng = float(point[0]), float(point[1])
                if not (-90 <= lat <= 90):
                    raise serializers.ValidationError(
                        f"Invalid latitude in route point {i+1}: {lat}"
                    )
                if not (-180 <= lng <= 180):
                    raise serializers.ValidationError(
                        f"Invalid longitude in route point {i+1}: {lng}"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Route point {i+1} must contain numeric coordinates"
                )
        
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Ensure timestamp is not in the future
        from django.utils import timezone
        if 'timestamp' in data and data['timestamp'] > timezone.now():
            raise serializers.ValidationError({
                'timestamp': 'Flight timestamp cannot be in the future'
            })
        
        # Validate coordinate consistency
        if 'latitude' in data and 'longitude' in data and 'route_points' in data:
            current_coords = [data['latitude'], data['longitude']]
            route_points = data['route_points']
            
            # Check if current position is reasonable relative to route
            if route_points and len(route_points) > 0:
                # This is a simplified check - in practice you might want more sophisticated validation
                pass
        
        return data


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyDetection model with nested flight data"""
    flight_details = FlightSerializer(source='flight', read_only=True)
    is_high_confidence = serializers.ReadOnlyField()
    needs_review = serializers.ReadOnlyField()
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'flight', 'flight_details', 'anomaly_type', 
            'confidence_score', 'detected_at', 'ml_model_version',
            'anomaly_details', 'is_reviewed', 'reviewer_notes',
            'is_false_positive', 'is_high_confidence', 'needs_review'
        ]
        read_only_fields = ['id', 'detected_at', 'is_high_confidence', 'needs_review']

    def validate_confidence_score(self, value):
        """Validate confidence score is between 0 and 1"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Confidence score must be a number")
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                "Confidence score must be between 0.0 and 1.0"
            )
        return float(value)

    def validate_anomaly_type(self, value):
        """Validate anomaly type is from allowed choices"""
        valid_types = [choice[0] for choice in AnomalyDetection.ANOMALY_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid anomaly type. Must be one of: {', '.join(valid_types)}"
            )
        return value

    def validate_ml_model_version(self, value):
        """Validate ML model version format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("ML model version cannot be empty")
        if len(value) > 20:
            raise serializers.ValidationError("ML model version cannot exceed 20 characters")
        return value.strip()

    def validate_anomaly_details(self, value):
        """Validate anomaly details structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Anomaly details must be a dictionary")
        
        # Validate common fields that should be present
        if 'features' in value and not isinstance(value['features'], dict):
            raise serializers.ValidationError("Features in anomaly details must be a dictionary")
        
        if 'threshold' in value and not isinstance(value['threshold'], (int, float)):
            raise serializers.ValidationError("Threshold in anomaly details must be a number")
        
        return value

    def validate_reviewer_notes(self, value):
        """Validate reviewer notes"""
        if value and len(value) > 1000:
            raise serializers.ValidationError("Reviewer notes cannot exceed 1000 characters")
        return value

    def validate(self, data):
        """Cross-field validation for anomaly detection"""
        # If marked as reviewed, ensure reviewer notes are provided for high confidence anomalies
        if data.get('is_reviewed') and data.get('confidence_score', 0) > 0.8:
            if not data.get('reviewer_notes') or len(data.get('reviewer_notes', '').strip()) == 0:
                raise serializers.ValidationError({
                    'reviewer_notes': 'Reviewer notes are required for high confidence anomalies'
                })
        
        # If marked as false positive, it should be reviewed
        if data.get('is_false_positive') and not data.get('is_reviewed'):
            raise serializers.ValidationError({
                'is_reviewed': 'Anomaly must be reviewed before marking as false positive'
            })
        
        return data


class DataSourceSerializer(serializers.ModelSerializer):
    """Serializer for DataSource model with comprehensive validation"""
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'source_type', 'endpoint_url', 'api_key',
            'is_active', 'last_ingestion', 'ingestion_frequency_minutes',
            'created_at', 'updated_at', 'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue']
        extra_kwargs = {
            'api_key': {'write_only': True}  # Don't expose API keys in responses
        }

    def validate_name(self, value):
        """Validate data source name"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Data source name cannot be empty")
        if len(value) > 100:
            raise serializers.ValidationError("Data source name cannot exceed 100 characters")
        return value.strip()

    def validate_source_type(self, value):
        """Validate source type is from allowed choices"""
        valid_types = [choice[0] for choice in DataSource.SOURCE_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid source type. Must be one of: {', '.join(valid_types)}"
            )
        return value

    def validate_endpoint_url(self, value):
        """Validate endpoint URL format"""
        if value and len(value.strip()) > 0:
            value = value.strip()
            # Basic URL validation
            if not (value.startswith('http://') or value.startswith('https://')):
                raise serializers.ValidationError("URL must start with http:// or https://")
            if len(value) > 2048:
                raise serializers.ValidationError("URL cannot exceed 2048 characters")
        return value

    def validate_api_key(self, value):
        """Validate API key format"""
        if value and len(value.strip()) > 0:
            value = value.strip()
            if len(value) < 8:
                raise serializers.ValidationError("API key must be at least 8 characters")
            if len(value) > 255:
                raise serializers.ValidationError("API key cannot exceed 255 characters")
        return value

    def validate_ingestion_frequency_minutes(self, value):
        """Validate ingestion frequency is reasonable"""
        if not isinstance(value, int):
            raise serializers.ValidationError("Ingestion frequency must be an integer")
        if value < 1:
            raise serializers.ValidationError(
                "Ingestion frequency must be at least 1 minute"
            )
        if value > 10080:  # 1 week in minutes
            raise serializers.ValidationError(
                "Ingestion frequency cannot exceed 1 week (10080 minutes)"
            )
        return value

    def validate_last_ingestion(self, value):
        """Validate last ingestion timestamp"""
        if value:
            from django.utils import timezone
            if value > timezone.now():
                raise serializers.ValidationError("Last ingestion cannot be in the future")
        return value

    def validate(self, data):
        """Cross-field validation for data source"""
        source_type = data.get('source_type')
        endpoint_url = data.get('endpoint_url')
        api_key = data.get('api_key')

        # API endpoints and real-time feeds require endpoint URL
        if source_type in ['api_endpoint', 'real_time_feed']:
            if not endpoint_url or len(endpoint_url.strip()) == 0:
                raise serializers.ValidationError({
                    'endpoint_url': f'Endpoint URL is required for {source_type}'
                })

        # Real-time feeds typically require API keys
        if source_type == 'real_time_feed':
            if not api_key or len(api_key.strip()) == 0:
                raise serializers.ValidationError({
                    'api_key': 'API key is typically required for real-time feeds'
                })

        # CSV uploads don't need endpoint URLs or API keys
        if source_type == 'csv_upload':
            if endpoint_url and len(endpoint_url.strip()) > 0:
                raise serializers.ValidationError({
                    'endpoint_url': 'CSV uploads do not require endpoint URLs'
                })

        return data


class FlightListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for flight lists"""
    anomaly_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_id', 'aircraft_id', 'timestamp',
            'origin', 'destination', 'altitude', 'speed',
            'anomaly_count'
        ]
    
    def get_anomaly_count(self, obj):
        """Get count of anomalies for this flight"""
        return obj.anomaly_detections.count()


class AnomalyDetectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for anomaly lists"""
    flight_id = serializers.CharField(source='flight.flight_id', read_only=True)
    aircraft_id = serializers.CharField(source='flight.aircraft_id', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'flight_id', 'aircraft_id', 'anomaly_type',
            'confidence_score', 'detected_at', 'is_reviewed'
        ]
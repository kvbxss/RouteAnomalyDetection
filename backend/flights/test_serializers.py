"""
Tests for flight serializers
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Flight, AnomalyDetection, DataSource
from .serializers import (
    FlightSerializer, 
    AnomalyDetectionSerializer, 
    DataSourceSerializer,
    FlightListSerializer,
    AnomalyDetectionListSerializer
)


class FlightSerializerTest(TestCase):
    """Test FlightSerializer validation and functionality"""

    def setUp(self):
        self.valid_flight_data = {
            'flight_id': 'ABC123',
            'aircraft_id': 'N12345',
            'timestamp': timezone.now(),
            'latitude': 40.7128,
            'longitude': -74.0060,
            'altitude': 35000,
            'speed': 450.5,
            'heading': 180.0,
            'origin': 'JFK',
            'destination': 'LAX',
            'route_points': [[40.7128, -74.0060], [34.0522, -118.2437]]
        }

    def test_valid_flight_serialization(self):
        """Test serializing valid flight data"""
        serializer = FlightSerializer(data=self.valid_flight_data)
        self.assertTrue(serializer.is_valid())
        flight = serializer.save()
        self.assertEqual(flight.flight_id, 'ABC123')
        self.assertEqual(flight.aircraft_id, 'N12345')

    def test_flight_id_validation(self):
        """Test flight ID validation"""
        # Empty flight ID
        data = self.valid_flight_data.copy()
        data['flight_id'] = ''
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('flight_id', serializer.errors)

        # Too long flight ID
        data['flight_id'] = 'A' * 51
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('flight_id', serializer.errors)

    def test_coordinate_validation(self):
        """Test latitude and longitude validation"""
        # Invalid latitude
        data = self.valid_flight_data.copy()
        data['latitude'] = 91.0
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)

        # Invalid longitude
        data = self.valid_flight_data.copy()
        data['longitude'] = -181.0
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('longitude', serializer.errors)

    def test_altitude_validation(self):
        """Test altitude validation"""
        # Too low altitude
        data = self.valid_flight_data.copy()
        data['altitude'] = -2000
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('altitude', serializer.errors)

        # Too high altitude
        data['altitude'] = 70000
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('altitude', serializer.errors)

    def test_speed_validation(self):
        """Test speed validation"""
        # Negative speed
        data = self.valid_flight_data.copy()
        data['speed'] = -10.0
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('speed', serializer.errors)

        # Too high speed
        data['speed'] = 1500.0
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('speed', serializer.errors)

    def test_heading_validation(self):
        """Test heading validation"""
        # Invalid heading
        data = self.valid_flight_data.copy()
        data['heading'] = 361.0
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('heading', serializer.errors)

    def test_airport_code_validation(self):
        """Test origin and destination airport code validation"""
        # Invalid origin code
        data = self.valid_flight_data.copy()
        data['origin'] = 'AB'  # Too short
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('origin', serializer.errors)

        # Invalid destination code
        data = self.valid_flight_data.copy()
        data['destination'] = '12345'  # Contains numbers
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('destination', serializer.errors)

    def test_route_points_validation(self):
        """Test route points validation"""
        # Invalid route point format
        data = self.valid_flight_data.copy()
        data['route_points'] = [[40.7128]]  # Missing longitude
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('route_points', serializer.errors)

        # Invalid coordinates in route points
        data['route_points'] = [[91.0, -74.0060]]  # Invalid latitude
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('route_points', serializer.errors)

    def test_future_timestamp_validation(self):
        """Test that future timestamps are rejected"""
        data = self.valid_flight_data.copy()
        data['timestamp'] = timezone.now() + timezone.timedelta(days=1)
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('timestamp', serializer.errors)


class AnomalyDetectionSerializerTest(TestCase):
    """Test AnomalyDetectionSerializer validation and functionality"""

    def setUp(self):
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='N12345',
            timestamp=timezone.now(),
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            speed=450.5,
            heading=180.0
        )
        
        self.valid_anomaly_data = {
            'flight': self.flight.id,
            'anomaly_type': 'route_deviation',
            'confidence_score': 0.85,
            'ml_model_version': 'v1.0.0',
            'anomaly_details': {
                'features': {'deviation_distance': 50.2},
                'threshold': 0.8
            }
        }

    def test_valid_anomaly_serialization(self):
        """Test serializing valid anomaly data"""
        serializer = AnomalyDetectionSerializer(data=self.valid_anomaly_data)
        self.assertTrue(serializer.is_valid())
        anomaly = serializer.save()
        self.assertEqual(anomaly.anomaly_type, 'route_deviation')
        self.assertEqual(anomaly.confidence_score, 0.85)

    def test_confidence_score_validation(self):
        """Test confidence score validation"""
        # Invalid confidence score (too high)
        data = self.valid_anomaly_data.copy()
        data['confidence_score'] = 1.5
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confidence_score', serializer.errors)

        # Invalid confidence score (negative)
        data['confidence_score'] = -0.1
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confidence_score', serializer.errors)

    def test_anomaly_type_validation(self):
        """Test anomaly type validation"""
        data = self.valid_anomaly_data.copy()
        data['anomaly_type'] = 'invalid_type'
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('anomaly_type', serializer.errors)

    def test_ml_model_version_validation(self):
        """Test ML model version validation"""
        # Empty model version
        data = self.valid_anomaly_data.copy()
        data['ml_model_version'] = ''
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ml_model_version', serializer.errors)

    def test_anomaly_details_validation(self):
        """Test anomaly details validation"""
        # Invalid anomaly details (not a dict)
        data = self.valid_anomaly_data.copy()
        data['anomaly_details'] = "invalid"
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('anomaly_details', serializer.errors)

    def test_cross_field_validation(self):
        """Test cross-field validation"""
        # High confidence anomaly marked as reviewed without notes
        data = self.valid_anomaly_data.copy()
        data['confidence_score'] = 0.9
        data['is_reviewed'] = True
        data['reviewer_notes'] = ''
        serializer = AnomalyDetectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reviewer_notes', serializer.errors)

    def test_nested_flight_data(self):
        """Test that flight details are properly nested"""
        anomaly = AnomalyDetection.objects.create(
            flight=self.flight,
            anomaly_type='route_deviation',
            confidence_score=0.85,
            ml_model_version='v1.0.0'
        )
        serializer = AnomalyDetectionSerializer(anomaly)
        data = serializer.data
        self.assertIn('flight_details', data)
        self.assertEqual(data['flight_details']['flight_id'], 'TEST123')


class DataSourceSerializerTest(TestCase):
    """Test DataSourceSerializer validation and functionality"""

    def setUp(self):
        self.valid_data_source_data = {
            'name': 'Test API Source',
            'source_type': 'api_endpoint',
            'endpoint_url': 'https://api.example.com/flights',
            'api_key': 'test_api_key_12345',
            'is_active': True,
            'ingestion_frequency_minutes': 60
        }

    def test_valid_data_source_serialization(self):
        """Test serializing valid data source data"""
        serializer = DataSourceSerializer(data=self.valid_data_source_data)
        self.assertTrue(serializer.is_valid())
        data_source = serializer.save()
        self.assertEqual(data_source.name, 'Test API Source')
        self.assertEqual(data_source.source_type, 'api_endpoint')

    def test_name_validation(self):
        """Test data source name validation"""
        # Empty name
        data = self.valid_data_source_data.copy()
        data['name'] = ''
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_source_type_validation(self):
        """Test source type validation"""
        data = self.valid_data_source_data.copy()
        data['source_type'] = 'invalid_type'
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('source_type', serializer.errors)

    def test_endpoint_url_validation(self):
        """Test endpoint URL validation"""
        # Invalid URL format
        data = self.valid_data_source_data.copy()
        data['endpoint_url'] = 'not-a-url'
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('endpoint_url', serializer.errors)

    def test_api_key_validation(self):
        """Test API key validation"""
        # Too short API key
        data = self.valid_data_source_data.copy()
        data['api_key'] = '1234567'  # Less than 8 characters
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('api_key', serializer.errors)

    def test_ingestion_frequency_validation(self):
        """Test ingestion frequency validation"""
        # Too low frequency
        data = self.valid_data_source_data.copy()
        data['ingestion_frequency_minutes'] = 0
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ingestion_frequency_minutes', serializer.errors)

        # Too high frequency
        data['ingestion_frequency_minutes'] = 20000
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ingestion_frequency_minutes', serializer.errors)

    def test_cross_field_validation(self):
        """Test cross-field validation"""
        # API endpoint without URL
        data = self.valid_data_source_data.copy()
        data['source_type'] = 'api_endpoint'
        data['endpoint_url'] = ''
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('endpoint_url', serializer.errors)

        # CSV upload with endpoint URL (should not be allowed)
        data = self.valid_data_source_data.copy()
        data['source_type'] = 'csv_upload'
        data['endpoint_url'] = 'https://example.com'
        serializer = DataSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('endpoint_url', serializer.errors)

    def test_api_key_write_only(self):
        """Test that API key is write-only"""
        data_source = DataSource.objects.create(**self.valid_data_source_data)
        serializer = DataSourceSerializer(data_source)
        serialized_data = serializer.data
        self.assertNotIn('api_key', serialized_data)


class ListSerializerTest(TestCase):
    """Test list serializers"""

    def setUp(self):
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='N12345',
            timestamp=timezone.now(),
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            speed=450.5,
            heading=180.0
        )
        
        self.anomaly = AnomalyDetection.objects.create(
            flight=self.flight,
            anomaly_type='route_deviation',
            confidence_score=0.85,
            ml_model_version='v1.0.0'
        )

    def test_flight_list_serializer(self):
        """Test FlightListSerializer includes anomaly count"""
        serializer = FlightListSerializer(self.flight)
        data = serializer.data
        self.assertIn('anomaly_count', data)
        self.assertEqual(data['anomaly_count'], 1)

    def test_anomaly_list_serializer(self):
        """Test AnomalyDetectionListSerializer includes flight info"""
        serializer = AnomalyDetectionListSerializer(self.anomaly)
        data = serializer.data
        self.assertIn('flight_id', data)
        self.assertIn('aircraft_id', data)
        self.assertEqual(data['flight_id'], 'TEST123')
        self.assertEqual(data['aircraft_id'], 'N12345')
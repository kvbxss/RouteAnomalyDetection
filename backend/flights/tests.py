from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Flight, AnomalyDetection, DataSource


class FlightModelTest(TestCase):
    """Test cases for the Flight model"""
    
    def setUp(self):
        """Set up test data"""
        self.flight_data = {
            'flight_id': 'TEST123',
            'aircraft_id': 'N12345',
            'timestamp': timezone.now(),
            'latitude': 40.7128,
            'longitude': -74.0060,
            'altitude': 35000,
            'speed': 450.5,
            'heading': 90.0,
            'origin': 'JFK',
            'destination': 'LAX',
            'route_points': [[40.7128, -74.0060], [34.0522, -118.2437]]
        }
    
    def test_flight_creation(self):
        """Test creating a flight with valid data"""
        flight = Flight.objects.create(**self.flight_data)
        self.assertEqual(flight.flight_id, 'TEST123')
        self.assertEqual(flight.aircraft_id, 'N12345')
        self.assertEqual(flight.origin, 'JFK')
        self.assertEqual(flight.destination, 'LAX')
        self.assertEqual(len(flight.route_points), 2)
    
    def test_flight_str_representation(self):
        """Test string representation of flight"""
        flight = Flight.objects.create(**self.flight_data)
        expected_str = f"Flight {flight.flight_id} - {flight.aircraft_id}"
        self.assertEqual(str(flight), expected_str)
    
    def test_flight_unique_constraint(self):
        """Test that flight_id must be unique"""
        Flight.objects.create(**self.flight_data)
        
        # Try to create another flight with same flight_id
        with self.assertRaises(Exception):
            Flight.objects.create(**self.flight_data)
    
    def test_coordinate_validation(self):
        """Test latitude and longitude validation"""
        # Test invalid latitude
        invalid_data = self.flight_data.copy()
        invalid_data['latitude'] = 91.0  # Invalid latitude
        
        flight = Flight(**invalid_data)
        with self.assertRaises(ValidationError):
            flight.full_clean()
        
        # Test invalid longitude
        invalid_data = self.flight_data.copy()
        invalid_data['longitude'] = 181.0  # Invalid longitude
        
        flight = Flight(**invalid_data)
        with self.assertRaises(ValidationError):
            flight.full_clean()
    
    def test_speed_validation(self):
        """Test speed validation (must be non-negative)"""
        invalid_data = self.flight_data.copy()
        invalid_data['speed'] = -10.0  # Invalid negative speed
        
        flight = Flight(**invalid_data)
        with self.assertRaises(ValidationError):
            flight.full_clean()
    
    def test_heading_validation(self):
        """Test heading validation (0-360 degrees)"""
        invalid_data = self.flight_data.copy()
        invalid_data['heading'] = 361.0  # Invalid heading
        
        flight = Flight(**invalid_data)
        with self.assertRaises(ValidationError):
            flight.full_clean()


class AnomalyDetectionModelTest(TestCase):
    """Test cases for the AnomalyDetection model"""
    
    def setUp(self):
        """Set up test data"""
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='N12345',
            timestamp=timezone.now(),
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            speed=450.5,
            heading=90.0,
            origin='JFK',
            destination='LAX',
            route_points=[[40.7128, -74.0060], [34.0522, -118.2437]]
        )
        
        self.anomaly_data = {
            'flight': self.flight,
            'anomaly_type': 'route_deviation',
            'confidence_score': 0.85,
            'ml_model_version': 'v1.0',
            'anomaly_details': {'deviation_distance': 50.2, 'threshold': 30.0}
        }
    
    def test_anomaly_creation(self):
        """Test creating an anomaly detection record"""
        anomaly = AnomalyDetection.objects.create(**self.anomaly_data)
        self.assertEqual(anomaly.flight, self.flight)
        self.assertEqual(anomaly.anomaly_type, 'route_deviation')
        self.assertEqual(anomaly.confidence_score, 0.85)
        self.assertFalse(anomaly.is_reviewed)
        self.assertFalse(anomaly.is_false_positive)
    
    def test_anomaly_str_representation(self):
        """Test string representation of anomaly"""
        anomaly = AnomalyDetection.objects.create(**self.anomaly_data)
        expected_str = f"Anomaly: {anomaly.anomaly_type} for {anomaly.flight.flight_id} (confidence: {anomaly.confidence_score:.2f})"
        self.assertEqual(str(anomaly), expected_str)
    
    def test_confidence_score_validation(self):
        """Test confidence score validation (0.0 to 1.0)"""
        # Test invalid high confidence score
        invalid_data = self.anomaly_data.copy()
        invalid_data['confidence_score'] = 1.5  # Invalid score > 1.0
        
        anomaly = AnomalyDetection(**invalid_data)
        with self.assertRaises(ValidationError):
            anomaly.full_clean()
        
        # Test invalid negative confidence score
        invalid_data['confidence_score'] = -0.1  # Invalid negative score
        
        anomaly = AnomalyDetection(**invalid_data)
        with self.assertRaises(ValidationError):
            anomaly.full_clean()
    
    def test_is_high_confidence_property(self):
        """Test is_high_confidence property"""
        # High confidence anomaly
        high_conf_data = self.anomaly_data.copy()
        high_conf_data['confidence_score'] = 0.9
        high_conf_anomaly = AnomalyDetection.objects.create(**high_conf_data)
        self.assertTrue(high_conf_anomaly.is_high_confidence)
        
        # Low confidence anomaly
        low_conf_data = self.anomaly_data.copy()
        low_conf_data['confidence_score'] = 0.7
        low_conf_anomaly = AnomalyDetection.objects.create(**low_conf_data)
        self.assertFalse(low_conf_anomaly.is_high_confidence)
    
    def test_needs_review_property(self):
        """Test needs_review property"""
        # High confidence, not reviewed - should need review
        high_conf_data = self.anomaly_data.copy()
        high_conf_data['confidence_score'] = 0.9
        anomaly = AnomalyDetection.objects.create(**high_conf_data)
        self.assertTrue(anomaly.needs_review)
        
        # High confidence, already reviewed - should not need review
        anomaly.is_reviewed = True
        anomaly.save()
        self.assertFalse(anomaly.needs_review)
    
    def test_flight_relationship(self):
        """Test relationship between Flight and AnomalyDetection"""
        anomaly = AnomalyDetection.objects.create(**self.anomaly_data)
        
        # Test forward relationship
        self.assertEqual(anomaly.flight, self.flight)
        
        # Test reverse relationship
        self.assertIn(anomaly, self.flight.anomaly_detections.all())


class DataSourceModelTest(TestCase):
    """Test cases for the DataSource model"""
    
    def setUp(self):
        """Set up test data"""
        self.data_source_data = {
            'name': 'Test ADS-B Feed',
            'source_type': 'api_endpoint',
            'endpoint_url': 'https://api.example.com/adsb',
            'api_key': 'test_api_key_123',
            'is_active': True,
            'ingestion_frequency_minutes': 30
        }
    
    def test_data_source_creation(self):
        """Test creating a data source"""
        source = DataSource.objects.create(**self.data_source_data)
        self.assertEqual(source.name, 'Test ADS-B Feed')
        self.assertEqual(source.source_type, 'api_endpoint')
        self.assertTrue(source.is_active)
        self.assertEqual(source.ingestion_frequency_minutes, 30)
    
    def test_data_source_str_representation(self):
        """Test string representation of data source"""
        source = DataSource.objects.create(**self.data_source_data)
        expected_str = f"{source.name} ({source.source_type})"
        self.assertEqual(str(source), expected_str)
    
    def test_unique_name_constraint(self):
        """Test that data source name must be unique"""
        DataSource.objects.create(**self.data_source_data)
        
        # Try to create another source with same name
        with self.assertRaises(Exception):
            DataSource.objects.create(**self.data_source_data)
    
    def test_is_overdue_property(self):
        """Test is_overdue property"""
        source = DataSource.objects.create(**self.data_source_data)
        
        # New source with no last_ingestion should be overdue
        self.assertTrue(source.is_overdue)
        
        # Source with recent ingestion should not be overdue
        source.last_ingestion = timezone.now() - timedelta(minutes=15)
        source.save()
        self.assertFalse(source.is_overdue)
        
        # Source with old ingestion should be overdue
        source.last_ingestion = timezone.now() - timedelta(minutes=45)
        source.save()
        self.assertTrue(source.is_overdue)
    
    def test_frequency_validation(self):
        """Test ingestion frequency validation (must be positive)"""
        invalid_data = self.data_source_data.copy()
        invalid_data['ingestion_frequency_minutes'] = 0  # Invalid frequency
        
        source = DataSource(**invalid_data)
        with self.assertRaises(ValidationError):
            source.full_clean()

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Flight, AnomalyDetection, DataSource
from .serializers import FlightSerializer, AnomalyDetectionSerializer, DataSourceSerializer


class FlightAPITest(APITestCase):
    """Test cases for Flight API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.flight1 = Flight.objects.create(
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
        
        self.flight2 = Flight.objects.create(
            flight_id='TEST456',
            aircraft_id='N67890',
            timestamp=timezone.now(),
            latitude=34.0522,
            longitude=-118.2437,
            altitude=30000,
            speed=425.0,
            heading=270.0,
            origin='LAX',
            destination='JFK',
            route_points=[[34.0522, -118.2437], [40.7128, -74.0060]]
        )
        
        # URL for flight list endpoint
        self.list_url = reverse('flight-list')
        
        # URL for flight detail endpoint
        self.detail_url = reverse('flight-detail', args=[self.flight1.id])
    
    def test_get_flight_list(self):
        """Test retrieving list of flights"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that both flights are in the response
        self.assertEqual(response.data['count'], 2)
        
        # Check that the response contains the expected flight IDs
        flight_ids = [item['flight_id'] for item in response.data['results']]
        self.assertIn('TEST123', flight_ids)
        self.assertIn('TEST456', flight_ids)
    
    def test_get_flight_detail(self):
        """Test retrieving a specific flight"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected flight data
        self.assertEqual(response.data['flight_id'], 'TEST123')
        self.assertEqual(response.data['aircraft_id'], 'N12345')
        self.assertEqual(response.data['origin'], 'JFK')
        self.assertEqual(response.data['destination'], 'LAX')
    
    def test_create_flight(self):
        """Test creating a new flight"""
        new_flight_data = {
            'flight_id': 'TEST789',
            'aircraft_id': 'N54321',
            'timestamp': timezone.now().isoformat(),
            'latitude': 41.8781,
            'longitude': -87.6298,
            'altitude': 32000,
            'speed': 430.0,
            'heading': 180.0,
            'origin': 'ORD',
            'destination': 'MIA',
            'route_points': [[41.8781, -87.6298], [25.7617, -80.1918]]
        }
        
        response = self.client.post(self.list_url, new_flight_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the flight was created in the database
        self.assertTrue(Flight.objects.filter(flight_id='TEST789').exists())
    
    def test_update_flight(self):
        """Test updating an existing flight"""
        update_data = {
            'altitude': 36000,
            'speed': 460.0
        }
        
        response = self.client.patch(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the flight was updated in the database
        updated_flight = Flight.objects.get(id=self.flight1.id)
        self.assertEqual(updated_flight.altitude, 36000)
        self.assertEqual(updated_flight.speed, 460.0)
    
    def test_delete_flight(self):
        """Test deleting a flight"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that the flight was deleted from the database
        self.assertFalse(Flight.objects.filter(id=self.flight1.id).exists())
    
    def test_filter_flights_by_origin(self):
        """Test filtering flights by origin"""
        url = f"{self.list_url}?origin=JFK"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only flights with origin=JFK are returned
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['flight_id'], 'TEST123')
    
    def test_filter_flights_by_date_range(self):
        """Test filtering flights by date range"""
        # Create a flight with an older timestamp
        past_time = timezone.now() - timezone.timedelta(days=7)
        Flight.objects.create(
            flight_id='PAST123',
            aircraft_id='N99999',
            timestamp=past_time,
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            speed=450.5,
            heading=90.0,
            origin='JFK',
            destination='LAX',
            route_points=[[40.7128, -74.0060], [34.0522, -118.2437]]
        )
        
        # Filter for recent flights only
        start_date = (timezone.now() - timezone.timedelta(days=1)).isoformat()
        url = f"{self.list_url}?start_date={start_date}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only recent flights are returned
        self.assertEqual(response.data['count'], 2)
        flight_ids = [item['flight_id'] for item in response.data['results']]
        self.assertIn('TEST123', flight_ids)
        self.assertIn('TEST456', flight_ids)
        self.assertNotIn('PAST123', flight_ids)
    
    def test_flight_anomalies_endpoint(self):
        """Test retrieving anomalies for a specific flight"""
        # Create anomalies for the flight
        AnomalyDetection.objects.create(
            flight=self.flight1,
            anomaly_type='route_deviation',
            confidence_score=0.85,
            ml_model_version='v1.0',
            anomaly_details={'deviation_distance': 50.2, 'threshold': 30.0}
        )
        
        AnomalyDetection.objects.create(
            flight=self.flight1,
            anomaly_type='speed_anomaly',
            confidence_score=0.75,
            ml_model_version='v1.0',
            anomaly_details={'speed_delta': 100, 'threshold': 50}
        )
        
        # Test the custom action endpoint
        url = reverse('flight-anomalies', args=[self.flight1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that both anomalies are returned
        self.assertEqual(len(response.data), 2)
        anomaly_types = [item['anomaly_type'] for item in response.data]
        self.assertIn('route_deviation', anomaly_types)
        self.assertIn('speed_anomaly', anomaly_types)


class AnomalyDetectionAPITest(APITestCase):
    """Test cases for AnomalyDetection API endpoints"""
    
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
        
        self.anomaly1 = AnomalyDetection.objects.create(
            flight=self.flight,
            anomaly_type='route_deviation',
            confidence_score=0.85,
            ml_model_version='v1.0',
            anomaly_details={'deviation_distance': 50.2, 'threshold': 30.0}
        )
        
        self.anomaly2 = AnomalyDetection.objects.create(
            flight=self.flight,
            anomaly_type='speed_anomaly',
            confidence_score=0.75,
            ml_model_version='v1.0',
            anomaly_details={'speed_delta': 100, 'threshold': 50}
        )
        
        # URL for anomaly list endpoint
        self.list_url = reverse('anomalydetection-list')
        
        # URL for anomaly detail endpoint
        self.detail_url = reverse('anomalydetection-detail', args=[self.anomaly1.id])
    
    def test_get_anomaly_list(self):
        """Test retrieving list of anomalies"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that both anomalies are in the response
        self.assertEqual(response.data['count'], 2)
        
        # Check that the response contains the expected anomaly types
        anomaly_types = [item['anomaly_type'] for item in response.data['results']]
        self.assertIn('route_deviation', anomaly_types)
        self.assertIn('speed_anomaly', anomaly_types)
    
    def test_get_anomaly_detail(self):
        """Test retrieving a specific anomaly"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected anomaly data
        self.assertEqual(response.data['anomaly_type'], 'route_deviation')
        self.assertEqual(response.data['confidence_score'], 0.85)
        self.assertEqual(response.data['ml_model_version'], 'v1.0')
    
    def test_create_anomaly(self):
        """Test creating a new anomaly"""
        new_anomaly_data = {
            'flight': self.flight.id,
            'anomaly_type': 'altitude_anomaly',
            'confidence_score': 0.95,
            'ml_model_version': 'v1.0',
            'anomaly_details': {'altitude_delta': 5000, 'threshold': 2000}
        }
        
        response = self.client.post(self.list_url, new_anomaly_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the anomaly was created in the database
        self.assertTrue(AnomalyDetection.objects.filter(anomaly_type='altitude_anomaly').exists())
    
    def test_update_anomaly(self):
        """Test updating an existing anomaly"""
        update_data = {
            'is_reviewed': True,
            'reviewer_notes': 'This is a valid anomaly',
            'is_false_positive': False
        }
        
        response = self.client.patch(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the anomaly was updated in the database
        updated_anomaly = AnomalyDetection.objects.get(id=self.anomaly1.id)
        self.assertTrue(updated_anomaly.is_reviewed)
        self.assertEqual(updated_anomaly.reviewer_notes, 'This is a valid anomaly')
        self.assertFalse(updated_anomaly.is_false_positive)
    
    def test_filter_anomalies_by_type(self):
        """Test filtering anomalies by type"""
        url = f"{self.list_url}?anomaly_type=route_deviation"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only route_deviation anomalies are returned
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['anomaly_type'], 'route_deviation')
    
    def test_filter_anomalies_by_confidence(self):
        """Test filtering anomalies by confidence score"""
        url = f"{self.list_url}?min_confidence=0.8"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only high confidence anomalies are returned
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['anomaly_type'], 'route_deviation')
    
    def test_needs_review_endpoint(self):
        """Test the needs_review custom action"""
        # Create a high confidence anomaly that needs review
        AnomalyDetection.objects.create(
            flight=self.flight,
            anomaly_type='temporal_anomaly',
            confidence_score=0.9,
            ml_model_version='v1.0',
            anomaly_details={'time_delta': 30, 'threshold': 15}
        )
        
        # Test the custom action endpoint
        url = reverse('anomalydetection-needs-review')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only high confidence, unreviewed anomalies are returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['anomaly_type'], 'temporal_anomaly')
        self.assertEqual(response.data[0]['confidence_score'], 0.9)
    
    def test_mark_reviewed_endpoint(self):
        """Test the mark_reviewed custom action"""
        url = reverse('anomalydetection-mark-reviewed', args=[self.anomaly1.id])
        review_data = {
            'notes': 'Reviewed and confirmed',
            'is_false_positive': False
        }
        
        response = self.client.post(url, review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the anomaly was marked as reviewed
        updated_anomaly = AnomalyDetection.objects.get(id=self.anomaly1.id)
        self.assertTrue(updated_anomaly.is_reviewed)
        self.assertEqual(updated_anomaly.reviewer_notes, 'Reviewed and confirmed')
        self.assertFalse(updated_anomaly.is_false_positive)


class DataSourceAPITest(APITestCase):
    """Test cases for DataSource API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.data_source1 = DataSource.objects.create(
            name='Test ADS-B Feed',
            source_type='api_endpoint',
            endpoint_url='https://api.example.com/adsb',
            api_key='test_api_key_123',
            is_active=True,
            ingestion_frequency_minutes=30
        )
        
        self.data_source2 = DataSource.objects.create(
            name='CSV Upload Source',
            source_type='csv_upload',
            is_active=True,
            ingestion_frequency_minutes=60
        )
        
        # URL for data source list endpoint
        self.list_url = reverse('datasource-list')
        
        # URL for data source detail endpoint
        self.detail_url = reverse('datasource-detail', args=[self.data_source1.id])
    
    def test_get_data_source_list(self):
        """Test retrieving list of data sources"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that both data sources are in the response
        self.assertEqual(response.data['count'], 2)
        
        # Check that the response contains the expected data source names
        source_names = [item['name'] for item in response.data['results']]
        self.assertIn('Test ADS-B Feed', source_names)
        self.assertIn('CSV Upload Source', source_names)
    
    def test_get_data_source_detail(self):
        """Test retrieving a specific data source"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected data source data
        self.assertEqual(response.data['name'], 'Test ADS-B Feed')
        self.assertEqual(response.data['source_type'], 'api_endpoint')
        self.assertEqual(response.data['endpoint_url'], 'https://api.example.com/adsb')
        
        # API key should not be included in response
        self.assertNotIn('api_key', response.data)
    
    def test_create_data_source(self):
        """Test creating a new data source"""
        new_source_data = {
            'name': 'Real-time Feed',
            'source_type': 'real_time_feed',
            'endpoint_url': 'wss://feed.example.com/adsb',
            'api_key': 'new_api_key_456',
            'is_active': True,
            'ingestion_frequency_minutes': 15
        }
        
        response = self.client.post(self.list_url, new_source_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the data source was created in the database
        self.assertTrue(DataSource.objects.filter(name='Real-time Feed').exists())
    
    def test_update_data_source(self):
        """Test updating an existing data source"""
        update_data = {
            'is_active': False,
            'ingestion_frequency_minutes': 120
        }
        
        response = self.client.patch(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the data source was updated in the database
        updated_source = DataSource.objects.get(id=self.data_source1.id)
        self.assertFalse(updated_source.is_active)
        self.assertEqual(updated_source.ingestion_frequency_minutes, 120)
    
    def test_filter_data_sources_by_type(self):
        """Test filtering data sources by type"""
        url = f"{self.list_url}?source_type=api_endpoint"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only api_endpoint sources are returned
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test ADS-B Feed')
    
    def test_filter_data_sources_by_active(self):
        """Test filtering data sources by active status"""
        # Set one source to inactive
        self.data_source2.is_active = False
        self.data_source2.save()
        
        url = f"{self.list_url}?is_active=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only active sources are returned
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test ADS-B Feed')
    
    def test_overdue_endpoint(self):
        """Test the overdue custom action"""
        # Set last_ingestion for one source to make it not overdue
        self.data_source1.last_ingestion = timezone.now()
        self.data_source1.save()
        
        # The other source should be overdue (no last_ingestion)
        
        # Test the custom action endpoint
        url = reverse('datasource-overdue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only overdue sources are returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'CSV Upload Source')
    
    def test_trigger_ingestion_endpoint(self):
        """Test the trigger_ingestion custom action"""
        url = reverse('datasource-trigger-ingestion', args=[self.data_source1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected message
        self.assertEqual(response.data['message'], f'Ingestion triggered for {self.data_source1.name}')
        self.assertEqual(response.data['source_id'], self.data_source1.id)
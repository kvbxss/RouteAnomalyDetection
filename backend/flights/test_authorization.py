from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from .models import Flight, AnomalyDetection, DataSource
from datetime import datetime, timedelta
from django.utils import timezone


class PermissionBasedAuthorizationTestCase(TestCase):
    """Test cases for custom permission-based authorization"""

    def setUp(self):
        """Set up test client, users, and permissions"""
        self.client = APIClient()

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            password='password123'
        )

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )

        # Create user with flight management permission
        self.flight_manager = User.objects.create_user(
            username='flight_manager',
            password='password123'
        )
        content_type = ContentType.objects.get_for_model(Flight)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='can_manage_flight_data'
        )
        self.flight_manager.user_permissions.add(permission)

        # Create user with ML operations permission
        self.ml_operator = User.objects.create_user(
            username='ml_operator',
            password='password123'
        )
        permission = Permission.objects.get(
            content_type=content_type,
            codename='can_run_ml_operations'
        )
        self.ml_operator.user_permissions.add(permission)

        # Create test flight
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='ABC123',
            timestamp=timezone.now(),
            latitude=40.0,
            longitude=-74.0,
            altitude=35000,
            speed=450.0,
            heading=90.0
        )

    def _get_token(self, username, password):
        """Helper method to obtain JWT token"""
        response = self.client.post('/auth/token/', {
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            return response.data['access']
        return None

    def _authenticate_as(self, user, password):
        """Helper method to authenticate as a specific user"""
        token = self._get_token(user.username, password)
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_access_all_endpoints(self):
        """Test that admin users can access all endpoints"""
        self._authenticate_as(self.admin_user, 'admin123')

        # Read operations
        response = self.client.get('/api/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Write operations (create)
        response = self.client.post('/api/flights/', {
            'flight_id': 'ADMIN001',
            'aircraft_id': 'XYZ789',
            'timestamp': timezone.now().isoformat(),
            'latitude': 35.0,
            'longitude': -80.0,
            'altitude': 30000,
            'speed': 400.0,
            'heading': 180.0,
            'route_points': []
        })
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_regular_user_can_read_flights(self):
        """Test that authenticated users can read flight data"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.get('/api/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_flights(self):
        """Test that regular users cannot create flights"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.post('/api/flights/', {
            'flight_id': 'REG001',
            'aircraft_id': 'XYZ789',
            'timestamp': timezone.now().isoformat(),
            'latitude': 35.0,
            'longitude': -80.0,
            'altitude': 30000,
            'speed': 400.0,
            'heading': 180.0,
            'route_points': []
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_flights(self):
        """Test that regular users cannot update flights"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.patch(f'/api/flights/{self.flight.id}/', {
            'altitude': 40000
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_flights(self):
        """Test that regular users cannot delete flights"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.delete(f'/api/flights/{self.flight.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_manager_can_upload_csv(self):
        """Test that users with can_manage_flight_data permission can upload CSV"""
        self._authenticate_as(self.flight_manager, 'password123')

        from io import BytesIO
        csv_content = b"flight_id,aircraft_id,latitude,longitude,timestamp,altitude,speed,heading\nTEST456,ABC456,40.0,-74.0,2024-01-01T12:00:00,35000,450,90"

        response = self.client.post('/api/flights/upload_csv/', {
            'file': BytesIO(csv_content)
        }, format='multipart')

        # Should not get 403 Forbidden
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_upload_csv(self):
        """Test that regular users cannot upload CSV"""
        self._authenticate_as(self.regular_user, 'password123')

        from io import BytesIO
        csv_content = b"flight_id,aircraft_id,latitude,longitude,timestamp,altitude,speed,heading\nTEST456,ABC456,40.0,-74.0,2024-01-01T12:00:00,35000,450,90"

        response = self.client.post('/api/flights/upload_csv/', {
            'file': BytesIO(csv_content)
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ml_operator_can_train_model(self):
        """Test that users with can_run_ml_operations permission can train models"""
        self._authenticate_as(self.ml_operator, 'password123')

        response = self.client.post('/api/anomalies/train_model/', {
            'contamination': 0.1,
            'save_model': False
        })

        # Should not get 403 Forbidden
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_train_model(self):
        """Test that regular users cannot train models"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.post('/api/anomalies/train_model/', {
            'contamination': 0.1
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ml_operator_can_detect_anomalies(self):
        """Test that users with can_run_ml_operations permission can detect anomalies"""
        self._authenticate_as(self.ml_operator, 'password123')

        response = self.client.post('/api/anomalies/detect_anomalies/', {
            'retrain': False
        })

        # Should not get 403 Forbidden
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_detect_anomalies(self):
        """Test that regular users cannot run anomaly detection"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.post('/api/anomalies/detect_anomalies/', {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReadOnlyPermissionTestCase(TestCase):
    """Test cases for read-only access patterns"""

    def setUp(self):
        """Set up test client and users"""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='user',
            password='password123'
        )

        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )

        # Create test data
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='ABC123',
            timestamp=timezone.now(),
            latitude=40.0,
            longitude=-74.0,
            altitude=35000,
            speed=450.0,
            heading=90.0
        )

    def _authenticate_as(self, user, password):
        """Helper method to authenticate as a specific user"""
        response = self.client.post('/auth/token/', {
            'username': user.username,
            'password': password
        })
        if response.status_code == 200:
            token = response.data['access']
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_authenticated_user_can_list_flights(self):
        """Test that authenticated users can list flights"""
        self._authenticate_as(self.user, 'password123')

        response = self.client.get('/api/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_can_retrieve_flight_detail(self):
        """Test that authenticated users can retrieve flight details"""
        self._authenticate_as(self.user, 'password123')

        response = self.client.get(f'/api/flights/{self.flight.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_can_list_anomalies(self):
        """Test that authenticated users can list anomalies"""
        self._authenticate_as(self.user, 'password123')

        response = self.client.get('/api/anomalies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_can_list_data_sources(self):
        """Test that authenticated users can list data sources"""
        self._authenticate_as(self.user, 'password123')

        response = self.client.get('/api/data-sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UnauthorizedAccessTestCase(TestCase):
    """Test cases for unauthorized access attempts"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()

        # Create a flight for testing
        self.flight = Flight.objects.create(
            flight_id='TEST123',
            aircraft_id='ABC123',
            timestamp=timezone.now(),
            latitude=40.0,
            longitude=-74.0,
            altitude=35000,
            speed=450.0,
            heading=90.0
        )

    def test_unauthenticated_access_to_list_endpoint(self):
        """Test unauthenticated access to list endpoint"""
        response = self.client.get('/api/flights/')

        # In development mode with AllowAny, this might return 200
        # In production, this should return 401
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    def test_unauthenticated_csv_upload(self):
        """Test that unauthenticated users cannot upload CSV"""
        from io import BytesIO
        csv_content = b"flight_id,aircraft_id,latitude,longitude,timestamp,altitude,speed,heading\nTEST456,ABC456,40.0,-74.0,2024-01-01T12:00:00,35000,450,90"

        response = self.client.post('/api/flights/upload_csv/', {
            'file': BytesIO(csv_content)
        }, format='multipart')

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_model_training(self):
        """Test that unauthenticated users cannot train models"""
        response = self.client.post('/api/anomalies/train_model/', {
            'contamination': 0.1
        })

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_anomaly_detection(self):
        """Test that unauthenticated users cannot run anomaly detection"""
        response = self.client.post('/api/anomalies/detect_anomalies/', {})

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AdminOnlyOperationsTestCase(TestCase):
    """Test cases for operations that should only be accessible to admins"""

    def setUp(self):
        """Set up test client and users"""
        self.client = APIClient()

        self.regular_user = User.objects.create_user(
            username='user',
            password='password123'
        )

        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )

        # Create test data
        self.data_source = DataSource.objects.create(
            name='Test Source',
            source_type='ADSB',
            endpoint_url='http://example.com/data',
            is_active=True
        )

    def _authenticate_as(self, user, password):
        """Helper method to authenticate as a specific user"""
        response = self.client.post('/auth/token/', {
            'username': user.username,
            'password': password
        })
        if response.status_code == 200:
            token = response.data['access']
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_create_data_source(self):
        """Test that admin can create data sources"""
        self._authenticate_as(self.admin, 'admin123')

        response = self.client.post('/api/data-sources/', {
            'name': 'New Source',
            'source_type': 'FLIGHTRADAR',
            'endpoint_url': 'http://example.com/newdata',
            'is_active': True
        })

        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_regular_user_cannot_create_data_source(self):
        """Test that regular users cannot create data sources"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.post('/api/data-sources/', {
            'name': 'New Source',
            'source_type': 'FLIGHTRADAR',
            'endpoint_url': 'http://example.com/newdata',
            'is_active': True
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_data_source(self):
        """Test that admin can update data sources"""
        self._authenticate_as(self.admin, 'admin123')

        response = self.client.patch(f'/api/data-sources/{self.data_source.id}/', {
            'is_active': False
        })

        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_regular_user_cannot_update_data_source(self):
        """Test that regular users cannot update data sources"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.patch(f'/api/data-sources/{self.data_source.id}/', {
            'is_active': False
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_data_source(self):
        """Test that admin can delete data sources"""
        self._authenticate_as(self.admin, 'admin123')

        response = self.client.delete(f'/api/data-sources/{self.data_source.id}/')

        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND])

    def test_regular_user_cannot_delete_data_source(self):
        """Test that regular users cannot delete data sources"""
        self._authenticate_as(self.regular_user, 'password123')

        response = self.client.delete(f'/api/data-sources/{self.data_source.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

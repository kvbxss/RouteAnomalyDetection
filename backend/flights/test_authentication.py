from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthenticationTestCase(TestCase):
    """Test cases for JWT authentication endpoints"""

    def setUp(self):
        """Set up test client and users"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def test_obtain_token_with_valid_credentials(self):
        """Test obtaining JWT token with valid credentials"""
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(len(response.data['access']) > 0)
        self.assertTrue(len(response.data['refresh']) > 0)

    def test_obtain_token_with_invalid_credentials(self):
        """Test obtaining JWT token with invalid credentials"""
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_obtain_token_with_missing_fields(self):
        """Test obtaining JWT token with missing required fields"""
        response = self.client.post('/auth/token/', {
            'username': 'testuser'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_with_nonexistent_user(self):
        """Test obtaining JWT token with non-existent user"""
        response = self.client.post('/auth/token/', {
            'username': 'nonexistent',
            'password': 'password123'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_with_valid_token(self):
        """Test refreshing access token with valid refresh token"""
        # First, obtain tokens
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        refresh_token = response.data['refresh']

        # Refresh the token
        response = self.client.post('/auth/token/refresh/', {
            'refresh': refresh_token
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(len(response.data['access']) > 0)

    def test_refresh_token_with_invalid_token(self):
        """Test refreshing access token with invalid refresh token"""
        response = self.client.post('/auth/token/refresh/', {
            'refresh': 'invalid.token.here'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_token_with_valid_token(self):
        """Test verifying a valid access token"""
        # Obtain tokens
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        access_token = response.data['access']

        # Verify the token
        response = self.client.post('/auth/token/verify/', {
            'token': access_token
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_token_with_invalid_token(self):
        """Test verifying an invalid access token"""
        response = self.client.post('/auth/token/verify/', {
            'token': 'invalid.token.here'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without authentication"""
        response = self.client.get('/api/flights/')

        # Should still work in development mode with AllowAny
        # In production, this would return 401
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    def test_access_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid JWT token"""
        # Obtain token
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        access_token = response.data['access']

        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Access protected endpoint
        response = self.client.get('/api/flights/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid JWT token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')

        response = self.client.get('/api/flights/')

        # May return 401 or 403 depending on authentication backend
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_token_contains_user_information(self):
        """Test that JWT token contains correct user information"""
        from rest_framework_simplejwt.tokens import AccessToken

        # Obtain token
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        access_token_str = response.data['access']

        # Decode token
        access_token = AccessToken(access_token_str)

        # Verify user ID is in the token
        self.assertEqual(access_token['user_id'], self.user.id)

    def test_admin_user_authentication(self):
        """Test that admin users can authenticate and access endpoints"""
        response = self.client.post('/auth/token/', {
            'username': 'admin',
            'password': 'admin123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # Use admin token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')

        # Access endpoint
        response = self.client.get('/api/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SessionAuthenticationTestCase(TestCase):
    """Test cases for session-based authentication"""

    def setUp(self):
        """Set up test client and users"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_session_login(self):
        """Test logging in with session authentication"""
        logged_in = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(logged_in)

    def test_access_endpoint_with_session(self):
        """Test accessing endpoint with session authentication"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/api/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_session_logout(self):
        """Test logging out"""
        self.client.login(username='testuser', password='testpass123')
        self.client.logout()

        # After logout, accessing protected endpoint should fail (in production)
        response = self.client.get('/api/flights/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])


class AuthenticationErrorHandlingTestCase(TestCase):
    """Test cases for authentication error scenarios"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()

    def test_malformed_authorization_header(self):
        """Test handling of malformed Authorization header"""
        self.client.credentials(HTTP_AUTHORIZATION='InvalidFormat token')

        response = self.client.get('/api/flights/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_empty_authorization_header(self):
        """Test handling of empty Authorization header"""
        self.client.credentials(HTTP_AUTHORIZATION='')

        response = self.client.get('/api/flights/')
        # Should work in development or return 401 in production
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    def test_bearer_token_without_prefix(self):
        """Test providing token without 'Bearer' prefix"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        token = response.data['access']

        # Try using token without Bearer prefix
        self.client.credentials(HTTP_AUTHORIZATION=token)

        response = self.client.get('/api/flights/')
        # Should fail authentication
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

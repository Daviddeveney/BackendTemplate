from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import firebase_admin
from firebase_admin import auth
import time
import requests
from unittest.mock import patch

class FirebaseAuthTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user with a timestamp to avoid conflicts
        self.test_email = f"test_{int(time.time())}@roundreserve.test"
        self.test_password = "testpass123"
        
        # Create test user in Firebase
        self.test_user = auth.create_user(
            email=self.test_email,
            password=self.test_password,
            email_verified=True
        )
        
        # Create custom token and exchange it for an ID token
        custom_token = auth.create_custom_token(self.test_user.uid).decode('utf-8')
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken",
            params={"key": settings.FIREBASE_WEB_API_KEY},
            json={"token": custom_token, "returnSecureToken": True}
        )
        self.id_token = response.json()['idToken']

    def tearDown(self):
        # Clean up test user
        try:
            auth.delete_user(self.test_user.uid)
        except:
            pass

    def test_health_check_no_auth(self):
        """Test health check endpoint (should be public)"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')

    def test_protected_endpoint_with_token(self):
        """Test protected endpoint with valid token"""
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.id_token}"}
        with patch('apps.api.utils.browserbase_runner.run_browserbase', return_value={'status': 'success', 'session_url': 'dummy', 'page_title': 'dummy title'}):
            response = self.client.post('/api/run-browserbase/', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())

    def test_protected_endpoint_no_token(self):
        """Test protected endpoint without token"""
        response = self.client.post('/api/run-browserbase/')
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_protected_endpoint_invalid_token(self):
        """Test protected endpoint with invalid token"""
        headers = {"HTTP_AUTHORIZATION": "Bearer invalid_token"}
        response = self.client.post('/api/run-browserbase/', **headers)
        self.assertEqual(response.status_code, 401)  # Unauthorized 
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
import firebase_admin
from firebase_admin import auth
import time
import requests
from unittest.mock import patch, MagicMock

class EndpointTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test user with timestamp
        self.test_email = f"test_{int(time.time())}@roundreserve.test"
        self.test_user = auth.create_user(
            email=self.test_email,
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
        # Clean up
        try:
            auth.delete_user(self.test_user.uid)
        except:
            pass

    @patch('apps.api.views.SQSClient')
    def test_queue_automation(self, MockSQSClient):
        """Test queue automation endpoint"""
        # Set up the mock SQS client
        mock_instance = MockSQSClient.return_value
        mock_instance.send_message.return_value = {
            'status': 'success',
            'message_id': 'fake_message_id'
        }
        
        # Prepare test data with proper message structure
        test_data = {
            'task_type': 'browser_automation',
            'parameters': {
                'test_param': 'test_value'
            }
        }
        
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.id_token}"}
        response = self.client.post('/api/queue-automation/', test_data, format='json', **headers)
        
        # Verify the response
        self.assertEqual(response.status_code, 202)  # Accepted
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['message_id'], 'fake_message_id')
        
        # Verify the mock was called correctly
        mock_instance.send_message.assert_called_once_with(test_data)

    def test_run_browserbase(self):
        """Test browserbase endpoint"""
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.id_token}"}
        response = self.client.post('/api/run-browserbase/', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json()) 
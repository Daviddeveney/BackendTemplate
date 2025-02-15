import os
import firebase_admin
from firebase_admin import auth, credentials
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from pathlib import Path
from django.contrib.auth.models import AnonymousUser

# Initialize Firebase Admin SDK
cred = credentials.Certificate(
    Path(settings.BASE_DIR) / settings.FIREBASE_CREDENTIALS_PATH
)

try:
    firebase_admin.initialize_app(cred)
except ValueError:
    # App already initialized
    pass

class FirebaseUser:
    def __init__(self, firebase_data):
        self.firebase_data = firebase_data
        self.id = firebase_data.get('uid')
        self.is_authenticated = True

    @property
    def is_anonymous(self):
        return False

class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Firebase token verification.
    Validates the Authorization header containing the Firebase ID token.
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        # Check if the Authorization header starts with 'Bearer '
        if not auth_header.startswith('Bearer '):
            return None

        # Extract the token
        id_token = auth_header.split(' ')[1]

        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(id_token)
            
            # Get user identifier from token
            uid = decoded_token.get('uid')
            if not uid:
                raise exceptions.AuthenticationFailed('Invalid Firebase token: no UID')
                
            # Create a user object from the token data
            user = FirebaseUser(decoded_token)
            return (user, None)
            
        except auth.InvalidIdTokenError:
            raise exceptions.AuthenticationFailed('Invalid Firebase token')
        except auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed('Expired Firebase token')
        except auth.RevokedIdTokenError:
            raise exceptions.AuthenticationFailed('Revoked Firebase token')
        except auth.CertificateFetchError:
            raise exceptions.AuthenticationFailed('Firebase certificate fetch failed')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Firebase token verification failed: {str(e)}')

    def authenticate_header(self, request):
        """
        Return the authentication header format expected
        """
        return 'Bearer' 
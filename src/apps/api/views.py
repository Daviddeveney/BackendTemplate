from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .utils.browserbase_runner import run_browserbase
from rest_framework import status
from .sqs_queue_manager.client import SQSClient
from .auth.firebase import FirebaseAuthentication
import logging
from rest_framework.views import APIView
from .serializers import DeviceTokenSerializer
from .models import DeviceToken
from .notifications.sender import send_push_notification

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])  # Keep health check public for AWS
def health_check(request):
    return Response({"status": "healthy"})

@api_view(['POST'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def run_browserbase_view(request):
    """
    Endpoint to trigger the browserbase script.
    """
    result = run_browserbase(request)
    if result.get('status') == 'error':
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def queue_automation(request):
    """
    Queue a browser automation task to be processed asynchronously
    """
    try:
        # Validate request data
        if not request.data:
            return Response({
                'status': 'error',
                'message': 'Request body is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize SQS client
        try:
            sqs_client = SQSClient()
        except Exception as e:
            logger.error(f"Failed to initialize SQS client: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to initialize queue service',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Send message to queue
        try:
            result = sqs_client.send_message(request.data)
        except Exception as e:
            logger.error(f"Failed to send message to queue: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to send message to queue',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if result['status'] == 'success':
            return Response({
                'status': 'success',
                'message': 'Task queued successfully',
                'message_id': result['message_id']
            }, status=status.HTTP_202_ACCEPTED)
        else:
            logger.error(f"Queue service returned error: {result.get('error')}")
            return Response({
                'status': 'error',
                'message': 'Failed to queue task',
                'error': result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Unexpected error in queue_automation: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to queue task',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Register or update a device token"""
        serializer = DeviceTokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            device_type = serializer.validated_data['device_type']
            
            # Update or create the device token
            device_token, created = DeviceToken.objects.update_or_create(
                user=request.user,
                token=token,
                defaults={
                    'device_type': device_type,
                    'is_active': True
                }
            )
            
            action = 'registered' if created else 'updated'
            logger.info(f"Device token {action} for user {request.user.id}")
            
            # Send a test notification if requested
            if request.query_params.get('test') == 'true':
                success, failure = send_push_notification(
                    request.user,
                    "Test Notification",
                    "Your device has been successfully registered for notifications!"
                )
                return Response({
                    'message': f'Device token {action} successfully',
                    'test_notification': {
                        'success': success > 0,
                        'message': 'Test notification sent successfully' if success > 0 else 'Failed to send test notification'
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'message': f'Device token {action} successfully'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Deactivate a device token"""
        token = request.data.get('token')
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deactivate the token
        updated = DeviceToken.objects.filter(
            user=request.user,
            token=token
        ).update(is_active=False)
        
        if updated:
            logger.info(f"Device token deactivated for user {request.user.id}")
            return Response({
                'message': 'Device token deactivated successfully'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Token not found'
        }, status=status.HTTP_404_NOT_FOUND)

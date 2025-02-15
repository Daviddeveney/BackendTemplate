from firebase_admin import messaging
from django.conf import settings
from ..models import DeviceToken
import logging

logger = logging.getLogger(__name__)

def send_push_notification(user, title, body, data=None):
    """
    Send push notification to all active devices for a user
    
    Args:
        user: User object
        title: Notification title
        body: Notification body
        data: Optional dictionary of extra data to send
    
    Returns:
        tuple: (success_count, failure_count)
    """
    if not data:
        data = {}
        
    # Get all active device tokens for the user
    device_tokens = DeviceToken.objects.filter(
        user=user,
        is_active=True
    ).values_list('token', 'device_type')
    
    if not device_tokens:
        logger.info(f"No active devices found for user {user.id}")
        return 0, 0
    
    success_count = 0
    failure_count = 0
    
    for token, device_type in device_tokens:
        try:
            # Configure the notification based on device type
            notification = messaging.Notification(
                title=title,
                body=body
            )
            
            # Configure platform-specific options
            apns = None
            android = None
            
            if device_type == 'ios':
                apns = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1
                        )
                    )
                )
            elif device_type == 'android':
                android = messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default'
                    )
                )
            
            # Create the message
            message = messaging.Message(
                notification=notification,
                data=data,
                token=token,
                apns=apns,
                android=android
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent notification to token {token[:16]}... Response: {response}")
            success_count += 1
            
        except messaging.ApiCallError as e:
            logger.error(f"Error sending notification to token {token[:16]}...: {str(e)}")
            failure_count += 1
            
            # Handle invalid token
            if isinstance(e, messaging.UnregisteredError):
                DeviceToken.objects.filter(token=token).update(is_active=False)
                logger.info(f"Marked token {token[:16]}... as inactive due to UnregisteredError")
    
    return success_count, failure_count 
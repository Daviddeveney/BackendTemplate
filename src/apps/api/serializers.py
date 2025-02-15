from rest_framework import serializers
from .models import DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    device_type = serializers.ChoiceField(choices=['ios', 'android'], default='ios')
    
    class Meta:
        model = DeviceToken
        fields = ['token', 'device_type']
        
    def validate_token(self, value):
        if not value or len(value) < 32:  # Basic validation for token length
            raise serializers.ValidationError("Invalid FCM token format")
        return value 
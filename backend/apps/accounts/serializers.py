import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation

# Get a logger for this module
logger = logging.getLogger(__name__)

User = get_user_model()

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}, label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'password', 'password2')
        extra_kwargs = {
            'role': {'required': True}
        }
    
    def validate(self, data):
        # Ensure both passwords match
        if data['password'] != data['password2']:
            logger.warning("Password mismatch for user signup: username=%s", data.get('username'))
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate the password using Django's validators
        try:
            password_validation.validate_password(data['password'], self.instance)
        except Exception as e:
            logger.warning("Password validation error for username=%s: %s", data.get('username'), str(e))
            raise serializers.ValidationError({"password": str(e)})
        
        logger.debug("Password validation passed for user: %s", data.get('username'))
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            role=validated_data.get('role', User.Role.STUDENT)
        )
        user.set_password(validated_data['password'])
        user.save()
        logger.info("Created new user: username=%s, id=%s", user.username, user.id)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
    # For login, you may add additional logging in your view rather than here,
    # as this serializer simply passes data for authentication.

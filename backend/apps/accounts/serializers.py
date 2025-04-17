import logging
from django.forms import ValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from .models import StudentProfile, TeacherProfile
from django.contrib.auth import password_validation
# Get a logger for this module
logger = logging.getLogger(__name__)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
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



# apps/accounts/serializers.py
# apps/accounts/serializers.py
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            logger.info(f"No user found for email {value}")
            return value  # Don't raise error to avoid leaking existence
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password2 = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, data):
        # Check password match
        if data['password'] != data['password2']:
            logger.warning("Passwords do not match in reset request")
            raise serializers.ValidationError({"password2": "Passwords must match"})
        
        # Validate password strength
        try:
            password_validation.validate_password(data['password'])
        except ValidationError as e:
            logger.warning(f"Password validation failed: {str(e)}")
            raise serializers.ValidationError({"password": str(e)})
        
        return data

    def validate_token(self, value):
        # Optional: Pre-check token existence (view handles full validation)
        from .models import PasswordResetToken
        try:
            token_obj = PasswordResetToken.objects.get(token=value)
            if not token_obj.is_valid():
                logger.warning(f"Expired reset token {value}")
                raise serializers.ValidationError("Token has expired")
        except PasswordResetToken.DoesNotExist:
            logger.warning(f"Invalid reset token {value}")
            raise serializers.ValidationError("Invalid token")
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password2 = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, data):
        user = self.context['request'].user
        # Check old password
        if not user.check_password(data['old_password']):
            logger.warning(f"Invalid old password for {user.email}")
            raise serializers.ValidationError({"old_password": "Incorrect old password"})
        # Check new password match
        if data['new_password'] != data['new_password2']:
            logger.warning("New passwords do not match")
            raise serializers.ValidationError({"new_password2": "New passwords must match"})
        # Validate new password strength
        try:
            password_validation.validate_password(data['new_password'], user)
        except ValidationError as e:
            logger.warning(f"New password validation failed: {str(e)}")
            raise serializers.ValidationError({"new_password": str(e)})
        return data


# apps/accounts/serializers.py
class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)
    confirm_deletion = serializers.BooleanField(required=True)

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            logger.warning(f"Invalid password for account deletion by {user.email}")
            raise serializers.ValidationError("Incorrect password")
        return value

    def validate_confirm_deletion(self, value):
        if not value:
            logger.warning(f"Deletion not confirmed by {self.context['request'].user.email}")
            raise serializers.ValidationError("You must confirm account deletion")
        return value

# apps/accounts/serializers.py
from .models import User
class UpdateEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate_new_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            logger.warning(f"Email {value} already in use")
            raise serializers.ValidationError("Email already in use")
        return value

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            logger.warning(f"Invalid password for email update by {user.email}")
            raise serializers.ValidationError("Incorrect password")
        return value
    


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'grade_level', 'parent_email']
        extra_kwargs = {
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
            'gender': {'required': False},
            'avatar': {'required': False},
            'grade_level': {'required': False},
            'parent_email': {'required': False},
        }

class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'department', 'office_number', 'qualifications']
        extra_kwargs = {
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
            'gender': {'required': False},
            'avatar': {'required': False},
            'department': {'required': False},
            'office_number': {'required': False},
            'qualifications': {'required': False},
        }


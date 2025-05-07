import logging
from django.forms import ValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, TeacherProfile, ApprovalRequest
from apps.accounts.utils.validations import (
    validate_phone_number, validate_date_of_birth, validate_gender, validate_avatar,
    validate_parent_email, validate_grade_level, validate_department,
    validate_office_number, validate_qualifications, validate_first_name,
    validate_last_name, validate_username, validate_password_strength
)
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration and updates.
    Handles username, email, role, and password fields with validation.
    """
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
    
    def validate_username(self, value):
        """
        Validate username using centralized validator and check uniqueness.
        """
        value = validate_username(value)
        if User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            logger.warning("Username already in use: %s", value)
            raise serializers.ValidationError(_('Username already in use'))
        return value
    
    def validate(self, data):
        """
        Validate that passwords match and meet strength requirements.
        """
        if data['password'] != data['password2']:
            logger.warning("Password mismatch for user signup: username=%s", data.get('username'))
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        data['password'] = validate_password_strength(data['password'])

        return data
    
    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
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
    """
    Serializer for user login.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for initiating password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Check if email exists without leaking information.
        """
        if not User.objects.filter(email=value).exists():
            logger.info(f"No user found for email {value}")
            return value
        return value

class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting password with a token.
    """
    token = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Validate that passwords match and meet strength requirements.
        """
        if data['password'] != data['password2']:
            logger.warning("Password mismatch for user signup: username=%s", data.get('username'))
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        data['password'] = validate_password_strength(data['password'])
        return data

    def validate_token(self, value):
        """
        Validate the password reset token.
        """
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
    """
    Serializer for changing an existing user's password.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Validate old password and new password requirements.
        """
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            logger.warning(f"Invalid old password for {user.email}")
            raise serializers.ValidationError({"old_password": "Incorrect old password"})
        if data['new_password'] != data['new_password2']:
            logger.warning("New passwords do not match")
            raise serializers.ValidationError({"new_password2": "New passwords must match"})
        data['new_password'] = validate_password_strength(data['new_password'], user)
        return data

class DeleteAccountSerializer(serializers.Serializer):
    """
    Serializer for account deletion.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    confirm_deletion = serializers.BooleanField(required=True)

    def validate_old_password(self, value):
        """
        Validate the old password for account deletion.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            logger.warning(f"Invalid password for account deletion by {user.email}")
            raise serializers.ValidationError("Incorrect password")
        return value

    def validate_confirm_deletion(self, value):
        """
        Ensure deletion is confirmed.
        """
        if not value:
            logger.warning(f"Deletion not confirmed by {self.context['request'].user.email}")
            raise ValidationError("You must confirm account deletion")
        return value

class UpdateEmailSerializer(serializers.Serializer):
    """
    Serializer for updating user email.
    """
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate_new_email(self, value):
        """
        Check if the new email is unique.
        """
        if User.objects.filter(email__iexact=value).exists():
            logger.warning(f"Email {value} already in use")
            raise serializers.ValidationError("Email already in use")
        return value

    def validate_password(self, value):
        """
        Validate the password for email update.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            logger.warning(f"Invalid password for email update by {user.email}")
            raise serializers.ValidationError("Incorrect password")
        return value

class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for student profile data.
    """
    phone_number = serializers.CharField(validators=[validate_phone_number], required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(validators=[validate_date_of_birth], required=False, allow_null=True)
    gender = serializers.CharField(validators=[validate_gender], required=False, allow_blank=True, allow_null=True)
    avatar = serializers.ImageField(validators=[validate_avatar], required=False, allow_null=True)
    grade_level = serializers.CharField(validators=[validate_grade_level], required=False, allow_blank=True, allow_null=True)
    parent_email = serializers.CharField(validators=[validate_parent_email], required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = StudentProfile
        fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'grade_level', 'parent_email']

class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher profile data.
    """
    phone_number = serializers.CharField(validators=[validate_phone_number], required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(validators=[validate_date_of_birth], required=False, allow_null=True)
    gender = serializers.CharField(validators=[validate_gender], required=False, allow_blank=True, allow_null=True)
    avatar = serializers.ImageField(validators=[validate_avatar], required=False, allow_null=True)
    department = serializers.CharField(validators=[validate_department], required=False, allow_blank=True, allow_null=True)
    office_number = serializers.CharField(validators=[validate_office_number], required=False, allow_blank=True, allow_null=True)
    qualifications = serializers.CharField(validators=[validate_qualifications], required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = TeacherProfile
        fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'department', 'office_number', 'qualifications']

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating basic user information.
    """
    first_name = serializers.CharField(validators=[validate_first_name], required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(validators=[validate_last_name], required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name']




class ApprovalRequestSerializer(serializers.ModelSerializer):
    qualifications = serializers.CharField(required=True)
    document = serializers.FileField(required=True)

    class Meta:
        model = ApprovalRequest
        fields = ('qualifications', 'document', 'message')

    def validate(self, data):
        document = data.get('document')
        if document:
            if document.size > 5 * 1024 * 1024:  # 5MB
                raise serializers.ValidationError({"document": "File size must be under 5MB."})
            if not document.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError({"document": "Only PDF, JPEG, or PNG files are allowed."})
        if not data.get('qualifications').strip():
            raise serializers.ValidationError({"qualifications": "Qualifications cannot be empty."})
        return data

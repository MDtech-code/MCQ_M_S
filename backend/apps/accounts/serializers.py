import logging
from django.forms import ValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from .models import StudentProfile, TeacherProfile,ApprovalRequest
from django.contrib.auth import password_validation
from .validators import (
    validate_phone_number, validate_date_of_birth, validate_gender, validate_avatar,
    validate_parent_email, validate_grade_level, validate_department,
    validate_office_number, validate_qualifications, validate_first_name, validate_last_name
)
# Get a logger for this moduleGH
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
        
        
        return data
    
    def create(self, validated_data):
        
        validated_data.pop('password2')
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            role=validated_data.get('role', User.Role.STUDENT)
        )
        \
        user.set_password(validated_data['password'])
        user.save()
        logger.info("Created new user: username=%s, id=%s", user.username, user.id)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
  
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
    old_password = serializers.CharField(required=True, write_only=True)
    confirm_deletion = serializers.BooleanField(required=True)

    def validate_old_password(self, value):
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
# class StudentProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudentProfile
#         fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'grade_level', 'parent_email']
#         extra_kwargs = {
#             'phone_number': {'required': False},
#             'date_of_birth': {'required': False},
#             'gender': {'required': False},
#             'avatar': {'required': False},
#             'grade_level': {'required': False},
#             'parent_email': {'required': False},
#         }



# class TeacherProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TeacherProfile
#         fields = ['phone_number', 'date_of_birth', 'gender', 'avatar', 'department', 'office_number', 'qualifications']
#         extra_kwargs = {
#             'phone_number': {'required': False},
#             'date_of_birth': {'required': False},
#             'gender': {'required': False},
#             'avatar': {'required': False},
#             'department': {'required': False},
#             'office_number': {'required': False},
#             'qualifications': {'required': False},
#         }



# class UserUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name']
#         extra_kwargs = {
#             'first_name': {'required': False},
#             'last_name': {'required': False},
#         }
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from apps.accounts.utils.validations import validate_phone_number
from django.db.models.functions import Lower
from apps.common.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from apps.common.choices.role import Role


from apps.common.choices.gender import Gender
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
import uuid



#! RoleRegsitry import 
# at top of models.py
def get_role_registry():
    from apps.accounts.config.roles import RoleRegistry
    return RoleRegistry



class User(AbstractUser):
    """
    Custom user model implementing username or email-based authentication with role-based access control.
    """
    
  
    
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Valid email address serving as username.')
    )
    role = models.CharField(
        _('system role'),
        max_length=2,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('Determines user permissions and interface')
    )
    is_verified = models.BooleanField(
        _('verified status'),
        default=False,
        help_text=_('Designates whether the user has verified their email')
    )

    is_approved = models.BooleanField(
        _('approved status'),
        default=True,
        help_text=_('Designates whether the user (teacher) is approved by admin')
    )
    
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="custom_user",
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            # For common user lookups
            models.Index(fields=['username', 'email'], name='auth_credential_idx'),
            # Partial index for unverified users
            models.Index(
                fields=['is_verified'],
                condition=Q(is_verified=False),
                name='unverified_users_idx'
            ),
            models.Index(fields=['role']),
            models.Index(fields=['is_approved']),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='unique_lower_email'
            ),
            models.CheckConstraint(
                check=~Q(username__iregex=r'^[0-9]+$'),
                name='username_not_all_numeric'
            )
        ]

        ordering = ['-date_joined']

    
    # def clean(self):
    #     """Validate role consistency"""
    #     super().clean()
        
        
    #     if self.role == Role.ADMIN and not self.is_staff:
    #         raise ValidationError({
    #             'role': _('ADMIN role requires staff status.')
    #         })
            
    #     # Prevent non-staff from being assigned ADMIN role
    #     if not self.is_staff and self.role == Role.ADMIN:
    #         raise ValidationError({
    #             'role': _('Only staff members can have ADMIN role.')
    #         })
    #     # Teachers require approval
    #     if self.role == Role.TEACHER and self.is_approved is None:
    #         self.is_approved = False
    
    # def save(self, *args, **kwargs):
    #     """
    #     Automatically enforce role consistency during save.
    #     """
    #     if self.is_staff and  self.is_superuser:
    #         self.role = Role.ADMIN
    #         self.is_approved = True
    #     elif self.role == Role.TEACHER and self.is_approved is None:
    #         self.is_approved = False
    #     super().save(*args, **kwargs)
    

    # def _assign_role_group(self) -> None:
    #     """
    #     Assign user to default group based on role.
    #     Creates group if it doesn't exist.
    #     """
    #     group_name = f"{self.get_role_display()}_Group"
    #     group, _ = Group.objects.get_or_create(name=group_name)
    #     self.groups.add(group)

   
    # def get_profile(self):
    #     from apps.accounts.service.profile_service import ProfileService
    #     profile = ProfileService.get_profile(self)
    #     return profile
    def clean(self) -> None:
        """Validate user fields using role-specific validators from RoleRegistry.

        Raises:
            ValidationError: If any role-specific validation fails.
        """
        super().clean()
        registry=get_role_registry()
        validators = registry.get_validators(self.role)
        for validator in validators:
            try:
                validator(self)
            except ValidationError as e:
                logger.warning("Validation failed for user %s: %s", self.username, str(e))
                raise e

    def save(self, *args, **kwargs) -> None:
        """Save the user instance, applying role-specific logic.

        Ensures role consistency and assigns role-based groups.
        """
        if self.is_superuser or self.is_staff:
            self.role = Role.ADMIN
            self.is_approved = True
        super().save(*args, **kwargs)
        self._assign_role_group()
        logger.info("Saved user: username=%s, id=%s, role=%s", self.username, self.id, self.role)

    def _assign_role_group(self) -> None:
        """Assign the user to role-based groups using RoleRegistry."""
        registry=get_role_registry()
        group_names = registry.get_groups(self.role)
        for group_name in group_names:
            group, _ = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)
            logger.info("Assigned group %s to user %s", group_name, self.username)

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Retrieve the user's profile data.

        Returns:
            Serialized profile data or None if no profile exists.
        """
        from apps.accounts.service.profile_service import ProfileService
        return ProfileService.get_profile(self)
    

    def __str__(self) -> str:
        """String representation using email and role"""
        return f"{self.username} ({self.get_role_display()})"



class EmailVerificationToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    new_email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name = _('email verification token')
        verbose_name_plural = _('email verification tokens')

        indexes = [
            models.Index(fields=['token']),  # New
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # 24-hour expiry
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Token for {self.user.email}"
    
# apps/accounts/models.py
class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)  # 1-hour expiry
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email}"
    


class BaseProfile(TimeStampedModel):
    """
    Abstract base profile containing common personal information.
    """
    
    
       

   
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True,
        null=True,
        # default='',
        unique=True,
        help_text=_('E.164 formatted international number')
    )
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
        help_text=_('YYYY-MM-DD format')
    )
    gender = models.CharField(
        _('gender'),
        max_length=2,
        choices=Gender.choices,
        default=Gender.UNDISCLOSED
    )
    avatar = models.ImageField(
        _('profile picture'),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Square image 512x512 pixels max')
    )

    class Meta:
        abstract = True
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['user', 'phone_number']),
        ]

    def __str__(self) -> str:
        """String representation using associated user"""
        return f"{self.user.email} Profile"


class StudentProfile(BaseProfile):
    """
    Extended profile model for students containing educational information.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='studentprofile'
    )
    grade_level = models.CharField(
        _('grade level'),
        max_length=50,
        blank=True,
        help_text=_('Current educational level (e.g., 10th Grade)')
    )
    parent_email = models.EmailField(
        _('parent email'),
        blank=True,
        help_text=_('Guardian contact information')
    )
    enrolled_date = models.DateField(
        _('enrollment date'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('student profile')
        verbose_name_plural = _('student profiles')


class TeacherProfile(BaseProfile):
    """
    Extended profile model for teachers containing professional information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='teacherprofile'
    )
    
    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        help_text=_('Academic department affiliation')
    )
    office_number = models.CharField(
        _('office number'),
        max_length=20,
        blank=True,
        help_text=_('Building and room number')
    )
    qualifications = models.TextField(
        _('qualifications'),
        blank=True,
        help_text=_('Professional certifications and degrees')
    )
    hire_date = models.DateField(
        _('hire date'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('teacher profile')
        verbose_name_plural = _('teacher profiles')




class ApprovalRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PE', _('Pending')
        APPROVED = 'AP', _('Approved')
        REJECTED = 'RE', _('Rejected')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    message = models.TextField(blank=True, help_text=_('Optional message from teacher'))
    document = models.FileField(upload_to='approval_documents/%Y/%m/%d/', blank=True, null=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.PENDING)
    qualifications = models.TextField(
        help_text=_('Professional certifications and degrees')
    )
    rejection_reason = models.TextField(blank=True, help_text=_('Reason for rejection, if any'))
    

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'status'], name='unique_pending_request')
        ]

    def clean(self):
        if self.status == 'PE' and ApprovalRequest.objects.filter(user=self.user, status='PE').exists():
            raise ValidationError("User can have only one pending request.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Approval Request for {self.user.username} ({self.status})"

















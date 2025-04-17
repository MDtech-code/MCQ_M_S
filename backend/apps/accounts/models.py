from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.validators import ASCIIUsernameValidator

from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q
from apps.accounts.validators import validate_phone_number
from django.db.models.functions import Lower
from apps.common.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import uuid




class User(AbstractUser):
    """
    Custom user model implementing username or email-based authentication with role-based access control.
    """
    
    class Role(models.TextChoices):
        STUDENT = 'ST', _('Student')
        TEACHER = 'TE', _('Teacher')
        ADMIN = 'AD', _('Admin')
    
    # Authentication fields
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[ASCIIUsernameValidator()],   # Explicit validator
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
    
    # Related model configurations
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

    def __str__(self) -> str:
        """String representation using email and role"""
        return f"{self.username} ({self.get_role_display()})"
    def clean(self):
        """Validate role consistency"""
        super().clean()
        
        # Enforce ADMIN role requires staff status
        if self.role == User.Role.ADMIN and not self.is_staff:
            raise ValidationError({
                'role': _('ADMIN role requires staff status.')
            })
            
        # Prevent non-staff from being assigned ADMIN role
        if not self.is_staff and self.role == User.Role.ADMIN:
            raise ValidationError({
                'role': _('Only staff members can have ADMIN role.')
            })
    # def save(self, *args, **kwargs) -> None:
    #     """
    #     Save user while ensuring role-based group assignment.
    #     Uses atomic transaction for data integrity.
    #     """
    #     with transaction.atomic():
    #         super().save(*args, **kwargs)
    #         if self._state.adding:  # Only on creation
    #             self._assign_role_group()
    def save(self, *args, **kwargs):
        """
        Automatically enforce role consistency during save.
        """
        if self.is_staff and  self.is_superuser:
            self.role = User.Role.ADMIN
        super().save(*args, **kwargs)
    

    def _assign_role_group(self) -> None:
        """
        Assign user to default group based on role.
        Creates group if it doesn't exist.
        """
        group_name = f"{self.get_role_display()}_Group"
        group, _ = Group.objects.get_or_create(name=group_name)
        self.groups.add(group)

    def get_profile(self):
        """
        Explicitly fetch the related profile based on the user's role.
        """
        if self.role == self.Role.STUDENT:
            try:
                return self.studentprofile
            except StudentProfile.DoesNotExist:
                return None
        elif self.role == self.Role.TEACHER:
            try:
                return self.teacherprofile
            except TeacherProfile.DoesNotExist:
                return None
        return None



class EmailVerificationToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = _('email verification token')
        verbose_name_plural = _('email verification tokens')

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
    
    class Gender(models.TextChoices):
        MALE = 'MA', _('Male')
        FEMALE = 'FE', _('Female')
        UNDISCLOSED = 'UD', _('Prefer not to say')
       

    # user = models.OneToOneField(
    #     User,
    #     on_delete=models.CASCADE,
    #     primary_key=True,
    #     related_name='%(class)s_profile'
    # )
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






















# accounts/tests.py
from django.test import TestCase, RequestFactory
from apps.accounts.service.auth_service import AuthService, CookieTokenAuthStrategy
from rest_framework.authtoken.models import Token
from .models import User

# accounts/tests.py
from django.test import TestCase, RequestFactory
from apps.accounts.service.auth_service import AuthService, CookieTokenAuthStrategy
from .models import User
from django_redis import get_redis_connection
from django.db import transaction

class AuthServiceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='Test@1234'
        )
        self.user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Test@1234',
            'password2': 'Test@1234',
            'role': 'ST'
        }

    def test_signup_atomic(self):
        request = self.factory.post('/signup/', self.user_data)
        auth_service = AuthService(CookieTokenAuthStrategy())
        with self.assertRaises(Exception):  # Simulate DB error
            with transaction.atomic():
                user, token, errors = auth_service.signup(request)
                raise Exception("Test rollback")
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_rate_limit(self):
        username = 'testuser'
        redis = get_redis_connection('default')
        cache_key = f"login_attempts:{username.lower()}"
        for _ in range(5):
            redis.setex(cache_key, 300, 5)
            request = self.factory.post('/login/', {'username': username, 'password': 'wrong'})
            auth_service = AuthService(CookieTokenAuthStrategy())
            user, token, errors = auth_service.login(request)
            self.assertIsNone(user)
            self.assertEqual(errors['non_field_errors'], ["Too many login attempts. Please try again in 5 minutes."])




# accounts/tests.py
from django.test import TestCase
from apps.accounts.service.profile_service import ProfileService, ProfileFactory
from .models import User, StudentProfile, TeacherProfile

class ProfileServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='Test@1234', role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(user=self.user)

    def test_get_profile(self):
        profile_data = ProfileService.get_profile(self.user)
        self.assertIsNotNone(profile_data)
        self.assertEqual(profile_data['user']['id'], self.user.id)

    def test_update_profile(self):
        data = {'profile': {'bio': 'Updated bio'}}
        profile_data, errors = ProfileService.update_profile(self.user, data)
        self.assertIsNone(errors)
        self.assertEqual(profile_data['bio'], 'Updated bio')







# accounts/tests.py
from django.test import TestCase
from django_redis import get_redis_connection
from .backends import EmailOrUsernameBackend
from .models import User

class EmailOrUsernameBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='Test@1234'
        )
        self.backend = EmailOrUsernameBackend()

    def test_authenticate_with_cache(self):
        redis = get_redis_connection('default')
        cache_key = f"user:auth:{self.user.username.lower()}"
        redis.setex(cache_key, 3600, self.user.id)
        user = self.backend.authenticate(None, username='testuser', password='Test@1234')
        self.assertEqual(user, self.user)

    def test_authenticate_without_cache(self):
        user = self.backend.authenticate(None, username='test@example.com', password='Test@1234')
        self.assertEqual(user, self.user)
        redis = get_redis_connection('default')
        cache_key = f"user:auth:{self.user.email.lower()}"
        self.assertTrue(redis.get(cache_key))


    



# accounts/tests.py
from apps.accounts.service.auth_service import get_or_create_token
from rest_framework.authtoken.models import Token

class TokenCacheTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='Test@1234'
        )

    def test_token_caching(self):
        token, created = get_or_create_token(self.user)
        self.assertTrue(created)
        cached_token, created = get_or_create_token(self.user)
        self.assertFalse(created)
        self.assertEqual(token, cached_token)






# accounts/tests.py
from django.test import TestCase
from apps.accounts.service.role_service import RoleService
from .models import User, StudentProfile, TeacherProfile, ApprovalRequest, EmailVerificationToken
from django.contrib.auth.models import Group

class RoleServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='Test@1234', role=User.Role.STUDENT
        )

    def test_handle_user_creation_student(self):
        RoleService.handle_user_creation(self.user, created=True)
        self.assertTrue(StudentProfile.objects.filter(user=self.user).exists())
        self.assertTrue(self.user.groups.filter(name='Student').exists())
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user).exists())

    def test_handle_user_creation_teacher(self):
        teacher = User.objects.create_user(
            username='teacher', email='teacher@example.com', password='Test@1234', role=User.Role.TEACHER
        )
        RoleService.handle_user_creation(teacher, created=True)
        self.assertFalse(teacher.is_approved)
        self.assertTrue(TeacherProfile.objects.filter(user=teacher).exists())
        self.assertTrue(ApprovalRequest.objects.filter(user=teacher).exists())
        self.assertTrue(teacher.groups.filter(name='Teacher').exists())










# accounts/tests.py
from django.test import TestCase
from django_redis import get_redis_connection
from apps.accounts.service.security_service import SecurityService
from django.core.exceptions import ValidationError

class SecurityServiceTest(TestCase):
    def test_rate_limit_exceeded(self):
        redis = get_redis_connection('default')
        username = 'testuser'
        cache_key = f"login_attempts:{username.lower()}"
        for _ in range(5):
            SecurityService.limit_login_attempts(username)
        with self.assertRaises(ValidationError) as cm:
            SecurityService.limit_login_attempts(username)
        self.assertEqual(str(cm.exception), "Too many login attempts. Please try again in 5 minutes.")
        self.assertEqual(int(redis.get(cache_key)), 6)

    def test_rate_limit_within_limit(self):
        username = 'testuser'
        result = SecurityService.limit_login_attempts(username)
        self.assertTrue(result)
        redis = get_redis_connection('default')
        cache_key = f"login_attempts:{username.lower()}"
        self.assertEqual(int(redis.get(cache_key)), 1)
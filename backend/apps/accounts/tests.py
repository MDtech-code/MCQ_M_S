# accounts/tests.py
from django.test import TestCase, RequestFactory
from apps.accounts.service.auth_service import AuthService, CookieTokenAuthStrategy
from rest_framework.authtoken.models import Token
from .models import User


class AuthServiceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Test@1234',
            'password2': 'Test@1234',
            'role': 'ST'
        }

    def test_signup_success(self):
        request = self.factory.post('/signup/', self.user_data)
        auth_service = AuthService(CookieTokenAuthStrategy())
        user, token, errors = auth_service.signup(request)
        self.assertIsNotNone(user)
        self.assertIsNone(errors)
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_login_success(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='Test@1234')
        request = self.factory.post('/login/', {'username': 'testuser', 'password': 'Test@1234'})
        auth_service = AuthService(CookieTokenAuthStrategy())
        user, token, errors = auth_service.login(request)
        self.assertIsNotNone(user)
        self.assertIsNone(errors)
        self.assertTrue(Token.objects.filter(user=user).exists())





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
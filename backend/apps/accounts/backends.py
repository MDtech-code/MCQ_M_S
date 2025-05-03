# #! both username and email 
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.db.models.functions import Lower
User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to get the user by username or email (case-insensitive)
            username = username.strip().lower()
            user = User.objects.annotate(
                lower_email=Lower('email'),
                lower_username=Lower('username')
            ).filter(Q(lower_email=username) | Q(lower_username=username)).first()
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Handle the case where multiple users have the same email
            return User.objects.filter(email__iexact=username).order_by('id').first()

        if user is not None and user.check_password(password):
            return user
        return None
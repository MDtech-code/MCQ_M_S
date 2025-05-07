from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        print(request.user.role)
        return request.user.is_authenticated and request.user.role == 'TE'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'AD'

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ST'



class IsApprovedTeacher(BasePermission):
    message = "You are not approved to perform this action. Please contact the admin."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'TE' and
            request.user.is_approved
        )

class IsVerified(BasePermission):
    message = "You are not verified to perform this action. Please verify your account."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_verified
        )
    

class IsNotAuthenticated(BasePermission):
    """
    Allows access **only** to non-authenticated users.
    """
    def has_permission(self, request, view):
        return not request.user.is_authenticated

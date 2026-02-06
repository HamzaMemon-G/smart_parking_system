"""
Custom authentication backend for email-based authentication
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from .models import User


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email and password
        
        Args:
            request: HTTP request object
            username: Email address (called username for compatibility)
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Get user by email
            user = User.objects.get(email=username)
            
            # Check password using Django's hasher
            if check_password(password, user.password_hash):
                return user
            else:
                return None
                
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        
        Args:
            user_id: Primary key of user
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

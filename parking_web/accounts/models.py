"""
Django models for accounts app
Uses existing database tables from Tkinter app
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that maps to existing users table
    """
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=255, db_column='password_hash')
    user_type = models.CharField(max_length=20, default='customer')
    loyalty_points = models.IntegerField(default=0)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']
    
    # Tell Django to use password_hash for the password field
    PASSWORD_FIELD = 'password_hash'
    
    class Meta:
        db_table = 'users'
        managed = False
    
    def __str__(self):
        return self.email
    
    @property
    def password(self):
        """Map Django's password attribute to password_hash column"""
        return self.password_hash
    
    @password.setter
    def password(self, raw_password):
        """Set password using Django's hasher"""
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)


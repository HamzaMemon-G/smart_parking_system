"""Vehicle models"""

from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    """Maps to existing vehicles table"""
    vehicle_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id')
    vehicle_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50)
    brand = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'vehicles'
        managed = False
    
    def __str__(self):
        return f"{self.vehicle_number} - {self.brand} {self.model}"


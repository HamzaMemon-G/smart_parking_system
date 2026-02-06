"""Booking and parking slot models"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json


class ParkingSlot(models.Model):
    """Maps to existing parking_slots table"""
    slot_id = models.AutoField(primary_key=True)
    slot_number = models.CharField(max_length=20, unique=True)
    floor = models.IntegerField()
    section = models.CharField(max_length=10)
    slot_type = models.CharField(max_length=50, default='regular')
    vehicle_type = models.CharField(max_length=50)
    base_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='available')
    location_x = models.IntegerField(null=True)
    location_y = models.IntegerField(null=True)
    
    class Meta:
        db_table = 'parking_slots'
        managed = False
    
    def __str__(self):
        return f"{self.slot_number} ({self.status})"
    
    @property
    def is_available(self):
        return self.status == 'available'


class Booking(models.Model):
    """Maps to existing bookings table with QR support"""
    booking_id = models.AutoField(primary_key=True)
    ticket_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, db_column='vehicle_id')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, db_column='slot_id')
    booking_date = models.DateField(auto_now_add=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    surge_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payment_status = models.CharField(max_length=20, default='pending')
    booking_status = models.CharField(max_length=20, default='active')
    booking_type = models.CharField(max_length=20, default='instant')
    qr_code_data = models.TextField(unique=True, null=True, blank=True)
    qr_code_path = models.CharField(max_length=255, null=True, blank=True)
    booking_time = models.DateTimeField(null=True, blank=True)
    checkin_deadline = models.DateTimeField(null=True, blank=True)
    checkin_time = models.DateTimeField(null=True, blank=True)
    forfeited = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'bookings'
        managed = False
        ordering = ['-booking_id']
    
    def __str__(self):
        return f"{self.ticket_number} - {self.user.name}"
    
    def generate_qr_data(self):
        """Generate QR code data for this booking"""
        import sys
        import os
        # Add parent directory to path to import utils
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from utils.qr_handler import QRHandler
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'qrcodes')
        os.makedirs(output_dir, exist_ok=True)
        
        handler = QRHandler(output_dir=output_dir)
        qr_data, qr_path = handler.generate_booking_qr(
            booking_id=self.booking_id,
            ticket_number=self.ticket_number,
            user_id=self.user.user_id,
            vehicle_number=self.vehicle.vehicle_number,
            slot_number=self.slot.slot_number
        )
        
        self.qr_code_data = qr_data
        self.qr_code_path = qr_path
        self.save(update_fields=['qr_code_data', 'qr_code_path'])
        
        return qr_path
    
    def is_expired(self):
        """Check if booking has expired (30-min window)"""
        if self.booking_status != 'pending':
            return False
        
        if not self.checkin_deadline:
            return False
        
        return timezone.now() > self.checkin_deadline
    
    def mark_checked_in(self):
        """Mark booking as checked in"""
        self.checkin_time = timezone.now()
        self.checkin_time = datetime.now()
        self.slot.status = 'occupied'
        self.slot.save()
        self.save()
    
    def mark_expired(self):
        """Mark booking as expired and forfeit payment"""
        self.booking_status = 'expired'
        self.forfeited = True
        self.slot.status = 'available'
        self.slot.save()
        self.save()
    
    @staticmethod
    def get_by_qr(qr_data):
        """Get booking by QR code data"""
        try:
            qr_dict = json.loads(qr_data)
            booking_id = qr_dict.get('booking_id')
            return Booking.objects.get(booking_id=booking_id)
        except:
            return None


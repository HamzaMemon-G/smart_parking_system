"""Payment models"""

from django.db import models


class Payment(models.Model):
    """Maps to existing payments table"""
    payment_id = models.AutoField(primary_key=True)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, db_column='booking_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_time = models.DateTimeField(auto_now_add=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        managed = False
    
    def __str__(self):
        return f"Payment {self.payment_id} - ₹{self.amount}"


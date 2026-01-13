"""Booking System and Payment Processing"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import uuid
from database.db_manager import get_db_manager


class BookingManager:
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.db = get_db_manager()
    
    @staticmethod
    def generate_ticket_number() -> str:
        """Generate unique ticket number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:4].upper()
        return f"PKG{timestamp}{unique_id}"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:4].upper()
        return f"PKG{timestamp}{unique_id}"
    
    def create_booking(self, vehicle_id: int, slot_id: int, 
                      booking_type: str = 'instant') -> Tuple[bool, Optional[str], str]:
        
        vehicle = self.db.fetch_one("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
        if not vehicle:
            return False, None, "Vehicle not found or doesn't belong to you"
        
        slot = self.db.get_slot_by_id(slot_id)
        if not slot:
            return False, None, "Parking slot not found"
        
        if slot['status'] != 'available':
            return False, None, f"Slot is {slot['status']} - not available"
        
        user = self.db.get_user_by_id(self.user_id)
        estimated_cost = slot['base_price_per_hour'] * 2
        if user['wallet_balance'] < estimated_cost:
            return False, None, f"Insufficient wallet balance. Need at least ₹{estimated_cost:.2f} (2 hrs estimate). Current balance: ₹{user['wallet_balance']:.2f}"
        
        if vehicle['vehicle_type'] != slot['vehicle_type']:
            return False, None, f"Slot is for {slot['vehicle_type']}, your vehicle is {vehicle['vehicle_type']}"
        
        active = self.db.fetch_one(
            "SELECT * FROM bookings WHERE vehicle_id = ? AND booking_status = 'active'",
            (vehicle_id,)
        )
        if active:
            return False, None, "Vehicle already has an active booking"
        
        ticket_number = self.generate_ticket_number()
        booking_id = self.db.create_booking(
            ticket_number, self.user_id, vehicle_id, slot_id, booking_type
        )
        
        if booking_id:
            self.db.update_slot_status(slot_id, 'occupied')
            self.db.create_notification(
                self.user_id,
                f"Booking confirmed! Ticket: {ticket_number}, Slot: {slot['slot_number']}",
                'booking'
            )
            
            return True, ticket_number, f"Booking successful! Ticket: {ticket_number}"
        
        return False, None, "Failed to create booking"
    
    def get_booking_details(self, ticket_number: str) -> Optional[Dict]:
        """Get complete booking details"""
        booking = self.db.get_booking_by_ticket(ticket_number)
        return dict(booking) if booking else None
    
    def get_my_active_bookings(self) -> list:
        """Get current user's active bookings"""
        if not self.user_id:
            return []
        bookings = self.db.get_active_bookings(self.user_id)
        return [dict(b) for b in bookings]
    
    def get_all_active_bookings(self) -> list:
        """Get all active bookings (for admin)"""
        bookings = self.db.get_active_bookings()
        return [dict(b) for b in bookings]
    
    def cancel_booking(self, ticket_number: str) -> Tuple[bool, str]:
        """Cancel a booking"""
        booking = self.get_booking_details(ticket_number)
        
        if not booking:
            return False, "Booking not found"
        
        if booking['booking_status'] != 'active':
            return False, f"Booking is already {booking['booking_status']}"
        
        if self.user_id and booking['user_id'] != self.user_id:
            return False, "You can only cancel your own bookings"
        
        success = self.db.cancel_booking(ticket_number)
        
        if success:
            self.db.update_slot_status(booking['slot_id'], 'available')
            self.db.create_notification(
                booking['user_id'],
                f"Booking {ticket_number} cancelled",
                'booking'
            )
            
            return True, "Booking cancelled successfully"
        
        return False, "Failed to cancel booking"
    
    def exit_parking(self, ticket_number: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Process exit from parking - automatically deducts from wallet
        Returns: (success, bill_details, message)
        """
        booking = self.get_booking_details(ticket_number)
        
        if not booking:
            return False, None, "Booking not found"
        
        if booking['booking_status'] != 'active':
            return False, None, f"Booking is {booking['booking_status']} - cannot exit"
        
        entry_time = datetime.strptime(booking['entry_time'], '%Y-%m-%d %H:%M:%S')
        exit_time = datetime.now()
        duration = (exit_time - entry_time).total_seconds() / 3600
        
        base_price = booking['base_price_per_hour']
        pricing = PricingCalculator(base_price, entry_time, exit_time)
        
        total_amount = pricing.calculate_total()
        surge_amount = pricing.surge_amount
        
        user = self.db.get_user_by_id(booking['user_id'])
        if user['wallet_balance'] < total_amount:
            return False, None, f"Insufficient wallet balance. Need ₹{total_amount:.2f}, you have ₹{user['wallet_balance']:.2f}"
        
        success = self.db.execute_query(
            "UPDATE bookings SET exit_time = ?, booking_status = 'completed' WHERE ticket_number = ?",
            (exit_time.strftime('%Y-%m-%d %H:%M:%S'), ticket_number)
        )
        
        if success:
            new_balance = user['wallet_balance'] - total_amount
            self.db.update_wallet_balance(booking['user_id'], new_balance)
            
            transaction_id = f"WALLET{datetime.now().strftime('%Y%m%d%H%M%S')}"
            payment_id = self.db.create_payment(
                booking['booking_id'], total_amount, 'wallet', transaction_id
            )
            
            loyalty_points = int(total_amount / 10)
            self.db.update_loyalty_points(booking['user_id'], loyalty_points)
            
            self.db.update_slot_status(booking['slot_id'], 'available')
            
            bill_details = {
                'ticket_number': ticket_number,
                'vehicle_number': booking['vehicle_number'],
                'slot_number': booking['slot_number'],
                'entry_time': booking['entry_time'],
                'exit_time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_hours': round(duration, 2),
                'base_price': base_price,
                'base_amount': round(base_price * duration, 2),
                'surge_amount': round(surge_amount, 2),
                'total_amount': round(total_amount, 2),
                'transaction_id': transaction_id,
                'loyalty_points_earned': loyalty_points,
                'wallet_balance': round(new_balance, 2),
                'pricing_breakdown': pricing.get_breakdown()
            }
            
            self.db.create_notification(
                booking['user_id'],
                f"Parking completed. ₹{total_amount:.2f} deducted from wallet. Earned {loyalty_points} points!",
                'billing'
            )
            return True, bill_details, "Exit processed successfully. Amount deducted from wallet."
        
        return False, None, "Failed to process exit"
    
    def get_booking_history(self, limit: int = 10) -> list:
        """Get booking history for current user"""
        if not self.user_id:
            return []
        bookings = self.db.get_booking_history(self.user_id, limit)
        return [dict(b) for b in bookings]


class PricingCalculator:
    def __init__(self, base_price: float, entry_time: datetime, exit_time: datetime):
        self.base_price = base_price
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.duration_hours = (exit_time - entry_time).total_seconds() / 3600
        self.surge_amount = 0.0
        
        if self.duration_hours < 1:
            self.duration_hours = 1.0
    
    def is_peak_hours(self, time: datetime) -> bool:
        hour = time.hour
        return 9 <= hour < 18
    
    def is_weekend(self, time: datetime) -> bool:
        return time.weekday() >= 5
    
    def is_night_time(self, time: datetime) -> bool:
        hour = time.hour
        return hour >= 22 or hour < 6
    
    def calculate_total(self) -> float:
        base_amount = self.base_price * self.duration_hours
        total = base_amount
        
        if self.is_peak_hours(self.entry_time):
            peak_charge = base_amount * 0.5
            total += peak_charge
            self.surge_amount += peak_charge
        
        if self.is_weekend(self.entry_time):
            weekend_charge = base_amount * 0.3
            total += weekend_charge
            self.surge_amount += weekend_charge
        
        if self.is_night_time(self.entry_time):
            night_charge = self.base_price * 5
            total = night_charge
            self.surge_amount = total - base_amount
        
        if self.duration_hours > 5:
            discount = total * 0.1
            total -= discount
            self.surge_amount = total - base_amount
        
        return max(total, self.base_price)
    
    def get_breakdown(self) -> Dict:
        base_amount = self.base_price * self.duration_hours
        return {
            'base_price': self.base_price,
            'duration_hours': round(self.duration_hours, 2),
            'base_amount': round(base_amount, 2),
            'is_peak_hours': self.is_peak_hours(self.entry_time),
            'is_weekend': self.is_weekend(self.entry_time),
            'is_night': self.is_night_time(self.entry_time),
            'surge_amount': round(self.surge_amount, 2),
            'long_duration_discount': round(base_amount * 0.1, 2) if self.duration_hours > 5 else 0,
            'total_amount': round(self.calculate_total(), 2)
        }
        
        return breakdown


class PaymentManager:
    """Handle payment processing"""
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.db = get_db_manager()
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.db = get_db_manager()
    
    def process_payment(self, booking_id: int, amount: float, 
                       payment_method: str) -> Tuple[bool, Optional[str], str]:
        booking = self.db.fetch_one(
            "SELECT * FROM bookings WHERE booking_id = ?", (booking_id,)
        )
        if not booking:
            return False, None, "Booking not found"
        
        if booking['payment_status'] == 'paid':
            return False, None, "Booking already paid"
        
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if payment_method == 'wallet':
            user = self.db.get_user_by_id(booking['user_id'])
            if not user or user['wallet_balance'] < amount:
                return False, None, "Insufficient wallet balance"
            
            self.db.update_wallet_balance(booking['user_id'], user['wallet_balance'] - amount)
            transaction_id = f"WALLET{transaction_id}"
        
        elif payment_method in ['upi', 'card']:
            transaction_id = f"{payment_method.upper()}{transaction_id}"
        
        elif payment_method == 'cash':
            transaction_id = f"CASH{transaction_id}"
        
        payment_id = self.db.create_payment(
            booking_id, amount, payment_method, transaction_id
        )
        
        if payment_id:
            loyalty_points = int(amount / 10)
            self.db.update_loyalty_points(booking['user_id'], loyalty_points)
            
            self.db.create_notification(
                booking['user_id'],
                f"Payment of ₹{amount:.2f} successful! Earned {loyalty_points} loyalty points.",
                'payment'
            )
            
            return True, transaction_id, f"Payment successful! Transaction ID: {transaction_id}"
        
        return False, None, "Failed to create payment record"
    
    def get_payment_details(self, booking_id: int) -> Optional[Dict]:
        payment = self.db.get_payment_by_booking(booking_id)
        return dict(payment) if payment else None

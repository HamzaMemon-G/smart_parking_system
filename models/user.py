"""User Authentication and Management"""

import hashlib
import re
from typing import Optional, Dict
from database.db_manager import get_db_manager


class UserAuth:
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        pattern = r'^\d{10}$'
        return re.match(pattern, phone.replace('-', '').replace(' ', '')) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        if len(password) > 50:
            return False, "Password too long"
        return True, "Password valid"
    
    @staticmethod
    def register_user(name: str, email: str, phone: str, password: str, 
                     user_type: str = 'customer') -> tuple[bool, str]:
        if not name or len(name) < 2:
            return False, "Name must be at least 2 characters"
        
        if not UserAuth.validate_email(email):
            return False, "Invalid email format"
        
        if not UserAuth.validate_phone(phone):
            return False, "Invalid phone number (10 digits required)"
        
        is_valid, msg = UserAuth.validate_password(password)
        if not is_valid:
            return False, msg
        
        db = get_db_manager()
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return False, "Email already registered"
        
        password_hash = UserAuth.hash_password(password)
        user_id = db.create_user(name, email, phone, password_hash, user_type)
        
        if user_id:
            db.create_notification(
                user_id, 
                f"Welcome to Smart Parking System, {name}! 🎉",
                'welcome'
            )
            return True, f"Registration successful! User ID: {user_id}"
        else:
            return False, "Registration failed. Please try again."
    
    @staticmethod
    def login_user(email: str, password: str) -> tuple[bool, Optional[Dict], str]:
        if not email or not password:
            return False, None, "Email and password required"
        
        db = get_db_manager()
        user = db.get_user_by_email(email)
        
        if not user:
            return False, None, "User not found"
        
        password_hash = UserAuth.hash_password(password)
        password_hash = UserAuth.hash_password(password)
        if user['password_hash'] != password_hash:
            return False, None, "Incorrect password"
        
        db.update_user_login(user['user_id'])
        
        user_dict = {
            'user_id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'user_type': user['user_type'],
            'wallet_balance': user['wallet_balance'],
            'loyalty_points': user['loyalty_points']
        }
        
        return True, user_dict, "Login successful"


class UserManager:
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = get_db_manager()
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = get_db_manager()
        self.user_info = self.get_user_info()
    
    def get_user_info(self) -> Optional[Dict]:
        user = self.db.get_user_by_id(self.user_id)
        if user:
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone'],
                'user_type': user['user_type'],
                'wallet_balance': user['wallet_balance'],
                'loyalty_points': user['loyalty_points'],
                'created_at': user['created_at']
            }
        return None
    
    def add_vehicle(self, vehicle_number: str, vehicle_type: str,
                   brand: str = None, model: str = None, color: str = None) -> tuple[bool, str]:
        vehicle_number = vehicle_number.upper().replace(' ', '').replace('-', '')
        
        if len(vehicle_number) < 6:
            return False, "Invalid vehicle number format"
        
        existing = self.db.get_vehicle_by_number(vehicle_number)
        if existing:
            return False, "Vehicle already registered"
        
        vehicle_id = self.db.add_vehicle(
            self.user_id, vehicle_number, vehicle_type, brand or 'Unknown', 
            model or 'Unknown', color or 'Unknown'
        )
        
        if vehicle_id:
            return True, f"Vehicle {vehicle_number} added successfully"
        return False, "Failed to add vehicle"
    
    def get_my_vehicles(self) -> list:
        vehicles = self.db.get_user_vehicles(self.user_id)
        return [dict(v) for v in vehicles]
    
    def delete_vehicle(self, vehicle_id: int) -> tuple[bool, str]:
        """Delete a vehicle belonging to the user"""
        vehicle = self.db.fetch_one(
            "SELECT * FROM vehicles WHERE vehicle_id = ? AND user_id = ?",
            (vehicle_id, self.user_id)
        )
        
        if not vehicle:
            return False, "Vehicle not found or doesn't belong to you"
        
        active_booking = self.db.fetch_one(
            "SELECT * FROM bookings WHERE vehicle_id = ? AND booking_status = 'active'",
            (vehicle_id,)
        )
        
        if active_booking:
            return False, "Cannot delete vehicle with active bookings"
        
        success = self.db.execute_query(
            "DELETE FROM vehicles WHERE vehicle_id = ?",
            (vehicle_id,)
        )
        
        if success:
            return True, "Vehicle deleted successfully"
        return False, "Failed to delete vehicle"
    
    def get_wallet_balance(self) -> float:
        user = self.db.get_user_by_id(self.user_id)
        return user['wallet_balance'] if user else 0.0
    
    def add_money_to_wallet(self, amount: float) -> tuple[bool, str]:
        if amount <= 0:
            return False, "Amount must be positive"
        
        if self.db.update_wallet_balance(self.user_id, amount):
            return True, f"₹{amount:.2f} added to wallet successfully"
        return False, "Failed to add money"
    
    def get_loyalty_points(self) -> int:
        user = self.db.get_user_by_id(self.user_id)
        return user['loyalty_points'] if user else 0
    
    def get_my_bookings(self, active_only: bool = False) -> list:
        if active_only:
            bookings = self.db.get_active_bookings(self.user_id)
        else:
            bookings = self.db.get_booking_history(self.user_id, limit=20)
        return [dict(b) for b in bookings]
    
    def get_loyalty_points(self) -> int:
        user = self.db.get_user_by_id(self.user_id)
        return user['loyalty_points'] if user else 0
    
    def get_my_bookings(self, active_only: bool = False) -> list:
        if active_only:
            bookings = self.db.get_active_bookings(self.user_id)
        else:
            bookings = self.db.get_booking_history(self.user_id, limit=20)
        return [dict(b) for b in bookings]
    
    def get_notifications(self, unread_only: bool = False) -> list:
        notifications = self.db.get_user_notifications(self.user_id, unread_only)
        return [dict(n) for n in notifications]
    
    def mark_notification_read(self, notification_id: int) -> bool:
        return self.db.mark_notification_read(notification_id)
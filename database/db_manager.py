"""Database Manager for Smart Parking System"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple


class DatabaseManager:
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'parking_system.db')
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
    
    def initialize_database(self):
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        try:
            with open(schema_path, 'r') as schema_file:
                schema_sql = schema_file.read()
            
            self.cursor.executescript(schema_sql)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> bool:
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Query execution error: {e}")
            return False
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[sqlite3.Row]:
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Fetch error: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Fetch error: {e}")
            return []
    
    def get_last_insert_id(self) -> int:
        return self.cursor.lastrowid
    
    def create_user(self, name: str, email: str, phone: str, 
                   password_hash: str, user_type: str = 'customer') -> Optional[int]:
        query = """
            INSERT INTO users (name, email, phone, password_hash, user_type)
            VALUES (?, ?, ?, ?, ?)
        """
        if self.execute_query(query, (name, email, phone, password_hash, user_type)):
            return self.get_last_insert_id()
        return None
    
    def get_user_by_email(self, email: str) -> Optional[sqlite3.Row]:
        query = "SELECT * FROM users WHERE email = ?"
        return self.fetch_one(query, (email,))
    
    def get_user_by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        query = "SELECT * FROM users WHERE user_id = ?"
        return self.fetch_one(query, (user_id,))
    
    def update_user_login(self, user_id: int):
        """Update last login timestamp"""
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?"
        return self.execute_query(query, (user_id,))
    
    def update_wallet_balance(self, user_id: int, amount: float) -> bool:
        """Update wallet balance"""
        query = "UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?"
        return self.execute_query(query, (amount, user_id))
    
    def update_loyalty_points(self, user_id: int, points: int) -> bool:
        query = "UPDATE users SET loyalty_points = loyalty_points + ? WHERE user_id = ?"
        return self.execute_query(query, (points, user_id))
    
    def add_vehicle(self, user_id: int, vehicle_number: str, vehicle_type: str,
                   brand: str = None, model: str = None, color: str = None) -> Optional[int]:
        """Add new vehicle"""
        query = """
            INSERT INTO vehicles (user_id, vehicle_number, vehicle_type, brand, model, color)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        if self.execute_query(query, (user_id, vehicle_number, vehicle_type, brand, model, color)):
            return self.get_last_insert_id()
        return None
    
    def get_user_vehicles(self, user_id: int) -> List[sqlite3.Row]:
        """Get all vehicles of a user"""
        query = "SELECT * FROM vehicles WHERE user_id = ?"
        return self.fetch_all(query, (user_id,))
    
    def get_vehicle_by_number(self, vehicle_number: str) -> Optional[sqlite3.Row]:
        query = "SELECT * FROM vehicles WHERE vehicle_number = ?"
        return self.fetch_one(query, (vehicle_number,))
    
    def create_parking_slot(self, slot_number: str, floor: int, section: str,
                           vehicle_type: str, base_price: float, slot_type: str = 'regular') -> Optional[int]:
        """Create new parking slot"""
        query = """
            INSERT INTO parking_slots (slot_number, floor, section, slot_type, 
                                      vehicle_type, base_price_per_hour, status)
            VALUES (?, ?, ?, ?, ?, ?, 'available')
        """
        if self.execute_query(query, (slot_number, floor, section, slot_type, 
                                     vehicle_type, base_price)):
            return self.get_last_insert_id()
        return None
    
    def get_available_slots(self, vehicle_type: str = None) -> List[sqlite3.Row]:
        """Get all available parking slots"""
        if vehicle_type:
            query = """
                SELECT * FROM parking_slots 
                WHERE status = 'available' AND vehicle_type = ?
                ORDER BY floor, section, slot_number
            """
            return self.fetch_all(query, (vehicle_type,))
        else:
            query = """
                SELECT * FROM parking_slots 
                WHERE status = 'available'
                ORDER BY floor, section, slot_number
            """
            return self.fetch_all()
    
    def get_slot_by_id(self, slot_id: int) -> Optional[sqlite3.Row]:
        """Get slot by ID"""
        query = "SELECT * FROM parking_slots WHERE slot_id = ?"
        return self.fetch_one(query, (slot_id,))
    
    def get_all_slots(self) -> List[sqlite3.Row]:
        """Get all parking slots"""
        query = "SELECT * FROM parking_slots ORDER BY floor, section, slot_number"
        return self.fetch_all(query)
    
    def update_slot_status(self, slot_id: int, status: str) -> bool:
        """Update slot status"""
        query = "UPDATE parking_slots SET status = ? WHERE slot_id = ?"
        return self.execute_query(query, (status, slot_id))
    
    def get_slot_statistics(self) -> Dict:
        """Get parking slot statistics"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved,
                SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance
            FROM parking_slots
        """
        result = self.fetch_one(query)
        if result:
            return dict(result)
        return {}
    
    def create_booking(self, ticket_number: str, user_id: int, vehicle_id: int,
                      slot_id: int, booking_type: str = 'instant') -> Optional[int]:
        """Create new booking"""
        query = """
            INSERT INTO bookings (ticket_number, user_id, vehicle_id, slot_id, 
                                 booking_type, booking_status, payment_status)
            VALUES (?, ?, ?, ?, ?, 'active', 'pending')
        """
        if self.execute_query(query, (ticket_number, user_id, vehicle_id, 
                                     slot_id, booking_type)):
            self.update_slot_status(slot_id, 'occupied')
            return self.get_last_insert_id()
        return None
    
    def get_booking_by_ticket(self, ticket_number: str) -> Optional[sqlite3.Row]:
        """Get booking by ticket number"""
        query = """
            SELECT b.*, u.name as user_name, u.email, u.phone,
                   v.vehicle_number, v.vehicle_type,
                   s.slot_number, s.floor, s.section, s.base_price_per_hour
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots s ON b.slot_id = s.slot_id
            WHERE b.ticket_number = ?
        """
        return self.fetch_one(query, (ticket_number,))
    
    def get_active_bookings(self, user_id: int = None) -> List[sqlite3.Row]:
        """Get active bookings"""
        if user_id:
            query = """
                SELECT b.*, v.vehicle_number, s.slot_number, s.floor, s.section
                FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                JOIN parking_slots s ON b.slot_id = s.slot_id
                WHERE b.user_id = ? AND b.booking_status = 'active'
                ORDER BY b.entry_time DESC
            """
            return self.fetch_all(query, (user_id,))
        else:
            query = """
                SELECT b.*, u.name, v.vehicle_number, s.slot_number
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                JOIN parking_slots s ON b.slot_id = s.slot_id
                WHERE b.booking_status = 'active'
                ORDER BY b.entry_time DESC
            """
            return self.fetch_all(query)
    
    def complete_booking(self, booking_id: int, exit_time: datetime, 
                        duration: float, total_amount: float) -> bool:
        """Complete a booking with exit details"""
        query = """
            UPDATE bookings 
            SET exit_time = ?, duration_hours = ?, total_amount = ?, 
                booking_status = 'completed'
            WHERE booking_id = ?
        """
        result = self.execute_query(query, (exit_time, duration, total_amount, booking_id))
        
        if result:
            booking = self.fetch_one("SELECT slot_id FROM bookings WHERE booking_id = ?", 
                                    (booking_id,))
            if booking:
                self.update_slot_status(booking['slot_id'], 'available')
        
        return result
    
    def get_booking_history(self, user_id: int, limit: int = 10) -> List[sqlite3.Row]:
        """Get user's booking history"""
        query = """
            SELECT b.*, v.vehicle_number, s.slot_number, s.floor, s.section
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots s ON b.slot_id = s.slot_id
            WHERE b.user_id = ? AND b.booking_status = 'completed'
            ORDER BY b.exit_time DESC
            LIMIT ?
        """
        return self.fetch_all(query, (user_id, limit))
    
    def cancel_booking(self, ticket_number: str) -> bool:
        """Cancel an active booking"""
        query = "UPDATE bookings SET booking_status = 'cancelled' WHERE ticket_number = ? AND booking_status = 'active'"
        return self.execute_query(query, (ticket_number,))
    
    def create_payment(self, booking_id: int, amount: float, 
                      payment_method: str, transaction_id: str = None) -> Optional[int]:
        """Create payment record"""
        query = """
            INSERT INTO payments (booking_id, amount, payment_method, transaction_id)
            VALUES (?, ?, ?, ?)
        """
        if self.execute_query(query, (booking_id, amount, payment_method, transaction_id)):
            self.execute_query(
                "UPDATE bookings SET payment_status = 'paid' WHERE booking_id = ?",
                (booking_id,)
            )
            return self.get_last_insert_id()
        return None
    
    def get_payment_by_booking(self, booking_id: int) -> Optional[sqlite3.Row]:
        """Get payment details for a booking"""
        query = "SELECT * FROM payments WHERE booking_id = ?"
        return self.fetch_one(query, (booking_id,))
    
    
    def get_revenue_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get revenue statistics"""
        if start_date and end_date:
            query = """
                SELECT 
                    COUNT(*) as total_bookings,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_revenue,
                    SUM(duration_hours) as total_hours
                FROM bookings
                WHERE booking_status = 'completed' 
                AND DATE(exit_time) BETWEEN ? AND ?
            """
            result = self.fetch_one(query, (start_date, end_date))
        else:
            query = """
                SELECT 
                    COUNT(*) as total_bookings,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_revenue,
                    SUM(duration_hours) as total_hours
                FROM bookings
                WHERE booking_status = 'completed'
            """
            result = self.fetch_one(query)
        
        return dict(result) if result else {}
    
    def get_daily_revenue(self, days: int = 7) -> List[sqlite3.Row]:
        """Get daily revenue for last N days"""
        query = """
            SELECT 
                DATE(exit_time) as date,
                COUNT(*) as bookings,
                SUM(total_amount) as revenue
            FROM bookings
            WHERE booking_status = 'completed'
            AND exit_time >= date('now', '-' || ? || ' days')
            GROUP BY DATE(exit_time)
            ORDER BY date DESC
        """
        return self.fetch_all(query, (days,))
    
    def get_peak_hours_analysis(self) -> List[sqlite3.Row]:
        """Analyze peak parking hours"""
        query = """
            SELECT 
                CAST(strftime('%H', entry_time) AS INTEGER) as hour,
                COUNT(*) as bookings
            FROM bookings
            GROUP BY hour
            ORDER BY bookings DESC
        """
        return self.fetch_all(query)
    
    def get_vehicle_type_distribution(self) -> List[sqlite3.Row]:
        """Get distribution of vehicle types"""
        query = """
            SELECT 
                v.vehicle_type,
                COUNT(*) as count
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            GROUP BY v.vehicle_type
        """
        return self.fetch_all(query)
    
    def create_notification(self, user_id: int, message: str, 
                          notification_type: str = 'info') -> Optional[int]:
        """Create notification for user"""
        query = """
            INSERT INTO notifications (user_id, message, notification_type)
            VALUES (?, ?, ?)
        """
        if self.execute_query(query, (user_id, message, notification_type)):
            return self.get_last_insert_id()
        return None
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[sqlite3.Row]:
        """Get user notifications"""
        if unread_only:
            query = """
                SELECT * FROM notifications 
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
            """
        else:
            query = """
                SELECT * FROM notifications 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            """
        return self.fetch_all(query, (user_id,))
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        query = "UPDATE notifications SET is_read = 1 WHERE notification_id = ?"
        return self.execute_query(query, (notification_id,))


_db_instance = None

def get_db_manager() -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
        _db_instance.connect()
    return _db_instance

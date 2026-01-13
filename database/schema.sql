-- Smart Parking Management System Database Schema

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    user_type TEXT DEFAULT 'customer',
    loyalty_points INTEGER DEFAULT 0,
    wallet_balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_number TEXT UNIQUE NOT NULL,
    vehicle_type TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    color TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Parking Slots Table
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number TEXT UNIQUE NOT NULL,
    floor INTEGER NOT NULL,
    section TEXT NOT NULL,
    slot_type TEXT DEFAULT 'regular',
    vehicle_type TEXT NOT NULL,
    base_price_per_hour REAL NOT NULL,
    status TEXT DEFAULT 'available',
    location_x INTEGER,
    location_y INTEGER
);

-- Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    booking_date DATE DEFAULT CURRENT_DATE,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP,
    duration_hours REAL,
    base_amount REAL,
    surge_amount REAL DEFAULT 0.0,
    discount_amount REAL DEFAULT 0.0,
    total_amount REAL,
    payment_status TEXT DEFAULT 'pending',
    booking_status TEXT DEFAULT 'active',
    booking_type TEXT DEFAULT 'instant',
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    transaction_id TEXT,
    payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    refund_amount REAL DEFAULT 0.0,
    refund_reason TEXT,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

-- Pricing Rules Table
CREATE TABLE IF NOT EXISTS pricing_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    day_type TEXT,
    time_slot TEXT,
    multiplier REAL DEFAULT 1.0,
    flat_rate REAL,
    is_active INTEGER DEFAULT 1
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- System Logs Table
CREATE TABLE IF NOT EXISTS system_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    description TEXT,
    ip_address TEXT
);

-- Analytics Cache Table
CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_bookings INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0.0,
    occupancy_rate REAL DEFAULT 0.0,
    peak_hour TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin user (password: admin123)
INSERT OR IGNORE INTO users (user_id, name, email, phone, password_hash, user_type)
VALUES (1, 'Admin', 'admin@parking.com', '9999999999', 
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin');

-- Insert default pricing rules
INSERT OR IGNORE INTO pricing_rules (rule_name, day_type, time_slot, multiplier)
VALUES 
    ('Peak Hours', 'weekday', 'afternoon', 1.5),
    ('Weekend', 'weekend', 'all', 1.3),
    ('Night Discount', 'all', 'night', 0.5);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_vehicle ON bookings(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_bookings_slot ON bookings(slot_id);
CREATE INDEX IF NOT EXISTS idx_bookings_ticket ON bookings(ticket_number);
CREATE INDEX IF NOT EXISTS idx_vehicles_user ON vehicles(user_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_number ON vehicles(vehicle_number);
CREATE INDEX IF NOT EXISTS idx_parking_slots_status ON parking_slots(status);
CREATE INDEX IF NOT EXISTS idx_parking_slots_type ON parking_slots(vehicle_type);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);

-- Initialize 100 parking slots
INSERT OR IGNORE INTO parking_slots (slot_number, floor, section, vehicle_type, base_price_per_hour, location_x, location_y)
SELECT 
    section || '-' || printf('%02d', slot),
    floor,
    section,
    CASE 
        WHEN section IN ('A', 'B') THEN 'car'
        WHEN section = 'C' THEN 'bike'
        ELSE 'truck'
    END,
    CASE 
        WHEN section IN ('A', 'B') THEN 20.0
        WHEN section = 'C' THEN 10.0
        ELSE 30.0
    END,
    ((slot - 1) % 10) * 80 + 50,
    ((slot - 1) / 10) * 60 + 50
FROM 
    (SELECT 1 as floor, 'A' as section UNION SELECT 1, 'B' UNION SELECT 2, 'A' UNION SELECT 2, 'B' UNION SELECT 3, 'C'),
    (SELECT 1 as slot UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
     UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
     UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
     UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20);

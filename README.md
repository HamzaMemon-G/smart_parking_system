# 🚗 Smart Parking Management System

A comprehensive parking management solution with **dual interfaces**: Django web portal for customers and Tkinter desktop app for admin management. Features real-time slot management, QR code verification, automated billing with dynamic pricing, digital wallet, automatic booking expiration, and modern GUI.

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Django](https://img.shields.io/badge/Django-6.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Development-orange.svg)

## ✨ Features

### Dual Interface System
- 🌐 **Django Web Portal** - Customer booking interface with responsive design
- 🖥️ **Tkinter Admin Dashboard** - Desktop application for parking management
- 🔄 **Unified Database** - Seamless data synchronization between both interfaces

### Core Features
- 🅿️ **Real-time Parking Slot Management** - 120 slots across 3 floors with multiple sections
- 📱 **QR Code Booking System** - Scan QR codes for entry/exit verification
- ⏰ **Automatic Expiration** - 30-minute check-in deadline with auto-cancellation
- 🕐 **Timezone Management** - Proper UTC to local time conversion
- 👤 **User Authentication** - Django authentication with secure password hashing
- 🚗 **Vehicle Management** - Register multiple vehicles with brand, model, and color
- 💰 **Automatic Payment** - Money deducted from wallet on exit
- 🎫 **QR Code Generation** - Automatic QR ticket creation with booking details
- 📄 **PDF Receipts** - Professional parking receipts with transaction details
- 💳 **Digital Wallet** - Add money and manage balance (Django web portal)
- ⏱️ **30-Minute Check-in Window** - Automatic deadline enforcement
- ❌ **Auto-Cancellation** - Expired bookings freed automatically
- 🔄 **Real-time Sync** - Django web and Tkinter desktop share same database
- 🧭 **Timezone Aware** - Proper UTC to local time conversion
- ✅ **Balance Check Before Booking** - Prevents booking without sufficient funds
- 🔍 **QR Code Verification** - Scan QR for entry/exit with detailed booking info
- 📱 **Web-based Booking** - Book parking slots via Django portal
- 🖥️ **Admin Check-in/out** - Process customer entry/exit via Tkinter app
- 💸 **Instant Receipts** - Beautiful receipt with transaction ID and points (2-hour minimum)
- 🚘 **Vehicle Selection Dialog** - Easy selection when multiple vehicles registered
- 🔍 **Floor Filtering** - Filter parking slots by floor with integer-based search
- 📱 **Ticket QR Preview** - View QR codes directly in the application
- 💸 **Instant Receipts** - Beautiful receipt with transaction ID, points earned, and balance
- 🎯 **Active Book (Tkinter Desktop)
- 🔧 **QR Code Scanning** - Scan booking QR codes via webcam or file upload
- ✅ **Manual Check-in/out** - Process customer entry and exit
- 📋 **Pending Bookings Monitor** - View all pending check-ins with time remaining
- ⚙️ **Manual Expiration** - Force expire old bookings with confirmation
- 👥 **User Management** - View all users and bookings
- 📈 **Revenue Reports** - Daily, weekly, monthly analytics
- 📊 **Chart Generation** - Revenue trends, occupancy, peak hours
- 📁 **Data Export** - Export bookings to CSV
- 🔍 **Real-time Monitoring** - Live parking status
- 💾 **Database Backup** - One-click database backuper 5 hours

### Admin Features
- 🔧 **Parking Structure Initialization** - Setup slots automatically
- 👥 **User Management** - View all users and bookings
- 📈 **Revenue Reports** - Daily, weekly, monthly analytics
- 📊 **Chart Generation** - Revenue trends, occupancy, peak hours
- 📁 **Data Export** - Export bookings to CSV
- 🔍 **Real-time Monitoring** - Live parking status

## 🚀 Quick Start

### Prerequisites
# or
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run Django migrations (first time setup):**
```bash
cd parking_web
python manage.py migrate
cd ..
```

5. **Start the Django web server:**
```bash
cd parking_web
python manage.py runserver
```
- Web portal will be available at: http://127.0.0.1:8000/

6. **Start the Tkinter admin dashboard (in separate terminal):**
```bash
python main.py
```

### Quick Setup with start_system.bat (Windows)
```bash
start_system.bat
```
This will:
- Check and initialize database if needed
- Activate virtual environment
- Start Django web server
- Verify database
- Launch Tkinter admin dashboard

## 📖 User Guide

### For Customers (Django Web Portal)

#### 1. Register Account
- Navigate to http://127.0.0.1:8000/accounts/register/
- Fill in name, email, phone, and password
- Login with your credentials at /accounts/login/

#### 2. Add Vehicle
- Go to "My Vehicles" section
- Click "Add New Vehicle"
- Enter vehicle details (number, type, brand, model, color)
- Vehicle will be available for booking

#### 3. Recharge Wallet
- Go to "Wallet" section
- Enter amount to add
- Balance updates instantly

#### 4. Book Parking Slot
- Go to "Browse Slots" or "Quick Booking"
- Filter by floor or section
- Select available slot
- Choose hours (1-8 hours)
- Confirm booking
- **30-minute check-in window starts immediately**
- QR code generated automatically

#### 5. View Bookings
- Go to "My Bookings" to see all bookings
- Download QR code for check-in
- Check remaining time before deadline
- View booking status (Pending/Active/Completed/Cancelled)

### For Admins (Tkinter Desktop App)

#### 1. QR Code Verification
- Open "🔍 QR Verification" tab
- Select mode: Entry or Exit
- Scan QR via webcam OR upload QR image file
- Booking details display automatically
- Shows time remaining for check-in
- Warning if booking expired

#### 2. Process Check-in (Entry Mode)
- Scan customer's QR code
- Review booking details:
  - Customer name, vehicle, slot
  - Time remaining before deadline
- Click "Process Entry" to check-in
- Customer status changes to "Active"
- Slot marked as occupied
5. Monitor Pending Check-ins
#### 7. Generate Analytics
- Go to "📈 Analytics" tab
- Click buttons to generate:
  - Revenue trend charts (saved to outputs/charts/)
  - Occupancy pie charts
  - Peak hours analysis
  - CSV export of all bookings (saved to outputs/reports/)

## 🏗️ Project Structure

```
smart_parking_system/
│
├── .venv/                          # Virtual environment (not in repo)
├── main.py                         # Tkinter admin dashboard (2180+ lines)
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── start_system.bat                # Windows quick start script
│
├── database/
│   ├── __init__.py
│   ├── db_manager.py              # Database operations manager
│   ├── schema.sql                 # Database schema with indexes
│   └── parking_system.db          # SQLite database (UNIFIED - used by both Django & Tkinter)
│
├── parking_web/                   # Django Web Application
│   ├── manage.py                  # Django management script
│   ├── parking_web/               # Django project settings
│   │   ├── settings.py            # Django configuration (database path: database/parking_system.db)
│   │   ├── urls.py                # URL routing
│   │   └── wsgi.py                # WSGI configuration
│   ├── accounts/                  # User authentication app
│   │   ├── views.py               # Login, register, profile
│   │   ├── models.py              # User model
│   │   └── backends.py            # Custom auth backend
│   ├── bookings/                  # Booking management app
│   │   ├── views.py               # Booking CRUD, QR generation, auto-expiry
│   │   ├── models.py              # Booking, ParkingSlot models
│   │   └── templates/             # HTML templates
│   ├── vehicles/                  # Vehicle management app
│   ├── payments/                  # Payment processing app
│   ├── media/                     # User-uploaded files (QR codes)
│   └── static/                    # CSS, JS, images
│
├── models/
│   ├── __init__.py
│   ├── user.py                    # User operations (legacy - replaced by Django)
│   ├── parking_slot.py            # Parking slot operations
│   ├── booking.py                 # Booking system
│   └── analytics.py               # Analytics & report generation
│
├── utils/
│   ├── __ini(17 columns) - User accounts
   - Core: user_id, name, email, phone, password_hash, user_type
   - Wallet: wallet_balance, loyalty_points
   - Dates: created_at, last_login
   - Django auth: is_superuser, is_staff, is_active, date_joined, first_name, last_name, username

2. **vehicles** - User vehicles
   - vehicle_id, user_id, vehicle_number, vehicle_type
   - brand, model, color

3. **parking_slots** - Parking slot inventory
   - slot_id, slot_number, floor, section
   - vehicle_type, base_price_per_hour, status

4. **bookings** (24 columns) - Parking bookings
   - Core: booking_id, ticket_number, user_id, vehicle_id, slot_id
   - Dates: booking_date, booking_time, entry_time, exit_time
   - Check-in: checkin_time, checkout_time, checkin_deadline, forfeited
   - Pricing: duration_hours, base_amount, surge_amount, discount_amount, total_amount
   - Status: booking_status (pending/active/completed/cancelled), booking_type, payment_status
   - QR: qr_code_data, qr_code_path
   - Notes: notes

### Django System Tables
- django_session - Session management
- django_migrations - Migration history
- auth_* - Django authentication tables
- admin_* - Django admin interface
- contenttypes - Django content types

## 🛠️ Technical Stack
Dynamic Pricing Engine

The system calculates parking charges based on:

1. **Base Rate** - Varies by vehicle type
   - Car: ₹20/hour
   - Bike: ₹10/hour  
   - Truck: ₹30/hour

2. **Time-based Surcharges**:
   - Peak hours (9 AM - 6 PM): +50%
   - Weekends (Saturday/Sunday): +30%
   - Night parking (10 PM - 6 AM): Flat ₹100

3. **Duration Discounts**:
   - Over 5 hours: -10%

### Database Unification

**Single Source of Truth:**
- Both Django and Tkinter use: `database/parking_system.db`
- Django settings: `BASE_DIR.parent / 'database' / 'parking_system.db'`
- Tkinter default: `database/parking_system.db`
- Real-time synchronization between web and desktop interfaces

### Security Features

- **Django Authentication** - Built-in user management with password hashing
- **Custom Auth Backend** - Supports existing SHA-256 hashes + Django hashing
- **SQL Injection Prevention** - Parameterized queries throughout
- **Session Management** - Django session handling + secure Tkinter architecture
- **Data Validation** - Comprehensive input sanitization
- **Active Booking Protection** - Cannot delete vehicles/users with active bookings
- **Ownership Verification** - Users can only modify their own data# User auth, registration, vehicle management, wallet
│   ├── parking_slot.py            # Parking slot operations with floor filtering
│   ├── booking.py                 # Booking system with automatic payment
│   └── analytics.py               # Analytics & report generation
│
├── utils/
│   ├── __init__.py
│   ├── qr_generator.py            # QR code generation for tickets
│   └── pdf_generator.py           # PDF receipt generation
│
├── outputs/
│   ├── charts/                    # Generated analytics charts
│   ├── reports/                   # CSV exports and reports
│   └── tickets/                   # QR code ticket images
│
└── .vscode/                       # VSCode settings (optional)
```

## 💾 Database Schema

### Tables

1. **users** - User accounts (customer/admin)
   - user_id, name, email, phone, password_hash, user_type
   - wallet_balance, loyalty_points, created_at, last_login

2. **vehicles** - User vehicles
   - vehicle_id, user_id, vehicle_number, vehicle_type
   - brand, model, color

3. **parking_slots** - Parking slot inventory
   - slot_id, slot_number, floor, section, slot_type
   - vehicle_type, base_price_per_hour, status
   - location_x, location_y

4. **bookings12.2** - Programming language
## 🎯 Use Cases

### Personal Use
- Manage small parking lots
- Track personal vehicle parking
- Analyze parking patterns
- Digital wallet convenience

### Commercial Use
- Apartment complex parking management
- Office parking allocation
- Shopping mall parking systems
- Educational institution parking
- Hospital parking management

### Business Intelligence
- Revenue optimization with dynamic pricing
- Peak hour staffing decisions
- Pricing strategy adjustments
- Occupancy forecasting
- Customer behavior analysis

## 🚧 Roadmap / Future Enhancements

- [x] Django web portal for customers
- [x] QR code booking system
- [x] Automatic booking expiration (30-min deadline)
- [x] Timezone-aware datetime handling
- [x] Unified database system
- [ ] Email/SMS notifications for bookings
- [ ] Advance booking (book for future date/time)
- [ ] Waiting list when parking full
- [ ] Multi-location support
- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Security camera integration
- [ ] Mobile app (React Native)
- [ ] Public API with authentication
- [ ] Subscription plans for regular users
- [ ] Loyalty point redemption system
- Track personal vehicle parking
- Analyze parking patterns
- Digital wallet convenience

### Commercial Use
- Apartment complex parking management
- Office parking allocation
- Shopping mall parking systems
- Educational institution parking
- Hospital parking management

### Business Intelligence
- Revenue optimization with dynamic pricing
- Peak hour staffing decisions
- Pricing strategy adjustments
- Occupancy forecasting
- Customer behavior analysisty
- ✅ User authentication
- ✅ Parking slot management
- ✅ Booking system
- ✅ Analytics module
- ✅ QR code generation
- ✅ PDF generation

## 🔒 Security Features

- **Password Hashing** - SHA-256 encryption for passwords
- **SQL Injection Prevention** - Parameterized queries
- **Session Management** - Secure user sessions
- **Data Validation** - Input sanitization

## 📝 Sample Data

After running `initialize_data.py`, you get:

**Users:**
- Admin: admin@parking.com / admin123
- John Doe: john@example.com / password123
- Jane Smith: jane@example.com / password123
- Bob Wilson: bob@example.com / password123

**Parking Structure:**
- 60 slots across 3 floors
- 3 sections per floor (A, B, C)
- Mix of Car/Bike/Truck slots
- Regular, Covered, and EV Charging slots

**Sample Bookings:**
- 4 completed bookings with payment history
- Revenue analytics available

## 🎯 Use Cases

### Personal Use
- Manage small parking lots
- Track personal vehicle parking
- Analyze parking patterns

### Commercial Use
- Apartment parking management
- Office parking allocation
- Shopping mall parking
- Educational institution parking
 for both Django and Tkinter
2. Additional payment gateways
3. Advanced analytics and reporting
4. Mobile app development
5. API development for third-party integration
6. Test coverage
7. Documentation improvements

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Authors

Created for Smart Parking Management System Project

## 🙏 Acknowledgments

- Python community for excellent libraries
- Django framework for robust web development
- Tkinter for cross-platform desktop GUI support
- SQLite for reliable embedded database
- Open source QR code libraries (qrcode, pyzbar)

## 📧 Support

For issues or questions:
1. Check the README for setup instructions
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure database exists: `database/parking_system.db`
4. Check Django migrations: `python manage.py migrate`

## 🎓 Educational Purpose

This project demonstrates:
- **Full-Stack Development** - Django backend + Tkinter frontend
- **Database Design** - Unified SQLite database with 4 main tables
- **Object-Oriented Programming** - Clean OOP architecture
- **Real-time Systems** - Synchronized web and desktop interfaces
- **QR Technology** - Generation and scanning implementation
- **Timezone Management** - UTC to local conversion
- **Business Logic** - Dynamic pricing, automatic expiration
- **Data Analytics** - Visualization and reporting
- **Security Practices** - Authentication, authorization, validation

---

**Made with ❤️ using Python, Django & Tkinter** | **Version 2.0** | **February 2026**

## Tech Stack Summary

- **Backend:** Python 3.12.2, Django 6.0.2
- **Database:** SQLite3 (unified)
- **Desktop GUI:** Tkinter + ttkthemes
- **Web Framework:** Django + djangorestframework
- **QR Codes:** qrcode (generation), pyzbar (scanning)
- **Analytics:** Pandas, Matplotlib
- **Reports:** ReportLab (PDF)
- **Image Processing:** Pillow (PIL)

## Database Location

⚠️ **Important:** Both Django and Tkinter use the same database:
- Path: `database/parking_system.db`
- Size: ~126KB
- All changes sync automatically between interfaces
This project demonstrates:
- Object-Oriented Programming (OOP)
- Database design and operations
- GUI application development
- Business logic implementation
- Data analytics and visualization
- File I/O operations
- Real-world problem solving

---

**Made with ❤️ using Python** | **Version 1.0** | **January 2026**

## Tech Stack

- **GUI:** Tkinter + ttkthemes
- **Database:** SQLite3
- **Analytics:** Pandas, Matplotlib
- **Reports:** ReportLab
- **QR Codes:** qrcode library

## License

MIT License - College Project

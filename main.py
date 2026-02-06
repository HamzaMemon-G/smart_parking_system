"""
Main GUI Application for Smart Parking System
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import UserAuth, UserManager
from models.parking_slot import ParkingSlotManager
from models.booking import BookingManager, PaymentManager
from models.analytics import AnalyticsManager
from utils.qr_generator import QRCodeGenerator
from utils.pdf_generator import PDFGenerator
from utils.qr_handler import QRHandler
from database.db_manager import get_db_manager
from datetime import datetime, timedelta
import json
from PIL import Image, ImageTk


class LoginWindow:
    """Login and Registration Window"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        
        main_frame = ttk.Frame(root, padding="40")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        title = ttk.Label(main_frame, text="🚗 Smart Parking System", 
                         font=('Arial', 24, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(main_frame, text="Email:", font=('Arial', 12)).grid(
            row=1, column=0, sticky='e', padx=10, pady=10)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=30, font=('Arial', 11))
        email_entry.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Password:", font=('Arial', 12)).grid(
            row=2, column=0, sticky='e', padx=10, pady=10)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                   width=30, show='*', font=('Arial', 11))
        password_entry.grid(row=2, column=1, padx=10, pady=10)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        login_btn = ttk.Button(btn_frame, text="Admin Login", command=self.login, width=20)
        login_btn.pack(padx=5)
        
        password_entry.bind('<Return>', lambda e: self.login())
    
    def login(self):
        """Handle admin login only"""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter email and password")
            return
        
        success, user_data, message = UserAuth.login_user(email, password)
        
        if success:
            # Only allow admin users
            if user_data['user_type'] != 'admin':
                messagebox.showerror("Access Denied", "Only administrators can access this application.\\nCustomers please use the web portal.")
                return
            
            messagebox.showinfo("Success", f"Welcome, {user_data['name']}!")
            self.on_login_success(user_data)
        else:
            messagebox.showerror("Login Failed", message)


class MainApplication:
    """Main Application Window"""
    
    def __init__(self, root, user_data):
        self.root = root
        self.user_data = user_data
        self.user_manager = UserManager(user_data['user_id'])
        self.parking_manager = ParkingSlotManager()
        self.booking_manager = BookingManager(user_data['user_id'])
        self.payment_manager = PaymentManager(user_data['user_id'])
        self.analytics_manager = AnalyticsManager()
        
        self.root.title(f"Smart Parking System - {user_data['name']}")
        self.root.geometry("1200x700")
        
        self.setup_ui()
        self.refresh_dashboard()
    
    def setup_ui(self):
        top_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        top_frame.pack(fill='x')
        top_frame.pack_propagate(False)
        
        welcome_label = tk.Label(top_frame, text=f"Welcome, {self.user_data['name']}", 
                                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='#ecf0f1')
        welcome_label.pack(side='left', padx=20, pady=15)
        
        wallet_frame = tk.Frame(top_frame, bg='#27ae60', relief='raised', bd=2)
        wallet_frame.pack(side='left', padx=10, pady=15)
        tk.Label(wallet_frame, text="💰 Wallet", font=('Arial', 10, 'bold'), 
                bg='#27ae60', fg='white').pack(padx=10, pady=2)
        tk.Label(wallet_frame, text=f"₹{self.user_data['wallet_balance']:.2f}", 
                font=('Arial', 14, 'bold'), bg='#27ae60', fg='white').pack(padx=10, pady=2)
        
        points_frame = tk.Frame(top_frame, bg='#e67e22', relief='raised', bd=2)
        points_frame.pack(side='left', padx=10, pady=15)
        tk.Label(points_frame, text="⭐ Points", font=('Arial', 10, 'bold'), 
                bg='#e67e22', fg='white').pack(padx=10, pady=2)
        tk.Label(points_frame, text=str(self.user_data['loyalty_points']), 
                font=('Arial', 14, 'bold'), bg='#e67e22', fg='white').pack(padx=10, pady=2)
        
        btn_frame = tk.Frame(top_frame, bg='#2c3e50')
        btn_frame.pack(side='right', padx=20, pady=15)
        refresh_btn = tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_dashboard,
                               bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                               relief='raised', bd=2, padx=15, pady=8, cursor='hand2')
        refresh_btn.pack(side='left', padx=5)
        logout_btn = tk.Button(btn_frame, text="🚪 Logout", command=self.logout,
                              bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                              relief='raised', bd=2, padx=15, pady=8, cursor='hand2')
        logout_btn.pack(side='left', padx=5)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Admin-only interface
        self.create_dashboard_tab()
        self.create_admin_tab()
        self.create_qr_verification_tab()
        self.create_analytics_tab()
        
        # Auto-expire old bookings on startup
        self.auto_expire_bookings()
    
    def create_dashboard_tab(self):
        """Dashboard tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Dashboard")
        
        stats_frame = ttk.LabelFrame(tab, text="Parking Statistics", padding="15")
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_labels = {}
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()
        
        stat_names = [
            ('total', 'Total Slots', 0, 0),
            ('available', 'Available', 0, 1),
            ('occupied', 'Occupied', 0, 2),
            ('active_bookings', 'Active Bookings', 1, 0),
            ('total_revenue', 'Total Revenue', 1, 1),
        ]
        
        for key, label, row, col in stat_names:
            frame = tk.Frame(stats_grid, bg='#ecf0f1', relief='raised', bd=2)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            tk.Label(frame, text=label, font=('Arial', 10), bg='#ecf0f1').pack(pady=5)
            self.stats_labels[key] = tk.Label(frame, text='0', font=('Arial', 16, 'bold'), bg='#ecf0f1')
            self.stats_labels[key].pack(pady=5)
    
    def create_admin_tab(self):
        """Admin panel tab with parking slot management"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Admin Panel")
        
        # Create sub-notebook for admin sections
        admin_notebook = ttk.Notebook(tab)
        admin_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Parking Slots Management Tab
        slots_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(slots_tab, text="🅿️ Parking Slots")
        self.create_slots_management(slots_tab)
        
        # User Management Tab
        users_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(users_tab, text="👥 Users")
        self.create_users_management(users_tab)
        
        # Active Bookings Tab
        bookings_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(bookings_tab, text="📋 Bookings")
        self.create_bookings_management(bookings_tab)
        
        # System Settings Tab
        settings_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(settings_tab, text="⚙️ Settings")
        self.create_system_settings(settings_tab)
    
    def create_slots_management(self, parent):
        """Create parking slots management interface"""
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="Slot Management", padding="10")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="➕ Add Slot", command=self.add_parking_slot, 
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Slot", command=self.edit_parking_slot,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Slot", command=self.delete_parking_slot,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_parking_slots,
                  width=15).pack(side='left', padx=5)
        
        # Filter frame
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(filter_frame, text="Filter:").pack(side='left', padx=5)
        
        ttk.Label(filter_frame, text="Floor:").pack(side='left')
        self.slot_floor_filter = ttk.Combobox(filter_frame, width=10, 
                                             values=['All', '1', '2', '3'])
        self.slot_floor_filter.set('All')
        self.slot_floor_filter.pack(side='left', padx=5)
        self.slot_floor_filter.bind('<<ComboboxSelected>>', lambda e: self.load_parking_slots())
        
        ttk.Label(filter_frame, text="Type:").pack(side='left', padx=(10, 0))
        self.slot_type_filter = ttk.Combobox(filter_frame, width=10,
                                            values=['All', 'car', 'bike', 'truck'])
        self.slot_type_filter.set('All')
        self.slot_type_filter.pack(side='left', padx=5)
        self.slot_type_filter.bind('<<ComboboxSelected>>', lambda e: self.load_parking_slots())
        
        ttk.Label(filter_frame, text="Status:").pack(side='left', padx=(10, 0))
        self.slot_status_filter = ttk.Combobox(filter_frame, width=12,
                                              values=['All', 'available', 'occupied', 'reserved'])
        self.slot_status_filter.set('All')
        self.slot_status_filter.pack(side='left', padx=5)
        self.slot_status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_parking_slots())
        
        # Slots list
        list_frame = ttk.LabelFrame(parent, text="Parking Slots", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('Slot ID', 'Slot Number', 'Floor', 'Section', 'Type', 
                  'Vehicle Type', 'Price/Hr', 'Status')
        self.slots_tree = ttk.Treeview(list_frame, columns=columns, 
                                      show='tree headings', height=15)
        
        for col in columns:
            self.slots_tree.heading(col, text=col)
            width = 100 if col in ['Slot Number', 'Section'] else 80
            self.slots_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.slots_tree.yview)
        self.slots_tree.configure(yscrollcommand=scrollbar.set)
        
        self.slots_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Stats frame
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.total_slots_label = ttk.Label(stats_frame, text="Total: 0", font=('Arial', 10, 'bold'))
        self.total_slots_label.pack(side='left', padx=10)
        
        self.available_slots_label = ttk.Label(stats_frame, text="Available: 0", 
                                              font=('Arial', 10), foreground='green')
        self.available_slots_label.pack(side='left', padx=10)
        
        self.occupied_slots_label = ttk.Label(stats_frame, text="Occupied: 0",
                                             font=('Arial', 10), foreground='red')
        self.occupied_slots_label.pack(side='left', padx=10)
        
        # Load slots
        self.load_parking_slots()
    
    def create_users_management(self, parent):
        """Create users management interface"""
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="User Management", padding="10")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="👁️ View Details", command=self.view_user_details,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💰 Add Balance", command=self.add_user_balance,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_users,
                  width=15).pack(side='left', padx=5)
        
        # Users list
        list_frame = ttk.LabelFrame(parent, text="Users", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('User ID', 'Name', 'Email', 'Phone', 'Type', 
                  'Wallet Balance', 'Loyalty Points', 'Registered')
        self.users_tree = ttk.Treeview(list_frame, columns=columns,
                                      show='tree headings', height=15)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            width = 150 if col in ['Name', 'Email'] else 100
            self.users_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Load users
        self.load_users()
    
    def create_bookings_management(self, parent):
        """Create bookings management interface"""
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="Booking Management", padding="10")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="📋 View Details", command=self.view_booking_details,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ Cancel Booking", command=self.admin_cancel_booking,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_admin_bookings,
                  width=15).pack(side='left', padx=5)
        
        # Filter
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(filter_frame, text="Status:").pack(side='left', padx=5)
        self.booking_status_filter = ttk.Combobox(filter_frame, width=15,
                                                 values=['All', 'pending', 'active', 'completed', 'cancelled', 'expired'])
        self.booking_status_filter.set('All')
        self.booking_status_filter.pack(side='left', padx=5)
        self.booking_status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_admin_bookings())
        
        # Bookings list
        list_frame = ttk.LabelFrame(parent, text="All Bookings", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('Booking ID', 'Ticket', 'User', 'Vehicle', 'Slot', 
                  'Status', 'Amount', 'Entry Time')
        self.admin_bookings_tree = ttk.Treeview(list_frame, columns=columns,
                                               show='tree headings', height=15)
        
        for col in columns:
            self.admin_bookings_tree.heading(col, text=col)
            width = 120 if col in ['Ticket', 'User', 'Vehicle'] else 100
            self.admin_bookings_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.admin_bookings_tree.yview)
        self.admin_bookings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.admin_bookings_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Load bookings
        self.load_admin_bookings()
    
    def create_system_settings(self, parent):
        """Create system settings interface"""
        settings_frame = ttk.LabelFrame(parent, text="System Configuration", padding="15")
        settings_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pricing settings
        pricing_frame = ttk.LabelFrame(settings_frame, text="Pricing", padding="10")
        pricing_frame.pack(fill='x', pady=5)
        
        ttk.Label(pricing_frame, text="Default Car Rate (₹/hr):").grid(row=0, column=0, sticky='w', pady=5)
        self.car_rate_var = tk.StringVar(value="20")
        ttk.Entry(pricing_frame, textvariable=self.car_rate_var, width=15).grid(row=0, column=1, padx=10)
        
        ttk.Label(pricing_frame, text="Default Bike Rate (₹/hr):").grid(row=1, column=0, sticky='w', pady=5)
        self.bike_rate_var = tk.StringVar(value="10")
        ttk.Entry(pricing_frame, textvariable=self.bike_rate_var, width=15).grid(row=1, column=1, padx=10)
        
        ttk.Label(pricing_frame, text="Default Truck Rate (₹/hr):").grid(row=2, column=0, sticky='w', pady=5)
        self.truck_rate_var = tk.StringVar(value="30")
        ttk.Entry(pricing_frame, textvariable=self.truck_rate_var, width=15).grid(row=2, column=1, padx=10)
        
        # Booking settings
        booking_frame = ttk.LabelFrame(settings_frame, text="Booking", padding="10")
        booking_frame.pack(fill='x', pady=5)
        
        ttk.Label(booking_frame, text="Check-in Window (minutes):").grid(row=0, column=0, sticky='w', pady=5)
        self.checkin_window_var = tk.StringVar(value="30")
        ttk.Entry(booking_frame, textvariable=self.checkin_window_var, width=15).grid(row=0, column=1, padx=10)
        
        # Database operations
        db_frame = ttk.LabelFrame(settings_frame, text="Database Operations", padding="10")
        db_frame.pack(fill='x', pady=5)
        
        ttk.Button(db_frame, text="🔄 Backup Database", command=self.backup_database,
                  width=20).pack(pady=5)
        ttk.Button(db_frame, text="📊 View Statistics", command=self.show_statistics,
                  width=20).pack(pady=5)
        ttk.Button(db_frame, text="🗑️ Clear Old Data", command=self.clear_old_data,
                  width=20).pack(pady=5)
    
    def create_qr_verification_tab(self):
        """QR Code Verification Tab for Entry/Exit Processing"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📷 QR Verification")
        
        # Entry/Exit Selection
        mode_frame = ttk.LabelFrame(tab, text="Processing Mode", padding="10")
        mode_frame.pack(fill='x', padx=10, pady=10)
        
        self.qr_mode_var = tk.StringVar(value="entry")
        ttk.Radiobutton(mode_frame, text="Entry (Check-In)", variable=self.qr_mode_var, 
                       value="entry").pack(side='left', padx=20)
        ttk.Radiobutton(mode_frame, text="Exit (Check-Out)", variable=self.qr_mode_var, 
                       value="exit").pack(side='left', padx=20)
        
        # QR Scan Options
        scan_frame = ttk.LabelFrame(tab, text="Scan QR Code", padding="15")
        scan_frame.pack(fill='x', padx=10, pady=10)
        
        btn_grid = ttk.Frame(scan_frame)
        btn_grid.pack()
        
        ttk.Button(btn_grid, text="📷 Scan with Webcam", command=self.scan_qr_webcam,
                  width=20).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(btn_grid, text="📁 Upload QR Image", command=self.scan_qr_file,
                  width=20).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(btn_grid, text="⌨️ Manual Entry", command=self.manual_qr_entry,
                  width=20).grid(row=0, column=2, padx=10, pady=5)
        
        # Booking Details Display
        details_frame = ttk.LabelFrame(tab, text="Booking Details", padding="15")
        details_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.qr_details_text = tk.Text(details_frame, height=12, width=80, font=('Courier', 10))
        self.qr_details_text.pack(fill='both', expand=True)
        self.qr_details_text.config(state='disabled')
        
        # Action Buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        self.qr_process_btn = ttk.Button(action_frame, text="✓ Process Entry/Exit", 
                                         command=self.process_qr_booking, state='disabled')
        self.qr_process_btn.pack(side='left', padx=10)
        
        ttk.Button(action_frame, text="🔄 Clear", command=self.clear_qr_details).pack(side='left', padx=10)
        ttk.Button(action_frame, text="📋 Pending Check-ins", 
                  command=self.show_pending_checkins).pack(side='left', padx=10)
        
        # Pending bookings monitor
        monitor_frame = ttk.LabelFrame(tab, text="Pending Check-ins (30-min window)", padding="10")
        monitor_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Ticket', 'User', 'Vehicle', 'Slot', 'Deadline', 'Time Left')
        self.pending_tree = ttk.Treeview(monitor_frame, columns=columns, 
                                        show='tree headings', height=6)
        
        for col in columns:
            self.pending_tree.heading(col, text=col)
            self.pending_tree.column(col, width=120)
        
        self.pending_tree.pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(monitor_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="🔄 Refresh Pending", 
                  command=self.refresh_pending_checkins).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="⏰ Expire Old Bookings", 
                  command=self.manual_expire_bookings).pack(side='left', padx=5)
        
        # Initialize
        self.current_qr_booking = None
        self.refresh_pending_checkins()
    
    def scan_qr_webcam(self):
        """Scan QR code using webcam"""
        try:
            qr_handler = QRHandler()
            qr_data = qr_handler.scan_qr_from_webcam()
            
            if qr_data:
                self.process_scanned_qr(json.dumps(qr_data))
            else:
                messagebox.showwarning("Scan Failed", "No QR code detected. Please try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Webcam scan failed: {str(e)}")
    
    def scan_qr_file(self):
        """Scan QR code from uploaded image file"""
        file_path = filedialog.askopenfilename(
            title="Select QR Code Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                qr_handler = QRHandler()
                qr_data = qr_handler.scan_qr_from_image(file_path)
                
                if qr_data:
                    self.process_scanned_qr(json.dumps(qr_data))
                else:
                    messagebox.showwarning("Scan Failed", "No QR code found in image.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to scan QR: {str(e)}")
    
    def manual_qr_entry(self):
        """Manual QR data entry dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual QR Entry")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter Ticket Number:", font=('Arial', 12)).pack(pady=20)
        
        ticket_var = tk.StringVar()
        ticket_entry = ttk.Entry(dialog, textvariable=ticket_var, width=30, font=('Arial', 11))
        ticket_entry.pack(pady=10)
        ticket_entry.focus()
        
        def submit():
            ticket = ticket_var.get().strip()
            if ticket:
                # Look up booking by ticket number
                db = get_db_manager()
                booking = db.fetch_one("""
                    SELECT b.*, u.name, u.email, v.vehicle_number, ps.slot_number, ps.floor, ps.section
                    FROM bookings b
                    JOIN users u ON b.user_id = u.user_id
                    JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                    JOIN parking_slots ps ON b.slot_id = ps.slot_id
                    WHERE b.ticket_number = ?
                """, (ticket,))
                
                if booking:
                    # Create QR data manually
                    qr_data = json.dumps({
                        "type": "parking_booking",
                        "booking_id": booking['booking_id'],
                        "ticket": booking['ticket_number'],
                        "user_id": booking['user_id'],
                        "vehicle": booking['vehicle_number'],
                        "slot": booking['slot_number']
                    })
                    dialog.destroy()
                    self.process_scanned_qr(qr_data)
                else:
                    messagebox.showerror("Not Found", f"No booking found with ticket: {ticket}")
            else:
                messagebox.showwarning("Invalid Input", "Please enter a ticket number")
        
        ttk.Button(dialog, text="Submit", command=submit).pack(pady=10)
        ticket_entry.bind('<Return>', lambda e: submit())
    
    def process_scanned_qr(self, qr_data):
        """Process scanned QR code and display booking details"""
        try:
            # Parse QR data
            qr_dict = json.loads(qr_data)
            
            # Validate QR format
            if qr_dict.get('type') != 'parking_booking':
                messagebox.showerror("Invalid QR", "This is not a valid parking booking QR code")
                return
            
            booking_id = qr_dict.get('booking_id')
            ticket_number = qr_dict.get('ticket')
            
            # Fetch booking details - verify both booking_id AND ticket number match
            db = get_db_manager()
            booking = db.fetch_one("""
                SELECT b.*, u.name, u.email, u.phone, v.vehicle_number, v.vehicle_type,
                       ps.slot_number, ps.floor, ps.section
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                JOIN parking_slots ps ON b.slot_id = ps.slot_id
                WHERE b.booking_id = ? AND b.ticket_number = ?
            """, (booking_id, ticket_number))
            
            if not booking:
                # Try searching by ticket number only in case booking_id is wrong
                booking = db.fetch_one("""
                    SELECT b.*, u.name, u.email, u.phone, v.vehicle_number, v.vehicle_type,
                           ps.slot_number, ps.floor, ps.section
                    FROM bookings b
                    JOIN users u ON b.user_id = u.user_id
                    JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                    JOIN parking_slots ps ON b.slot_id = ps.slot_id
                    WHERE b.ticket_number = ?
                """, (ticket_number,))
                
                if not booking:
                    messagebox.showerror("Not Found", 
                                       f"Booking not found in database.\n\n"
                                       f"QR Code Data:\n"
                                       f"  Ticket: {ticket_number}\n"
                                       f"  Booking ID: {booking_id}\n"
                                       f"  Vehicle: {qr_dict.get('vehicle')}\n"
                                       f"  Slot: {qr_dict.get('slot')}\n\n"
                                       f"This QR code may be invalid or the booking was deleted.\n"
                                       f"Note: Booking ID {booking_id} was removed from the database.")
                    return
            
            # Convert Row object to dictionary
            booking_dict = dict(booking)
            
            self.current_qr_booking = booking_dict
            self.display_booking_details(booking_dict)
            self.qr_process_btn.config(state='normal')
            
        except json.JSONDecodeError:
            messagebox.showerror("Invalid QR", "QR code data is corrupted")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process QR: {str(e)}")
    
    def display_booking_details(self, booking):
        """Display booking details in the text widget"""
        self.qr_details_text.config(state='normal')
        self.qr_details_text.delete('1.0', tk.END)
        
        mode = self.qr_mode_var.get()
        status = booking.get('booking_status', 'unknown')
        
        details = f"""
{'='*70}
                BOOKING VERIFICATION
{'='*70}

Ticket Number:    {booking.get('ticket_number', 'N/A')}
Booking Status:   {status.upper()}

Customer Details:
  Name:           {booking.get('name', 'N/A')}
  Email:          {booking.get('email', 'N/A')}
  Phone:          {booking.get('phone', 'N/A')}

Vehicle Details:
  Number:         {booking.get('vehicle_number', 'N/A')}
  Type:           {booking.get('vehicle_type', 'N/A')}

Parking Details:
  Slot:           {booking.get('slot_number', 'N/A')}
  Location:       Floor {booking.get('floor', 'N/A')}, Section {booking.get('section', 'N/A')}
  Amount Paid:    ₹{booking.get('total_amount') or booking.get('base_amount') or 0.0}

Timing:
  Booked At:      {booking.get('booking_time') or booking.get('entry_time', 'N/A')}
"""
        
        if booking.get('checkin_time'):
            details += f"  Checked In:        {booking['checkin_time']}\n"
        
        if booking.get('checkout_time'):
            details += f"  Checked Out:       {booking['checkout_time']}\n"
        
        details += f"\n{'='*70}\n"
        
        # Validation for current mode
        if mode == 'entry':
            if status == 'pending':
                # Check if expired
                if booking.get('checkin_deadline'):
                    deadline = datetime.fromisoformat(booking['checkin_deadline']) if isinstance(booking['checkin_deadline'], str) else booking['checkin_deadline']
                    # Convert UTC to local time if timezone is present
                    if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                        local_deadline = deadline.astimezone().replace(tzinfo=None)
                    else:
                        local_deadline = deadline
                    if datetime.now() > local_deadline:
                        details += "\n⚠️ BOOKING EXPIRED: Check-in deadline passed!\n"
                        details += "   This booking should be cancelled automatically.\n"
                    else:
                        details += "\n✅ READY FOR CHECK-IN\n"
                        time_left = (local_deadline - datetime.now()).total_seconds() / 60
                        details += f"   Time remaining: {int(time_left)} minutes\n"
                else:
                    details += "\n✅ READY FOR CHECK-IN\n"
            elif status == 'active':
                details += "\n⚠️ WARNING: Customer already checked in!\n"
            elif status == 'cancelled':
                details += "\n❌ BOOKING CANCELLED\n"
            elif status == 'completed':
                details += "\n❌ BOOKING COMPLETED: Cannot reuse this booking.\n"
        
        elif mode == 'exit':
            if status == 'active':
                details += "\n✅ READY FOR CHECK-OUT\n"
                if booking.get('checkin_time'):
                    checkin = datetime.fromisoformat(booking['checkin_time'])
                    duration = (datetime.now() - checkin).total_seconds() / 3600
                    details += f"   Parking Duration: {duration:.2f} hours\n"
            elif status == 'pending':
                details += "\n⚠️ WARNING: Customer not yet checked in!\n"
            elif status == 'completed':
                details += "\n❌ BOOKING ALREADY COMPLETED\n"
        
        details += f"{'='*70}\n"
        
        self.qr_details_text.insert('1.0', details)
        self.qr_details_text.config(state='disabled')
    
    def process_qr_booking(self):
        """Process the booking (check-in or check-out)"""
        if not self.current_qr_booking:
            messagebox.showwarning("No Booking", "Please scan a QR code first")
            return
        
        mode = self.qr_mode_var.get()
        booking = self.current_qr_booking
        status = booking['booking_status']
        
        if mode == 'entry':
            self.process_checkin(booking)
        elif mode == 'exit':
            self.process_checkout(booking)
    
    def process_checkin(self, booking):
        """Process customer check-in"""
        if booking['booking_status'] != 'pending':
            messagebox.showerror("Invalid Status", 
                               f"Cannot check in. Booking status is: {booking['booking_status']}")
            return
        
        # Check if expired
        if booking.get('checkin_deadline'):
            deadline = datetime.fromisoformat(booking['checkin_deadline']) if isinstance(booking['checkin_deadline'], str) else booking['checkin_deadline']
            # Convert UTC to local time if timezone is present
            if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                local_deadline = deadline.astimezone().replace(tzinfo=None)
            else:
                local_deadline = deadline
            if datetime.now() > local_deadline:
                result = messagebox.askyesno(
                    "Booking Expired",
                    "This booking has passed its check-in deadline.\n\n"
                    "Mark as cancelled and free the parking slot?"
                )
                if result:
                    db = get_db_manager()
                    db.execute_query("""
                        UPDATE bookings 
                        SET booking_status = 'cancelled', 
                            notes = 'Expired - deadline passed',
                            forfeited = 1
                        WHERE booking_id = ?
                    """, (booking['booking_id'],))
                    
                    db.execute_query("""
                        UPDATE parking_slots 
                        SET status = 'available'
                        WHERE slot_id = ?
                    """, (booking['slot_id'],))
                    
                    messagebox.showinfo("Cancelled", "Booking marked as cancelled. Slot freed.")
                    self.clear_qr_details()
                    self.refresh_pending_checkins()
                    self.refresh_dashboard()
                return
        
        # Confirm check-in
        if messagebox.askyesno("Confirm Check-In", 
                              f"Check in customer:\n\n"
                              f"Ticket: {booking['ticket_number']}\n"
                              f"Name: {booking['name']}\n"
                              f"Vehicle: {booking['vehicle_number']}\n"
                              f"Slot: {booking['slot_number']}\n\n"
                              f"Proceed with check-in?"):
            
            try:
                db = get_db_manager()
                now = datetime.now().isoformat()
                
                # Update booking
                db.execute_query("""
                    UPDATE bookings 
                    SET booking_status = 'active', checkin_time = ?
                    WHERE booking_id = ?
                """, (now, booking['booking_id']))
                
                # Update slot
                db.execute_query("""
                    UPDATE parking_slots 
                    SET status = 'occupied'
                    WHERE slot_id = ?
                """, (booking['slot_id'],))
                
                messagebox.showinfo("Success", 
                                  f"✅ Check-in successful!\n\n"
                                  f"Ticket: {booking['ticket_number']}\n"
                                  f"Slot: {booking['slot_number']}\n"
                                  f"Time: {now}")
                
                self.clear_qr_details()
                self.refresh_pending_checkins()
                self.refresh_dashboard()
                
            except Exception as e:
                messagebox.showerror("Error", f"Check-in failed: {str(e)}")
    
    def process_checkout(self, booking):
        """Process customer check-out"""
        if booking['booking_status'] != 'active':
            messagebox.showerror("Invalid Status", 
                               f"Cannot check out. Booking status is: {booking['booking_status']}")
            return
        
        # Calculate charges
        checkin = datetime.fromisoformat(booking['checkin_time'])
        now = datetime.now()
        duration_hours = (now - checkin).total_seconds() / 3600
        
        # Confirm check-out
        if messagebox.askyesno("Confirm Check-Out", 
                              f"Check out customer:\n\n"
                              f"Ticket: {booking['ticket_number']}\n"
                              f"Name: {booking['name']}\n"
                              f"Vehicle: {booking['vehicle_number']}\n"
                              f"Slot: {booking['slot_number']}\n\n"
                              f"Duration: {duration_hours:.2f} hours\n"
                              f"Amount Paid: ₹{booking.get('total_amount') or booking.get('base_amount', 0)}\n\n"
                              f"Proceed with check-out?"):
            
            try:
                db = get_db_manager()
                checkout_time = now.isoformat()
                
                # Update booking
                db.execute_query("""
                    UPDATE bookings 
                    SET booking_status = 'completed', checkout_time = ?
                    WHERE booking_id = ?
                """, (checkout_time, booking['booking_id']))
                
                # Free slot
                db.execute_query("""
                    UPDATE parking_slots 
                    SET status = 'available'
                    WHERE slot_id = ?
                """, (booking['slot_id'],))
                
                messagebox.showinfo("Success", 
                                  f"✅ Check-out successful!\n\n"
                                  f"Ticket: {booking['ticket_number']}\n"
                                  f"Duration: {duration_hours:.2f} hours\n"
                                  f"Thank you for using Smart Parking!")
                
                self.clear_qr_details()
                self.refresh_dashboard()
                
            except Exception as e:
                messagebox.showerror("Error", f"Check-out failed: {str(e)}")
    
    def clear_qr_details(self):
        """Clear QR details display"""
        self.qr_details_text.config(state='normal')
        self.qr_details_text.delete('1.0', tk.END)
        self.qr_details_text.config(state='disabled')
        self.current_qr_booking = None
        self.qr_process_btn.config(state='disabled')
    
    def refresh_pending_checkins(self):
        """Refresh pending check-ins list and auto-expire old bookings"""
        # First, expire old pending bookings
        self.auto_expire_bookings()
        
        self.pending_tree.delete(*self.pending_tree.get_children())
        
        db = get_db_manager()
        pending = db.fetch_all("""
            SELECT b.ticket_number, u.name, v.vehicle_number, 
                   ps.slot_number, b.entry_time, b.checkin_deadline
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
            WHERE b.booking_status = 'pending'
            ORDER BY b.entry_time DESC
        """)
        
        now = datetime.now()
        for booking in pending:
            deadline = booking.get('checkin_deadline')
            if deadline:
                deadline_dt = datetime.fromisoformat(deadline) if isinstance(deadline, str) else deadline
                # Convert UTC to local time if timezone is present
                if hasattr(deadline_dt, 'tzinfo') and deadline_dt.tzinfo is not None:
                    local_deadline = deadline_dt.astimezone().replace(tzinfo=None)
                else:
                    local_deadline = deadline_dt
                time_left = (local_deadline - now).total_seconds() / 60
                time_left_str = f"{int(time_left)} min" if time_left > 0 else "EXPIRED"
            else:
                deadline = "N/A"
                time_left_str = "No deadline"
            
            self.pending_tree.insert('', 'end', values=(
                booking['ticket_number'],
                booking['name'],
                booking['vehicle_number'],
                booking['slot_number'],
                deadline,
                time_left_str
            ))
    
    def auto_expire_bookings(self):
        """Automatically expire pending bookings past their deadline"""
        db = get_db_manager()
        now = datetime.now()
        
        # Find expired bookings - fetch all pending and check in Python to handle timezone comparison
        all_pending = db.fetch_all("""
            SELECT b.booking_id, b.ticket_number, b.slot_id, b.checkin_deadline,
                   ps.slot_number
            FROM bookings b
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
            WHERE b.booking_status = 'pending' 
            AND b.checkin_deadline IS NOT NULL
        """)
        
        # Filter expired bookings in Python with proper timezone handling
        expired = []
        for booking in all_pending:
            deadline_str = booking['checkin_deadline']
            if deadline_str:
                deadline = datetime.fromisoformat(deadline_str) if isinstance(deadline_str, str) else deadline_str
                # Convert UTC to local time if timezone is present
                if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                    local_deadline = deadline.astimezone().replace(tzinfo=None)
                else:
                    local_deadline = deadline
                if now > local_deadline:
                    expired.append(booking)
        
        if expired:
            for booking in expired:
                try:
                    # Mark booking as cancelled
                    db.execute_query("""
                        UPDATE bookings 
                        SET booking_status = 'cancelled', 
                            notes = 'Auto-cancelled: Check-in deadline expired',
                            forfeited = 1
                        WHERE booking_id = ?
                    """, (booking['booking_id'],))
                    
                    # Free up the parking slot
                    db.execute_query("""
                        UPDATE parking_slots 
                        SET status = 'available'
                        WHERE slot_id = ?
                    """, (booking['slot_id'],))
                    
                    print(f"✓ Auto-expired booking: {booking['ticket_number']} - Slot {booking['slot_number']} freed")
                except Exception as e:
                    print(f"✗ Error expiring booking {booking['ticket_number']}: {e}")
            
            print(f"\n✓ Auto-expired {len(expired)} booking(s)")
            self.refresh_dashboard()  # Update dashboard stats
    
    def manual_expire_bookings(self):
        """Manually trigger expiration of old bookings"""
        db = get_db_manager()
        now = datetime.now()
        
        # Fetch all pending bookings with deadlines
        all_pending = db.fetch_all("""
            SELECT booking_id, checkin_deadline FROM bookings 
            WHERE booking_status = 'pending' 
            AND checkin_deadline IS NOT NULL
        """)
        
        # Count expired in Python with proper timezone handling
        count = 0
        for booking in all_pending:
            deadline_str = booking['checkin_deadline']
            if deadline_str:
                deadline = datetime.fromisoformat(deadline_str) if isinstance(deadline_str, str) else deadline_str
                # Convert UTC to local time if timezone is present
                if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                    local_deadline = deadline.astimezone().replace(tzinfo=None)
                else:
                    local_deadline = deadline
                if now > local_deadline:
                    count += 1
        
        if count == 0:
            messagebox.showinfo("No Expired Bookings", "No expired bookings found.")
            return
        
        result = messagebox.askyesno(
            "Expire Bookings",
            f"Found {count} expired booking(s).\n\n"
            "These bookings will be:\n"
            "• Marked as CANCELLED\n"
            "• Slots freed and made available\n"
            "• Marked as forfeited (payment not refunded)\n\n"
            "Continue?"
        )
        
        if result:
            self.auto_expire_bookings()
            self.refresh_pending_checkins()
            messagebox.showinfo("Success", f"✓ Expired {count} booking(s) and freed parking slots")
    
    def show_pending_checkins(self):
        """Show detailed pending check-ins window"""
        self.refresh_pending_checkins()
        messagebox.showinfo("Pending Check-ins", 
                          f"Total pending check-ins: {len(self.pending_tree.get_children())}\n\n"
                          "Check the table below for details.")
    
    def create_analytics_tab(self):
        """Analytics tab for admin"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📈 Analytics")
        
        revenue_frame = ttk.LabelFrame(tab, text="Revenue Statistics", padding="15")
        revenue_frame.pack(fill='x', padx=10, pady=10)
        
        self.revenue_labels = {}
        
        charts_frame = ttk.LabelFrame(tab, text="Generate Reports", padding="15")
        charts_frame.pack(fill='x', padx=10, pady=10)
        
        btn_grid = ttk.Frame(charts_frame)
        btn_grid.pack()
        
        ttk.Button(btn_grid, text="Revenue Chart", command=self.generate_revenue_chart).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_grid, text="Occupancy Chart", command=self.generate_occupancy_chart).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_grid, text="Peak Hours Chart", command=self.generate_peak_hours_chart).grid(
            row=0, column=2, padx=5, pady=5)
        ttk.Button(btn_grid, text="Export Bookings CSV", command=self.export_bookings).grid(
            row=0, column=3, padx=5, pady=5)
    
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        stats = self.parking_manager.get_slot_statistics()
        
        if hasattr(self, 'stats_labels') and self.stats_labels:
            self.stats_labels['total'].config(text=str(stats.get('total', 0)))
            self.stats_labels['available'].config(text=str(stats.get('available', 0)), fg='#27ae60')
            self.stats_labels['occupied'].config(text=str(stats.get('occupied', 0)), fg='#e74c3c')
            
            # Get active bookings count
            active_bookings = len(self.booking_manager.get_my_active_bookings())
            self.stats_labels['active_bookings'].config(text=str(active_bookings))
            
            # Get total revenue from database
            revenue = self.booking_manager.db.fetch_one(
                "SELECT COALESCE(SUM(amount), 0) as total FROM payments"
            )
            total_revenue = revenue['total'] if revenue else 0
            self.stats_labels['total_revenue'].config(text=f"₹{total_revenue:.2f}", fg='#27ae60')
        
        self.user_data = self.user_manager.get_user_info()
    
    def search_slots(self):
        """Search available slots"""
        vehicle_type = self.vehicle_type_var.get()
        floor = self.floor_var.get()
        floor_num = int(floor) if floor != "Any" else None
        
        slots = self.parking_manager.get_available_slots(vehicle_type, floor_num)
        
        for item in self.slots_tree.get_children():
            self.slots_tree.delete(item)
        
        for slot in slots:
            self.slots_tree.insert('', 'end', iid=slot['slot_id'], values=(
                slot['slot_number'],
                slot['floor'],
                slot['section'],
                slot['slot_type'],
                f"₹{slot['base_price_per_hour']:.2f}"
            ))
        
        filter_text = f"Floor {floor}" if floor != "Any" else "All floors"
        messagebox.showinfo("Search Results", f"Found {len(slots)} available {vehicle_type} slots\n{filter_text}")
    
    def book_slot(self):
        """Book selected slot"""
        selection = self.slots_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a slot")
            return
        
        slot_id = int(selection[0])
        
        vehicles = self.user_manager.get_my_vehicles()
        if not vehicles:
            messagebox.showerror("Error", "Please add a vehicle first")
            self.notebook.select(3)
            return
        
        if len(vehicles) == 1:
            vehicle_id = vehicles[0]['vehicle_id']
        else:
            vehicle_id = self.select_vehicle_dialog(vehicles, slot_id)
            if not vehicle_id:
                return
        
        success, ticket, message = self.booking_manager.create_booking(vehicle_id, slot_id)
        
        if success:
            messagebox.showinfo("Success", f"Booking successful!\n{message}")
            self.search_slots()  # Refresh slots
            self.load_my_bookings()
        else:
            messagebox.showerror("Booking Failed", message)
    
    def select_vehicle_dialog(self, vehicles, slot_id):
        """Show dialog to select vehicle for booking"""
        slot = self.parking_manager.get_slot_by_id(slot_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Vehicle")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        selected_vehicle = [None]
        
        ttk.Label(dialog, text=f"Select vehicle for Slot {slot['slot_number']}", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(dialog, text=f"Slot type: {slot['vehicle_type']}", 
                 font=('Arial', 10)).pack(pady=5)
        
        frame = ttk.Frame(dialog)
        frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ('Number', 'Type', 'Brand', 'Model')
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)
        
        compatible_vehicles = [v for v in vehicles if v['vehicle_type'] == slot['vehicle_type']]
        
        if not compatible_vehicles:
            ttk.Label(dialog, text=f"No {slot['vehicle_type']} vehicles found!", 
                     foreground='red').pack(pady=10)
            ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=10)
            dialog.wait_window()
            return None
        
        for vehicle in compatible_vehicles:
            tree.insert('', 'end', iid=vehicle['vehicle_id'], values=(
                vehicle['vehicle_number'],
                vehicle['vehicle_type'],
                vehicle.get('brand', 'N/A'),
                vehicle.get('model', 'N/A')
            ))
        
        def on_select():
            selection = tree.selection()
            if selection:
                selected_vehicle[0] = int(selection[0])
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Please select a vehicle", parent=dialog)
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Book with Selected Vehicle", command=on_select).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        dialog.wait_window()
        return selected_vehicle[0]
    
    def load_my_bookings(self):
        """Load user's active bookings"""
        bookings = self.booking_manager.get_my_active_bookings()
        
        for item in self.active_bookings_tree.get_children():
            self.active_bookings_tree.delete(item)
        
        for booking in bookings:
            self.active_bookings_tree.insert('', 'end', iid=booking['booking_id'], values=(
                booking['ticket_number'],
                booking['vehicle_number'],
                booking['slot_number'],
                booking['entry_time'],
                booking['booking_status']
            ))
    
    def exit_parking(self):
        """Exit from parking"""
        selection = self.active_bookings_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a booking")
            return
        
        booking_id = int(selection[0])
        booking = self.booking_manager.db.fetch_one(
            "SELECT ticket_number FROM bookings WHERE booking_id = ?", (booking_id,))
        
        if not booking:
            return
        
        success, bill, message = self.booking_manager.exit_parking(booking['ticket_number'])
        
        if success:
            self.show_receipt_dialog(bill)
            self.load_my_bookings()
            self.refresh_dashboard()
        else:
            messagebox.showerror("Error", message)
    
    def show_receipt_dialog(self, bill):
        """Show receipt after automatic payment"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Parking Receipt")
        dialog.geometry("450x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        success_label = tk.Label(frame, text="✅ Payment Successful!", 
                                font=('Arial', 18, 'bold'), fg='#27ae60')
        success_label.pack(pady=10)
        
        ttk.Label(frame, text="Amount deducted from wallet", 
                 font=('Arial', 10), foreground='gray').pack(pady=5)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(frame, text="PARKING RECEIPT", font=('Arial', 14, 'bold')).pack(pady=10)
        
        details = [
            ('Ticket Number:', bill['ticket_number']),
            ('Transaction ID:', bill['transaction_id']),
            ('', ''),
            ('Vehicle:', bill['vehicle_number']),
            ('Slot:', bill['slot_number']),
            ('Entry Time:', bill['entry_time']),
            ('Exit Time:', bill['exit_time']),
            ('Duration:', f"{bill['duration_hours']:.2f} hours"),
            ('', ''),
            ('Base Charges:', f"₹{bill['base_amount']:.2f}"),
            ('Surcharge:', f"₹{bill['surge_amount']:.2f}"),
        ]
        
        details_frame = ttk.Frame(frame)
        details_frame.pack(fill='x', pady=10)
        
        for label, value in details:
            if label == '':
                ttk.Separator(details_frame, orient='horizontal').pack(fill='x', pady=5)
            else:
                row = ttk.Frame(details_frame)
                row.pack(fill='x', pady=3)
                ttk.Label(row, text=label, font=('Arial', 10)).pack(side='left')
                ttk.Label(row, text=value, font=('Arial', 10)).pack(side='right')
        
        total_frame = tk.Frame(frame, bg='#2c3e50', relief='raised', bd=2)
        total_frame.pack(fill='x', pady=15)
        tk.Label(total_frame, text="TOTAL PAID", font=('Arial', 11, 'bold'), 
                bg='#2c3e50', fg='white').pack(pady=5)
        tk.Label(total_frame, text=f"₹{bill['total_amount']:.2f}", 
                font=('Arial', 20, 'bold'), bg='#2c3e50', fg='#27ae60').pack(pady=5)
        
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill='x', pady=10)
        
        points_frame = tk.Frame(info_frame, bg='#f39c12', relief='raised', bd=2)
        points_frame.pack(side='left', padx=5, expand=True, fill='x')
        tk.Label(points_frame, text=f"🎁 +{bill['loyalty_points_earned']} Points", 
                font=('Arial', 10, 'bold'), bg='#f39c12', fg='white').pack(pady=8)
        
        balance_frame = tk.Frame(info_frame, bg='#27ae60', relief='raised', bd=2)
        balance_frame.pack(side='right', padx=5, expand=True, fill='x')
        tk.Label(balance_frame, text=f"💰 Balance: ₹{bill['wallet_balance']:.2f}", 
                font=('Arial', 10, 'bold'), bg='#27ae60', fg='white').pack(pady=8)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=15)
        
        def save_pdf():
            from utils.pdf_generator import PDFGenerator
            pdf_gen = PDFGenerator()
            pdf_path = pdf_gen.generate_parking_receipt(bill)
            messagebox.showinfo("Receipt Saved", f"Receipt saved at:\n{pdf_path}")
        
        ttk.Button(btn_frame, text="💾 Save PDF", command=save_pdf).pack(side='left', padx=5, expand=True, fill='x')
        ttk.Button(btn_frame, text="✅ Done", command=dialog.destroy).pack(side='right', padx=5, expand=True, fill='x')
    
    def show_payment_dialog(self, booking_id, bill):
        """Show payment dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Payment")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="PARKING BILL", font=('Arial', 16, 'bold')).pack(pady=10)
        
        details = [
            ('Ticket:', bill['ticket_number']),
            ('Vehicle:', bill['vehicle_number']),
            ('Slot:', bill['slot_number']),
            ('Duration:', f"{bill['duration_hours']:.2f} hours"),
            ('Base Amount:', f"₹{bill['base_amount']:.2f}"),
            ('Surcharge:', f"₹{bill['surge_amount']:.2f}"),
            ('', ''),
            ('TOTAL:', f"₹{bill['total_amount']:.2f}")
        ]
        
        for label, value in details:
            row = ttk.Frame(frame)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label, font=('Arial', 11)).pack(side='left')
            ttk.Label(row, text=value, font=('Arial', 11, 'bold')).pack(side='right')
        
        ttk.Label(frame, text="Payment Method:", font=('Arial', 12)).pack(pady=10)
        payment_method = tk.StringVar(value="wallet")
        ttk.Radiobutton(frame, text="Wallet", variable=payment_method, value="wallet").pack()
        ttk.Radiobutton(frame, text="UPI", variable=payment_method, value="upi").pack()
        ttk.Radiobutton(frame, text="Card", variable=payment_method, value="card").pack()
        ttk.Radiobutton(frame, text="Cash", variable=payment_method, value="cash").pack()
        
        def make_payment():
            method = payment_method.get()
            success, txn_id, msg = self.payment_manager.process_payment(
                booking_id, bill['total_amount'], method)
            
            if success:
                messagebox.showinfo("Success", msg)
                
                pdf_gen = PDFGenerator()
                pdf_path = pdf_gen.generate_parking_receipt(bill)
                
                messagebox.showinfo("Receipt Generated", f"Receipt saved at:\n{pdf_path}")
                dialog.destroy()
                self.load_my_bookings()
                self.refresh_dashboard()
            else:
                messagebox.showerror("Payment Failed", msg)
        
        ttk.Button(frame, text="Pay Now", command=make_payment).pack(pady=20)
    
    def cancel_booking(self):
        """Cancel selected booking"""
        selection = self.active_bookings_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a booking")
            return
        
        booking_id = int(selection[0])
        booking = self.booking_manager.db.fetch_one(
            "SELECT ticket_number FROM bookings WHERE booking_id = ?", (booking_id,))
        
        if messagebox.askyesno("Confirm", "Cancel this booking?"):
            success, message = self.booking_manager.cancel_booking(booking['ticket_number'])
            if success:
                messagebox.showinfo("Success", message)
                self.load_my_bookings()
            else:
                messagebox.showerror("Error", message)
    
    def generate_ticket(self):
        """Generate and display QR code ticket"""
        selection = self.active_bookings_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a booking")
            return
        
        booking_id = int(selection[0])
        booking = self.booking_manager.get_booking_details(
            self.booking_manager.db.fetch_one(
                "SELECT ticket_number FROM bookings WHERE booking_id = ?", 
                (booking_id,))['ticket_number'])
        
        if booking:
            from utils.qr_generator import QRCodeGenerator
            from PIL import Image, ImageTk
            
            qr_gen = QRCodeGenerator()
            qr_path = qr_gen.generate_ticket_qr({
                'ticket_number': booking['ticket_number'],
                'vehicle_number': booking['vehicle_number'],
                'slot_number': booking['slot_number'],
                'entry_time': booking['entry_time']
            })
            
            qr_window = tk.Toplevel(self.root)
            qr_window.title(f"Ticket QR Code - {booking['ticket_number']}")
            qr_window.geometry("400x500")
            
            ttk.Label(qr_window, text="Parking Ticket", font=('Arial', 16, 'bold')).pack(pady=10)
            
            details_frame = ttk.Frame(qr_window)
            details_frame.pack(pady=10)
            ttk.Label(details_frame, text=f"Ticket: {booking['ticket_number']}", font=('Arial', 10)).pack()
            ttk.Label(details_frame, text=f"Vehicle: {booking['vehicle_number']}", font=('Arial', 10)).pack()
            ttk.Label(details_frame, text=f"Slot: {booking['slot_number']}", font=('Arial', 10)).pack()
            ttk.Label(details_frame, text=f"Entry: {booking['entry_time']}", font=('Arial', 10)).pack()
            
            img = Image.open(qr_path)
            img = img.convert('RGB')
            img = img.resize((300, 300), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            qr_label = tk.Label(qr_window, image=photo, bg='white')
            qr_label.photo = photo  
            qr_label.pack(pady=10)
            
            ttk.Label(qr_window, text=f"Saved at: {qr_path}", font=('Arial', 8), foreground='gray').pack(pady=5)
            ttk.Button(qr_window, text="Close", command=qr_window.destroy).pack(pady=10)
    
    def load_vehicles(self):
        """Load user vehicles"""
        vehicles = self.user_manager.get_my_vehicles()
        
        for item in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(item)
        
        for vehicle in vehicles:
            self.vehicles_tree.insert('', 'end', values=(
                vehicle['vehicle_id'],
                vehicle['vehicle_number'],
                vehicle['vehicle_type'],
                vehicle.get('brand', 'N/A'),
                vehicle.get('model', 'N/A')
            ))
    
    def add_vehicle(self):
        """Add new vehicle"""
        number = self.vehicle_entry.get().strip()
        v_type = self.new_vehicle_type_var.get()
        brand = self.vehicle_brand_var.get().strip()
        model = self.vehicle_model_var.get().strip()
        color = self.vehicle_color_var.get().strip()
        
        if not number:
            messagebox.showerror("Error", "Please enter a vehicle number (minimum 6 characters)\nExample: ABC1234 or MH12AB1234")
            return
        
        if not brand:
            brand = "Unknown"
        if not model:
            model = "Unknown"
        if not color:
            color = "Unknown"
        
        success, message = self.user_manager.add_vehicle(number, v_type, brand, model, color)
        
        if success:
            messagebox.showinfo("Success", message)
            self.vehicle_entry.delete(0, tk.END)
            self.vehicle_brand_var.set("")
            self.vehicle_model_var.set("")
            self.vehicle_color_var.set("")
            self.load_vehicles()
        else:
            messagebox.showerror("Error", message)
    

    
    def delete_vehicle(self):
        """Delete selected vehicle"""
        selection = self.vehicles_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a vehicle to delete")
            return
        
        values = self.vehicles_tree.item(selection[0])['values']
        vehicle_id = values[0]
        vehicle_number = values[1]
        
        if messagebox.askyesno("Confirm Deletion", 
                              f"Are you sure you want to delete vehicle {vehicle_number}?\n\n"
                              "This action cannot be undone."):
            success, message = self.user_manager.delete_vehicle(vehicle_id)
            
            if success:
                messagebox.showinfo("Success", message)
                self.load_vehicles()
            else:
                messagebox.showerror("Error", message)
    
    def add_to_wallet(self):
        """Add money to wallet"""
        try:
            amount_str = self.recharge_entry.get().strip()
            
            if not amount_str:
                messagebox.showerror("Error", "Please enter an amount")
                return
            
            amount = float(amount_str)
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0")
                return
            
            success, message = self.user_manager.add_money_to_wallet(amount)
            
            if success:
                messagebox.showinfo("Success", message)
                self.user_data = self.user_manager.get_user_info()
                self.balance_label.config(text=f"₹{self.user_data['wallet_balance']:.2f}")
                self.recharge_entry.delete(0, tk.END)
                self.recharge_amount_var.set("")
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number (e.g., 100 or 500.50)")
    
    def initialize_parking(self):
        """Initialize parking structure"""
        if messagebox.askyesno("Confirm", "Initialize parking structure with default configuration?"):
            success, message = self.parking_manager.initialize_parking_structure()
            messagebox.showinfo("Result", message)
    
    def load_parking_slots(self):
        """Load parking slots with filters"""
        for item in self.slots_tree.get_children():
            self.slots_tree.delete(item)
        
        floor_filter = self.slot_floor_filter.get()
        type_filter = self.slot_type_filter.get()
        status_filter = self.slot_status_filter.get()
        
        db = get_db_manager()
        query = "SELECT * FROM parking_slots WHERE 1=1"
        params = []
        
        if floor_filter != 'All':
            query += " AND floor = ?"
            params.append(int(floor_filter))
        if type_filter != 'All':
            query += " AND vehicle_type = ?"
            params.append(type_filter)
        if status_filter != 'All':
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY floor, section, slot_number"
        slots = db.fetch_all(query, params)
        
        total = 0
        available = 0
        occupied = 0
        
        for slot in slots:
            self.slots_tree.insert('', 'end', values=(
                slot['slot_id'],
                slot['slot_number'],
                slot['floor'],
                slot['section'],
                slot['slot_type'],
                slot['vehicle_type'],
                f"₹{slot['base_price_per_hour']}",
                slot['status']
            ))
            total += 1
            if slot['status'] == 'available':
                available += 1
            elif slot['status'] == 'occupied':
                occupied += 1
        
        self.total_slots_label.config(text=f"Total: {total}")
        self.available_slots_label.config(text=f"Available: {available}")
        self.occupied_slots_label.config(text=f"Occupied: {occupied}")
    
    def add_parking_slot(self):
        """Add new parking slot"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Parking Slot")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Slot Number:").grid(row=0, column=0, sticky='w', pady=5)
        slot_num_var = tk.StringVar()
        ttk.Entry(frame, textvariable=slot_num_var, width=25).grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Floor:").grid(row=1, column=0, sticky='w', pady=5)
        floor_var = tk.StringVar()
        floor_combo = ttk.Combobox(frame, textvariable=floor_var, width=23,
                                   values=['1', '2', '3', '4', '5'])
        floor_combo.grid(row=1, column=1, pady=5)
        floor_combo.set('1')
        
        ttk.Label(frame, text="Section:").grid(row=2, column=0, sticky='w', pady=5)
        section_var = tk.StringVar()
        ttk.Entry(frame, textvariable=section_var, width=25).grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Slot Type:").grid(row=3, column=0, sticky='w', pady=5)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(frame, textvariable=type_var, width=23,
                                  values=['regular', 'premium', 'handicap', 'electric'])
        type_combo.grid(row=3, column=1, pady=5)
        type_combo.set('regular')
        
        ttk.Label(frame, text="Vehicle Type:").grid(row=4, column=0, sticky='w', pady=5)
        vehicle_var = tk.StringVar()
        vehicle_combo = ttk.Combobox(frame, textvariable=vehicle_var, width=23,
                                     values=['car', 'bike', 'truck', 'bus'])
        vehicle_combo.grid(row=4, column=1, pady=5)
        vehicle_combo.set('car')
        
        ttk.Label(frame, text="Price per Hour (₹):").grid(row=5, column=0, sticky='w', pady=5)
        price_var = tk.StringVar(value="20")
        ttk.Entry(frame, textvariable=price_var, width=25).grid(row=5, column=1, pady=5)
        
        def save_slot():
            slot_number = slot_num_var.get().strip().upper()
            floor = floor_var.get()
            section = section_var.get().strip().upper()
            slot_type = type_var.get()
            vehicle_type = vehicle_var.get()
            price = price_var.get().strip()
            
            if not all([slot_number, floor, section, slot_type, vehicle_type, price]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                price = float(price)
                if price <= 0:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Invalid price")
                return
            
            db = get_db_manager()
            # Check if slot already exists
            existing = db.fetch_one("SELECT slot_id FROM parking_slots WHERE slot_number = ?",
                                   (slot_number,))
            if existing:
                messagebox.showerror("Error", "Slot number already exists")
                return
            
            db.execute_query("""
                INSERT INTO parking_slots 
                (slot_number, floor, section, slot_type, vehicle_type, base_price_per_hour, status)
                VALUES (?, ?, ?, ?, ?, ?, 'available')
            """, (slot_number, int(floor), section, slot_type, vehicle_type, price))
            
            messagebox.showinfo("Success", "Parking slot added successfully")
            dialog.destroy()
            self.load_parking_slots()
        
        ttk.Button(frame, text="Save", command=save_slot, width=15).grid(row=6, column=0, 
                                                                          columnspan=2, pady=20)
    
    def edit_parking_slot(self):
        """Edit selected parking slot"""
        selected = self.slots_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a slot to edit")
            return
        
        slot_data = self.slots_tree.item(selected[0])['values']
        slot_id = slot_data[0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Parking Slot")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Slot Number:").grid(row=0, column=0, sticky='w', pady=5)
        slot_num_var = tk.StringVar(value=slot_data[1])
        ttk.Entry(frame, textvariable=slot_num_var, width=25, state='readonly').grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Floor:").grid(row=1, column=0, sticky='w', pady=5)
        floor_var = tk.StringVar(value=slot_data[2])
        floor_combo = ttk.Combobox(frame, textvariable=floor_var, width=23,
                                   values=['1', '2', '3', '4', '5'])
        floor_combo.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Section:").grid(row=2, column=0, sticky='w', pady=5)
        section_var = tk.StringVar(value=slot_data[3])
        ttk.Entry(frame, textvariable=section_var, width=25).grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Slot Type:").grid(row=3, column=0, sticky='w', pady=5)
        type_var = tk.StringVar(value=slot_data[4])
        type_combo = ttk.Combobox(frame, textvariable=type_var, width=23,
                                  values=['regular', 'premium', 'handicap', 'electric'])
        type_combo.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Vehicle Type:").grid(row=4, column=0, sticky='w', pady=5)
        vehicle_var = tk.StringVar(value=slot_data[5])
        vehicle_combo = ttk.Combobox(frame, textvariable=vehicle_var, width=23,
                                     values=['car', 'bike', 'truck', 'bus'])
        vehicle_combo.grid(row=4, column=1, pady=5)
        
        ttk.Label(frame, text="Price per Hour (₹):").grid(row=5, column=0, sticky='w', pady=5)
        price_var = tk.StringVar(value=slot_data[6].replace('₹', ''))
        ttk.Entry(frame, textvariable=price_var, width=25).grid(row=5, column=1, pady=5)
        
        ttk.Label(frame, text="Status:").grid(row=6, column=0, sticky='w', pady=5)
        status_var = tk.StringVar(value=slot_data[7])
        status_combo = ttk.Combobox(frame, textvariable=status_var, width=23,
                                    values=['available', 'occupied', 'reserved', 'maintenance'])
        status_combo.grid(row=6, column=1, pady=5)
        
        def save_changes():
            floor = floor_var.get()
            section = section_var.get().strip().upper()
            slot_type = type_var.get()
            vehicle_type = vehicle_var.get()
            price = price_var.get().strip()
            status = status_var.get()
            
            if not all([floor, section, slot_type, vehicle_type, price, status]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                price = float(price)
                if price <= 0:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Invalid price")
                return
            
            db = get_db_manager()
            db.execute_query("""
                UPDATE parking_slots 
                SET floor = ?, section = ?, slot_type = ?, vehicle_type = ?, 
                    base_price_per_hour = ?, status = ?
                WHERE slot_id = ?
            """, (int(floor), section, slot_type, vehicle_type, price, status, slot_id))
            
            messagebox.showinfo("Success", "Parking slot updated successfully")
            dialog.destroy()
            self.load_parking_slots()
        
        ttk.Button(frame, text="Save Changes", command=save_changes, width=15).grid(row=7, column=0,
                                                                                     columnspan=2, pady=20)
    
    def delete_parking_slot(self):
        """Delete selected parking slot"""
        selected = self.slots_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a slot to delete")
            return
        
        slot_data = self.slots_tree.item(selected[0])['values']
        slot_id = slot_data[0]
        slot_number = slot_data[1]
        
        # Check if slot has active bookings
        db = get_db_manager()
        active = db.fetch_one("""
            SELECT COUNT(*) as count FROM bookings 
            WHERE slot_id = ? AND booking_status IN ('pending', 'active')
        """, (slot_id,))
        
        if active and active['count'] > 0:
            messagebox.showerror("Error", "Cannot delete slot with active bookings")
            return
        
        if messagebox.askyesno("Confirm", f"Delete parking slot {slot_number}?"):
            db.execute_query("DELETE FROM parking_slots WHERE slot_id = ?", (slot_id,))
            messagebox.showinfo("Success", "Parking slot deleted successfully")
            self.load_parking_slots()
    
    def load_users(self):
        """Load all users"""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        db = get_db_manager()
        users = db.fetch_all("""
            SELECT user_id, name, email, phone, user_type, wallet_balance, 
                   loyalty_points, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        
        for user in users:
            self.users_tree.insert('', 'end', values=(
                user['user_id'],
                user['name'],
                user['email'],
                user['phone'],
                user['user_type'],
                f"₹{user['wallet_balance']:.2f}",
                user['loyalty_points'],
                user['created_at']
            ))
    
    def view_user_details(self):
        """View detailed user information"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        user_data = self.users_tree.item(selected[0])['values']
        user_id = user_data[0]
        
        db = get_db_manager()
        
        # Get user stats
        booking_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM bookings WHERE user_id = ?
        """, (user_id,))['count']
        
        vehicle_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM vehicles WHERE user_id = ?
        """, (user_id,))['count']
        
        total_spent = db.fetch_one("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM bookings WHERE user_id = ? AND booking_status = 'completed'
        """, (user_id,))['total']
        
        info = f"""
User Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ID: {user_data[0]}
Name: {user_data[1]}
Email: {user_data[2]}
Phone: {user_data[3]}
Type: {user_data[4]}
Wallet Balance: {user_data[5]}
Loyalty Points: {user_data[6]}
Registered: {user_data[7]}

Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Bookings: {booking_count}
Registered Vehicles: {vehicle_count}
Total Amount Spent: ₹{total_spent:.2f}
        """
        
        messagebox.showinfo("User Details", info)
    
    def add_user_balance(self):
        """Add balance to user wallet"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        user_data = self.users_tree.item(selected[0])['values']
        user_id = user_data[0]
        user_name = user_data[1]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Wallet Balance")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text=f"User: {user_name}", font=('Arial', 11, 'bold')).pack(pady=10)
        
        ttk.Label(frame, text="Amount to Add (₹):").pack(pady=5)
        amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=amount_var, width=20, font=('Arial', 11)).pack(pady=5)
        
        def add_balance():
            try:
                amount = float(amount_var.get().strip())
                if amount <= 0:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Invalid amount")
                return
            
            db = get_db_manager()
            db.execute_query("""
                UPDATE users SET wallet_balance = wallet_balance + ?
                WHERE user_id = ?
            """, (amount, user_id))
            
            messagebox.showinfo("Success", f"₹{amount:.2f} added to {user_name}'s wallet")
            dialog.destroy()
            self.load_users()
        
        ttk.Button(frame, text="Add Balance", command=add_balance, width=15).pack(pady=15)
    
    def load_admin_bookings(self):
        """Load all bookings with filter"""
        for item in self.admin_bookings_tree.get_children():
            self.admin_bookings_tree.delete(item)
        
        status_filter = self.booking_status_filter.get()
        
        db = get_db_manager()
        query = """
            SELECT b.booking_id, b.ticket_number, u.name, v.vehicle_number, 
                   ps.slot_number, b.booking_status, b.total_amount, b.entry_time
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
        """
        params = []
        
        if status_filter != 'All':
            query += " WHERE b.booking_status = ?"
            params.append(status_filter)
        
        query += " ORDER BY b.booking_id DESC LIMIT 200"
        bookings = db.fetch_all(query, params)
        
        for booking in bookings:
            self.admin_bookings_tree.insert('', 'end', values=(
                booking['booking_id'],
                booking['ticket_number'],
                booking['name'],
                booking['vehicle_number'],
                booking['slot_number'],
                booking['booking_status'],
                f"₹{booking['total_amount']:.2f}" if booking['total_amount'] else 'N/A',
                booking['entry_time']
            ))
    
    def view_booking_details(self):
        """View detailed booking information"""
        selected = self.admin_bookings_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a booking")
            return
        
        booking_data = self.admin_bookings_tree.item(selected[0])['values']
        booking_id = booking_data[0]
        
        db = get_db_manager()
        booking = db.fetch_one("""
            SELECT b.*, u.name, u.email, v.vehicle_number, ps.slot_number
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
            WHERE b.booking_id = ?
        """, (booking_id,))
        
        if not booking:
            messagebox.showerror("Error", "Booking not found")
            return
        
        info = f"""
Booking Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Booking ID: {booking['booking_id']}
Ticket Number: {booking['ticket_number']}
Status: {booking['booking_status']}

User Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {booking['name']}
Email: {booking['email']}

Vehicle: {booking['vehicle_number']}
Slot: {booking['slot_number']}

Timing:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry: {booking['entry_time']}
Exit: {booking['exit_time'] or 'Not yet'}
Duration: {booking['duration_hours'] or 'N/A'} hours

Payment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Base Amount: ₹{booking['base_amount'] or 0:.2f}
Total Amount: ₹{booking['total_amount'] or 0:.2f}
Payment Status: {booking['payment_status']}
        """
        
        messagebox.showinfo("Booking Details", info)
    
    def admin_cancel_booking(self):
        """Admin cancel a booking"""
        selected = self.admin_bookings_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a booking")
            return
        
        booking_data = self.admin_bookings_tree.item(selected[0])['values']
        if len(booking_data) < 6:
            messagebox.showerror("Error", "Invalid booking data")
            return
            
        booking_id = booking_data[0]
        ticket_number = booking_data[1]
        status = booking_data[5]
        
        if status not in ['pending', 'active']:
            messagebox.showwarning("Warning", "Can only cancel pending or active bookings")
            return
        
        if messagebox.askyesno("Confirm", f"Cancel booking {ticket_number}?"):
            db = get_db_manager()
            
            # Get booking amount for refund
            booking = db.fetch_one("SELECT total_amount, slot_id FROM bookings WHERE booking_id = ?",
                                  (booking_id,))
            
            if booking:
                # Update booking status
                db.execute_query("UPDATE bookings SET booking_status = 'cancelled' WHERE booking_id = ?",
                          (booking_id,))
                
                # Free the slot
                db.execute_query("UPDATE parking_slots SET status = 'available' WHERE slot_id = ?",
                          (booking['slot_id'],))
                
                messagebox.showinfo("Success", "Booking cancelled successfully")
                self.load_admin_bookings()
    
    def backup_database(self):
        """Backup database"""
        from shutil import copy2
        from datetime import datetime
        
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"parking_backup_{timestamp}.db")
        
        try:
            copy2("database/parking_system.db", backup_path)
            messagebox.showinfo("Success", f"Database backed up to:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def show_statistics(self):
        """Show database statistics"""
        db = get_db_manager()
        
        total_users = db.fetch_one("SELECT COUNT(*) as count FROM users")['count']
        total_slots = db.fetch_one("SELECT COUNT(*) as count FROM parking_slots")['count']
        total_bookings = db.fetch_one("SELECT COUNT(*) as count FROM bookings")['count']
        active_bookings = db.fetch_one("""
            SELECT COUNT(*) as count FROM bookings WHERE booking_status IN ('pending', 'active')
        """)['count']
        total_revenue = db.fetch_one("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM bookings WHERE booking_status = 'completed'
        """)['total']
        
        stats = f"""
System Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Users: {total_users}
Total Parking Slots: {total_slots}
Total Bookings: {total_bookings}
Active Bookings: {active_bookings}
Total Revenue: ₹{total_revenue:.2f}
        """
        
        messagebox.showinfo("Database Statistics", stats)
    
    def clear_old_data(self):
        """Clear old completed bookings"""
        if messagebox.askyesno("Confirm", 
                              "Delete bookings older than 90 days?\nThis cannot be undone!"):
            db = get_db_manager()
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            
            db.execute_query("""
                DELETE FROM bookings 
                WHERE booking_status = 'completed' AND entry_time < ?
            """, (cutoff_date,))
            
            messagebox.showinfo("Success", f"Old data cleaned successfully")
    
    def generate_revenue_chart(self):
        """Generate revenue chart"""
        path = self.analytics_manager.generate_revenue_chart(7)
        if path:
            messagebox.showinfo("Success", f"Chart saved at:\n{path}")
            os.startfile(path)
    
    def generate_occupancy_chart(self):
        """Generate occupancy chart"""
        path = self.analytics_manager.generate_occupancy_chart()
        if path:
            messagebox.showinfo("Success", f"Chart saved at:\n{path}")
            os.startfile(path)
    
    def generate_peak_hours_chart(self):
        """Generate peak hours chart"""
        path = self.analytics_manager.generate_peak_hours_chart()
        if path:
            messagebox.showinfo("Success", f"Chart saved at:\n{path}")
            os.startfile(path)
    
    def export_bookings(self):
        """Export bookings to CSV"""
        path = self.analytics_manager.export_bookings_to_csv()
        if path:
            messagebox.showinfo("Success", f"Report exported to:\n{path}")
            os.startfile(os.path.dirname(path))
    
    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Confirm", "Are you sure you want to logout?"):
            self.root.destroy()
            start_app()


def start_app():
    """Start the application"""
    root = ThemedTk(theme="radiance")
    root.title("Smart Parking System - Login")
    root.geometry("600x400")
    
    def on_login_success(user_data):
        for widget in root.winfo_children():
            widget.destroy()
        
        root.title(f"Smart Parking System - {user_data['name']}")
        root.geometry("1200x700")
        root.deiconify()
        
        app = MainApplication(root, user_data)
    
    LoginWindow(root, on_login_success)
    root.mainloop()


if __name__ == "__main__":
    db = get_db_manager()
    db.initialize_database()
    
    admin = db.get_user_by_email("admin@parking.com")
    if not admin:
        UserAuth.register_user("Admin", "admin@parking.com", "1234567890", 
                              "admin123", "admin")
    
    start_app()

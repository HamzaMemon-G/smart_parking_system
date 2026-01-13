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
from database.db_manager import get_db_manager


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
        
        login_btn = ttk.Button(btn_frame, text="Login", command=self.login, width=15)
        login_btn.pack(side='left', padx=5)
        
        register_btn = ttk.Button(btn_frame, text="Register", command=self.show_register, width=15)
        register_btn.pack(side='left', padx=5)
        
        password_entry.bind('<Return>', lambda e: self.login())
    
    def login(self):
        """Handle login"""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter email and password")
            return
        
        success, user_data, message = UserAuth.login_user(email, password)
        
        if success:
            messagebox.showinfo("Success", f"Welcome, {user_data['name']}!")
            self.on_login_success(user_data)
        else:
            messagebox.showerror("Login Failed", message)
    
    def show_register(self):
        """Show registration dialog"""
        RegisterWindow(self.root)


class RegisterWindow:
    """Registration Dialog"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Register New User")
        self.window.geometry("400x450")
        self.window.transient(parent)
        self.window.grab_set()
        
        frame = ttk.Frame(self.window, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Create Account", font=('Arial', 18, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=15)
        
        fields = [
            ("Name:", 'name'),
            ("Email:", 'email'),
            ("Phone:", 'phone'),
            ("Password:", 'password'),
            ("Confirm Password:", 'confirm_password')
        ]
        
        self.vars = {}
        for idx, (label, key) in enumerate(fields, start=1):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky='e', padx=5, pady=8)
            var = tk.StringVar()
            self.vars[key] = var
            show = '*' if 'password' in key.lower() else None
            ttk.Entry(frame, textvariable=var, width=25, show=show).grid(
                row=idx, column=1, padx=5, pady=8)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Register", command=self.register).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side='left', padx=5)
    
    def register(self):
        """Handle registration"""
        name = self.vars['name'].get().strip()
        email = self.vars['email'].get().strip()
        phone = self.vars['phone'].get().strip()
        password = self.vars['password'].get()
        confirm = self.vars['confirm_password'].get()
        
        if not all([name, email, phone, password]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        success, message = UserAuth.register_user(name, email, phone, password)
        
        if success:
            messagebox.showinfo("Success", "Registration successful! You can now login.")
            self.window.destroy()
        else:
            messagebox.showerror("Registration Failed", message)


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
        
        self.create_dashboard_tab()
        self.create_booking_tab()
        self.create_my_bookings_tab()
        self.create_vehicles_tab()
        self.create_wallet_tab()
        
        if self.user_data['user_type'] == 'admin':
            self.create_admin_tab()
            self.create_analytics_tab()
    
    def create_dashboard_tab(self):
        """Dashboard tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Dashboard")
        
        stats_frame = ttk.LabelFrame(tab, text="Parking Statistics", padding="15")
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_labels = {}
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()
    
    def create_booking_tab(self):
        """Create booking tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🅿️ Book Parking")
        

        filter_frame = ttk.LabelFrame(tab, text="Search Filters", padding="10")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Vehicle Type:").grid(row=0, column=0, padx=5, pady=5)
        self.vehicle_type_var = tk.StringVar(value="car")
        ttk.Combobox(filter_frame, textvariable=self.vehicle_type_var, 
                    values=["car", "bike", "truck"], state='readonly', width=15).grid(
                    row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Floor:").grid(row=0, column=2, padx=5, pady=5)
        self.floor_var = tk.StringVar(value="Any")
        ttk.Combobox(filter_frame, textvariable=self.floor_var, 
                    values=["Any", "1", "2", "3"], state='readonly', width=10).grid(
                    row=0, column=3, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Search", command=self.search_slots).grid(
            row=0, column=4, padx=10, pady=5)
        
        slots_frame = ttk.LabelFrame(tab, text="Available Slots", padding="10")
        slots_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Slot', 'Floor', 'Section', 'Type', 'Price/Hr')
        self.slots_tree = ttk.Treeview(slots_frame, columns=columns, show='tree headings', height=15)
        
        for col in columns:
            self.slots_tree.heading(col, text=col)
            self.slots_tree.column(col, width=100)
        
        self.slots_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(slots_frame, orient='vertical', command=self.slots_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.slots_tree.configure(yscrollcommand=scrollbar.set)
        
        ttk.Button(tab, text="Book Selected Slot", command=self.book_slot).pack(pady=10)
        
        self.search_slots()
    
    def create_my_bookings_tab(self):
        """My bookings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 My Bookings")
        

        active_frame = ttk.LabelFrame(tab, text="Active Bookings", padding="10")
        active_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Ticket', 'Vehicle', 'Slot', 'Entry Time', 'Status')
        self.active_bookings_tree = ttk.Treeview(active_frame, columns=columns, 
                                                show='tree headings', height=8)
        
        for col in columns:
            self.active_bookings_tree.heading(col, text=col)
            self.active_bookings_tree.column(col, width=120)
        
        self.active_bookings_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(active_frame, orient='vertical', 
                                 command=self.active_bookings_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.active_bookings_tree.configure(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Exit Parking", command=self.exit_parking).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel Booking", command=self.cancel_booking).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Generate Ticket", command=self.generate_ticket).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_my_bookings).pack(side='left', padx=5)
        
        self.load_my_bookings()
    
    def create_vehicles_tab(self):
        """Vehicles management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🚗 My Vehicles")
        

        add_frame = ttk.LabelFrame(tab, text="Add New Vehicle", padding="15")
        add_frame.pack(fill='x', padx=10, pady=10)
        
        form_frame = ttk.Frame(add_frame)
        form_frame.pack()
        
        ttk.Label(form_frame, text="Vehicle Number:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.vehicle_number_var = tk.StringVar()
        self.vehicle_entry = ttk.Entry(form_frame, textvariable=self.vehicle_number_var, width=20)
        self.vehicle_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.new_vehicle_type_var = tk.StringVar(value="car")
        ttk.Combobox(form_frame, textvariable=self.new_vehicle_type_var, 
                    values=["car", "bike", "truck"], state='readonly', width=15).grid(
                    row=0, column=3, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Brand:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.vehicle_brand_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.vehicle_brand_var, width=20).grid(
            row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Model:").grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.vehicle_model_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.vehicle_model_var, width=15).grid(
            row=1, column=3, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Color:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.vehicle_color_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.vehicle_color_var, width=20).grid(
            row=2, column=1, padx=5, pady=5)
        
        ttk.Button(form_frame, text="➕ Add Vehicle", command=self.add_vehicle).grid(
            row=2, column=2, columnspan=2, padx=10, pady=5, sticky='ew')
        
        vehicles_frame = ttk.LabelFrame(tab, text="My Vehicles", padding="10")
        vehicles_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Number', 'Type', 'Brand', 'Model')
        self.vehicles_tree = ttk.Treeview(vehicles_frame, columns=columns, 
                                         show='tree headings', height=10)
        
        for col in columns:
            self.vehicles_tree.heading(col, text=col)
            self.vehicles_tree.column(col, width=120)
        
        self.vehicles_tree.pack(fill='both', expand=True, pady=(0, 10))
        
        btn_frame = ttk.Frame(vehicles_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="🗑️ Delete Selected Vehicle", 
                  command=self.delete_vehicle).pack(side='right', padx=5)
        
        self.load_vehicles()
    
    def create_wallet_tab(self):
        """Wallet management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="💰 Wallet")
        

        balance_frame = tk.Frame(tab, bg='#27ae60', relief='raised', bd=3)
        balance_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(balance_frame, text="💰 Current Balance", 
                font=('Arial', 14, 'bold'), bg='#27ae60', fg='white').pack(pady=10)
        
        self.balance_label = tk.Label(balance_frame, 
                                      text=f"₹{self.user_data['wallet_balance']:.2f}", 
                                      font=('Arial', 48, 'bold'), bg='#27ae60', fg='#ecf0f1')
        self.balance_label.pack(pady=20)
        
        add_frame = ttk.LabelFrame(tab, text="Add Money", padding="15")
        add_frame.pack(fill='x', padx=10, pady=10)
        
        form = ttk.Frame(add_frame)
        form.pack()
        
        ttk.Label(form, text="Amount:", font=('Arial', 11)).grid(row=0, column=0, padx=5, pady=5)
        self.recharge_amount_var = tk.StringVar()
        self.recharge_entry = ttk.Entry(form, textvariable=self.recharge_amount_var, width=20, font=('Arial', 11))
        self.recharge_entry.grid(row=0, column=1, padx=5, pady=5)
        
        add_btn = tk.Button(form, text="💵 Add to Wallet", command=self.add_to_wallet,
                           bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                           relief='raised', bd=2, padx=20, pady=10, cursor='hand2')
        add_btn.grid(row=0, column=2, padx=10, pady=5)
    
    def create_admin_tab(self):
        """Admin panel tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Admin Panel")
        
        init_frame = ttk.LabelFrame(tab, text="Initialize Parking", padding="15")
        init_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(init_frame, text="Initialize Parking Structure", 
                  command=self.initialize_parking).pack(pady=5)
        
        bookings_frame = ttk.LabelFrame(tab, text="All Active Bookings", padding="10")
        bookings_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Ticket', 'User', 'Vehicle', 'Slot', 'Entry')
        self.admin_bookings_tree = ttk.Treeview(bookings_frame, columns=columns, 
                                               show='tree headings', height=15)
        
        for col in columns:
            self.admin_bookings_tree.heading(col, text=col)
            self.admin_bookings_tree.column(col, width=120)
        
        self.admin_bookings_tree.pack(fill='both', expand=True)
        
        ttk.Button(tab, text="Refresh Bookings", command=self.load_admin_bookings).pack(pady=5)
    
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
            pass
        
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
    
    def load_admin_bookings(self):
        """Load all active bookings"""
        bookings = self.booking_manager.get_all_active_bookings()
        
        for item in self.admin_bookings_tree.get_children():
            self.admin_bookings_tree.delete(item)
        
        for booking in bookings:
            self.admin_bookings_tree.insert('', 'end', values=(
                booking['ticket_number'],
                booking['name'],
                booking['vehicle_number'],
                booking['slot_number'],
                booking['entry_time']
            ))
    
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

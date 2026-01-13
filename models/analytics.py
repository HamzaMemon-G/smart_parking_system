"""Analytics and Reports"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime, timedelta
from typing import Dict, List
import os
from database.db_manager import get_db_manager


class AnalyticsManager:
    
    def __init__(self):
        self.db = get_db_manager()
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'charts')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_revenue_stats(self, days: int = 30) -> Dict:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        stats = self.db.get_revenue_stats(start_date, end_date)
        
        if stats:
            stats['total_revenue'] = round(stats.get('total_revenue', 0) or 0, 2)
            stats['avg_revenue'] = round(stats.get('avg_revenue', 0) or 0, 2)
            stats['total_hours'] = round(stats.get('total_hours', 0) or 0, 2)
        
        return stats
    
    def get_occupancy_trends(self) -> Dict:

        stats = self.db.get_slot_statistics()
        
        trends = {
            'current_occupancy_rate': 0,
            'total_slots': stats.get('total_slots', 0),
            'available': stats.get('available', 0),
            'occupied': stats.get('occupied', 0),
            'reserved': stats.get('reserved', 0),
            'maintenance': stats.get('maintenance', 0)
        }
        
        if trends['total_slots'] > 0:
            trends['current_occupancy_rate'] = round(
                (trends['occupied'] / trends['total_slots']) * 100, 2
            )
        
        return trends
    
    def get_peak_hours(self) -> List[Dict]:
        data = self.db.get_peak_hours_analysis()
        return [dict(row) for row in data]
    
    def get_vehicle_distribution(self) -> List[Dict]:
        data = self.db.get_vehicle_type_distribution()
        return [dict(row) for row in data]
    
    def generate_revenue_chart(self, days: int = 7) -> str:
        data = self.db.get_daily_revenue(days)
        
        if not data:
            return None
        
        df = pd.DataFrame([dict(row) for row in data])
        df['revenue'] = df['revenue'].fillna(0)
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['date'], df['revenue'], marker='o', linewidth=2, markersize=8)
        plt.title(f'Revenue Trend - Last {days} Days', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Revenue (₹)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filename = f'revenue_trend_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_occupancy_chart(self) -> str:
        stats = self.db.get_slot_statistics()
        
        labels = ['Occupied', 'Available', 'Reserved', 'Maintenance']
        sizes = [
            stats.get('occupied', 0),
            stats.get('available', 0),
            stats.get('reserved', 0),
            stats.get('maintenance', 0)
        ]
        colors = ['#ff6b6b', '#51cf66', '#ffd43b', '#868e96']
        explode = (0.1, 0, 0, 0)
        
        plt.figure(figsize=(10, 8))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title('Current Parking Occupancy', fontsize=16, fontweight='bold')
        plt.axis('equal')
        
        filename = f'occupancy_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_peak_hours_chart(self) -> str:

        data = self.get_peak_hours()
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df = df.sort_values('hour')
        
        plt.figure(figsize=(12, 6))
        plt.bar(df['hour'], df['bookings'], color='#339af0', alpha=0.8)
        plt.title('Peak Parking Hours Analysis', fontsize=16, fontweight='bold')
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Number of Bookings', fontsize=12)
        plt.xticks(range(0, 24))
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        filename = f'peak_hours_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_vehicle_type_chart(self) -> str:

        data = self.get_vehicle_distribution()
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        plt.figure(figsize=(10, 6))
        plt.bar(df['vehicle_type'], df['count'], color=['#845ef7', '#20c997', '#ff6b6b'])
        plt.title('Vehicle Type Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Vehicle Type', fontsize=12)
        plt.ylabel('Number of Bookings', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        filename = f'vehicle_types_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()
        
        return filepath
    
    def generate_dashboard_report(self) -> Dict:

        dashboard = {
            'revenue_stats': self.get_revenue_stats(30),
            'occupancy_trends': self.get_occupancy_trends(),
            'peak_hours': self.get_peak_hours(),
            'vehicle_distribution': self.get_vehicle_distribution(),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return dashboard
    
    def export_bookings_to_csv(self, start_date: str = None, end_date: str = None) -> str:
        """Export booking data to CSV"""
        query = """
            SELECT 
                b.ticket_number, b.booking_date, b.entry_time, b.exit_time,
                b.duration_hours, b.total_amount, b.payment_status, b.booking_status,
                u.name as user_name, u.email, u.phone,
                v.vehicle_number, v.vehicle_type,
                s.slot_number, s.floor, s.section
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            JOIN parking_slots s ON b.slot_id = s.slot_id
        """
        
        if start_date and end_date:
            query += f" WHERE DATE(b.booking_date) BETWEEN '{start_date}' AND '{end_date}'"
        
        query += " ORDER BY b.booking_date DESC"
        
        data = self.db.fetch_all(query)
        
        if not data:
            return None
        
        df = pd.DataFrame([dict(row) for row in data])
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f'bookings_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath

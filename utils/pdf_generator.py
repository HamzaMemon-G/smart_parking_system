"""PDF Report Generation"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
import os


class PDFGenerator:
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'outputs', 'tickets')
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
    
    def generate_parking_receipt(self, bill_data: dict, qr_code_path: str = None) -> str:
        """Generate PDF parking receipt"""
        filename = f"receipt_{bill_data['ticket_number']}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("PARKING RECEIPT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        if qr_code_path and os.path.exists(qr_code_path):
            img = Image(qr_code_path, width=1.5*inch, height=1.5*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
        
        data = [
            ['Vehicle Number:', bill_data.get('vehicle_number', 'N/A')],
            ['Slot:', bill_data.get('slot_number', 'N/A')],
            ['', ''],
            ['Entry Time:', bill_data.get('entry_time', 'N/A')],
            ['Exit Time:', bill_data.get('exit_time', 'N/A')],
            ['Duration (hours):', str(bill_data.get('duration_hours', 0))],
            ['', ''],
            ['Base Rate (₹/hr):', f"₹{bill_data.get('base_price', 0):.2f}"],
            ['Base Amount:', f"₹{bill_data.get('base_amount', 0):.2f}"],
            ['Surge/Charges:', f"₹{bill_data.get('surge_amount', 0):.2f}"],
            ['', ''],
            ['TOTAL AMOUNT:', f"₹{bill_data.get('total_amount', 0):.2f}"],
        ]
        
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1e3a8a')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, -1), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        footer_style = ParagraphStyle(
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("Thank you for using Smart Parking System!", footer_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              footer_style))
        
        doc.build(story)
        return filepath
    
    def generate_monthly_report(self, user_data: dict, bookings: list) -> str:
        filename = f"monthly_report_{user_data['user_id']}_{datetime.now().strftime('%Y%m')}.pdf"
        report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'reports')
        os.makedirs(report_dir, exist_ok=True)
        filepath = os.path.join(report_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        story.append(Paragraph("MONTHLY PARKING REPORT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        user_info = [
            ['User Name:', user_data.get('name', 'N/A')],
            ['Email:', user_data.get('email', 'N/A')],
            ['Report Period:', datetime.now().strftime('%B %Y')],
        ]
        
        user_table = Table(user_info, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(user_table)
        story.append(Spacer(1, 0.3*inch))
        
        if bookings:
            booking_data = [['Date', 'Slot', 'Duration (hrs)', 'Amount (₹)']]
            total_amount = 0
            total_hours = 0
            
            for booking in bookings:
                booking_data.append([
                    booking.get('booking_date', 'N/A'),
                    booking.get('slot_number', 'N/A'),
                    f"{booking.get('duration_hours', 0):.2f}",
                    f"₹{booking.get('total_amount', 0):.2f}"
                ])
                total_amount += booking.get('total_amount', 0) or 0
                total_hours += booking.get('duration_hours', 0) or 0
            
            booking_data.append(['TOTAL', '', f"{total_hours:.2f}", f"₹{total_amount:.2f}"])
            
            booking_table = Table(booking_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            booking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(booking_table)
        else:
            story.append(Paragraph("No bookings found for this period.", self.styles['Normal']))
        
        doc.build(story)
        return filepath

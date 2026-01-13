"""QR Code Generation"""

import qrcode
from PIL import Image
import os
from datetime import datetime


class QRCodeGenerator:
    
    @staticmethod
    def generate_ticket_qr(ticket_data: dict, output_dir: str = None) -> str:
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     'outputs', 'tickets')
        os.makedirs(output_dir, exist_ok=True)
        
        qr_data = f"""Ticket: {ticket_data.get('ticket_number')}
Vehicle: {ticket_data.get('vehicle_number')}
Slot: {ticket_data.get('slot_number')}
Entry: {ticket_data.get('entry_time')}
"""
        

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"ticket_{ticket_data.get('ticket_number')}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath)
        
        return filepath
    
    @staticmethod
    def generate_simple_qr(data: str, filename: str, output_dir: str = None) -> str:
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     'outputs', 'tickets')
        os.makedirs(output_dir, exist_ok=True)
        
        qr = qrcode.make(data)
        
        if not filename.endswith('.png'):
            filename += '.png'
        
        filepath = os.path.join(output_dir, filename)
        qr.save(filepath)
        
        return filepath

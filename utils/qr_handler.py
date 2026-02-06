"""QR Code Generation and Scanning Utilities"""

import qrcode
import cv2
from pyzbar.pyzbar import decode
import json
from PIL import Image
import os
from datetime import datetime


class QRHandler:
    """Handle QR code generation and scanning for parking system"""
    
    def __init__(self, output_dir="outputs/qrcodes"):
        """Initialize QR handler with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_booking_qr(self, booking_id, ticket_number, user_id, vehicle_number, slot_number):
        """
        Generate QR code for a booking
        
        Args:
            booking_id: Unique booking ID
            ticket_number: Ticket number
            user_id: User ID
            vehicle_number: Vehicle registration number
            slot_number: Assigned slot number
            
        Returns:
            tuple: (qr_data_string, qr_image_path)
        """
        qr_data = {
            "type": "parking_booking",
            "booking_id": booking_id,
            "ticket": ticket_number,
            "user_id": user_id,
            "vehicle": vehicle_number,
            "slot": slot_number,
            "timestamp": datetime.now().isoformat()
        }
        
        qr_data_str = json.dumps(qr_data)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data_str)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"booking_{booking_id}_{ticket_number}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        return qr_data_str, filepath
    
    def scan_qr_from_image(self, image_path):
        """
        Scan QR code from image file
        
        Args:
            image_path: Path to image file containing QR code
            
        Returns:
            dict: Decoded QR data or None if no QR found
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            decoded_objects = decode(img)
            
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                return json.loads(qr_data)
            
            return None
        except Exception as e:
            print(f"Error scanning QR: {e}")
            return None
    
    def scan_qr_from_webcam(self):
        """
        Scan QR code from webcam feed
        
        Returns:
            dict: Decoded QR data or None if cancelled
        """
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return None
        
        print("=" * 60)
        print("QR CODE SCANNER - Press ESC to cancel")
        print("=" * 60)
        
        detected_data = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            decoded_objects = decode(frame)
            
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    
                    points = obj.polygon
                    if len(points) == 4:
                        pts = [(point.x, point.y) for point in points]
                        for i in range(4):
                            cv2.line(frame, pts[i], pts[(i + 1) % 4], (0, 255, 0), 3)
                    
                    cv2.putText(frame, "QR Detected!", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    try:
                        detected_data = json.loads(qr_data)
                        cv2.putText(frame, "Press SPACE to confirm", (10, 70),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    except:
                        cv2.putText(frame, "Invalid QR format", (10, 70),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "No QR detected - Show QR to camera", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('QR Scanner - SPACE to confirm | ESC to cancel', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') and detected_data:
                break
            elif key == 27:
                detected_data = None
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return detected_data
    
    def validate_booking_qr(self, qr_data):
        """
        Validate QR code data format
        
        Args:
            qr_data: Decoded QR data dictionary
            
        Returns:
            bool: True if valid booking QR
        """
        if not isinstance(qr_data, dict):
            return False
        
        required_fields = ['type', 'booking_id', 'ticket', 'user_id', 'vehicle', 'slot']
        
        for field in required_fields:
            if field not in qr_data:
                return False
        
        if qr_data['type'] != 'parking_booking':
            return False
        
        return True
    
    def get_qr_as_base64(self, qr_image_path):
        """
        Convert QR image to base64 for web display
        
        Args:
            qr_image_path: Path to QR image
            
        Returns:
            str: Base64 encoded image
        """
        import base64
        
        with open(qr_image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')


def test_qr_handler():
    """Test QR generation and scanning"""
    handler = QRHandler()
    
    print("Testing QR Code Generation...")
    qr_data, qr_path = handler.generate_booking_qr(
        booking_id=12345,
        ticket_number="TKT123456",
        user_id=1,
        vehicle_number="MH12DE1234",
        slot_number="G-001"
    )
    
    print(f"✓ QR Generated: {qr_path}")
    print(f"✓ QR Data: {qr_data}")
    
    print("\nTesting QR Scanning from file...")
    scanned_data = handler.scan_qr_from_image(qr_path)
    
    if scanned_data:
        print(f"✓ QR Scanned Successfully!")
        print(f"  Booking ID: {scanned_data['booking_id']}")
        print(f"  Ticket: {scanned_data['ticket']}")
        print(f"  Vehicle: {scanned_data['vehicle']}")
        print(f"  Slot: {scanned_data['slot']}")
    else:
        print("✗ Failed to scan QR")
    
    print("\nTesting validation...")
    is_valid = handler.validate_booking_qr(scanned_data)
    print(f"✓ QR Valid: {is_valid}")


if __name__ == "__main__":
    test_qr_handler()

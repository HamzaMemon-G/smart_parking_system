"""License Plate Detection using OpenCV and Tesseract OCR"""

import cv2
import pytesseract
import numpy as np
import re
from typing import Optional, Tuple
import imutils


class LicensePlateDetector:
    """Detect and read license plates from images or camera"""
    
    def __init__(self):
        # Set tesseract path (update this path based on installation)
        # Download from: https://github.com/UB-Mannheim/tesseract/wiki
        try:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass  # Will use system PATH
    
    def preprocess_image(self, image):
        """Preprocess image for better plate detection - multiple techniques"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        
        gray_adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gray_morph = cv2.morphologyEx(gray_bilateral, cv2.MORPH_CLOSE, kernel)
        edged = cv2.Canny(gray_morph, 30, 200)
        
        return gray_bilateral, edged, gray_adaptive
    
    def find_license_plate_contour(self, edged):
        """Find license plate contour in the image"""
        contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        plate_contour = None
        
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
            
            if len(approx) == 4:
                plate_contour = approx
                break
        
        return plate_contour
    
    def extract_text_from_plate(self, image, contour):
        """Extract text from detected license plate region - handles single and two-line plates"""
        if contour is None:
            return None
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        x, y, w, h = cv2.boundingRect(contour)
        plate_region = image[y:y+h, x:x+w]
        plate_region = cv2.resize(plate_region, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        gray_plate = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        height, width = gray_plate.shape
        is_two_line = height > width * 0.4
        
        if is_two_line:
            return self.extract_text_two_line(gray_plate)
        else:
            return self.extract_text_single_line(gray_plate)
    
    def extract_text_two_line(self, gray_plate):
        """Extract text from two-line license plates (4 chars top, 6 chars bottom)"""
        height, width = gray_plate.shape
        
        # Split into top and bottom halves
        mid_point = height // 2
        
        # Add some overlap to avoid cutting characters
        overlap = int(height * 0.1)
        
        top_half = gray_plate[0:mid_point + overlap, :]
        bottom_half = gray_plate[mid_point - overlap:, :]
        
        # Process each half separately
        top_results = []
        bottom_results = []
        
        for half, results_list in [(top_half, top_results), (bottom_half, bottom_results)]:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(half)
            _, thresh1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            bilateral = cv2.bilateralFilter(half, 9, 75, 75)
            thresh2 = cv2.adaptiveThreshold(
                bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            blur = cv2.GaussianBlur(half, (5, 5), 0)
            _, thresh3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(half, cv2.MORPH_CLOSE, kernel)
            _, thresh4 = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            configs = [
                '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                '--psm 13 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            ]
            
            for thresh in [thresh1, thresh2, thresh3, thresh4]:
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(thresh, config=config)
                        text = self.clean_ocr_text(text)
                        if len(text) >= 2:  # At least 2 characters
                            results_list.append(text)
                    except:
                        continue
        
        # Get most common result for each line
        from collections import Counter
        
        top_text = ""
        bottom_text = ""
        
        if top_results:
            top_text = Counter(top_results).most_common(1)[0][0]
        
        if bottom_results:
            bottom_text = Counter(bottom_results).most_common(1)[0][0]
        
        # Combine top and bottom
        combined = top_text + bottom_text
        
        if len(combined) >= 6:
            corrected = self.correct_ocr_errors(combined)
            return corrected if self.validate_plate_format(corrected) else None
        
        return None
    
    def extract_text_single_line(self, gray_plate):
        """Extract text from single-line license plates"""
        results = []
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_plate)
        _, thresh1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        bilateral = cv2.bilateralFilter(gray_plate, 9, 75, 75)
        thresh2 = cv2.adaptiveThreshold(
            bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        blur = cv2.GaussianBlur(gray_plate, (5, 5), 0)
        _, thresh3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(gray_plate, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        _, thresh4 = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        _, thresh5 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray_plate, -1, kernel_sharp)
        _, thresh6 = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        configs = [
            '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 13 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        ]
        
        for thresh in [thresh1, thresh2, thresh3, thresh4, thresh5, thresh6]:
            for config in configs:
                try:
                    text = pytesseract.image_to_string(thresh, config=config)
                    text = self.clean_ocr_text(text)
                    
                    if len(text) >= 6 and len(text) <= 15:
                        results.append(text)
                except:
                    continue
        
        # Return most common result with OCR error correction
        if results:
            from collections import Counter
            most_common = Counter(results).most_common(1)[0][0]
            corrected = self.correct_ocr_errors(most_common)
            return corrected if self.validate_plate_format(corrected) else None
        
        return None
    
    def clean_ocr_text(self, text):
        """Clean OCR output"""
        text = text.strip().upper()
        # Remove all non-alphanumeric characters
        text = re.sub(r'[^A-Z0-9]', '', text)
        return text
    
    def correct_ocr_errors(self, text):
        """Correct common OCR mistakes in license plates"""
        corrections = {
            'O': '0', 'I': '1', 'Z': '2',
            'S': '5', 'B': '8', 'G': '6'
        }
        
        result = list(text)
        
        for i, char in enumerate(result):
            if i > 0 and i < len(result) - 1:
                prev_is_num = result[i-1].isdigit()
                next_is_num = result[i+1].isdigit()
                
                if prev_is_num and next_is_num and char in corrections:
                    result[i] = corrections[char]
            
            elif i == len(result) - 1 and i > 0:
                if result[i-1].isdigit() and char in corrections:
                    result[i] = corrections[char]
        
        corrected = ''.join(result)
        corrected = corrected.replace('0O', '00').replace('O0', '00')
        corrected = corrected.replace('I1', '11').replace('1I', '11')
        
        return corrected
    
    def validate_plate_format(self, text):
        """Validate if detected text matches typical plate format"""
        if not text or len(text) < 6:
            return False
        
        has_letter = any(c.isalpha() for c in text)
        has_number = any(c.isdigit() for c in text)
        
        return has_letter and has_number
    
    def detect_from_image(self, image_path: str) -> Optional[Tuple[str, np.ndarray]]:
        """
        Detect license plate from image file
        Returns: (plate_text, annotated_image) or (None, original_image)
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None, None
            
            return self.detect_from_frame(image)
        except Exception as e:
            print(f"Error detecting from image: {e}")
            return None, None
    
    def detect_from_frame(self, frame: np.ndarray) -> Optional[Tuple[str, np.ndarray]]:
        """
        Detect license plate from image frame with improved accuracy
        Returns: (plate_text, annotated_image) or (None, original_image)
        """
        try:
            frame = imutils.resize(frame, width=600)
            gray, edged, adaptive = self.preprocess_image(frame)
            plate_contour = self.find_license_plate_contour(edged)
            
            if plate_contour is not None:
                plate_text = self.extract_text_from_plate(frame, plate_contour)
                annotated = frame.copy()
                cv2.drawContours(annotated, [plate_contour], -1, (0, 255, 0), 3)
                
                if plate_text:
                    text_size = cv2.getTextSize(plate_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    cv2.rectangle(annotated, (5, 5), (text_size[0] + 15, 40), (0, 255, 0), -1)
                    cv2.putText(annotated, plate_text, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                    return plate_text, annotated
                else:
                    cv2.putText(annotated, "Detected - Analyzing...", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            return None, frame
        except Exception as e:
            print(f"Error detecting from frame: {e}")
            return None, frame
    
    def capture_from_camera(self, camera_index: int = 0) -> Optional[str]:
        """
        Open camera and capture license plate with improved accuracy
        Returns: detected plate text or None
        """
        cap = cv2.VideoCapture(camera_index)
        detected_plate = None
        last_detection = None
        detection_count = {}
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return None
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        
        print("=" * 60)
        print("LICENSE PLATE DETECTION - CAMERA MODE")
        print("=" * 60)
        print("Instructions:")
        print("  • Hold plate steady in frame (avoid blur)")
        print("  • Ensure good lighting")
        print("  • Keep plate parallel to camera")
        print("  • Wait for green box around plate")
        print("  • Press SPACE when text is detected")
        print("  • Press ESC to cancel")
        print("=" * 60)
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % 3 == 0:
                plate_text, annotated = self.detect_from_frame(frame)
                
                if plate_text:
                    last_detection = plate_text
                    detection_count[plate_text] = detection_count.get(plate_text, 0) + 1
                
                display_frame = annotated
            else:
                display_frame = frame
            
            status_text = "No plate detected"
            status_color = (0, 0, 255)
            
            if last_detection:
                count = detection_count.get(last_detection, 0)
                status_text = f"Detected: {last_detection} ({count}x) - Press SPACE"
                status_color = (0, 255, 0)
            
            cv2.rectangle(display_frame, (0, display_frame.shape[0]-40), 
                         (display_frame.shape[1], display_frame.shape[0]), (0, 0, 0), -1)
            cv2.putText(display_frame, status_text, (10, display_frame.shape[0]-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            cv2.imshow('License Plate Detection - SPACE to capture | ESC to exit', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):
                if last_detection:
                    detected_plate = max(detection_count.items(), key=lambda x: x[1])[0]
                    print(f"\n✓ Captured: {detected_plate} (confidence: {detection_count[detected_plate]})")
                    break
                else:
                    print("\n✗ No plate detected yet. Please position the plate in frame.")
            
            elif key == 27:
                print("\n✗ Cancelled by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return detected_plate


def test_detector():
    """Test the license plate detector"""
    detector = LicensePlateDetector()
    
    print("Testing License Plate Detector")
    print("1. From camera")
    print("2. From image file")
    
    choice = input("Enter choice: ")
    
    if choice == "1":
        plate = detector.capture_from_camera()
        if plate:
            print(f"Detected plate: {plate}")
        else:
            print("No plate detected")
    
    elif choice == "2":
        path = input("Enter image path: ")
        plate, image = detector.detect_from_image(path)
        if plate:
            print(f"Detected plate: {plate}")
            cv2.imshow("Result", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("No plate detected")


if __name__ == "__main__":
    test_detector()

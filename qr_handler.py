
import qrcode
import base64
import uuid
import hashlib
import cv2
import numpy as np
from pyzbar import pyzbar
from io import BytesIO
from datetime import datetime
import pytz
import logging
from PIL import Image

from app import db
from models import Order, QRScan

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

def generate_package_qr(order_id):
    """Generate QR code for package tracking by vendor"""
    try:
        # Create unique, secure QR data
        timestamp = datetime.now(IST).strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        qr_data = f"TRACKIT_PACKAGE_{order_id}_{timestamp}_{unique_id}"
        
        # Generate QR code with high error correction for better scanning
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        logging.info(f"Generated package QR code for order {order_id}: {qr_data}")
        return qr_data
        
    except Exception as e:
        logging.error(f"Error generating package QR code: {str(e)}")
        return None

def generate_customer_delivery_qr(order_id, customer_id):
    """Generate final delivery QR code for customer after 3rd package scan"""
    try:
        # Create unique customer delivery QR
        timestamp = datetime.now(IST).strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        qr_data = f"TRACKIT_CUSTOMER_DELIVERY_{order_id}_{customer_id}_{timestamp}_{unique_id}"
        
        # Generate QR code with highest error correction
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="darkblue", back_color="white")
        
        logging.info(f"Generated customer delivery QR code for order {order_id}: {qr_data}")
        return qr_data
        
    except Exception as e:
        logging.error(f"Error generating customer delivery QR code: {str(e)}")
        return None

def process_image_for_qr(image_data):
    """Process image using OpenCV and ZBar for real QR detection"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return {'qr_detected': False, 'error': 'Invalid image data'}
        
        # Convert to grayscale for better QR detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply image preprocessing for better QR detection
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Use ZBar to detect QR codes
        qr_codes = pyzbar.decode(enhanced)
        
        if qr_codes:
            # Get the first QR code found
            qr_code = qr_codes[0]
            qr_data = qr_code.data.decode('utf-8')
            
            # Validate QR format
            if qr_data.startswith('TRACKIT_'):
                logging.info(f"QR code detected: {qr_data}")
                return {
                    'qr_detected': True, 
                    'qr_data': qr_data,
                    'detection_method': 'OpenCV+ZBar'
                }
        
        # Try additional detection methods if ZBar fails
        # Use OpenCV's QR detector as backup
        qr_detector = cv2.QRCodeDetector()
        data, vertices_array, binary_qrcode = qr_detector.detectAndDecode(enhanced)
        
        if data and data.startswith('TRACKIT_'):
            logging.info(f"QR code detected with OpenCV: {data}")
            return {
                'qr_detected': True, 
                'qr_data': data,
                'detection_method': 'OpenCV'
            }
        
        return {'qr_detected': False, 'error': 'No valid QR code found'}
        
    except Exception as e:
        logging.error(f"Error processing image for QR: {str(e)}")
        return {'qr_detected': False, 'error': f'Processing error: {str(e)}'}

def get_qr_image_data(qr_data):
    """Convert QR data to base64 image for display"""
    try:
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        logging.error(f"Error creating QR image: {str(e)}")
        return None

def validate_qr_code(qr_data, scanned_by_user_id):
    """Validate and process QR code scan with enhanced logic"""
    try:
        # Parse QR data
        if not qr_data.startswith('TRACKIT_'):
            return {'success': False, 'error': 'Invalid QR code format.'}
        
        parts = qr_data.split('_')
        if len(parts) < 4:
            return {'success': False, 'error': 'Invalid QR code format.'}
        
        if parts[1] == 'PACKAGE':
            # Package QR: TRACKIT_PACKAGE_{order_id}_{timestamp}_{unique_id}
            order_id = int(parts[2])
            return process_package_qr_scan(qr_data, order_id, scanned_by_user_id)
            
        elif parts[1] == 'CUSTOMER' and parts[2] == 'DELIVERY':
            # Customer delivery QR: TRACKIT_CUSTOMER_DELIVERY_{order_id}_{customer_id}_{timestamp}_{unique_id}
            order_id = int(parts[3])
            return process_customer_delivery_qr_scan(qr_data, order_id, scanned_by_user_id)
            
        else:
            return {'success': False, 'error': 'Unknown QR type.'}
            
    except Exception as e:
        logging.error(f"Error validating QR code: {str(e)}")
        return {'success': False, 'error': 'Error processing QR code.'}

def process_package_qr_scan(qr_data, order_id, scanned_by_user_id):
    """Process package QR code scan by delivery partner"""
    try:
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found.'}
        
        # Verify this is the correct package QR for the order
        if order.package_qr_code != qr_data:
            return {'success': False, 'error': 'Wrong package QR code.'}
        
        # Verify scanner is the assigned delivery partner
        if order.delivery_partner_id != scanned_by_user_id:
            return {'success': False, 'error': 'Unauthorized scan.'}
        
        # Update order status based on scan count
        current_scan_count = order.qr_scan_count
        delivery_qr_generated = False
        
        if current_scan_count == 0:
            # First scan - Dispatched
            order.status = 'dispatched'
            order.dispatched_at = datetime.now(IST)
            status_message = 'Package dispatched from vendor.'
            
        elif current_scan_count == 1:
            # Second scan - In Transit
            order.status = 'in_transit'
            order.in_transit_at = datetime.now(IST)
            status_message = 'Package is now in transit.'
            
        elif current_scan_count == 2:
            # Third scan - Out for Delivery & Generate Customer Delivery QR
            order.status = 'out_for_delivery'
            order.out_for_delivery_at = datetime.now(IST)
            
            # Generate customer-specific delivery QR code
            customer_delivery_qr = generate_customer_delivery_qr(order.id, order.customer_id)
            order.delivery_qr_code = customer_delivery_qr
            delivery_qr_generated = True
            
            status_message = 'Package is out for delivery. Customer QR generated for final confirmation.'
            
        else:
            return {'success': False, 'error': 'Package QR already scanned maximum times.'}
        
        # Increment scan count
        order.qr_scan_count += 1
        
        # Record the scan
        scan_record = QRScan(
            order_id=order.id,
            scanned_by=scanned_by_user_id,
            scan_type='package',
            scan_data=qr_data
        )
        
        db.session.add(scan_record)
        db.session.commit()
        
        logging.info(f"Package QR scanned for order {order.id}, new status: {order.status}")
        
        return {
            'success': True,
            'message': status_message,
            'order': order,
            'new_status': order.status,
            'scan_count': order.qr_scan_count,
            'delivery_qr_generated': delivery_qr_generated,
            'scan_type': 'package'
        }
        
    except Exception as e:
        logging.error(f"Error processing package QR scan: {str(e)}")
        return {'success': False, 'error': 'Error processing scan.'}

def process_customer_delivery_qr_scan(qr_data, order_id, scanned_by_user_id):
    """Process customer delivery QR code scan for final confirmation"""
    try:
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found.'}
        
        # Verify this is the correct customer delivery QR for the order
        if order.delivery_qr_code != qr_data:
            return {'success': False, 'error': 'Wrong customer delivery QR code.'}
        
        # Verify scanner is the assigned delivery partner
        if order.delivery_partner_id != scanned_by_user_id:
            return {'success': False, 'error': 'Unauthorized scan.'}
        
        # Verify order is in correct status
        if order.status != 'out_for_delivery':
            return {'success': False, 'error': 'Order not ready for final delivery.'}
        
        # Update order to delivered
        order.status = 'delivered'
        order.delivered_at = datetime.now(IST)
        
        # Record the scan
        scan_record = QRScan(
            order_id=order.id,
            scanned_by=scanned_by_user_id,
            scan_type='customer_delivery',
            scan_data=qr_data
        )
        
        db.session.add(scan_record)
        db.session.commit()
        
        # Update order history for AI learning
        from ai_predictions import update_order_history
        update_order_history(order)
        
        logging.info(f"Customer delivery QR scanned for order {order.id}, status: delivered")
        
        return {
            'success': True,
            'message': 'Package delivered successfully to customer!',
            'order': order,
            'new_status': 'delivered',
            'scan_type': 'customer_delivery'
        }
        
    except Exception as e:
        logging.error(f"Error processing customer delivery QR scan: {str(e)}")
        return {'success': False, 'error': 'Error processing delivery scan.'}

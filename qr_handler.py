import qrcode
import base64
import uuid
import hashlib
from io import BytesIO
from datetime import datetime
import pytz
import logging

from app import db
from models import Order, QRScan

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

def generate_package_qr(order_id):
    """Generate QR code for package tracking"""
    try:
        # Create simpler, more reliable QR data
        qr_data = f"TRACKIT_PACKAGE_{order_id}_{uuid.uuid4().hex[:8]}"
        
        # Generate QR code with higher error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
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

def generate_delivery_qr(order_id):
    """Generate QR code for final delivery confirmation"""
    try:
        # Create simpler delivery QR data
        qr_data = f"TRACKIT_DELIVERY_{order_id}_{uuid.uuid4().hex[:8]}"
        
        # Generate QR code with higher error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        logging.info(f"Generated delivery QR code for order {order_id}: {qr_data}")
        return qr_data
        
    except Exception as e:
        logging.error(f"Error generating delivery QR code: {str(e)}")
        return None

def get_qr_image_data(qr_data):
    """Convert QR data to base64 image for display"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
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
    """Validate and process QR code scan"""
    try:
        # Parse QR data
        if not qr_data.startswith('TRACKIT_'):
            return {'success': False, 'error': 'Invalid QR code format.'}
        
        parts = qr_data.split('_')
        if len(parts) < 3:
            return {'success': False, 'error': 'Invalid QR code format.'}
        
        qr_type = parts[1]  # PACKAGE or DELIVERY
        order_id = int(parts[2])
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found.'}
        
        # Validate QR type and process accordingly
        if qr_type == 'PACKAGE':
            return process_package_qr_scan(order, qr_data, scanned_by_user_id)
        elif qr_type == 'DELIVERY':
            return process_delivery_qr_scan(order, qr_data, scanned_by_user_id)
        else:
            return {'success': False, 'error': 'Invalid QR type.'}
            
    except Exception as e:
        logging.error(f"Error validating QR code: {str(e)}")
        return {'success': False, 'error': 'Error processing QR code.'}

def process_package_qr_scan(order, qr_data, scanned_by_user_id):
    """Process package QR code scan by delivery partner"""
    try:
        # Verify this is the correct package QR for the order
        if order.package_qr_code != qr_data:
            return {'success': False, 'error': 'Wrong package QR code.'}
        
        # Verify scanner is the assigned delivery partner
        if order.delivery_partner_id != scanned_by_user_id:
            return {'success': False, 'error': 'Unauthorized scan.'}
        
        # Update order status based on scan count
        current_scan_count = order.qr_scan_count
        
        if current_scan_count == 0:
            # First scan - Dispatched
            order.status = 'dispatched'
            order.dispatched_at = datetime.now(IST)
            status_message = 'Package dispatched successfully.'
            
        elif current_scan_count == 1:
            # Second scan - In Transit
            order.status = 'in_transit'
            order.in_transit_at = datetime.now(IST)
            status_message = 'Package is now in transit.'
            
        elif current_scan_count == 2:
            # Third scan - Out for Delivery
            order.status = 'out_for_delivery'
            order.out_for_delivery_at = datetime.now(IST)
            
            # Generate delivery QR code for customer
            delivery_qr = generate_delivery_qr(order.id)
            order.delivery_qr_code = delivery_qr
            
            status_message = 'Package is out for delivery.'
            
        else:
            return {'success': False, 'error': 'QR code already scanned maximum times.'}
        
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
            'scan_count': order.qr_scan_count
        }
        
    except Exception as e:
        logging.error(f"Error processing package QR scan: {str(e)}")
        return {'success': False, 'error': 'Error processing scan.'}

def process_delivery_qr_scan(order, qr_data, scanned_by_user_id):
    """Process delivery QR code scan for final delivery confirmation"""
    try:
        # Verify this is the correct delivery QR for the order
        if order.delivery_qr_code != qr_data:
            return {'success': False, 'error': 'Wrong delivery QR code.'}
        
        # Verify scanner is the assigned delivery partner
        if order.delivery_partner_id != scanned_by_user_id:
            return {'success': False, 'error': 'Unauthorized scan.'}
        
        # Verify order is in correct status
        if order.status != 'out_for_delivery':
            return {'success': False, 'error': 'Order not ready for delivery.'}
        
        # Update order to delivered
        order.status = 'delivered'
        order.delivered_at = datetime.now(IST)
        
        # Record the scan
        scan_record = QRScan(
            order_id=order.id,
            scanned_by=scanned_by_user_id,
            scan_type='delivery',
            scan_data=qr_data
        )
        
        db.session.add(scan_record)
        db.session.commit()
        
        # Update order history for AI learning
        from ai_predictions import update_order_history
        update_order_history(order)
        
        logging.info(f"Delivery QR scanned for order {order.id}, status: delivered")
        
        return {
            'success': True,
            'message': 'Package delivered successfully!',
            'order': order,
            'new_status': 'delivered'
        }
        
    except Exception as e:
        logging.error(f"Error processing delivery QR scan: {str(e)}")
        return {'success': False, 'error': 'Error processing delivery scan.'}

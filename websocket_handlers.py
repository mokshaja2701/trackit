# TrackIt - WebSocket Event Handlers for Real-time Communication

from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} connected')
        emit('status', {'msg': f'Welcome {current_user.full_name}!'})
    else:
        logger.info('Anonymous user connected')

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} disconnected')

@socketio.on('join')
def on_join(data):
    """Join a room for real-time updates"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    if room:
        join_room(room)
        logger.info(f'User {current_user.username} joined room {room}')
        emit('status', {'msg': f'Joined {room}'}, room=room)

@socketio.on('leave')
def on_leave(data):
    """Leave a room"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    if room:
        leave_room(room)
        logger.info(f'User {current_user.username} left room {room}')
        emit('status', {'msg': f'Left {room}'}, room=room)

@socketio.on('order_update')
def handle_order_update(data):
    """Handle order status updates"""
    if not current_user.is_authenticated:
        return
    
    order_id = data.get('order_id')
    status = data.get('status')
    
    if order_id and status:
        # Emit to all relevant parties
        emit('order_status_changed', {
            'order_id': order_id,
            'status': status,
            'timestamp': data.get('timestamp'),
            'updated_by': current_user.full_name
        }, broadcast=True)
        
        logger.info(f'Order {order_id} status updated to {status} by {current_user.username}')

@socketio.on('qr_scanned')
def handle_qr_scan(data):
    """Handle QR code scan events"""
    if not current_user.is_authenticated:
        return
    
    order_id = data.get('order_id')
    scan_type = data.get('scan_type')
    
    if order_id and scan_type:
        # Emit to customer and vendor
        emit('qr_scan_update', {
            'order_id': order_id,
            'scan_type': scan_type,
            'scanned_by': current_user.full_name,
            'timestamp': data.get('timestamp')
        }, broadcast=True)
        
        logger.info(f'QR code scanned for order {order_id} by {current_user.username}')

@socketio.on('request_location')
def handle_location_request(data):
    """Handle delivery location updates"""
    if not current_user.is_authenticated or current_user.role != 'delivery_partner':
        return
    
    order_id = data.get('order_id')
    location = data.get('location')
    
    if order_id and location:
        # Emit location update to customer
        emit('location_update', {
            'order_id': order_id,
            'latitude': location.get('lat'),
            'longitude': location.get('lng'),
            'timestamp': data.get('timestamp')
        }, room=f'order_{order_id}')
        
        logger.info(f'Location update for order {order_id} from {current_user.username}')

# Error handling
@socketio.on_error_default
def default_error_handler(e):
    """Handle WebSocket errors"""
    logger.error(f'WebSocket error: {e}')
    emit('error', {'message': 'An error occurred'})
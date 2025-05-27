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

@socketio.on('join_room')
def on_join(data):
    """Join a room for real-time updates"""
    if not current_user.is_authenticated:
        return

    room = f"{current_user.role}_{current_user.id}"
    join_room(room)
    logger.info(f'User {current_user.username} joined room {room}')
    emit('status', {'msg': f'Joined room {room}'})

@socketio.on('leave_room')
def on_leave(data):
    """Leave a room"""
    if not current_user.is_authenticated:
        return

    room = f"{current_user.role}_{current_user.id}"
    leave_room(room)
    logger.info(f'User {current_user.username} left room {room}')
    emit('status', {'msg': f'Left room {room}'})

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

# Error handling
@socketio.on_error_default
def default_error_handler(e):
    """Handle WebSocket errors"""
    logger.error(f'WebSocket error: {e}')
    emit('error', {'message': 'An error occurred'})
import logging
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} connected')
        # Join user-specific room
        room = f"{current_user.role}_{current_user.id}"
        join_room(room)
        emit('status', {'msg': f'Connected as {current_user.role}'})
    else:
        logger.info('Anonymous user connected')
        emit('status', {'msg': 'Connected anonymously'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} disconnected')
        room = f"{current_user.role}_{current_user.id}"
        leave_room(room)
    else:
        logger.info('Anonymous user disconnected')

@socketio.on('join_room')
def on_join(data):
    """Handle joining rooms"""
    if current_user.is_authenticated:
        room = f"{current_user.role}_{current_user.id}"
        join_room(room)
        emit('status', {'msg': f'Joined room {room}'})
        logger.info(f'User {current_user.username} joined room {room}')

@socketio.on('leave_room')
def on_leave(data):
    """Handle leaving rooms"""
    if current_user.is_authenticated:
        room = f"{current_user.role}_{current_user.id}"
        leave_room(room)
        emit('status', {'msg': f'Left room {room}'})
        logger.info(f'User {current_user.username} left room {room}')

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

@socketio.on_error_default
def default_error_handler(e):
    """Handle WebSocket errors"""
    logger.error(f'WebSocket error: {e}')
    emit('error', {'message': 'An error occurred'})


from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
import random
import logging

from app import app, db, socketio
from models import User, Vendor, Order, QRScan, OrderHistory
from qr_handler import generate_package_qr, generate_customer_delivery_qr, validate_qr_code, process_image_for_qr
from ai_predictions import get_ai_predictions
from indian_data import get_available_vendors

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            if current_user.role == 'customer':
                return redirect(url_for('customer_dashboard'), code=302)
            elif current_user.role == 'vendor':
                return redirect(url_for('vendor_dashboard'), code=302)
            elif current_user.role == 'delivery_partner':
                return redirect(url_for('delivery_dashboard'), code=302)
        
        return redirect(url_for('login'), code=302)
    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        return redirect(url_for('login'), code=302)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome {user.full_name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page, code=302)
            
            if user.role == 'customer':
                return redirect(url_for('customer_dashboard'), code=302)
            elif user.role == 'vendor':
                return redirect(url_for('vendor_dashboard'), code=302)
            elif user.role == 'delivery_partner':
                return redirect(url_for('delivery_dashboard'), code=302)
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        address = request.form['address']
        role = request.form['role']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # If vendor, create vendor profile
        if role == 'vendor':
            business_name = request.form.get('business_name', '')
            business_type = request.form.get('business_type', '')
            
            vendor = Vendor(
                user_id=user.id,
                business_name=business_name,
                business_type=business_type
            )
            db.session.add(vendor)
            db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('Successfully logged out.', 'info')
        return redirect(url_for('login'), code=302)
    except Exception as e:
        logging.error(f"Error during logout: {str(e)}")
        flash('Error during logout. Please try again.', 'error')
        return redirect(url_for('login'), code=302)

@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer_dashboard.html', orders=orders)

@app.route('/vendor_dashboard')
@login_required
def vendor_dashboard():
    if current_user.role != 'vendor':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    pending_orders = Order.query.filter_by(vendor_id=current_user.id, status='pending').all()
    active_orders = Order.query.filter(
        Order.vendor_id == current_user.id,
        Order.status.in_(['accepted', 'dispatched', 'in_transit', 'out_for_delivery'])
    ).order_by(Order.created_at.desc()).all()
    completed_orders = Order.query.filter(
        Order.vendor_id == current_user.id,
        Order.status.in_(['delivered', 'rejected'])
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('vendor_dashboard.html', 
                         pending_orders=pending_orders,
                         active_orders=active_orders,
                         completed_orders=completed_orders)

@app.route('/delivery_dashboard')
@login_required
def delivery_dashboard():
    if current_user.role != 'delivery_partner':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    assigned_orders = Order.query.filter_by(delivery_partner_id=current_user.id).filter(
        Order.status.in_(['accepted', 'dispatched', 'in_transit', 'out_for_delivery'])
    ).order_by(Order.created_at.desc()).all()
    
    completed_orders = Order.query.filter_by(delivery_partner_id=current_user.id, status='delivered').order_by(Order.created_at.desc()).limit(10).all()
    
    # Get total completed deliveries count for this delivery partner
    total_completed_deliveries = Order.query.filter_by(delivery_partner_id=current_user.id, status='delivered').count()
    
    return render_template('delivery_dashboard.html', 
                         assigned_orders=assigned_orders,
                         completed_orders=completed_orders,
                         total_completed_deliveries=total_completed_deliveries)

@app.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    if current_user.role != 'customer':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        vendor_id = request.form.get('vendor_id')
        order_description = request.form.get('order_description', '').strip()
        window_time = request.form.get('window_time')
        delivery_speed = request.form.get('delivery_speed')
        
        # Validation
        if not vendor_id:
            flash('Please select a vendor.', 'error')
            vendors = get_available_vendors()
            predictions = None
            if current_user.can_use_ai_predictions():
                predictions = get_ai_predictions(current_user.id)
            return render_template('create_order.html', vendors=vendors, predictions=predictions)
        
        if not order_description:
            flash('Please provide order description.', 'error')
            vendors = get_available_vendors()
            predictions = None
            if current_user.can_use_ai_predictions():
                predictions = get_ai_predictions(current_user.id)
            return render_template('create_order.html', vendors=vendors, predictions=predictions)
        
        if not window_time or window_time not in ['9am-12pm', '12pm-4pm', '4pm-9pm', '9pm-9am']:
            flash('Please select a valid delivery window.', 'error')
            vendors = get_available_vendors()
            predictions = None
            if current_user.can_use_ai_predictions():
                predictions = get_ai_predictions(current_user.id)
            return render_template('create_order.html', vendors=vendors, predictions=predictions)
        
        if not delivery_speed or delivery_speed not in ['express', 'regular']:
            flash('Please select a valid delivery speed.', 'error')
            vendors = get_available_vendors()
            predictions = None
            if current_user.can_use_ai_predictions():
                predictions = get_ai_predictions(current_user.id)
            return render_template('create_order.html', vendors=vendors, predictions=predictions)
        
        # Calculate estimated amount
        base_amount = 100
        if delivery_speed == 'express':
            estimated_amount = base_amount + 50
        else:
            estimated_amount = base_amount
        
        # Create new order
        order = Order(
            customer_id=current_user.id,
            vendor_id=int(vendor_id),
            order_description=order_description,
            window_time=window_time,
            delivery_speed=delivery_speed,
            status='pending',
            estimated_amount=estimated_amount
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Emit WebSocket event for real-time update
        socketio.emit('new_order', {
            'order_id': order.id,
            'customer_name': current_user.full_name,
            'vendor_id': vendor_id,
            'description': order_description,
            'window_time': window_time,
            'delivery_speed': delivery_speed
        }, room=f'vendor_{vendor_id}')
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    vendors = get_available_vendors()
    
    # Get AI predictions if eligible
    predictions = None
    if current_user.can_use_ai_predictions():
        predictions = get_ai_predictions(current_user.id)
    
    return render_template('create_order.html', vendors=vendors, predictions=predictions)

@app.route('/order/<int:order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    if current_user.role != 'vendor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if order.status != 'pending':
        return jsonify({'error': 'Order cannot be accepted'}), 400
    
    # Update order status
    order.status = 'accepted'
    order.accepted_at = datetime.now(IST)
    
    # Generate package QR code
    qr_code = generate_package_qr(order.id)
    order.package_qr_code = qr_code
    
    # Auto-assign delivery partner
    delivery_partners = User.query.filter_by(role='delivery_partner').all()
    if delivery_partners:
        order.delivery_partner_id = random.choice(delivery_partners).id
    
    db.session.commit()
    
    # Emit WebSocket events
    socketio.emit('order_status_update', {
        'order_id': order.id,
        'status': 'accepted',
        'timestamp': order.accepted_at.strftime("%d/%m/%Y %I:%M %p"),
        'qr_code': qr_code
    }, room=f'customer_{order.customer_id}')
    
    if order.delivery_partner_id:
        socketio.emit('new_assignment', {
            'order_id': order.id,
            'customer_name': order.customer.full_name,
            'vendor_name': current_user.full_name,
            'description': order.order_description
        }, room=f'delivery_{order.delivery_partner_id}')
    
    return jsonify({'success': True, 'qr_code': qr_code, 'accepted': True})

@app.route('/order/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    if current_user.role != 'vendor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if order.status != 'pending':
        return jsonify({'error': 'Order cannot be rejected'}), 400
    
    order.status = 'rejected'
    db.session.commit()
    
    # Emit WebSocket event
    socketio.emit('order_status_update', {
        'order_id': order.id,
        'status': 'rejected',
        'timestamp': datetime.now(IST).strftime("%d/%m/%Y %I:%M %p")
    }, room=f'customer_{order.customer_id}')
    
    return jsonify({'success': True})

@app.route('/qr_scanner')
@login_required
def qr_scanner():
    if current_user.role not in ['delivery_partner', 'customer']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    return render_template('qr_scanner.html')

@app.route('/process_qr_image', methods=['POST'])
@login_required
def process_qr_image():
    """Process camera image for real QR code detection using OpenCV"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'qr_detected': False, 'error': 'No image data provided'})
        
        # Process image for QR detection
        result = process_image_for_qr(image_data)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing QR image: {str(e)}")
        return jsonify({'qr_detected': False, 'error': 'Image processing failed'})

@app.route('/scan_qr', methods=['POST'])
@login_required
def scan_qr():
    qr_data = request.json.get('qr_data')
    
    if not qr_data:
        return jsonify({'error': 'No QR data provided'}), 400
    
    # Validate and process QR code
    result = validate_qr_code(qr_data, current_user.id)
    
    if result['success']:
        order = result['order']
        
        # Emit WebSocket event for real-time update to all relevant parties
        update_data = {
            'order_id': order.id,
            'status': order.status,
            'timestamp': datetime.now(IST).strftime("%d/%m/%Y %I:%M %p"),
            'scanned_by': current_user.full_name,
            'scan_type': result.get('scan_type', 'unknown')
        }
        
        # Add delivery QR if generated
        if result.get('delivery_qr_generated'):
            update_data['delivery_qr_code'] = order.delivery_qr_code
        
        # Broadcast to customer
        socketio.emit('order_status_update', update_data, room=f'customer_{order.customer_id}')
        
        # Broadcast to vendor
        socketio.emit('order_status_update', update_data, room=f'vendor_{order.vendor_id}')
        
        # Broadcast to delivery partner
        if order.delivery_partner_id:
            socketio.emit('order_status_update', update_data, room=f'delivery_{order.delivery_partner_id}')
        
        # Broadcast to all connected clients for general updates
        socketio.emit('global_order_update', {
            'order_id': order.id,
            'status': order.status,
            'timestamp': update_data['timestamp']
        }, broadcast=True)
    
    return jsonify(result)

# WebSocket event handlers
@socketio.on('join_room')
def on_join(data):
    if current_user.is_authenticated:
        room = f"{current_user.role}_{current_user.id}"
        join_room(room)
        emit('status', {'msg': f'Joined room {room}'})

@socketio.on('leave_room')
def on_leave(data):
    if current_user.is_authenticated:
        room = f"{current_user.role}_{current_user.id}"
        leave_room(room)
        emit('status', {'msg': f'Left room {room}'})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

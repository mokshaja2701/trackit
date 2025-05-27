from datetime import datetime
import pytz
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    role = db.Column(db.Enum('customer', 'vendor', 'delivery_partner', name='user_roles'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    successful_orders = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    
    # Relationships
    customer_orders = db.relationship('Order', foreign_keys='Order.customer_id', backref='customer', lazy='dynamic')
    vendor_orders = db.relationship('Order', foreign_keys='Order.vendor_id', backref='vendor', lazy='dynamic')
    delivery_orders = db.relationship('Order', foreign_keys='Order.delivery_partner_id', backref='delivery_partner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_use_ai_predictions(self):
        return self.role == 'customer' and self.successful_orders >= 5
    
    def __repr__(self):
        return f'<User {self.username}>'

class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    user = db.relationship('User', backref='vendor_profile')
    
    def __repr__(self):
        return f'<Vendor {self.business_name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    delivery_partner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    order_description = db.Column(db.Text, nullable=False)
    window_time = db.Column(db.String(20), nullable=False)  # '30min', '1hour', '2hour', 'flexible'
    delivery_speed = db.Column(db.String(20), nullable=False)  # 'express', 'standard', 'economy'
    
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'dispatched', 'in_transit', 'out_for_delivery', 'delivered', name='order_status'), default='pending')
    
    package_qr_code = db.Column(db.String(255), nullable=True)
    delivery_qr_code = db.Column(db.String(255), nullable=True)
    qr_scan_count = db.Column(db.Integer, default=0)
    
    estimated_amount = db.Column(db.Float, nullable=True)
    final_amount = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    accepted_at = db.Column(db.DateTime, nullable=True)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    in_transit_at = db.Column(db.DateTime, nullable=True)
    out_for_delivery_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    def get_status_display(self):
        status_map = {
            'pending': 'Pending',
            'accepted': 'Accepted',
            'rejected': 'Rejected',
            'dispatched': 'Dispatched',
            'in_transit': 'In Transit',
            'out_for_delivery': 'Out for Delivery',
            'delivered': 'Delivered'
        }
        return status_map.get(self.status, self.status.title())
    
    def get_formatted_created_at(self):
        return self.created_at.strftime("%d/%m/%Y %I:%M %p")
    
    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'

class QRScan(db.Model):
    __tablename__ = 'qr_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    scanned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scan_type = db.Column(db.Enum('package', 'delivery', name='scan_types'), nullable=False)
    scan_data = db.Column(db.String(255), nullable=False)
    scanned_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    order = db.relationship('Order', backref='qr_scans')
    scanner = db.relationship('User', backref='scans_performed')
    
    def __repr__(self):
        return f'<QRScan {self.id} - {self.scan_type}>'

class OrderHistory(db.Model):
    __tablename__ = 'order_history'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    window_time = db.Column(db.String(20), nullable=False)
    delivery_speed = db.Column(db.String(20), nullable=False)
    order_day = db.Column(db.String(10), nullable=False)  # 'monday', 'tuesday', etc.
    order_hour = db.Column(db.Integer, nullable=False)
    was_successful = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    customer = db.relationship('User', foreign_keys=[customer_id], backref='order_patterns')
    vendor_user = db.relationship('User', foreign_keys=[vendor_id])
    
    def __repr__(self):
        return f'<OrderHistory {self.id} - {self.customer_id}>'

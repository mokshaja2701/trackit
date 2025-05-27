import random
from datetime import datetime, timedelta
import pytz
from werkzeug.security import generate_password_hash
import uuid  # Import UUID
from app import db
from models import User, Vendor, Order, OrderHistory, QRScan  # Import QRScan

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

# Authentic Indian data
INDIAN_NAMES = [
    # Customer names
    ("Aarav Mehta", "aarav.mehta", "aarav.mehta@gmail.com", "+91 9876543210", "Flat 502, Raj Residency, Andheri West, Mumbai – 400058"),
    ("Priya Sharma", "priya.sharma", "priya.sharma@yahoo.in", "+91 9123456789", "B-42, DLF Phase 2, Sector 25, Gurgaon – 122002"),
    ("Rohan Iyer", "rohan.iyer", "rohan.iyer@rediffmail.com", "+91 8765432109", "No. 15, Brigade Road, Bangalore – 560001"),
    ("Kavya Reddy", "kavya.reddy", "kavya.reddy@hotmail.com", "+91 7654321098", "Plot 78, Jubilee Hills, Hyderabad – 500033"),
    ("Arjun Singh", "arjun.singh", "arjun.singh@gmail.com", "+91 9987654321", "House 23, Sector 14, Chandigarh – 160014"),
    ("Ananya Gupta", "ananya.gupta", "ananya.gupta@gmail.com", "+91 8876543210", "C-45, South Extension, New Delhi – 110049"),
    ("Vikram Agarwal", "vikram.agarwal", "vikram.agarwal@gmail.com", "+91 9765432108", "12/A, Park Street, Kolkata – 700016"),
    ("Shreya Patel", "shreya.patel", "shreya.patel@gmail.com", "+91 8654321097", "Flat 301, Vastrapur, Ahmedabad – 380015"),
    ("Karan Malhotra", "karan.malhotra", "karan.malhotra@gmail.com", "+91 7543210986", "Villa 45, Koregaon Park, Pune – 411001"),
    ("Rhea Kapoor", "rhea.kapoor", "rhea.kapoor@gmail.com", "+91 9432109876", "Apartment 12B, Bandra East, Mumbai – 400051"),
    ("Deepak Kumar", "deepak.kumar", "deepak.kumar@gmail.com", "+91 8321098765", "House 12, Sector 22, Noida – 201301"),
    ("Meera Joshi", "meera.joshi", "meera.joshi@gmail.com", "+91 7210987654", "Plot 34, Banjara Hills, Hyderabad – 500034"),
    ("Rajesh Verma", "rajesh.verma", "rajesh.verma@gmail.com", "+91 9109876543", "Flat 15, Malviya Nagar, Jaipur – 302017"),
    ("Sunita Das", "sunita.das", "sunita.das@gmail.com", "+91 8098765432", "Building 7, Salt Lake, Kolkata – 700064"),
    ("Manish Tiwari", "manish.tiwari", "manish.tiwari@gmail.com", "+91 7987654321", "House 89, Gomti Nagar, Lucknow – 226010"),
    ("Pooja Nair", "pooja.nair", "pooja.nair@gmail.com", "+91 9876543210", "Flat 204, Marine Drive, Kochi – 682031"),
    ("Amit Saxena", "amit.saxena", "amit.saxena@gmail.com", "+91 8765432109", "Plot 56, Civil Lines, Allahabad – 211001"),
    ("Neha Chandra", "neha.chandra", "neha.chandra@gmail.com", "+91 7654321098", "House 78, Model Town, Ludhiana – 141002"),
    ("Sanjay Yadav", "sanjay.yadav", "sanjay.yadav@gmail.com", "+91 9543210987", "Flat 123, Vaishali, Ghaziabad – 201010"),
    ("Ritu Singh", "ritu.singh", "ritu.singh@gmail.com", "+91 8432109876", "Building 45, Kankurgachi, Kolkata – 700054")
]

VENDOR_DATA = [
    ("Smart Stationery Hub", "smart.stationery", "contact@smartstationery.in", "+91 9876501234", "Shop 15, Main Market, Karol Bagh, New Delhi – 110005", "Stationery"),
    ("Sports Zone India", "sports.zone", "info@sportszone.com", "+91 8765401239", "Ground Floor, Sports Complex, Vastrapur, Ahmedabad – 380015", "Sports"),
    ("Beauty Palace Cosmetics", "beauty.palace", "orders@beautypalace.in", "+91 7654301238", "56, Commercial Street, Bangalore – 560001", "Cosmetics"),
    ("Royal Furniture House", "royal.furniture", "sales@royalfurniture.co.in", "+91 9543201987", "Unit 12, Furniture Market, Mumbai – 400013", "Furniture"),
    ("Tech Gadgets Pro", "tech.gadgets", "support@techgadgets.in", "+91 8432109876", "Electronics Hub, Sector 19, Faridabad – 121002", "Electronics")
]

DELIVERY_PARTNERS = [
    ("Rahul Kumar", "rahul.delivery", "rahul.delivery@trackit.in", "+91 9876512345", "Delivery Hub A, Gurgaon – 122001"),
    ("Suresh Yadav", "suresh.delivery", "suresh.delivery@trackit.in", "+91 8765412340", "Delivery Hub B, Mumbai – 400001"),
    ("Amit Thakur", "amit.delivery", "amit.delivery@trackit.in", "+91 7654312389", "Delivery Hub C, Bangalore – 560001"),
    ("Deepak Sharma", "deepak.delivery", "deepak.delivery@trackit.in", "+91 9543212876", "Delivery Hub D, Delhi – 110001"),
    ("Rajesh Singh", "rajesh.delivery", "rajesh.delivery@trackit.in", "+91 8432112765", "Delivery Hub E, Pune – 411001")
]

WINDOW_TIMES = ['9am-12pm', '12pm-4pm', '4pm-9pm', '9pm-9am']
DELIVERY_SPEEDS = ['express', 'regular']

ORDER_DESCRIPTIONS = [
    "Set of 10 ballpoint pens, A4 notebooks (5 pieces), calculator",
    "Football, cricket bat, sports shoes size 9, water bottle",
    "Face cream, lipstick (red shade), nail polish, foundation",
    "Wooden study table, office chair, table lamp",
    "Wireless earbuds, mobile phone case, charging cable",
    "Art supplies - colors, brushes, drawing sheets, sketch pens",
    "Gym equipment - dumbbells 5kg, yoga mat, resistance bands",
    "Makeup kit - eyeshadow palette, mascara, compact powder",
    "Dining table set for 4 people, wooden chairs",
    "Laptop stand, wireless mouse, keyboard, screen cleaner"
]

# Reformat the data to fit the desired structure
INDIAN_CUSTOMERS = []
for name, username, email, phone, address in INDIAN_NAMES:
    INDIAN_CUSTOMERS.append({
        "full_name": name,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address
    })

INDIAN_VENDORS = []
for name, username, email, phone, address, business_type in VENDOR_DATA:
    INDIAN_VENDORS.append({
        "full_name": f"{name} Owner",
        "business_name": name,
        "business_type": business_type,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address
    })

INDIAN_DELIVERY_PARTNERS = []
for name, username, email, phone, address in DELIVERY_PARTNERS:
    INDIAN_DELIVERY_PARTNERS.append({
        "full_name": name,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address
    })

INDIAN_ORDER_DESCRIPTIONS = ORDER_DESCRIPTIONS  # Use the original descriptions list

def initialize_mock_data():
    """Initialize mock data with authentic Indian information"""
    print("Initializing mock data with authentic Indian information...")

    # Clear existing data
    OrderHistory.query.delete()
    QRScan.query.delete()
    Order.query.delete()
    Vendor.query.delete()
    User.query.delete()
    db.session.commit()

    # Create customers
    customers = []
    for i, customer_data in enumerate(INDIAN_CUSTOMERS):
        user = User(
            username=customer_data['username'],
            email=customer_data['email'],
            full_name=customer_data['full_name'],
            phone=customer_data['phone'],
            address=customer_data['address'],
            role='customer'
        )
        user.set_password('password123')
        customers.append(user)
        db.session.add(user)

    # Create vendors
    vendors = []
    for i, vendor_data in enumerate(INDIAN_VENDORS):
        user = User(
            username=vendor_data['username'],
            email=vendor_data['email'],
            full_name=vendor_data['full_name'],
            phone=vendor_data['phone'],
            address=vendor_data['address'],
            role='vendor'
        )
        user.set_password('vendor123')
        vendors.append(user)
        db.session.add(user)

    # Create delivery partners with extensive history
    delivery_partners = []
    for i, delivery_data in enumerate(INDIAN_DELIVERY_PARTNERS):
        user = User(
            username=delivery_data['username'],
            email=delivery_data['email'],
            full_name=delivery_data['full_name'],
            phone=delivery_data['phone'],
            address=delivery_data['address'],
            role='delivery_partner'
        )
        user.set_password('delivery123')
        delivery_partners.append(user)
        db.session.add(user)

    # Commit users first to get IDs
    db.session.commit()

    # Now create vendor profiles with proper user IDs
    for vendor_user in vendors:
        vendor_data = next(v for v in INDIAN_VENDORS if v['username'] == vendor_user.username)
        vendor = Vendor(
            user_id=vendor_user.id,
            business_name=vendor_data['business_name'],
            business_type=vendor_data['business_type']
        )
        db.session.add(vendor)
    
    db.session.commit()

    print("Creating extensive order history for delivery partners...")

    # Create comprehensive order history with focus on delivery partners
    for customer in customers:
        # Create 15 completed orders for each customer (300 total orders)
        for order_num in range(15):
            vendor = random.choice(vendors)
            delivery_partner = random.choice(delivery_partners)

            # Create realistic order dates (last 6 months)
            days_ago = random.randint(1, 180)
            order_date = datetime.now(IST) - timedelta(days=days_ago)

            order = Order(
                customer_id=customer.id,
                vendor_id=vendor.id,
                delivery_partner_id=delivery_partner.id,
                order_description=random.choice(INDIAN_ORDER_DESCRIPTIONS),
                window_time=random.choice(['9am-12pm', '12pm-4pm', '4pm-9pm', '9pm-9am']),
                delivery_speed=random.choice(['express', 'regular']),
                status='delivered',
                estimated_amount=random.randint(100, 500),
                qr_scan_count=3,
                created_at=order_date,
                accepted_at=order_date + timedelta(minutes=random.randint(5, 30)),
                dispatched_at=order_date + timedelta(hours=random.randint(1, 4)),
                in_transit_at=order_date + timedelta(hours=random.randint(2, 6)),
                out_for_delivery_at=order_date + timedelta(hours=random.randint(4, 8)),
                delivered_at=order_date + timedelta(hours=random.randint(6, 12))
            )

            # Generate QR codes
            from qr_handler import generate_package_qr, generate_customer_delivery_qr
            order.package_qr_code = generate_package_qr(order.id)
            order.delivery_qr_code = generate_customer_delivery_qr(order.id, customer.id)

            db.session.add(order)

            # Create QR scan records for completed orders
            scan_timestamps = [
                order.dispatched_at,
                order.in_transit_at, 
                order.out_for_delivery_at,
                order.delivered_at
            ]

            scan_types = ['package', 'package', 'package', 'customer_delivery']
            scan_data_prefixes = ['PACKAGE', 'PACKAGE', 'PACKAGE', 'CUSTOMER_DELIVERY']

            for scan_idx, (scan_time, scan_type, scan_prefix) in enumerate(zip(scan_timestamps, scan_types, scan_data_prefixes)):
                scan_record = QRScan(
                    order_id=order.id,
                    scanned_by=delivery_partner.id,
                    scan_type=scan_type,
                    scan_data=f"TRACKIT_{scan_prefix}_{order.id}_{scan_time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
                    scanned_at=scan_time
                )
                db.session.add(scan_record)

            # Create order history for AI
            history = OrderHistory(
                customer_id=customer.id,
                vendor_id=vendor.id,
                window_time=order.window_time,
                delivery_speed=order.delivery_speed,
                order_day=order.created_at.strftime('%A').lower(),
                order_hour=order.created_at.hour,
                was_successful=True
            )
            db.session.add(history)

    print("Creating additional recent completed orders for delivery partners...")

    # Create additional recent orders specifically for delivery partners
    for delivery_partner in delivery_partners:
        # Each delivery partner gets 5-10 additional recent completed orders
        additional_orders = random.randint(5, 10)
        for i in range(additional_orders):
            customer = random.choice(customers)
            vendor = random.choice(vendors)

            # Recent orders (last 30 days)
            days_ago = random.randint(1, 30)
            order_date = datetime.now(IST) - timedelta(days=days_ago)

            order = Order(
                customer_id=customer.id,
                vendor_id=vendor.id,
                delivery_partner_id=delivery_partner.id,
                order_description=random.choice(INDIAN_ORDER_DESCRIPTIONS),
                window_time=random.choice(['9am-12pm', '12pm-4pm', '4pm-9pm', '9pm-9am']),
                delivery_speed=random.choice(['express', 'regular']),
                status='delivered',
                estimated_amount=random.randint(100, 500),
                qr_scan_count=3,
                created_at=order_date,
                accepted_at=order_date + timedelta(minutes=random.randint(5, 30)),
                dispatched_at=order_date + timedelta(hours=random.randint(1, 4)),
                in_transit_at=order_date + timedelta(hours=random.randint(2, 6)),
                out_for_delivery_at=order_date + timedelta(hours=random.randint(4, 8)),
                delivered_at=order_date + timedelta(hours=random.randint(6, 12))
            )

            # Generate QR codes
            from qr_handler import generate_package_qr, generate_customer_delivery_qr
            order.package_qr_code = generate_package_qr(order.id)
            order.delivery_qr_code = generate_customer_delivery_qr(order.id, customer.id)

            db.session.add(order)

    print("Creating sample current orders...")

    # Create some current orders in various states
    for i in range(20):
        customer = random.choice(customers)
        vendor = random.choice(vendors)
        delivery_partner = random.choice(delivery_partners)

        status_options = ['pending', 'accepted', 'dispatched', 'in_transit', 'out_for_delivery']
        status = random.choice(status_options)

        order = Order(
            customer_id=customer.id,
            vendor_id=vendor.id,
            delivery_partner_id=delivery_partner.id if status != 'pending' else None,
            order_description=random.choice(INDIAN_ORDER_DESCRIPTIONS),
            window_time=random.choice(['9am-12pm', '12pm-4pm', '4pm-9pm', '9pm-9am']),
            delivery_speed=random.choice(['express', 'regular']),
            status=status,
            estimated_amount=random.randint(100, 500),
            qr_scan_count=0 if status == 'pending' else random.randint(0, 2)
        )

        # Set timestamps based on status
        if status != 'pending':
            order.accepted_at = datetime.now(IST) - timedelta(hours=random.randint(1, 24))
            from qr_handler import generate_package_qr
            order.package_qr_code = generate_package_qr(order.id)

        if status in ['dispatched', 'in_transit', 'out_for_delivery']:
            order.dispatched_at = order.accepted_at + timedelta(hours=random.randint(1, 4))
            order.qr_scan_count = max(1, order.qr_scan_count)

        if status in ['in_transit', 'out_for_delivery']:
            order.in_transit_at = order.dispatched_at + timedelta(hours=random.randint(1, 3))
            order.qr_scan_count = max(2, order.qr_scan_count)

        if status == 'out_for_delivery':
            order.out_for_delivery_at = order.in_transit_at + timedelta(hours=random.randint(1, 2))
            order.qr_scan_count = 3
            from qr_handler import generate_customer_delivery_qr
            order.delivery_qr_code = generate_customer_delivery_qr(order.id, customer.id)

        db.session.add(order)

    db.session.commit()

    # Calculate and display delivery partner statistics
    print("\nDelivery Partner Statistics:")
    for dp in delivery_partners:
        total_completed = Order.query.filter_by(delivery_partner_id=dp.id, status='delivered').count()
        recent_completed = Order.query.filter(
            Order.delivery_partner_id == dp.id,
            Order.status == 'delivered',
            Order.delivered_at >= datetime.now(IST) - timedelta(days=30)
        ).count()
        print(f"{dp.full_name}: {total_completed} total completed ({recent_completed} in last 30 days)")

    print(f"\nMock data initialization completed successfully!")
    print(f"Created {len(customers)} customers, {len(vendors)} vendors, {len(delivery_partners)} delivery partners")
    print("All customers have 15 successful orders and can use AI recommendations")
    print("Each delivery partner has 20-25 completed deliveries with full QR scan history")
    print("Sample login credentials:")
    print("Customer: aarav.mehta / password123")
    print("Vendor: smart.stationery / vendor123")
    print("Delivery: rahul.delivery / delivery123")

def get_available_vendors():
    """Get list of available vendors for order placement"""
    try:
        vendors = db.session.query(User, Vendor).join(Vendor, User.id == Vendor.user_id).filter(
            User.role == 'vendor',
            User.is_active == True,
            Vendor.is_active == True
        ).all()

        vendor_list = []
        for user, vendor_profile in vendors:
            vendor_list.append({
                'id': user.id,
                'business_name': vendor_profile.business_name,
                'business_type': vendor_profile.business_type,
                'address': user.address,
                'phone': user.phone
            })

        return vendor_list

    except Exception as e:
        print(f"Error getting vendors: {str(e)}")
        return []

def get_window_time_options():
    """Get available window time options"""
    return [
        {'value': '9am-12pm', 'label': '9 AM - 12 PM (Morning)'},
        {'value': '12pm-4pm', 'label': '12 PM - 4 PM (Afternoon)'},
        {'value': '4pm-9pm', 'label': '4 PM - 9 PM (Evening)'},
        {'value': '9pm-9am', 'label': '9 PM - 9 AM (Night/Early Morning)'}
    ]

def get_delivery_speed_options():
    """Get available delivery speed options"""
    return [
        {'value': 'express', 'label': 'Express - Same Day Delivery (+₹50)'},
        {'value': 'regular', 'label': 'Regular - 1-7 Days (Standard Rate)'}
    ]

# WebSocket handlers for real-time updates
def create_websocket_handlers():
    """Create WebSocket event handlers for real-time communication"""
    from flask_socketio import join_room, leave_room
    from app import socketio
    from flask_login import current_user

    @socketio.on('join_room')
    def on_join(data):
        if current_user.is_authenticated:
            room = f"{current_user.role}_{current_user.id}"
            join_room(room)
            print(f"User {current_user.username} joined room {room}")

    @socketio.on('leave_room')
    def on_leave(data):
        if current_user.is_authenticated:
            room = f"{current_user.role}_{current_user.id}"
            leave_room(room)
            print(f"User {current_user.username} left room {room}")
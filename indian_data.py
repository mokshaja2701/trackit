
import random
from datetime import datetime, timedelta
import pytz
from werkzeug.security import generate_password_hash

from app import db
from models import User, Vendor, Order, OrderHistory

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

def initialize_mock_data():
    """Initialize the database with authentic Indian mock data"""
    try:
        # Check if data already exists
        if User.query.first():
            return
        
        print("Initializing mock data with authentic Indian information...")
        
        # Create customers
        customers = []
        for i, (name, username, email, phone, address) in enumerate(INDIAN_NAMES):
            user = User(
                username=username,
                email=email,
                full_name=name,
                phone=phone,
                address=address,
                role='customer',
                successful_orders=10  # All customers have 10 successful orders
            )
            user.set_password('password123')
            customers.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Create vendors
        vendors = []
        vendor_profiles = []
        for name, username, email, phone, address, business_type in VENDOR_DATA:
            user = User(
                username=username,
                email=email,
                full_name=f"{name} Owner",
                phone=phone,
                address=address,
                role='vendor'
            )
            user.set_password('vendor123')
            vendors.append(user)
            db.session.add(user)
            db.session.commit()
            
            vendor_profile = Vendor(
                user_id=user.id,
                business_name=name,
                business_type=business_type
            )
            vendor_profiles.append(vendor_profile)
            db.session.add(vendor_profile)
        
        db.session.commit()
        
        # Create delivery partners
        delivery_partners = []
        for name, username, email, phone, address in DELIVERY_PARTNERS:
            user = User(
                username=username,
                email=email,
                full_name=name,
                phone=phone,
                address=address,
                role='delivery_partner'
            )
            user.set_password('delivery123')
            delivery_partners.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Create order history for AI training (200 successful orders total)
        print("Creating order history for AI training...")
        
        for customer in customers:
            # Create 10 orders per customer (200 total orders)
            for i in range(10):
                vendor = random.choice(vendors)
                
                # Create realistic order timing
                days_ago = random.randint(1, 180)
                order_time = datetime.now(IST) - timedelta(days=days_ago)
                
                # Create order history
                history = OrderHistory(
                    customer_id=customer.id,
                    vendor_id=vendor.id,
                    window_time=random.choice(WINDOW_TIMES),
                    delivery_speed=random.choice(DELIVERY_SPEEDS),
                    order_day=order_time.strftime('%A').lower(),
                    order_hour=order_time.hour,
                    was_successful=True,
                    created_at=order_time
                )
                db.session.add(history)
                
                # Also create actual orders for some recent history
                if i < 5:  # Create 5 actual orders per customer
                    order = Order(
                        customer_id=customer.id,
                        vendor_id=vendor.id,
                        order_description=random.choice(ORDER_DESCRIPTIONS),
                        window_time=history.window_time,
                        delivery_speed=history.delivery_speed,
                        status='delivered',
                        estimated_amount=random.uniform(150, 1500),
                        final_amount=random.uniform(150, 1500),
                        created_at=order_time,
                        delivered_at=order_time + timedelta(days=random.randint(1, 3))
                    )
                    db.session.add(order)
        
        db.session.commit()
        
        # Create some sample current orders
        print("Creating sample current orders...")
        
        for i in range(5):
            customer = random.choice(customers)
            vendor = random.choice(vendors)
            delivery_partner = random.choice(delivery_partners)
            
            order = Order(
                customer_id=customer.id,
                vendor_id=vendor.id,
                delivery_partner_id=delivery_partner.id,
                order_description=random.choice(ORDER_DESCRIPTIONS),
                window_time=random.choice(WINDOW_TIMES),
                delivery_speed=random.choice(DELIVERY_SPEEDS),
                status=random.choice(['pending', 'accepted', 'dispatched']),
                estimated_amount=random.uniform(150, 1500)
            )
            db.session.add(order)
        
        db.session.commit()
        
        print("Mock data initialization completed successfully!")
        print(f"Created {len(customers)} customers, {len(vendors)} vendors, {len(delivery_partners)} delivery partners")
        print("All customers have 10 successful orders and can use AI recommendations")
        print("Sample login credentials:")
        print("Customer: aarav.mehta / password123")
        print("Vendor: smart.stationery / vendor123")
        print("Delivery: rahul.delivery / delivery123")
        
    except Exception as e:
        print(f"Error initializing mock data: {str(e)}")
        db.session.rollback()

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

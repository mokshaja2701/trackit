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
    ("Rhea Kapoor", "rhea.kapoor", "rhea.kapoor@gmail.com", "+91 9432109876", "Apartment 12B, Bandra East, Mumbai – 400051")
]

VENDOR_DATA = [
    ("Shree Ganesh Mart", "shree.ganesh", "contact@shreeganeshmart.in", "+91 9876501234", "Shop 15, Main Bazaar, Karol Bagh, New Delhi – 110005", "Groceries"),
    ("Patel Groceries & More", "patel.groceries", "info@patelgroceries.com", "+91 8765401239", "Ground Floor, Commercial Complex, Vastrapur, Ahmedabad – 380015", "Groceries"),
    ("Royal Rajasthani Foods", "royal.rajasthani", "orders@royalrajasthani.in", "+91 7654301238", "56, MI Road, Jaipur – 302001", "Restaurant"),
    ("Mumbai Express Kitchen", "mumbai.express", "kitchen@mumbaiexpress.co.in", "+91 9543201987", "Unit 12, Food Court, Phoenix Mall, Mumbai – 400013", "Restaurant"),
    ("Fresh Farm Vegetables", "fresh.farm", "fresh@farmveggies.in", "+91 8432109876", "Mandi Area, Sector 19, Faridabad – 121002", "Fresh Produce")
]

DELIVERY_PARTNERS = [
    ("Rahul Kumar", "rahul.delivery", "rahul.delivery@trackit.in", "+91 9876512345", "Delivery Hub A, Gurgaon – 122001"),
    ("Suresh Yadav", "suresh.delivery", "suresh.delivery@trackit.in", "+91 8765412340", "Delivery Hub B, Mumbai – 400001"),
    ("Amit Thakur", "amit.delivery", "amit.delivery@trackit.in", "+91 7654312389", "Delivery Hub C, Bangalore – 560001"),
    ("Deepak Sharma", "deepak.delivery", "deepak.delivery@trackit.in", "+91 9543212876", "Delivery Hub D, Delhi – 110001"),
    ("Rajesh Singh", "rajesh.delivery", "rajesh.delivery@trackit.in", "+91 8432112765", "Delivery Hub E, Pune – 411001")
]

WINDOW_TIMES = ['30min', '1hour', '2hour', 'flexible']
DELIVERY_SPEEDS = ['express', 'standard', 'economy']

ORDER_DESCRIPTIONS = [
    "2 किलो चावल, 1 किलो दाल, 500 ग्राम चीनी (2kg rice, 1kg dal, 500g sugar)",
    "सब्जी का पैकेट - आलू, प्याज, टमाटर (Vegetable pack - potatoes, onions, tomatoes)",
    "पंजाबी थाली - रोटी, दाल, सब्जी, चावल (Punjabi thali - roti, dal, sabzi, rice)",
    "दूध, दही, पनीर और मक्खन (Milk, curd, paneer and butter)",
    "मिक्स फ्रूट्स - सेब, केला, संतरा (Mixed fruits - apples, bananas, oranges)",
    "मसाला पैकेट - हल्दी, धनिया, लाल मिर्च (Spice pack - turmeric, coriander, red chili)",
    "चाय पत्ती, चीनी, बिस्कुट (Tea leaves, sugar, biscuits)",
    "बिरयानी स्पेशल - चिकन बिरयानी विथ रायता (Biryani special - chicken biryani with raita)",
    "साउथ इंडियन मील - इडली, सांभर, चटनी (South Indian meal - idli, sambar, chutney)",
    "गुजराती थाली - रोटी, दाल, सब्जी, ढोकला (Gujarati thali - roti, dal, sabzi, dhokla)"
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
                successful_orders=random.randint(5, 15)  # Ensure AI eligibility
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
        
        # Create order history for AI training (100 successful orders)
        print("Creating order history for AI training...")
        
        for customer in customers:
            # Create 10 orders per customer
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
        print("Sample login credentials:")
        print("Customer: aarav.mehta / password123")
        print("Vendor: shree.ganesh / vendor123")
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
    """Get available window time options with Hindi translations"""
    return [
        {'value': '30min', 'label': '30 मिनट में (30 minutes)'},
        {'value': '1hour', 'label': '1 घंटे में (1 hour)'},
        {'value': '2hour', 'label': '2 घंटे में (2 hours)'},
        {'value': 'flexible', 'label': 'लचीला समय (Flexible timing)'}
    ]

def get_delivery_speed_options():
    """Get available delivery speed options with Hindi translations"""
    return [
        {'value': 'express', 'label': 'तेज़ डिलीवरी (Express) - ₹50 extra'},
        {'value': 'standard', 'label': 'सामान्य डिलीवरी (Standard)'},
        {'value': 'economy', 'label': 'मितव्यी डिलीवरी (Economy) - ₹20 discount'}
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

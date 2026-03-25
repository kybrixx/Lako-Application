from flask import Flask, send_from_directory, request, jsonify, session
from flask_cors import CORS
import os
import sqlite3
import secrets
import hashlib
import uuid
import json
from datetime import datetime, date, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'lako-super-secret-key-2026'
CORS(app, supports_credentials=True)

# Get the absolute path to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define paths to different frontend folders
CUSTOMER_FRONTEND = os.path.join(BASE_DIR, 'customer', 'frontend')
VENDOR_FRONTEND = os.path.join(BASE_DIR, 'vendor', 'frontend')
DEV_FRONTEND = os.path.join(BASE_DIR, 'dev', 'frontend')

DATABASE = os.path.join(os.path.dirname(__file__), 'lako.db')

# ============= DATABASE FUNCTIONS =============
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # ============= USERS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            device_id TEXT UNIQUE,
            user_type TEXT DEFAULT 'customer',
            eula_accepted INTEGER DEFAULT 0,
            eula_accepted_at TIMESTAMP,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============= VENDORS TABLE (for customer view) =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            category TEXT,
            description TEXT,
            logo_thumbnail TEXT,
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============= POSTS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            product_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            post_type TEXT DEFAULT 'text',
            rating INTEGER,
            image_thumbnail TEXT,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')
    
    # ============= COMMENTS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parent_id INTEGER,
            content TEXT NOT NULL,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_id) REFERENCES comments(id)
        )
    ''')
    
    # ============= VOTES TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            comment_id INTEGER,
            vote_type INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (comment_id) REFERENCES comments(id),
            UNIQUE(user_id, post_id, comment_id)
        )
    ''')
    
    # ============= ACTIVITIES TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            activity_type TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')
    
    # ============= SHORTLIST TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shortlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            UNIQUE(user_id, vendor_id)
        )
    ''')
    
    # ============= EULA ACCEPTANCE TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eula_acceptance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ============= VENDOR BUSINESS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_business (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            mayor_permit TEXT UNIQUE NOT NULL,
            business_address TEXT NOT NULL,
            business_phone TEXT,
            business_email TEXT,
            business_hours TEXT,
            description TEXT,
            logo_url TEXT,
            cover_url TEXT,
            latitude REAL,
            longitude REAL,
            category TEXT,
            is_open INTEGER DEFAULT 1,
            verification_status TEXT DEFAULT 'pending',
            service_radius INTEGER DEFAULT 10,
            views_today INTEGER DEFAULT 0,
            views_week INTEGER DEFAULT 0,
            views_month INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ============= VENDOR PRODUCTS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            moq INTEGER,
            category TEXT,
            image_url TEXT,
            is_visible INTEGER DEFAULT 1,
            review_count INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            shares INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')
    
    # ============= VENDOR ANALYTICS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            views INTEGER DEFAULT 0,
            searches INTEGER DEFAULT 0,
            reviews_count INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            UNIQUE(vendor_id, date)
        )
    ''')
    
    # ============= SAMPLE REQUESTS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sample_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            product_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            pickup_location TEXT,
            preferred_date TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (product_id) REFERENCES vendor_products(id)
        )
    ''')
    
    # ============= VENDOR MESSAGES TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_from_vendor INTEGER DEFAULT 0,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (customer_id) REFERENCES users(id)
        )
    ''')
    
    # ============= REVIEW REPLIES TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS review_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            reply TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES posts(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')
    
    # ============= DEV ADMIN TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dev_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============= SYSTEM LOGS TABLE =============
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES dev_admins(id)
        )
    ''')
    
    # Create default dev admin if none exists
    cursor.execute("SELECT id FROM dev_admins LIMIT 1")
    if not cursor.fetchone():
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(('lako2026' + salt).encode()).hexdigest()
        cursor.execute('''
            INSERT INTO dev_admins (username, password_hash, salt, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('lako_dev', password_hash, salt, 'Lako Master Developer', 'super_admin'))
        print("Default Dev Admin created: username='lako_dev', password='lako2026'")
    
    conn.commit()
    conn.close()
    print("Database initialized - Supports Customer, Vendor, and Dev Admin apps")

# Initialize database
with app.app_context():
    init_db()

# ============= HELPER FUNCTIONS =============
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def verify_password(password, salt, password_hash):
    return password_hash == hashlib.sha256((password + salt).encode()).hexdigest()

def get_or_create_device_id():
    return str(uuid.uuid4())

def check_eula(device_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM eula_acceptance WHERE device_id = ?", (device_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def update_vendor_analytics(vendor_id):
    """Update daily analytics for vendor"""
    today = date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM activities 
        WHERE vendor_id = ? AND date(created_at) = ?
    ''', (vendor_id, today))
    views = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*), AVG(rating) FROM posts 
        WHERE vendor_id = ? AND post_type = 'review' AND date(created_at) = ?
    ''', (vendor_id, today))
    result = cursor.fetchone()
    reviews_count = result[0] if result[0] else 0
    avg_rating = result[1] if result[1] else 0
    
    cursor.execute('''
        INSERT INTO vendor_analytics (vendor_id, date, views, reviews_count, avg_rating)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(vendor_id, date) DO UPDATE SET
        views = excluded.views,
        reviews_count = excluded.reviews_count,
        avg_rating = excluded.avg_rating
    ''', (vendor_id, today, views, reviews_count, avg_rating))
    
    cursor.execute('''
        SELECT AVG(rating) FROM posts 
        WHERE vendor_id = ? AND post_type = 'review'
    ''', (vendor_id,))
    overall_rating = cursor.fetchone()[0] or 0
    
    cursor.execute('''
        UPDATE vendors SET rating = ?, review_count = (
            SELECT COUNT(*) FROM posts WHERE vendor_id = ? AND post_type = 'review'
        ) WHERE id = ?
    ''', (overall_rating, vendor_id, vendor_id))
    
    conn.commit()
    conn.close()

# ============= SERVE FRONTEND FILES =============
@app.route('/')
def serve_customer():
    return send_from_directory(CUSTOMER_FRONTEND, 'index.html')

@app.route('/customer')
def serve_customer_index():
    return send_from_directory(CUSTOMER_FRONTEND, 'index.html')

@app.route('/customer/<path:path>')
def serve_customer_static(path):
    return send_from_directory(CUSTOMER_FRONTEND, path)

@app.route('/vendor')
def serve_vendor():
    return send_from_directory(VENDOR_FRONTEND, 'index.html')

@app.route('/vendor/<path:path>')
def serve_vendor_static(path):
    return send_from_directory(VENDOR_FRONTEND, path)

@app.route('/dev')
def serve_dev():
    return send_from_directory(DEV_FRONTEND, 'index.html')

@app.route('/dev/<path:path>')
def serve_dev_static(path):
    return send_from_directory(DEV_FRONTEND, path)

# ============= EULA ENDPOINTS =============
@app.route('/api/eula/check', methods=['POST'])
def check_eula_status():
    data = request.json
    device_id = data.get('device_id')
    
    if not device_id:
        device_id = get_or_create_device_id()
    
    accepted = check_eula(device_id)
    
    eula_text = """
================================================================================
                    LAKO - END USER LICENSE AGREEMENT
================================================================================

Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325
Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp
Version 3.0 | Last Updated: March 26, 2026

================================================================================
1. INTRODUCTION
================================================================================

This End User License Agreement ("EULA") is a legal agreement between you 
("User" or "You") and Lako ("Company", "We", "Us", or "Our"), with principal 
offices located at 196 Bula, Tiaong, Quezon, Philippines 4325, developed by 
Kyle Brian M. Morillo and Alexander Collin Millicamp.

BY CLICKING "I ACCEPT", YOU AGREE TO BE BOUND BY THE TERMS OF THIS EULA. 
IF YOU DO NOT AGREE, DO NOT USE THE APPLICATION.

================================================================================
2. DATA COLLECTION AND PROCESSING
================================================================================

2.1 TYPES OF DATA COLLECTED
The Application collects and processes:

a) DEVICE INFORMATION: Unique device identifiers, MAC address (hashed), IP address
b) LOCATION DATA: GPS location for food spot discovery
c) USER ACCOUNT DATA: Full name, Gmail email address, preferences
d) USAGE DATA: Food spot views, searches, reviews, ratings
e) USER-GENERATED CONTENT: Food reviews, comments, shared spots

2.2 PURPOSE OF DATA COLLECTION
- User authentication and account management
- Food spot discovery and personalized recommendations
- Service improvement and analytics
- Security and fraud prevention

2.3 DATA STORAGE AND RETENTION
- Passwords: SHA-256 with individual salts
- Active accounts: Data retained while account exists
- Deleted accounts: Data anonymized within 30 days
- Data in transit: TLS 1.2+ encrypted

2.4 USER RIGHTS
You have the right to access, correct, delete your data, and opt out of tracking.

Contact: privacy@lako.com

================================================================================
3. LICENSE GRANT AND RESTRICTIONS
================================================================================

3.1 LICENSE GRANT
Lako grants you a non-exclusive, non-transferable license to use the Application.

3.2 PROHIBITED ACTIVITIES
You agree NOT to:
- Post false or misleading food reviews
- Harass other users
- Manipulate ratings or voting
- Use automated scripts

================================================================================
4. INTELLECTUAL PROPERTY
================================================================================

The Application is owned by Lako (196 Bula, Tiaong, Quezon). You retain ownership
of your reviews and comments.

================================================================================
5. DISCLAIMER OF WARRANTIES
================================================================================

THE APPLICATION IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND.

================================================================================
6. LIMITATION OF LIABILITY
================================================================================

LAKO SHALL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES.

================================================================================
7. TERMINATION
================================================================================

You may terminate by deleting your account. We may terminate for EULA violations.

================================================================================
8. GOVERNING LAW
================================================================================

This EULA is governed by the laws of the Republic of the Philippines.

================================================================================
9. CONTACT INFORMATION
================================================================================

Lako Support Team
Address: 196 Bula, Tiaong, Quezon, Philippines 4325
Email: support@lako.com
Privacy: privacy@lako.com

Developers:
Kyle Brian M. Morillo - kyle.morillo@lako.com
Alexander Collin Millicamp - alex.millicamp@lako.com

================================================================================
10. ACKNOWLEDGMENT
================================================================================

BY CLICKING "I ACCEPT", YOU ACKNOWLEDGE THAT:
- You have read and understand this EULA
- You agree to be bound by all terms
- You consent to the data collection practices
- You are at least 13 years of age
- Lako's headquarters is at 196 Bula, Tiaong, Quezon, Philippines 4325

================================================================================
"""
    
    return jsonify({
        'accepted': accepted,
        'device_id': device_id,
        'eula_text': eula_text
    })

@app.route('/api/eula/accept', methods=['POST'])
def accept_eula():
    data = request.json
    device_id = data.get('device_id')
    user_id = data.get('user_id')
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    if not device_id:
        device_id = get_or_create_device_id()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM eula_acceptance WHERE device_id = ?", (device_id,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute('''
            INSERT INTO eula_acceptance (device_id, user_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (device_id, user_id, ip_address, user_agent))
    
    if user_id:
        cursor.execute('UPDATE users SET eula_accepted = 1, eula_accepted_at = CURRENT_TIMESTAMP, device_id = ? WHERE id = ?', (device_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'EULA accepted successfully', 'device_id': device_id}), 200

# ============= USER ENDPOINTS (CUSTOMER + VENDOR) =============
@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').lower()
    device_id = data.get('device_id')
    user_type = data.get('user_type', 'customer')
    
    if not email.endswith('@gmail.com'):
        return jsonify({'error': 'Only Gmail addresses are allowed'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    password_hash, salt = hash_password(data.get('password'))
    preferences = json.dumps(data.get('preferences', {}))
    
    cursor.execute('''
        INSERT INTO users (full_name, email, password_hash, salt, device_id, user_type, eula_accepted, preferences)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('full_name'), email, password_hash, salt, device_id, user_type, 1, preferences))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': user_id,
        'full_name': data.get('full_name'),
        'email': email,
        'user_type': user_type,
        'device_id': device_id
    }), 201

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower()
    password = data.get('password')
    device_id = data.get('device_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, full_name, email, password_hash, salt, user_type, preferences FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user or not verify_password(password, user['salt'], user['password_hash']):
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if device_id:
        cursor.execute('UPDATE users SET device_id = ? WHERE id = ?', (device_id, user['id']))
        conn.commit()
    
    vendor_business = None
    if user['user_type'] == 'vendor':
        cursor.execute('SELECT * FROM vendor_business WHERE user_id = ?', (user['id'],))
        vendor_business = cursor.fetchone()
        if vendor_business:
            vendor_business = dict(vendor_business)
    
    conn.close()
    
    return jsonify({
        'id': user['id'],
        'full_name': user['full_name'],
        'email': user['email'],
        'user_type': user['user_type'],
        'device_id': device_id,
        'vendor_business': vendor_business,
        'preferences': json.loads(user['preferences']) if user['preferences'] else {}
    }), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, user_type, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'full_name': user['full_name'],
        'email': user['email'],
        'user_type': user['user_type'],
        'created_at': user['created_at']
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    if 'full_name' in data:
        cursor.execute('UPDATE users SET full_name = ? WHERE id = ?', (data['full_name'], user_id))
    
    if 'preferences' in data:
        cursor.execute('UPDATE users SET preferences = ? WHERE id = ?', (json.dumps(data['preferences']), user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Updated'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM votes WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM activities WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM shortlist WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM vendor_business WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/api/users/change-password', methods=['POST'])
def change_password():
    data = request.json
    user_id = data.get('user_id')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT password_hash, salt FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or not verify_password(current_password, user['salt'], user['password_hash']):
        conn.close()
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    new_hash, new_salt = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', (new_hash, new_salt, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Password changed successfully'}), 200

# ============= VENDOR REGISTRATION ENDPOINTS =============
@app.route('/api/vendor/register', methods=['POST'])
def vendor_register():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, email, full_name FROM users WHERE id = ? AND user_type = ?', (user_id, 'vendor'))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Vendor user not found'}), 404
    
    cursor.execute('SELECT id FROM vendor_business WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Business already registered'}), 400
    
    cursor.execute('SELECT id FROM vendor_business WHERE mayor_permit = ?', (data.get('mayor_permit'),))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Mayor\'s permit already registered'}), 400
    
    cursor.execute('''
        INSERT INTO vendor_business (
            user_id, business_name, mayor_permit, business_address, 
            business_phone, business_email, description, service_radius,
            latitude, longitude, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        data.get('business_name'),
        data.get('mayor_permit'),
        data.get('business_address'),
        data.get('business_phone'),
        data.get('business_email'),
        data.get('description'),
        data.get('service_radius', 10),
        data.get('latitude'),
        data.get('longitude'),
        data.get('category', 'Street Food')
    ))
    
    vendor_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO vendors (business_name, address, latitude, longitude, category, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('business_name'),
        data.get('business_address'),
        data.get('latitude'),
        data.get('longitude'),
        data.get('category', 'Street Food'),
        data.get('description')
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': vendor_id,
        'business_name': data.get('business_name'),
        'message': 'Vendor registration submitted for verification'
    }), 201

@app.route('/api/vendor/business/<int:user_id>', methods=['GET'])
def get_vendor_business(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendor_business WHERE user_id = ?', (user_id,))
    business = cursor.fetchone()
    conn.close()
    
    if not business:
        return jsonify({'error': 'Business not found'}), 404
    
    return jsonify(dict(business))

@app.route('/api/vendor/business/<int:vendor_id>', methods=['PUT'])
def update_vendor_business(vendor_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    allowed_fields = ['business_name', 'business_address', 'business_phone', 'business_email', 
                      'business_hours', 'description', 'logo_url', 'cover_url', 'is_open', 
                      'service_radius', 'latitude', 'longitude', 'category']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = ?")
            values.append(data[field])
    
    if update_fields:
        values.append(vendor_id)
        cursor.execute(f'UPDATE vendor_business SET {", ".join(update_fields)} WHERE id = ?', values)
        
        cursor.execute('''
            UPDATE vendors SET business_name = ?, address = ?, latitude = ?, longitude = ?, category = ?, description = ?
            WHERE id = (SELECT id FROM vendors WHERE business_name = (SELECT business_name FROM vendor_business WHERE id = ?))
        ''', (data.get('business_name'), data.get('business_address'), data.get('latitude'), 
              data.get('longitude'), data.get('category'), data.get('description'), vendor_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Business updated'}), 200

# ============= VENDOR PRODUCT ENDPOINTS =============
@app.route('/api/vendor/products/<int:vendor_id>', methods=['GET'])
def get_vendor_products(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendor_products WHERE vendor_id = ? ORDER BY created_at DESC', (vendor_id,))
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/vendor/products', methods=['POST'])
def create_vendor_product():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO vendor_products (vendor_id, name, description, price, moq, category, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['vendor_id'],
        data['name'],
        data.get('description'),
        data.get('price'),
        data.get('moq'),
        data.get('category'),
        data.get('image_url')
    ))
    
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': product_id, 'message': 'Product created'}), 201

@app.route('/api/vendor/products/<int:product_id>', methods=['PUT'])
def update_vendor_product(product_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    allowed_fields = ['name', 'description', 'price', 'moq', 'category', 'image_url', 'is_visible']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = ?")
            values.append(data[field])
    
    if update_fields:
        values.append(product_id)
        cursor.execute(f'UPDATE vendor_products SET {", ".join(update_fields)} WHERE id = ?', values)
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product updated'}), 200

@app.route('/api/vendor/products/<int:product_id>', methods=['DELETE'])
def delete_vendor_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vendor_products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted'}), 200

# ============= VENDOR ANALYTICS ENDPOINTS =============
@app.route('/api/vendor/analytics/<int:vendor_id>', methods=['GET'])
def get_vendor_analytics(vendor_id):
    days = request.args.get('days', 7, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM vendor_analytics 
        WHERE vendor_id = ? 
        ORDER BY date DESC LIMIT ?
    ''', (vendor_id, days))
    daily = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT 
            SUM(views) as total_views,
            SUM(reviews_count) as total_reviews,
            AVG(avg_rating) as overall_rating
        FROM vendor_analytics 
        WHERE vendor_id = ?
    ''', (vendor_id,))
    totals = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'daily': daily,
        'totals': dict(totals) if totals else {'total_views': 0, 'total_reviews': 0, 'overall_rating': 0}
    })

# ============= VENDOR MESSAGES ENDPOINTS =============
@app.route('/api/vendor/messages/<int:vendor_id>', methods=['GET'])
def get_vendor_messages(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*, u.full_name as customer_name 
        FROM vendor_messages m
        JOIN users u ON m.customer_id = u.id
        WHERE m.vendor_id = ?
        ORDER BY m.created_at DESC
    ''', (vendor_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(messages)

@app.route('/api/vendor/messages', methods=['POST'])
def create_vendor_message():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO vendor_messages (vendor_id, customer_id, message, is_from_vendor)
        VALUES (?, ?, ?, ?)
    ''', (data['vendor_id'], data['customer_id'], data['message'], data.get('is_from_vendor', 0)))
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': message_id}), 201

# ============= REVIEW REPLIES ENDPOINTS =============
@app.route('/api/reviews/<int:review_id>/reply', methods=['POST'])
def reply_to_review(review_id):
    data = request.json
    vendor_id = data.get('vendor_id')
    reply = data.get('reply')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO review_replies (review_id, vendor_id, reply)
        VALUES (?, ?, ?)
    ''', (review_id, vendor_id, reply))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Reply posted'}), 201

@app.route('/api/reviews/<int:review_id>/reply', methods=['GET'])
def get_review_reply(review_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM review_replies WHERE review_id = ?', (review_id,))
    reply = cursor.fetchone()
    conn.close()
    
    return jsonify(dict(reply) if reply else None)

# ============= SAMPLE REQUESTS ENDPOINTS =============
@app.route('/api/sample-requests/vendor/<int:vendor_id>', methods=['GET'])
def get_sample_requests(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sr.*, vp.name as product_name
        FROM sample_requests sr
        LEFT JOIN vendor_products vp ON sr.product_id = vp.id
        WHERE sr.vendor_id = ?
        ORDER BY sr.created_at DESC
    ''', (vendor_id,))
    requests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(requests)

@app.route('/api/sample-requests/<int:request_id>/approve', methods=['POST'])
def approve_sample_request(request_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sample_requests SET status = 'approved', notes = ?
        WHERE id = ?
    ''', (data.get('meetup_date', 'Confirmed'), request_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Sample request approved'}), 200

@app.route('/api/sample-requests/<int:request_id>/reject', methods=['POST'])
def reject_sample_request(request_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sample_requests SET status = 'rejected', notes = ?
        WHERE id = ?
    ''', (data.get('reason', 'No reason provided'), request_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Sample request rejected'}), 200

# ============= CUSTOMER ENDPOINTS (For Customer App) =============
@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendors ORDER BY rating DESC, review_count DESC')
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(vendors)

@app.route('/api/posts', methods=['GET'])
def get_posts():
    sort = request.args.get('sort', 'new')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    vendor_id = request.args.get('vendor_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if vendor_id:
        cursor.execute('SELECT * FROM posts WHERE vendor_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?', (vendor_id, limit, offset))
    elif sort == 'new':
        cursor.execute('SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
    elif sort == 'top':
        cursor.execute('SELECT *, (upvotes - downvotes) as score FROM posts ORDER BY score DESC LIMIT ? OFFSET ?', (limit, offset))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
    
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    for post in posts:
        post['score'] = post['upvotes'] - post['downvotes']
    
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO posts (user_id, vendor_id, product_id, title, content, post_type, rating, image_thumbnail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['user_id'], data.get('vendor_id'), data.get('product_id'), data['title'], data['content'],
          data.get('post_type', 'text'), data.get('rating'), data.get('image_thumbnail')))
    
    post_id = cursor.lastrowid
    
    if data.get('product_id'):
        cursor.execute('UPDATE vendor_products SET review_count = review_count + 1, avg_rating = (SELECT AVG(rating) FROM posts WHERE product_id = ?) WHERE id = ?', 
                      (data['product_id'], data['product_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'id': post_id}), 201

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    post_dict = dict(post)
    post_dict['score'] = post_dict['upvotes'] - post_dict['downvotes']
    return jsonify(post_dict)

@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
def share_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Shared'}), 200

@app.route('/api/comments', methods=['GET'])
def get_comments():
    post_id = request.args.get('post_id')
    conn = get_db()
    cursor = conn.cursor()
    
    if post_id:
        cursor.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC', (post_id,))
    else:
        cursor.execute('SELECT * FROM comments ORDER BY created_at DESC LIMIT 100')
    
    comments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    for comment in comments:
        comment['score'] = comment['upvotes'] - comment['downvotes']
    
    return jsonify(comments)

@app.route('/api/comments', methods=['POST'])
def create_comment():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO comments (post_id, user_id, parent_id, content)
        VALUES (?, ?, ?, ?)
    ''', (data['post_id'], data['user_id'], data.get('parent_id'), data['content']))
    
    comment_id = cursor.lastrowid
    cursor.execute('UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?', (data['post_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'id': comment_id}), 201

@app.route('/api/votes', methods=['POST'])
def create_vote():
    data = request.json
    user_id = data['user_id']
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    vote_type = data['vote_type']
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, vote_type FROM votes WHERE user_id = ? AND (post_id = ? OR comment_id = ?)', 
                   (user_id, post_id, comment_id))
    existing = cursor.fetchone()
    
    if existing:
        if existing['vote_type'] == vote_type:
            cursor.execute('DELETE FROM votes WHERE id = ?', (existing['id'],))
            if post_id:
                if vote_type == 1:
                    cursor.execute('UPDATE posts SET upvotes = upvotes - 1 WHERE id = ?', (post_id,))
                else:
                    cursor.execute('UPDATE posts SET downvotes = downvotes - 1 WHERE id = ?', (post_id,))
            elif comment_id:
                if vote_type == 1:
                    cursor.execute('UPDATE comments SET upvotes = upvotes - 1 WHERE id = ?', (comment_id,))
                else:
                    cursor.execute('UPDATE comments SET downvotes = downvotes - 1 WHERE id = ?', (comment_id,))
        else:
            cursor.execute('UPDATE votes SET vote_type = ? WHERE id = ?', (vote_type, existing['id']))
            if post_id:
                if vote_type == 1:
                    cursor.execute('UPDATE posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', (post_id,))
                else:
                    cursor.execute('UPDATE posts SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', (post_id,))
            elif comment_id:
                if vote_type == 1:
                    cursor.execute('UPDATE comments SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', (comment_id,))
                else:
                    cursor.execute('UPDATE comments SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', (comment_id,))
    else:
        cursor.execute('INSERT INTO votes (user_id, post_id, comment_id, vote_type) VALUES (?, ?, ?, ?)',
                       (user_id, post_id, comment_id, vote_type))
        if post_id:
            if vote_type == 1:
                cursor.execute('UPDATE posts SET upvotes = upvotes + 1 WHERE id = ?', (post_id,))
            else:
                cursor.execute('UPDATE posts SET downvotes = downvotes + 1 WHERE id = ?', (post_id,))
        elif comment_id:
            if vote_type == 1:
                cursor.execute('UPDATE comments SET upvotes = upvotes + 1 WHERE id = ?', (comment_id,))
            else:
                cursor.execute('UPDATE comments SET downvotes = downvotes + 1 WHERE id = ?', (comment_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Vote recorded'}), 200

@app.route('/api/votes/user/<int:user_id>', methods=['GET'])
def get_user_votes(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT post_id, comment_id, vote_type FROM votes WHERE user_id = ?', (user_id,))
    votes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(votes)

@app.route('/api/activities', methods=['POST'])
def create_activity():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO activities (user_id, vendor_id, activity_type, metadata)
        VALUES (?, ?, ?, ?)
    ''', (data['user_id'], data.get('vendor_id'), data['activity_type'], json.dumps(data.get('metadata', {}))))
    
    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': activity_id}), 201

@app.route('/api/activities/vendor/<int:vendor_id>', methods=['GET'])
def get_vendor_activities(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE vendor_id = ? ORDER BY created_at DESC LIMIT 500', (vendor_id,))
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(activities)

@app.route('/api/activities/user/<int:user_id>', methods=['GET'])
def get_user_activities(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, vendor_id, activity_type, metadata, created_at FROM activities WHERE user_id = ? ORDER BY created_at DESC LIMIT 100', (user_id,))
    
    activities = []
    for row in cursor.fetchall():
        activity = dict(row)
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        activities.append(activity)
    
    conn.close()
    return jsonify(activities)

@app.route('/api/shortlist', methods=['POST'])
def add_to_shortlist():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO shortlist (user_id, vendor_id) VALUES (?, ?)', (data['user_id'], data['vendor_id']))
        shortlist_id = cursor.lastrowid
        conn.commit()
        return jsonify({'id': shortlist_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Already in shortlist'}), 200

@app.route('/api/shortlist/user/<int:user_id>', methods=['GET'])
def get_shortlist(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.id, v.business_name, v.logo_thumbnail, v.rating, v.category
        FROM shortlist s JOIN vendors v ON s.vendor_id = v.id
        WHERE s.user_id = ?
    ''', (user_id,))
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(vendors)

@app.route('/api/shortlist/<int:vendor_id>/user/<int:user_id>', methods=['DELETE'])
def remove_from_shortlist(vendor_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM shortlist WHERE user_id = ? AND vendor_id = ?', (user_id, vendor_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Removed'}), 200

@app.route('/api/recommendations/user/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT preferences FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    preferences = json.loads(user['preferences']) if user and user['preferences'] else {}
    interests = preferences.get('interests', [])
    
    cursor.execute('SELECT DISTINCT vendor_id FROM activities WHERE user_id = ? AND vendor_id IS NOT NULL', (user_id,))
    viewed_vendors = [row['vendor_id'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT vendor_id FROM shortlist WHERE user_id = ?', (user_id,))
    saved_vendors = [row['vendor_id'] for row in cursor.fetchall()]
    
    excluded = list(set(viewed_vendors + saved_vendors))
    
    if interests:
        placeholders = ','.join(['?'] * len(interests))
        excluded_placeholders = ','.join(['?'] * len(excluded)) if excluded else '0'
        cursor.execute(f'''
            SELECT * FROM vendors 
            WHERE category IN ({placeholders})
            AND id NOT IN ({excluded_placeholders})
            ORDER BY rating DESC LIMIT 20
        ''', interests + excluded)
    else:
        excluded_placeholders = ','.join(['?'] * len(excluded)) if excluded else '0'
        cursor.execute(f'''
            SELECT * FROM vendors 
            WHERE id NOT IN ({excluded_placeholders})
            ORDER BY rating DESC LIMIT 20
        ''', excluded)
    
    recommendations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(recommendations)

# ============= DEV ADMIN ENDPOINTS =============
@app.route('/api/dev/login', methods=['POST'])
def dev_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, salt, full_name, role FROM dev_admins WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()
    
    if admin:
        password_hash = hashlib.sha256((password + admin['salt']).encode()).hexdigest()
        if password_hash == admin['password_hash']:
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_role'] = admin['role']
            return jsonify({
                'id': admin['id'],
                'username': admin['username'],
                'full_name': admin['full_name'],
                'role': admin['role']
            }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/dev/logout', methods=['POST'])
def dev_logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@app.route('/api/dev/check', methods=['GET'])
def dev_check():
    if session.get('admin_id'):
        return jsonify({
            'authenticated': True,
            'username': session.get('admin_username'),
            'role': session.get('admin_role')
        }), 200
    return jsonify({'authenticated': False}), 401

@app.route('/api/dev/stats', methods=['GET'])
@admin_required
def dev_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'customer'")
    stats['total_customers'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'vendor'")
    stats['total_vendors'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vendors")
    stats['total_food_spots'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM posts")
    stats['total_reviews'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM comments")
    stats['total_comments'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM activities WHERE date(created_at) = date('now')")
    stats['today_activity'] = cursor.fetchone()[0]
    
    conn.close()
    return jsonify(stats)

@app.route('/api/dev/users', methods=['GET'])
@admin_required
def dev_get_users():
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, full_name, email, user_type, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(users)

@app.route('/api/dev/users/<int:user_id>', methods=['DELETE'])
@admin_required
def dev_delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM votes WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM activities WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM shortlist WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM vendor_business WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    cursor.execute('''
        INSERT INTO system_logs (admin_id, action, target_type, target_id)
        VALUES (?, ?, ?, ?)
    ''', (session['admin_id'], 'delete_user', 'user', user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted'}), 200

@app.route('/api/dev/vendors', methods=['GET'])
@admin_required
def dev_get_vendors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.*, u.full_name as owner_name, u.email as owner_email
        FROM vendors v
        LEFT JOIN vendor_business vb ON v.id = vb.id
        LEFT JOIN users u ON vb.user_id = u.id
        ORDER BY v.created_at DESC
    ''')
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(vendors)

@app.route('/api/dev/vendors/<int:vendor_id>', methods=['DELETE'])
@admin_required
def dev_delete_vendor(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM posts WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM shortlist WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM activities WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM vendor_products WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM vendors WHERE id = ?', (vendor_id,))
    
    cursor.execute('''
        INSERT INTO system_logs (admin_id, action, target_type, target_id)
        VALUES (?, ?, ?, ?)
    ''', (session['admin_id'], 'delete_vendor', 'vendor', vendor_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Vendor deleted'}), 200

@app.route('/api/dev/posts', methods=['GET'])
@admin_required
def dev_get_posts():
    limit = request.args.get('limit', 100, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.full_name as author_name
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT ?
    ''', (limit,))
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(posts)

@app.route('/api/dev/posts/<int:post_id>', methods=['DELETE'])
@admin_required
def dev_delete_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM votes WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    
    cursor.execute('''
        INSERT INTO system_logs (admin_id, action, target_type, target_id)
        VALUES (?, ?, ?, ?)
    ''', (session['admin_id'], 'delete_post', 'post', post_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Post deleted'}), 200

@app.route('/api/dev/logs', methods=['GET'])
@admin_required
def dev_get_logs():
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.*, a.username as admin_name
        FROM system_logs l
        LEFT JOIN dev_admins a ON l.admin_id = a.id
        ORDER BY l.created_at DESC
        LIMIT ?
    ''', (limit,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(logs)

# ============= TEST ENDPOINT =============
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        "status": "ok",
        "message": "Lako API is working!",
        "apps": ["Customer App", "Vendor App", "Dev Admin App"],
        "version": "3.0",
        "headquarters": "196 Bula, Tiaong, Quezon",
        "developers": ["Kyle Brian M. Morillo", "Alexander Collin Millicamp"]
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("LAKO - COMPLETE BACKEND")
    print("Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp")
    print("Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325")
    print("="*60)
    print("\n📱 Apps Available:")
    print("   • Customer App: http://localhost:5000/customer")
    print("   • Vendor App:   http://localhost:5000/vendor")
    print("   • Dev Admin:    http://localhost:5000/dev")
    print("\n🔧 Dev Admin Login:")
    print("   Username: lako_dev")
    print("   Password: lako2026")
    print("\n🚀 Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
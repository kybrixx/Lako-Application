from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import secrets
import hashlib
import uuid
import json
from datetime import datetime

# Get the absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'Frontendpwa')
DATABASE = os.path.join(os.path.dirname(__file__), 'lako.db')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ============= DATABASE FUNCTIONS =============
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table - EMAIL ONLY (no phone number)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            device_id TEXT UNIQUE,
            eula_accepted INTEGER DEFAULT 0,
            eula_accepted_at TIMESTAMP,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Vendors table
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
    
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            post_type TEXT DEFAULT 'text',
            rating INTEGER,
            image_thumbnail TEXT,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')
    
    # Comments table
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
    
    # Votes table
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
    
    # Activities table
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
    
    # Shortlist table
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
    
    # EULA Acceptance table
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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully - NO SAMPLE DATA")

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
                    LAKO STREET FOOD - END USER LICENSE AGREEMENT
================================================================================

Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325
Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp
Version 2.0 | Last Updated: March 26, 2026

================================================================================
1. INTRODUCTION
================================================================================

This End User License Agreement ("EULA") is a legal agreement between you 
("User" or "You") and Lako ("Company", "We", "Us", or "Our"), with principal 
offices located at 196 Bula, Tiaong, Quezon, Philippines 4325, developed by 
Kyle Brian M. Morillo and Alexander Collin Millicamp, governing your use of 
the Lako Street Food mobile application and related services ("Application").

BY CLICKING "I ACCEPT", YOU AGREE TO BE BOUND BY THE TERMS OF THIS EULA. 
IF YOU DO NOT AGREE, DO NOT USE THE APPLICATION.

================================================================================
2. DATA COLLECTION AND PROCESSING
================================================================================

2.1 TYPES OF DATA COLLECTED
The Application collects and processes the following types of data:

a) DEVICE INFORMATION:
   - Unique device identifiers
   - MAC address (hashed for privacy)
   - Device model and operating system
   - IP address and network information

b) LOCATION DATA:
   - Precise GPS location (when enabled)
   - Location history for food spot discovery
   - Geofencing data for nearby vendors

c) USER ACCOUNT DATA:
   - Full name
   - Gmail email address (required for authentication)
   - Account creation date
   - User preferences and settings

d) USAGE AND BEHAVIORAL DATA:
   - Food spot views and searches
   - Reviews and ratings given
   - Interaction patterns
   - Features used

e) USER-GENERATED CONTENT:
   - Food reviews and ratings
   - Comments and replies
   - Shared food spots

f) SOCIAL INTERACTIONS:
   - Saved food spots (shortlist)
   - Votes on reviews
   - Activity history

2.2 PURPOSE OF DATA COLLECTION
Your data is collected for:
   - User authentication and account management
   - Food spot discovery and recommendations
   - Personalized suggestions based on your taste
   - Service improvement and analytics
   - Security and fraud prevention

2.3 DATA STORAGE AND RETENTION

a) STORAGE LOCATION:
   All user data is stored on secure servers in the Philippines.

b) RETENTION PERIOD:
   - Active accounts: Data retained while account exists
   - Deleted accounts: Data anonymized within 30 days
   - Log data: Retained for 12 months

c) DATA ENCRYPTION:
   - Passwords: SHA-256 with individual salts
   - Device identifiers: Hashed
   - Data in transit: TLS 1.2+
   - Data at rest: AES-256

2.4 USER RIGHTS
You have the right to:
   - Access all your data
   - Correct inaccurate information
   - Delete your account and data
   - Opt out of location tracking
   - Disable personalized recommendations

To exercise these rights, contact: privacy@lako.com

================================================================================
3. LICENSE GRANT AND RESTRICTIONS
================================================================================

3.1 LICENSE GRANT
Lako grants you a non-exclusive, non-transferable license to:
   - Install and use the Application
   - Post food reviews and interact with the community

3.2 PROHIBITED ACTIVITIES
You agree NOT to:
   - Post false or misleading food reviews
   - Harass other users
   - Manipulate ratings or voting
   - Use automated scripts
   - Share your account credentials

================================================================================
4. INTELLECTUAL PROPERTY
================================================================================

The Application is owned by Lako (196 Bula, Tiaong, Quezon) and protected by 
copyright laws. You retain ownership of your reviews and comments.

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

# ============= USER ENDPOINTS (EMAIL ONLY) =============
@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').lower()
    device_id = data.get('device_id')
    
    # EMAIL ONLY - Must be Gmail
    if not email.endswith('@gmail.com'):
        return jsonify({'error': 'Only Gmail addresses are allowed'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    # Hash password
    password_hash, salt = hash_password(data.get('password'))
    
    # Get preferences
    preferences = json.dumps(data.get('preferences', {}))
    
    # Create user
    cursor.execute('''
        INSERT INTO users (full_name, email, password_hash, salt, device_id, eula_accepted, preferences)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('full_name'), email, password_hash, salt, device_id, 1, preferences))
    
    user_id = cursor.lastrowid
    conn.commit()
    
    # Update EULA acceptance if device exists
    eula = EULAAcceptance.query.filter_by(device_id=device_id).first()
    if eula:
        eula.user_id = user_id
        db.session.commit()
    
    conn.close()
    
    return jsonify({
        'id': user_id,
        'full_name': data.get('full_name'),
        'email': email,
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
    
    cursor.execute('SELECT id, full_name, email, password_hash, salt, preferences FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user or not verify_password(password, user['salt'], user['password_hash']):
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update device_id if provided
    if device_id:
        cursor.execute('UPDATE users SET device_id = ? WHERE id = ?', (device_id, user['id']))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'id': user['id'],
        'full_name': user['full_name'],
        'email': user['email'],
        'device_id': device_id,
        'preferences': json.loads(user['preferences']) if user['preferences'] else {}
    }), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'full_name': user['full_name'],
        'email': user['email'],
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
    
    # Delete all related records
    cursor.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM votes WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM activities WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM shortlist WHERE user_id = ?', (user_id,))
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

# ============= VENDOR ENDPOINTS =============
@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendors ORDER BY created_at DESC')
    vendors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(vendors)

@app.route('/api/vendors', methods=['POST'])
def create_vendor():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO vendors (business_name, address, latitude, longitude, category, description, logo_thumbnail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('business_name'), data.get('address'), data.get('latitude'), 
          data.get('longitude'), data.get('category'), data.get('description'), data.get('logo_thumbnail')))
    
    vendor_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': vendor_id, 'message': 'Vendor created'}), 201

@app.route('/api/vendors/<int:vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM vendors WHERE id = ?', (vendor_id,))
    cursor.execute('DELETE FROM posts WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM activities WHERE vendor_id = ?', (vendor_id,))
    cursor.execute('DELETE FROM shortlist WHERE vendor_id = ?', (vendor_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Vendor deleted'}), 200

# ============= POST ENDPOINTS =============
@app.route('/api/posts', methods=['GET'])
def get_posts():
    sort = request.args.get('sort', 'new')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if sort == 'new':
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
        INSERT INTO posts (user_id, vendor_id, title, content, post_type, rating, image_thumbnail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['user_id'], data.get('vendor_id'), data['title'], data['content'],
          data.get('post_type', 'text'), data.get('rating'), data.get('image_thumbnail')))
    
    post_id = cursor.lastrowid
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

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM votes WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Post deleted'}), 200

# ============= COMMENT ENDPOINTS =============
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
    
    # Update comment count on post
    cursor.execute('UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?', (data['post_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'id': comment_id}), 201

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get post_id before deleting
    cursor.execute('SELECT post_id FROM comments WHERE id = ?', (comment_id,))
    comment = cursor.fetchone()
    
    if comment:
        cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        cursor.execute('UPDATE posts SET comment_count = comment_count - 1 WHERE id = ?', (comment['post_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Comment deleted'}), 200

# ============= VOTE ENDPOINTS =============
@app.route('/api/votes', methods=['POST'])
def create_vote():
    data = request.json
    user_id = data['user_id']
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    vote_type = data['vote_type']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check existing vote
    cursor.execute('''
        SELECT id, vote_type FROM votes 
        WHERE user_id = ? AND (post_id = ? OR comment_id = ?)
    ''', (user_id, post_id, comment_id))
    existing = cursor.fetchone()
    
    if existing:
        if existing['vote_type'] == vote_type:
            # Remove vote
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
            # Change vote
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
        # New vote
        cursor.execute('''
            INSERT INTO votes (user_id, post_id, comment_id, vote_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, post_id, comment_id, vote_type))
        
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

# ============= ACTIVITY ENDPOINTS =============
@app.route('/api/activities', methods=['POST'])
def create_activity():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO activities (user_id, vendor_id, activity_type, metadata)
        VALUES (?, ?, ?, ?)
    ''', (data['user_id'], data.get('vendor_id'), data['activity_type'], 
          json.dumps(data.get('metadata', {}))))
    
    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': activity_id}), 201

@app.route('/api/activities/user/<int:user_id>', methods=['GET'])
def get_user_activities(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, vendor_id, activity_type, metadata, created_at 
        FROM activities WHERE user_id = ? ORDER BY created_at DESC LIMIT 100
    ''', (user_id,))
    
    activities = []
    for row in cursor.fetchall():
        activity = dict(row)
        activity['metadata'] = json.loads(activity['metadata']) if activity['metadata'] else {}
        activities.append(activity)
    
    conn.close()
    return jsonify(activities)

@app.route('/api/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE id = ?', (activity_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'}), 200

# ============= SHORTLIST ENDPOINTS =============
@app.route('/api/shortlist', methods=['POST'])
def add_to_shortlist():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO shortlist (user_id, vendor_id)
            VALUES (?, ?)
        ''', (data['user_id'], data['vendor_id']))
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

# ============= RECOMMENDATIONS =============
@app.route('/api/recommendations/user/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user's preferences
    cursor.execute('SELECT preferences FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    preferences = json.loads(user['preferences']) if user and user['preferences'] else {}
    interests = preferences.get('interests', [])
    
    # Get user's activity
    cursor.execute('SELECT DISTINCT vendor_id FROM activities WHERE user_id = ? AND vendor_id IS NOT NULL', (user_id,))
    viewed_vendors = [row['vendor_id'] for row in cursor.fetchall()]
    
    # Get shortlist
    cursor.execute('SELECT vendor_id FROM shortlist WHERE user_id = ?', (user_id,))
    saved_vendors = [row['vendor_id'] for row in cursor.fetchall()]
    
    # Exclude already viewed/saved
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

# ============= SERVE FRONTEND =============
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/api/test')
def test():
    return jsonify({
        "status": "ok",
        "message": "Lako Street Food API is working!",
        "version": "2.0",
        "headquarters": "196 Bula, Tiaong, Quezon",
        "developers": ["Kyle Brian M. Morillo", "Alexander Collin Millicamp"]
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("LAKO STREET FOOD APP")
    print("Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp")
    print("Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325")
    print("="*60)
    print(f"\nFrontend folder: {FRONTEND_DIR}")
    print(f"Database: {DATABASE}")
    print(f"\nServer running at: http://localhost:5000")
    print(f"Test API: http://localhost:5000/api/test")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
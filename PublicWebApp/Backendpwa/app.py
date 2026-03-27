from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
import json
from functools import wraps
import io

app = Flask(__name__)
app.secret_key = os.urandom(32)
CORS(app, supports_credentials=True, origins=['http://localhost:5500', 'http://127.0.0.1:5500'])
DATABASE = os.path.join(os.path.dirname(__file__), 'lako.db')

def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt

def verify_password(password, salt, password_hash):
    return password_hash == hashlib.sha256((password + salt).encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"error": "Invalid user ID"}), 401
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "User not found"}), 401
        conn.close()
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            phone TEXT,
            avatar TEXT,
            eula_accepted BOOLEAN DEFAULT 0,
            eula_accepted_at TIMESTAMP,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            category TEXT,
            description TEXT,
            logo TEXT,
            cover_image TEXT,
            messenger_id TEXT,
            phone TEXT,
            email TEXT,
            hours TEXT,
            mayor_permit TEXT,
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            traffic_score INTEGER DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price TEXT,
            moq TEXT,
            image TEXT,
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            product_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            post_type TEXT DEFAULT 'review',
            rating INTEGER CHECK (rating BETWEEN 1 AND 5),
            image TEXT,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            is_edited BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    ''')
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
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            vote_type INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            UNIQUE(user_id, post_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            post_id INTEGER,
            activity_type TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE SET NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shortlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            UNIQUE(user_id, vendor_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sample_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            product_id INTEGER,
            message TEXT,
            location TEXT,
            preferred_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            direction TEXT DEFAULT 'outgoing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            hour INTEGER,
            count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            UNIQUE(vendor_id, date, hour)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eula_acceptances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

PROJECT_INFO = {
    "name": "Lako - Street Food Discovery & Navigation System",
    "version": "2.1.0",
    "institution": "Asian Institute of Technology and Education (AITE)",
    "campus": "Tiaong, Quezon",
    "department": "College of Information Technology",
    "program": "Bachelor of Science in Information Technology",
    "academic_year": "2026-2027",
    "semester": "2nd Semester",
    "project_type": "Capstone Project",
    "developers": [
        {"name": "Kyle Brian M. Morillo", "role": "Lead Developer"},
        {"name": "Alexander Collin Millicamp", "role": "Co-Developer"}
    ],
    "adviser": "Prof. Joy Ann De Lima",
    "description": "Lako is a mobile application designed to revolutionize street food discovery in Tiaong, Quezon. It provides real-time navigation, vendor discovery, geofencing alerts, and community-driven reviews, bridging the gap between local street food vendors and customers.",
    "features": [
        "Real-time GPS Navigation with Road Routing",
        "Vendor Discovery with Traffic Heatmaps",
        "Geofencing Alerts for Nearby Vendors",
        "Community Reviews and Ratings",
        "Interactive Map with Search Functionality",
        "Offline Support with Local Database Sync",
        "Facebook Messenger Integration",
        "Sample Request System",
        "Activity Timeline and History",
        "Personalized Recommendations"
    ],
    "technologies": [
        "Frontend: HTML5, CSS3, JavaScript, Leaflet Maps",
        "Backend: Python Flask, SQLite",
        "Navigation: OSRM (Open Source Routing Machine)",
        "Maps: OpenStreetMap",
        "Authentication: Session-based",
        "PWA: Service Workers, IndexedDB"
    ],
    "purpose": "This Capstone Project is submitted in partial fulfillment of the requirements for the degree of Bachelor of Science in Information Technology at the Asian Institute of Technology and Education (AITE). The application demonstrates the integration of modern web technologies, geolocation services, and community engagement features to solve real-world problems in the local street food industry.",
    "copyright_year": "2027",
    "rights": "All rights reserved. This project is for academic purposes only."
}

EULA_VERSION = "1.0.0"
EULA_TEXT = f"""
LAKO END USER LICENSE AGREEMENT (EULA)
Version {EULA_VERSION}
Last Updated: March 2027
A CAPSTONE PROJECT OF THE ASIAN INSTITUTE OF TECHNOLOGY AND EDUCATION (AITE)
Developers: Kyle Brian M. Morillo & Alexander Collin Millicamp
Adviser: Prof. Joy Ann De Lima
Academic Year: 2026-2027
1. ACCEPTANCE OF TERMS
By downloading, installing, or using the Lako application ("App"), you agree to be bound by this End User License Agreement.
2. ACADEMIC PURPOSE
This application is developed as a Capstone Project requirement for the Bachelor of Science in Information Technology program at AITE.
3. LICENSE GRANT
The developers grant you a non-exclusive, non-transferable license to use the App for personal, non-commercial purposes.
4. RESTRICTIONS
You may not modify, reverse engineer, or claim the App as your own work.
5. USER DATA AND PRIVACY
The App collects location, usage, and personal information as described in the Privacy Policy.
6. GEOLOCATION AND NAVIGATION
Navigation uses OpenStreetMap and OSRM. Use navigation at your own risk.
7. THIRD-PARTY SERVICES
The App integrates with OpenStreetMap, OSRM, and Facebook Messenger.
8. ACADEMIC ACKNOWLEDGMENT
You acknowledge this is a student Capstone Project for academic demonstration.
9. DISCLAIMER OF WARRANTIES
The App is provided "AS IS" without warranties.
10. LIMITATION OF LIABILITY
The developers and AITE shall not be liable for any damages.
11. GOVERNING LAW
This Agreement shall be governed by the laws of the Republic of the Philippines.
BY USING LAKO, YOU ACKNOWLEDGE THIS IS AN AITE CAPSTONE PROJECT AND AGREE TO BE BOUND BY ITS TERMS.
"""

TERMS_OF_SERVICE = f"""
LAKO TERMS OF SERVICE
AITE Capstone Project 2026-2027
1. SERVICE DESCRIPTION
Lako is a Capstone Project developed by Kyle Brian M. Morillo and Alexander Collin Millicamp under Prof. Joy Ann De Lima at AITE.
2. ACADEMIC NATURE
This application is a student project for academic evaluation purposes.
3. ELIGIBILITY
You must be at least 13 years old to use the App.
4. USER CONTENT
You retain ownership of content you post. The developers may display your content for academic demonstration.
5. MAP AND NAVIGATION
Map data from OpenStreetMap. Navigation routes are suggestions only.
6. MODIFICATIONS
The developers may modify or discontinue the App at any time.
7. ACKNOWLEDGMENT
By using this App, you acknowledge this is an AITE Capstone Project.
For questions: Prof. Joy Ann De Lima - Capstone Adviser, AITE Tiaong
"""

PRIVACY_POLICY = f"""
LAKO PRIVACY POLICY
AITE Capstone Project 2026-2027
1. INFORMATION COLLECTED
- Account: Name, email, phone
- Location: GPS data for navigation
- Usage: App interactions
- Content: Reviews, messages
2. HOW WE USE INFORMATION
- Provide navigation services
- Show nearby vendors
- Improve the App for academic evaluation
- Comply with AITE requirements
3. DATA SHARING
Data may be shared with AITE faculty for evaluation and third-party services (OpenStreetMap, OSRM).
4. DATA STORAGE
Data is stored securely and retained until academic evaluation is complete.
5. YOUR RIGHTS
You may access, correct, or delete your data by contacting your Capstone Adviser.
6. CONTACT
Prof. Joy Ann De Lima
Capstone Adviser
Asian Institute of Technology and Education (AITE)
Tiaong, Quezon
This Privacy Policy is part of an AITE Capstone Project.
"""

@app.route('/api/project/info', methods=['GET'])
def get_project_info():
    return jsonify(PROJECT_INFO)

@app.route('/api/legal/eula', methods=['GET'])
def get_eula():
    return jsonify({
        "version": EULA_VERSION,
        "content": EULA_TEXT,
        "updated_at": "2027-03-27",
        "project": "AITE Capstone Project 2026-2027",
        "developers": ["Kyle Brian M. Morillo", "Alexander Collin Millicamp"],
        "adviser": "Prof. Joy Ann De Lima"
    })

@app.route('/api/legal/eula/download', methods=['GET'])
def download_eula():
    content = f"""LAKO END USER LICENSE AGREEMENT (EULA)
Version: {EULA_VERSION}
AITE CAPSTONE PROJECT 2026-2027
Asian Institute of Technology and Education (AITE)
Developers: Kyle Brian M. Morillo & Alexander Collin Millicamp
Adviser: Prof. Joy Ann De Lima
{EULA_TEXT}
"""
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name='LAKO_EULA.txt'
    )

@app.route('/api/legal/terms', methods=['GET'])
def get_terms():
    return jsonify({
        "version": "1.0.0",
        "content": TERMS_OF_SERVICE,
        "updated_at": "2027-03-27"
    })

@app.route('/api/legal/privacy', methods=['GET'])
def get_privacy():
    return jsonify({
        "version": "1.0.0",
        "content": PRIVACY_POLICY,
        "updated_at": "2027-03-27"
    })

@app.route('/api/legal/accept-eula', methods=['POST'])
@login_required
def accept_eula():
    try:
        user_id = int(request.headers.get('X-User-Id'))
        data = request.get_json()
        version = data.get('version', EULA_VERSION)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET eula_accepted = 1, eula_accepted_at = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        cursor.execute('INSERT INTO eula_acceptances (user_id, version, ip_address, user_agent) VALUES (?, ?, ?, ?)',
                      (user_id, version, request.remote_addr, request.headers.get('User-Agent')))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "EULA accepted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/legal/check-eula', methods=['GET'])
@login_required
def check_eula():
    try:
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT eula_accepted, eula_accepted_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return jsonify({
            "accepted": bool(user['eula_accepted']) if user else False,
            "accepted_at": user['eula_accepted_at'] if user else None,
            "current_version": EULA_VERSION
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        full_name = data.get('full_name', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()
        if not all([email, full_name, password]):
            return jsonify({"error": "Missing required fields"}), 400
        if not email.endswith('@gmail.com'):
            return jsonify({"error": "Only Gmail addresses allowed"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        password_hash, salt = hash_password(password)
        cursor.execute('INSERT INTO users (full_name, email, password_hash, salt, phone) VALUES (?, ?, ?, ?, ?)',
                      (full_name, email, password_hash, salt, phone))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": user_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, email, phone, password_hash, salt FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if not user or not verify_password(password, user['salt'], user['password_hash']):
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401
        conn.close()
        return jsonify({
            "success": True,
            "id": user['id'],
            "full_name": user['full_name'],
            "email": user['email'],
            "phone": user['phone']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, phone, avatar, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        updates = []
        values = []
        if 'full_name' in data:
            updates.append("full_name = ?")
            values.append(data['full_name'])
        if 'phone' in data:
            updates.append("phone = ?")
            values.append(data['phone'])
        if 'avatar' in data:
            updates.append("avatar = ?")
            values.append(data['avatar'])
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors WHERE is_active = 1 ORDER BY rating DESC, review_count DESC')
        vendors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(vendors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors WHERE id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        if not vendor:
            conn.close()
            return jsonify({"error": "Vendor not found"}), 404
        cursor.execute('SELECT * FROM products WHERE vendor_id = ? AND is_active = 1', (vendor_id,))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        result = dict(vendor)
        result['products'] = products
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendors/<int:vendor_id>/messenger', methods=['GET'])
def get_messenger_link(vendor_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT messenger_id, business_name FROM vendors WHERE id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        conn.close()
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        messenger_url = f"https://m.me/{vendor['messenger_id']}" if vendor['messenger_id'] else "https://m.me/lakoapp"
        return jsonify({
            "messenger_url": messenger_url,
            "business_name": vendor['business_name']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts', methods=['GET'])
def get_posts():
    try:
        sort = request.args.get('sort', 'new')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        vendor_id = request.args.get('vendor_id')
        conn = get_db()
        cursor = conn.cursor()
        if vendor_id:
            cursor.execute('''
                SELECT p.*, u.full_name as author_name, u.avatar as author_avatar
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.vendor_id = ?
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (vendor_id, limit, offset))
        elif sort == 'top':
            cursor.execute('''
                SELECT p.*, u.full_name as author_name, u.avatar as author_avatar,
                       (p.upvotes - p.downvotes) as score
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY score DESC, p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        else:
            cursor.execute('''
                SELECT p.*, u.full_name as author_name, u.avatar as author_avatar
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        for post in posts:
            post['score'] = post['upvotes'] - post['downvotes']
        return jsonify(posts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (user_id, vendor_id, product_id, title, content, post_type, rating, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('vendor_id'),
            data.get('product_id'),
            data['title'],
            data['content'],
            data.get('post_type', 'review'),
            data.get('rating'),
            data.get('image_url') or data.get('image')
        ))
        post_id = cursor.lastrowid
        if data.get('rating') and data.get('vendor_id'):
            cursor.execute('''
                UPDATE vendors 
                SET rating = (SELECT AVG(rating) FROM posts WHERE vendor_id = ? AND rating IS NOT NULL),
                    review_count = (SELECT COUNT(*) FROM posts WHERE vendor_id = ? AND rating IS NOT NULL)
                WHERE id = ?
            ''', (data['vendor_id'], data['vendor_id'], data['vendor_id']))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": post_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.full_name as author_name, u.avatar as author_avatar
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        ''', (post_id,))
        post = cursor.fetchone()
        if not post:
            conn.close()
            return jsonify({"error": "Post not found"}), 404
        post_dict = dict(post)
        cursor.execute('''
            SELECT c.*, u.full_name as author_name, u.avatar as author_avatar
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        ''', (post_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        post_dict['comments'] = comments
        conn.close()
        return jsonify(post_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['POST'])
@login_required
def create_comment():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, parent_id, content)
            VALUES (?, ?, ?, ?)
        ''', (data['post_id'], user_id, data.get('parent_id'), data['content']))
        comment_id = cursor.lastrowid
        cursor.execute('UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?', (data['post_id'],))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": comment_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/votes', methods=['POST'])
@login_required
def vote():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        post_id = data['post_id']
        vote_type = data['vote_type']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, vote_type FROM votes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        existing = cursor.fetchone()
        if existing:
            if existing['vote_type'] == vote_type:
                cursor.execute('DELETE FROM votes WHERE id = ?', (existing['id'],))
                if vote_type == 1:
                    cursor.execute('UPDATE posts SET upvotes = upvotes - 1 WHERE id = ?', (post_id,))
                else:
                    cursor.execute('UPDATE posts SET downvotes = downvotes - 1 WHERE id = ?', (post_id,))
            else:
                cursor.execute('UPDATE votes SET vote_type = ? WHERE id = ?', (vote_type, existing['id']))
                if vote_type == 1:
                    cursor.execute('UPDATE posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', (post_id,))
                else:
                    cursor.execute('UPDATE posts SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', (post_id,))
        else:
            cursor.execute('INSERT INTO votes (user_id, post_id, vote_type) VALUES (?, ?, ?)', (user_id, post_id, vote_type))
            if vote_type == 1:
                cursor.execute('UPDATE posts SET upvotes = upvotes + 1 WHERE id = ?', (post_id,))
            else:
                cursor.execute('UPDATE posts SET downvotes = downvotes + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/votes/user/<int:user_id>', methods=['GET'])
def get_user_votes(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT post_id, vote_type FROM votes WHERE user_id = ?', (user_id,))
        votes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(votes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/activities', methods=['POST'])
@login_required
def create_activity():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activities (user_id, vendor_id, post_id, activity_type, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, data.get('vendor_id'), data.get('post_id'), data['activity_type'], json.dumps(data.get('metadata', {}))))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/activities/user/<int:user_id>', methods=['GET'])
def get_user_activities(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, v.business_name as vendor_name
            FROM activities a
            LEFT JOIN vendors v ON a.vendor_id = v.id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT 100
        ''', (user_id,))
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(activities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortlist', methods=['POST'])
@login_required
def add_to_shortlist():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        vendor_id = data['vendor_id']
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO shortlist (user_id, vendor_id) VALUES (?, ?)', (user_id, vendor_id))
            conn.commit()
            return jsonify({"success": True})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"message": "Already in shortlist"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortlist/user/<int:user_id>', methods=['GET'])
def get_shortlist(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.*
            FROM shortlist s
            JOIN vendors v ON s.vendor_id = v.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
        ''', (user_id,))
        vendors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(vendors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortlist/<int:vendor_id>/user/<int:user_id>', methods=['DELETE'])
def remove_from_shortlist(vendor_id, user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM shortlist WHERE user_id = ? AND vendor_id = ?', (user_id, vendor_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        vendor_id = request.args.get('vendor_id')
        conn = get_db()
        cursor = conn.cursor()
        if vendor_id:
            cursor.execute('SELECT * FROM products WHERE vendor_id = ? AND is_active = 1', (vendor_id,))
        else:
            cursor.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY rating DESC LIMIT 50')
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/user/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT preferences FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        preferences = json.loads(user['preferences']) if user and user['preferences'] else {}
        interests = preferences.get('interests', [])
        cursor.execute('SELECT DISTINCT vendor_id FROM activities WHERE user_id = ? AND vendor_id IS NOT NULL', (user_id,))
        viewed = [row['vendor_id'] for row in cursor.fetchall()]
        cursor.execute('SELECT vendor_id FROM shortlist WHERE user_id = ?', (user_id,))
        saved = [row['vendor_id'] for row in cursor.fetchall()]
        excluded = list(set(viewed + saved))
        if interests:
            placeholders = ','.join(['?'] * len(interests))
            if excluded:
                excluded_placeholders = ','.join(['?'] * len(excluded))
                cursor.execute(f'''
                    SELECT * FROM vendors 
                    WHERE category IN ({placeholders})
                    AND id NOT IN ({excluded_placeholders})
                    AND is_active = 1
                    ORDER BY rating DESC, review_count DESC
                    LIMIT 20
                ''', interests + excluded)
            else:
                cursor.execute(f'''
                    SELECT * FROM vendors 
                    WHERE category IN ({placeholders})
                    AND is_active = 1
                    ORDER BY rating DESC, review_count DESC
                    LIMIT 20
                ''', interests)
        else:
            if excluded:
                excluded_placeholders = ','.join(['?'] * len(excluded))
                cursor.execute(f'''
                    SELECT * FROM vendors 
                    WHERE id NOT IN ({excluded_placeholders})
                    AND is_active = 1
                    ORDER BY rating DESC, review_count DESC
                    LIMIT 20
                ''', excluded)
            else:
                cursor.execute('''
                    SELECT * FROM vendors 
                    WHERE is_active = 1
                    ORDER BY rating DESC, review_count DESC
                    LIMIT 20
                ''')
        recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({"vendors": [], "products": []})
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vendors 
            WHERE (business_name LIKE ? OR category LIKE ? OR address LIKE ?)
            AND is_active = 1
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        vendors = [dict(row) for row in cursor.fetchall()]
        cursor.execute('''
            SELECT p.*, v.business_name as vendor_name 
            FROM products p
            JOIN vendors v ON p.vendor_id = v.id
            WHERE p.name LIKE ? AND p.is_active = 1
            LIMIT 20
        ''', (f'%{query}%',))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"vendors": vendors, "products": products})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user_id, vendor_id, message, direction) VALUES (?, ?, ?, "outgoing")',
                       (user_id, data.get('vendor_id'), data.get('message')))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample-requests', methods=['POST'])
@login_required
def create_sample_request():
    try:
        data = request.get_json()
        user_id = int(request.headers.get('X-User-Id'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO sample_requests 
                          (user_id, vendor_id, product_id, message, location, preferred_date, status)
                          VALUES (?, ?, ?, ?, ?, ?, 'pending')''',
                       (user_id, data.get('vendor_id'), data.get('product_id'),
                        data.get('message'), data.get('location'), data.get('preferred_date')))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Lako API secure version running"})

if __name__ == '__main__':
    print("\n" + "="*80)
    print("LAKO - Street Food Discovery System")
    print("AITE Capstone Project 2026-2027 - SECURE BUILD")
    print("Backend: http://localhost:5000")
    print("="*80)
    app.run(debug=False, host='0.0.0.0', port=5000)
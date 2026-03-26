from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(os.path.dirname(__file__), 'lako.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
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
            logo TEXT,
            messenger_id TEXT,
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
            image TEXT,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
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
            vote_type INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            UNIQUE(user_id, post_id)
        )
    ''')
    
    # Activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendor_id INTEGER,
            activity_type TEXT NOT NULL,
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
    
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest(), salt

def verify_password(password, salt, password_hash):
    return password_hash == hashlib.sha256((password + salt).encode()).hexdigest()

init_db()

# ============= USER ENDPOINTS =============
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        full_name = data.get('full_name', '')
        password = data.get('password', '')
        preferences = data.get('preferences', {})
        
        if not email.endswith('@gmail.com'):
            return jsonify({"error": "Only Gmail addresses allowed"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        password_hash, salt = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (full_name, email, password_hash, salt, preferences)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, email, password_hash, salt, json.dumps(preferences)))
        
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
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not email.endswith('@gmail.com'):
            return jsonify({"error": "Only Gmail addresses allowed"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, full_name, email, preferences FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 401
        
        cursor.execute('SELECT password_hash, salt FROM users WHERE id = ?', (user['id'],))
        auth = cursor.fetchone()
        conn.close()
        
        if not verify_password(password, auth['salt'], auth['password_hash']):
            return jsonify({"error": "Invalid password"}), 401
        
        return jsonify({
            "success": True,
            "id": user['id'],
            "full_name": user['full_name'],
            "email": user['email'],
            "preferences": json.loads(user['preferences']) if user['preferences'] else {}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user['id'],
        "full_name": user['full_name'],
        "email": user['email'],
        "created_at": user['created_at']
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        if 'full_name' in data:
            cursor.execute('UPDATE users SET full_name = ? WHERE id = ?', (data['full_name'], user_id))
        
        if 'preferences' in data:
            cursor.execute('UPDATE users SET preferences = ? WHERE id = ?', (json.dumps(data['preferences']), user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= VENDOR ENDPOINTS =============
@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors ORDER BY rating DESC, review_count DESC')
        vendors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(vendors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendors', methods=['POST'])
def create_vendor():
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vendors (business_name, address, latitude, longitude, category, description, logo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('business_name'),
            data.get('address'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('category'),
            data.get('description'),
            data.get('logo')
        ))
        
        vendor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "id": vendor_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors WHERE id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        conn.close()
        
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        
        return jsonify(dict(vendor))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= MESSENGER INTEGRATION ENDPOINT =============
@app.route('/api/vendors/<int:vendor_id>/messenger', methods=['GET'])
def get_messenger_link(vendor_id):
    """Get Messenger link for vendor"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT messenger_id, business_name FROM vendors WHERE id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        conn.close()
        
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        
        if vendor['messenger_id']:
            # Use vendor's custom Messenger ID
            messenger_url = f"https://m.me/{vendor['messenger_id']}"
        else:
            # Default to Lako page
            messenger_url = "https://m.me/lakoapp"
        
        return jsonify({
            "messenger_url": messenger_url,
            "business_name": vendor['business_name']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= POST ENDPOINTS =============
@app.route('/api/posts', methods=['GET'])
def get_posts():
    try:
        sort = request.args.get('sort', 'new')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        vendor_id = request.args.get('vendor_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if vendor_id:
            cursor.execute('''
                SELECT p.*, u.full_name as author_name
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.vendor_id = ?
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (vendor_id, limit, offset))
        elif sort == 'new':
            cursor.execute('''
                SELECT p.*, u.full_name as author_name
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        elif sort == 'top':
            cursor.execute('''
                SELECT p.*, u.full_name as author_name, (p.upvotes - p.downvotes) as score
                FROM posts p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY score DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        else:
            cursor.execute('''
                SELECT p.*, u.full_name as author_name
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
def create_post():
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts (user_id, vendor_id, title, content, post_type, rating, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'],
            data.get('vendor_id'),
            data['title'],
            data['content'],
            data.get('post_type', 'text'),
            data.get('rating'),
            data.get('image_url') or data.get('image')
        ))
        
        post_id = cursor.lastrowid
        
        if data.get('rating') and data.get('vendor_id'):
            cursor.execute('''
                UPDATE vendors SET rating = (
                    SELECT AVG(rating) FROM posts WHERE vendor_id = ? AND rating IS NOT NULL
                ), review_count = (
                    SELECT COUNT(*) FROM posts WHERE vendor_id = ? AND rating IS NOT NULL
                ) WHERE id = ?
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
            SELECT p.*, u.full_name as author_name
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        ''', (post_id,))
        post = cursor.fetchone()
        
        if not post:
            conn.close()
            return jsonify({"error": "Post not found"}), 404
        
        post_dict = dict(post)
        post_dict['score'] = post_dict['upvotes'] - post_dict['downvotes']
        
        # Get comments for this post
        cursor.execute('''
            SELECT c.*, u.full_name as author_name
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        ''', (post_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        
        for comment in comments:
            comment['score'] = comment['upvotes'] - comment['downvotes']
        
        post_dict['comments'] = comments
        conn.close()
        
        return jsonify(post_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= COMMENT ENDPOINTS =============
@app.route('/api/comments', methods=['POST'])
def create_comment():
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, parent_id, content)
            VALUES (?, ?, ?, ?)
        ''', (
            data['post_id'],
            data['user_id'],
            data.get('parent_id'),
            data['content']
        ))
        
        comment_id = cursor.lastrowid
        cursor.execute('UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?', (data['post_id'],))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "id": comment_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= VOTE ENDPOINTS =============
@app.route('/api/votes', methods=['POST'])
def vote():
    try:
        data = request.get_json()
        user_id = data['user_id']
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

# ============= ACTIVITY ENDPOINTS =============
@app.route('/api/activities', methods=['POST'])
def create_activity():
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activities (user_id, vendor_id, activity_type)
            VALUES (?, ?, ?)
        ''', (data['user_id'], data.get('vendor_id'), data['activity_type']))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "id": activity_id})
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
            LIMIT 50
        ''', (user_id,))
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(activities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= SHORTLIST ENDPOINTS =============
@app.route('/api/shortlist', methods=['POST'])
def add_to_shortlist():
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO shortlist (user_id, vendor_id) VALUES (?, ?)', (data['user_id'], data['vendor_id']))
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
            SELECT v.id, v.business_name, v.address, v.category, v.rating, v.logo, v.messenger_id
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

# ============= RECOMMENDATIONS ENDPOINT =============
@app.route('/api/recommendations/user/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user's preferences
        cursor.execute('SELECT preferences FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        preferences = json.loads(user['preferences']) if user and user['preferences'] else {}
        interests = preferences.get('interests', [])
        
        # Get viewed vendors
        cursor.execute('SELECT DISTINCT vendor_id FROM activities WHERE user_id = ? AND vendor_id IS NOT NULL', (user_id,))
        viewed = [row['vendor_id'] for row in cursor.fetchall()]
        
        # Get saved vendors
        cursor.execute('SELECT vendor_id FROM shortlist WHERE user_id = ?', (user_id,))
        saved = [row['vendor_id'] for row in cursor.fetchall()]
        
        excluded = list(set(viewed + saved))
        
        # Recommend based on interests
        if interests:
            placeholders = ','.join(['?'] * len(interests))
            excluded_placeholders = ','.join(['?'] * len(excluded)) if excluded else '0'
            cursor.execute(f'''
                SELECT * FROM vendors 
                WHERE category IN ({placeholders})
                AND id NOT IN ({excluded_placeholders})
                ORDER BY rating DESC, review_count DESC
                LIMIT 20
            ''', interests + excluded)
        else:
            excluded_placeholders = ','.join(['?'] * len(excluded)) if excluded else '0'
            cursor.execute(f'''
                SELECT * FROM vendors 
                WHERE id NOT IN ({excluded_placeholders})
                ORDER BY rating DESC, review_count DESC
                LIMIT 20
            ''', excluded)
        
        recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Lako API is running!"})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("LAKO CUSTOMER APP API")
    print("="*60)
    print("\nBackend running on: http://localhost:5000")
    print("Frontend should run on: http://localhost:5500")
    print("\nAPI Test: http://localhost:5000/api/test")
    print("API Base for Frontend: http://localhost:5000/api")
    print("\nMessenger Integration:")
    print("- Chat opens Messenger app directly")
    print("- Vendor can set custom messenger_id")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
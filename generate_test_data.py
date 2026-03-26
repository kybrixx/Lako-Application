#!/usr/bin/env python3
"""
Lako Test Data Generator
Adds sample vendors and posts for testing
"""

import requests
import json
import time

API_BASE = "http://localhost:5000/api"
VENDORS_DATA = [
    {
        "business_name": "Maria's Chicken Isaw",
        "address": "123 Market Street, Tiaong, Quezon",
        "latitude": 13.9500,
        "longitude": 121.3167,
        "category": "Isaw",
        "description": "Grilled chicken intestines with special sauce. Best seller!"
    },
    {
        "business_name": "Juan's BBQ Skewers",
        "address": "456 Main Avenue, Tiaong, Quezon",
        "latitude": 13.9520,
        "longitude": 121.3185,
        "category": "BBQ",
        "description": "Authentic Filipino BBQ with marinated meat perfection"
    },
    {
        "business_name": "Siomai House",
        "address": "789 Commercial Road, Tiaong, Quezon",
        "latitude": 13.9480,
        "longitude": 121.3145,
        "category": "Siomai",
        "description": "Homemade siomai fresh from the steamer"
    },
    {
        "business_name": "Kwek-Kwek Corner",
        "address": "321 Food Street, Tiaong, Quezon",
        "latitude": 13.9540,
        "longitude": 121.3120,
        "category": "Kwek-Kwek",
        "description": "Crispy fried quail eggs in golden batter"
    },
    {
        "business_name": "Fishball Express",
        "address": "654 Beach Road, Tiaong, Quezon",
        "latitude": 13.9470,
        "longitude": 121.3200,
        "category": "Fishball",
        "description": "Fresh fishballs with special dipping sauce"
    }
]

def create_vendor(vendor_data):
    """Create a vendor via API"""
    try:
        response = requests.post(f"{API_BASE}/vendors", json=vendor_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Created vendor: {vendor_data['business_name']} (ID: {data['id']})")
            return data['id']
        else:
            print(f"✗ Failed to create vendor: {vendor_data['business_name']}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error creating vendor: {str(e)}")
        return None

def create_test_user():
    """Create a test user for posting"""
    user_data = {
        "full_name": "Test Foodie",
        "email": "testfoodie@gmail.com",
        "phone": "09123456789",
        "password": "test123"
    }
    try:
        response = requests.post(f"{API_BASE}/register", json=user_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Created test user (ID: {data['id']})")
            return data['id']
        else:
            print(f"! Test user might already exist: testfoodie@gmail.com")
            # Try to login
            response = requests.post(f"{API_BASE}/login", json={
                "email": "testfoodie@gmail.com",
                "password": "test123"
            })
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Logged in as test user (ID: {data['id']})")
                return data['id']
    except Exception as e:
        print(f"✗ Error with test user: {str(e)}")
    return None

def create_sample_posts(user_id, vendor_ids):
    """Create sample posts"""
    posts = [
        {
            "vendor_id": vendor_ids[0],
            "title": "Best isaw in town!",
            "content": "Maria's chicken isaw is absolutely delicious! Crispy outside, tender inside. Highly recommended!",
            "rating": 5,
            "post_type": "review"
        },
        {
            "vendor_id": vendor_ids[1],
            "title": "BBQ perfection",
            "content": "Juan's BBQ skewers are simply amazing. The meat is so flavorful and perfectly charred.",
            "rating": 5,
            "post_type": "review"
        },
        {
            "vendor_id": vendor_ids[2],
            "title": "Fresh siomai daily",
            "content": "Always fresh, always steaming hot. Siomai House never disappoints!",
            "rating": 4,
            "post_type": "review"
        },
        {
            "vendor_id": vendor_ids[3],
            "title": "Crispy and golden",
            "content": "The kwek-kwek here is consistently crispy. Love the dipping sauce too!",
            "rating": 4,
            "post_type": "review"
        },
        {
            "vendor_id": vendor_ids[4],
            "title": "Fishballs for lunch",
            "content": "Quick, affordable, and delicious. Perfect street food!",
            "rating": 3,
            "post_type": "review"
        }
    ]
    
    if not user_id:
        print("! Skipping posts - no user created")
        return
    
    for post in posts:
        post['user_id'] = user_id
        try:
            response = requests.post(f"{API_BASE}/posts", json=post)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Created post: {post['title']} (ID: {data['id']})")
            else:
                print(f"✗ Failed to create post: {post['title']}")
        except Exception as e:
            print(f"✗ Error creating post: {str(e)}")

def main():
    print("\n" + "="*50)
    print("🍜 LAKO TEST DATA GENERATOR")
    print("="*50 + "\n")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/test")
        if response.status_code != 200:
            print("✗ API not responding. Make sure backend is running:")
            print("  python3 PublicWebApp/Backendpwa/app.py")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API at http://localhost:5000")
        print("  Make sure backend is running:")
        print("  python3 PublicWebApp/Backendpwa/app.py")
        return
    
    print("✓ API is running!\n")
    
    # Create test user
    print("Creating test user...")
    user_id = create_test_user()
    print()
    
    # Create vendors
    print("Creating test vendors...")
    vendor_ids = []
    for vendor_data in VENDORS_DATA:
        vendor_id = create_vendor(vendor_data)
        if vendor_id:
            vendor_ids.append(vendor_id)
        time.sleep(0.5)
    print()
    
    # Create sample posts
    if vendor_ids and user_id:
        print("Creating sample posts...")
        create_sample_posts(user_id, vendor_ids)
        print()
    
    print("="*50)
    print("✓ Test data generation complete!")
    print("="*50 + "\n")
    
    print("Next steps:")
    print("1. Open the app: http://localhost:8000/index.html")
    print("2. Login with: testfoodie@gmail.com / test123")
    print("3. You should see the vendors on the map!")
    print()

if __name__ == "__main__":
    main()

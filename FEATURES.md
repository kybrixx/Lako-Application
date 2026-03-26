# Lako - Street Food Discovery & Navigation App

## 🍜 Overview
Lako is a mobile-first web application that helps users discover street food vendors nearby using real-time location tracking, geofencing, and interactive map navigation.

## ✨ Features Completed

### 1. **Real-Time Location Tracking** ✅
- Uses HTML5 Geolocation API with continuous updates
- High-precision location (±accuracy shown in console)
- Automatic map centering when location changes
- Location permission handling with user feedback

### 2. **Map Navigation** ✅
- **Leaflet.js Integration**: Interactive map display
- **Vendor Markers**: Color-coded by rating (green >= 4, yellow >= 3, red < 3)
- **User Location**: Displayed with distinct marker
- **Geofence Visualization**: Shows search radius as circle overlay
- **Map Controls**:
  - Center location button: Snap to current position
  - Refresh button: Update vendor locations
  - Zoom & pan

### 3. **Navigation to Vendors** ✅
Enhanced navigation with platform detection:
- **Mobile**: Uses native maps app (Google Maps on Android, Apple Maps on iOS)
- **Web**: Opens Google Maps directions in new tab
- Walking direction mode by default
- Toast notifications for successful navigation

### 4. **Search Functionality** ✅
New dedicated Search tab with:
- **Vendor Search**: By business name or category
- **Post Search**: By title or content
- Tab-based filtering (Vendors | Posts)
- Real-time search results

### 5. **Geofencing & Notifications** ✅
- 100m geofence alerts for nearby vendors
- Native browser notifications
- Toast notifications with vendor details
- Permission requests with graceful degradation

### 6. **Complete CRUD Operations** ✅
- **Users**: Register, Login, Profile management
- **Vendors**: Create, View, Filter by location
- **Posts**: Create with ratings, Images, comments
- **Votes**: Upvote/Downvote posts
- **Shortlist**: Save favorite vendors
- **Comments**: Add comments to posts

### 7. **User Preferences** ✅
- Theme selection (5 color themes)
- Discovery radius adjustment (0.5-2 km)
- Category filtering for food types
- Location tracking toggle
- Notification preferences

## 🚀 Setup & Installation

### Backend Requirements
```bash
cd /workspaces/Lako-Application
python3 -m venv venv
source venv/bin/activate
pip install -r PublicWebApp/Backendpwa/requirements.txt
```

### Start Backend Server
```bash
cd PublicWebApp/Backendpwa
python3 app.py
```

Server will run on: `http://localhost:5000`

### Frontend
Open in browser:
```
file:///workspaces/Lako-Application/PublicWebApp/Frontendpwa/index.html
```

Or serve with HTTP server:
```bash
cd PublicWebApp/Frontendpwa
python3 -m http.server 8000
# Then open: http://localhost:8000/index.html
```

## 📱 App Flow

### 1. **Landing Page**
- Login with Gmail (test: any @gmail.com account)
- Register new account

### 2. **Main App Tabs**
- **Feed**: Foodie posts sorted by newest/trending
- **Map**: Interactive map with vendors and your location
- **Nearby**: List of vendors within set radius
- **Search**: Find vendors and posts
- **Profile**: Settings, themes, preferences

### 3. **Vendor Details Modal**
- Star ratings and reviews
- Distance indicator
- Navigate, Chat, Save buttons
- Recent reviews section

### 4. **Create Posts**
- Select vendor
- Add title, rating, image URL, content
- Share food experiences and reviews

## 🗄️ Database Schema

### Tables
- **users**: Account info, preferences
- **vendors**: Business details, location, ratings
- **posts**: Food reviews and experiences
- **comments**: Post discussions
- **votes**: User engagement (upvote/downvote)
- **activities**: User interactions (navigate, chat, view)
- **shortlist**: Saved vendors

## 🔑 Key API Endpoints

```
POST   /api/register              - Create account
POST   /api/login                 - Login
GET    /api/vendors               - Get all vendors
GET    /api/posts?sort=new        - Get posts
POST   /api/posts                 - Create post
GET    /api/posts/<id>            - Get post with comments
POST   /api/comments              - Add comment
POST   /api/votes                 - Vote on post
POST   /api/shortlist             - Save vendor
GET    /api/shortlist/user/<id>   - Get saved vendors
POST   /api/activities            - Log activity (navigate, chat, view)
GET    /api/vendors/<id>/messenger - Get vendor Messenger link
```

## 🎯 Location Tracking Details

### How It Works
1. App requests geolocation permission on startup
2. Watches device location continuously
3. Updates user marker on map in real-time
4. Checks geofence for nearby vendors (100m radius)
5. Filters nearby vendors based on set radius (default 2km)
6. Shows distance and sorting by proximity

### Accuracy
- High accuracy mode enabled: `enableHighAccuracy: true`
- Maximum age: 3 seconds (fresh location data)
- Timeout: 10 seconds per request
- Accuracy indicator in console log

### Location Toggle
- Users can enable/disable location tracking in Profile settings
- Affects geofence alerts and nearby vendor discovery
- Gracefully degrades if location unavailable

## 🗺️ Map Features

### Vendor Markers
- Click marker to see popup with:
  - Business name
  - Rating and review count
  - Address
  - Navigate button (takes you to vendor location)
  - Chat button (Messenger integration)

### User Location
- Blue circle marker showing your position
- Can click to open popup
- Center button keeps map focused on you

### Search Radius
- Visual circle overlay on map
- Adjustable in Profile settings
- Affects "Nearby" tab filtering

## 💬 Messenger Integration
- Direct Messenger chat with vendors
- Falls back to Lako page if vendor ID not set
- Button in vendor detail modal and map popup

## 🎨 UI/UX Enhancements

### Responsive Design
- Mobile-first approach
- Touch-optimized buttons
- Fixed bottom navigation

### Accessibility
- Font Awesome icons for clarity
- Color-coded elements
- Large touch targets (48px buttons)

### Notifications
- Toast messages for actions
- Native browser notifications
- Geofence proximity alerts

## 📊 Sample Test Data

### Suggested Test Vendors (to add via API)
```json
{
  "business_name": "Maria's Chicken Isaw",
  "address": "Market Street, Tiaong",
  "latitude": 13.9500,
  "longitude": 121.3167,
  "category": "Isaw",
  "description": "Grilled chicken intestines",
  "price_range": "₱20-₱50"
}
```

## 🔧 Troubleshooting

### Location Not Updating
- Check browser permissions for Geolocation
- Enable "Always Allow" for this site
- Check console for error messages
- Ensure location toggle is ON in Profile

### Map Not Loading
- Verify internet connection
- Check if OpenStreetMap tiles are accessible
- Reload page to reinitialize map
- Clear browser cache

### API Connection Issues
- Ensure backend is running: `http://localhost:5000/api/test`
- Check CORS settings (enabled in Flask)
- Verify API_BASE URL is correct in HTML

### Notifications Not Showing
- Enable notifications when prompted
- Check browser notification settings
- Ensure Notification API is supported
- Check console for permission denial

## 🚀 Recent Improvements (v2.1)

1. **Enhanced Location Tracking**
   - Better error handling with specific messages
   - Accuracy feedback in console
   - Configurable tracking intervals

2. **Improved Map**
   - Geofence circle visualization
   - Better marker popups with distance info
   - Vendor rating color coding

3. **Search Tab**
   - New dedicated search interface
   - Dual search (vendors + posts)
   - Real-time filtering

4. **Better Navigation**
   - Platform detection for native apps
   - Walking directions by default
   - Fallback to web browser

5. **User Preferences**
   - Location tracking toggle
   - Better geolocation permission handling
   - Improved notification settings

6. **Code Quality**
   - Better error handling throughout
   - Location accuracy logs
   - Improved console feedback

## 📝 Notes

- All data stored locally in SQLite database
- Passwords hashed with SHA256 + salt
- CORS enabled for development
- Session data stored in localStorage
- Preferences saved in browser

## 🎯 Future Enhancements

- [ ] Image Upload to server
- [ ] Real-time vendor availability
- [ ] Advanced filtering by rating/price
- [ ] User following/favorites
- [ ] Post comments thread view
- [ ] Vendor analytics dashboard
- [ ] PWA installation support
- [ ] Offline mode

## 👨‍💻 Developers

- Kyle Morillo
- Alexander Millicamp

**Project**: Lako - AITE Capstone Project
**Version**: 2.1
**Last Updated**: March 26, 2026

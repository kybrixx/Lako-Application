// ============= LAKO CUSTOMER APP =============
// Capstone Project: Asian Institute of Technology and Education
// Project: Lako: Passive GPS Proximity Discovery of Micro Retail Vendors
// Location: Quipot to Poblacion 1-4, Tiaong, Quezon
// Developers: Kyle Brian M. Morillo & Alexander Collin Millicamp
// Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325

class LakoCustomerApp {
    constructor() {
        this.currentUser = null;
        this.deviceId = this.getDeviceId();
        this.currentLocation = null;
        this.map = null;
        this.markers = [];
        this.trafficLayer = null;
        this.trafficChart = null;
        this.vendors = [];
        this.posts = [];
        this.comments = [];
        this.votes = [];
        this.activities = [];
        this.shortlist = [];
        this.searchHistory = [];
        this.currentTheme = localStorage.getItem('lako_theme') || 'orange';
        this.userPreferences = {
            interests: [],
            theme: this.currentTheme,
            notifications: {
                posts: true,
                comments: true,
                suggestions: true,
                promos: false,
                traffic: false
            },
            radius: 10,
            feedContent: {
                reviews: true,
                questions: true,
                text: true
            },
            privacy: {
                shareLocation: true,
                trackActivity: true,
                personalizedAds: true
            }
        };
        this.currentSort = 'hot';
        this.currentPage = 0;
        this.hasMore = true;
        this.loading = false;
        this.selectedVendor = null;
        this.mapRadius = 10;
        this.currentPostId = null;
        this.currentSearchTab = 'vendors';
        this.filters = {
            category: '',
            minRating: 0,
            timeRange: 'week'
        };
        this.mapFilters = {
            category: '',
            minRating: 0
        };
        this.streetFoodTypes = ['BBQ', 'Fishball', 'Isaw', 'Kwek-Kwek', 'Turon', 'Siomai', 'Burgers', 'Pancit', 'Rice Meals', 'Desserts', 'Beverages'];
        this.init();
    }
    
    async init() {
        this.applyTheme(this.currentTheme);
        await this.checkEULA();
        this.setupEventListeners();
        this.loadSearchHistory();
        this.splashScreen();
    }
    
    getDeviceId() {
        let id = localStorage.getItem('lako_device_id');
        if (!id) {
            id = 'device_' + Math.random().toString(36).substr(2, 16);
            localStorage.setItem('lako_device_id', id);
        }
        return id;
    }
    
    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('lako_theme', theme);
        this.currentTheme = theme;
        
        document.querySelectorAll('.theme-btn').forEach(btn => {
            if (btn.dataset.theme === theme) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const colors = {
                orange: '#e67e22',
                green: '#28a745',
                blue: '#007bff',
                red: '#dc3545'
            };
            metaThemeColor.setAttribute('content', colors[theme] || '#e67e22');
        }
        
        if (this.currentUser) {
            this.userPreferences.theme = theme;
            this.saveUserPreferences();
        }
    }
    
    async checkEULA() {
        try {
            const response = await fetch('/api/eula/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: this.deviceId })
            });
            const data = await response.json();
            
            if (!data.accepted) {
                const eulaHtml = data.eula_text.replace(/\n/g, '<br>');
                document.getElementById('eula-text').innerHTML = eulaHtml;
                document.getElementById('eula-modal').style.display = 'flex';
                
                document.getElementById('accept-eula').onclick = () => this.acceptEULA(data.device_id);
                document.getElementById('decline-eula').onclick = () => this.declineEULA();
            } else {
                this.splashScreen();
            }
        } catch (error) {
            console.error('EULA check failed:', error);
            this.splashScreen();
        }
    }
    
    async acceptEULA(deviceId) {
        try {
            await fetch('/api/eula/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: deviceId })
            });
            document.getElementById('eula-modal').style.display = 'none';
            this.splashScreen();
        } catch (error) {
            console.error('EULA accept failed:', error);
        }
    }
    
    declineEULA() {
        alert('You must accept the EULA to use Lako Street Food App.');
    }
    
    splashScreen() {
        setTimeout(() => {
            const userId = localStorage.getItem('lako_user_id');
            if (userId) {
                this.loadUser(userId);
            } else {
                this.showLanding();
            }
        }, 2000);
    }
    
    showLanding() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('landing').classList.remove('hidden');
    }
    
    showLogin() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('login').classList.remove('hidden');
    }
    
    showRegister() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('register').classList.remove('hidden');
    }
    
    showForgot() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('forgot').classList.remove('hidden');
    }
    
    showMain() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('main').classList.remove('hidden');
        this.loadAllData();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Auth buttons
        document.getElementById('login-btn')?.addEventListener('click', () => this.showLogin());
        document.getElementById('signup-btn')?.addEventListener('click', () => this.showRegister());
        document.getElementById('back-to-landing')?.addEventListener('click', () => this.showLanding());
        document.getElementById('back-to-landing2')?.addEventListener('click', () => this.showLanding());
        document.getElementById('back-to-login')?.addEventListener('click', () => this.showLogin());
        document.getElementById('forgot-link')?.addEventListener('click', () => this.showForgot());
        
        // Forms
        document.getElementById('login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        document.getElementById('register-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });
        
        document.getElementById('forgot-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.forgotPassword();
        });
        
        // Main app buttons
        document.getElementById('fab-create-post')?.addEventListener('click', () => this.showCreatePostModal());
        document.getElementById('refresh-suggestions')?.addEventListener('click', () => this.loadSuggestions());
        document.getElementById('refresh-location')?.addEventListener('click', () => this.centerMap());
        document.getElementById('set-radius')?.addEventListener('click', () => this.showRadiusModal());
        document.getElementById('traffic-toggle')?.addEventListener('click', () => this.showTrafficAnalytics());
        document.getElementById('feed-filter-btn')?.addEventListener('click', () => this.showFeedFilters());
        document.getElementById('search-btn')?.addEventListener('click', () => this.search());
        document.getElementById('search-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        document.getElementById('clear-history')?.addEventListener('click', () => this.clearAllHistory());
        document.getElementById('edit-profile')?.addEventListener('click', () => this.editProfile());
        document.getElementById('change-password')?.addEventListener('click', () => this.changePassword());
        document.getElementById('preferences-btn')?.addEventListener('click', () => this.showPreferences());
        document.getElementById('notification-settings')?.addEventListener('click', () => this.showNotificationSettings());
        document.getElementById('privacy-settings')?.addEventListener('click', () => this.showPrivacySettings());
        document.getElementById('delete-account')?.addEventListener('click', () => this.deleteAccount());
        document.getElementById('logout-main')?.addEventListener('click', () => this.logout());
        
        // Feed sorting
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentSort = btn.dataset.sort;
                this.currentPage = 0;
                this.hasMore = true;
                document.getElementById('feed-container').innerHTML = '';
                this.loadFeed();
            });
        });
        
        // Search tabs
        document.querySelectorAll('.search-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.search-tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentSearchTab = btn.dataset.searchTab;
                this.search();
            });
        });
        
        // Filter modals
        document.getElementById('apply-feed-filters')?.addEventListener('click', () => this.applyFeedFilters());
        document.getElementById('clear-feed-filters')?.addEventListener('click', () => this.clearFeedFilters());
        document.getElementById('apply-map-filters')?.addEventListener('click', () => this.applyMapFilters());
        document.getElementById('clear-map-filters')?.addEventListener('click', () => this.clearMapFilters());
        document.getElementById('apply-radius')?.addEventListener('click', () => this.applyRadius());
        
        // Preferences modal
        document.getElementById('save-preferences')?.addEventListener('click', () => this.savePreferences());
        document.getElementById('save-notifications')?.addEventListener('click', () => this.saveNotificationSettings());
        document.getElementById('save-privacy')?.addEventListener('click', () => this.savePrivacySettings());
        
        // Radius slider
        const radiusSlider = document.getElementById('radius-slider');
        if (radiusSlider) {
            radiusSlider.addEventListener('input', (e) => {
                document.getElementById('radius-value').textContent = e.target.value;
            });
        }
        
        // Close modals
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('create-post-modal')?.classList.add('hidden');
                document.getElementById('post-detail-modal')?.classList.add('hidden');
                document.getElementById('feed-filter-modal')?.classList.add('hidden');
                document.getElementById('map-filter-modal')?.classList.add('hidden');
                document.getElementById('radius-modal')?.classList.add('hidden');
                document.getElementById('traffic-modal')?.classList.add('hidden');
                document.getElementById('preferences-modal')?.classList.add('hidden');
                document.getElementById('notification-modal')?.classList.add('hidden');
                document.getElementById('privacy-modal')?.classList.add('hidden');
            });
        });
        
        // Create post form
        document.getElementById('create-post-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createPost();
        });
        
        document.getElementById('post-type')?.addEventListener('change', (e) => {
            const isReview = e.target.value === 'review';
            document.getElementById('rating-container').classList.toggle('hidden', !isReview);
            document.getElementById('vendor-select-container').classList.toggle('hidden', !isReview);
        });
        
        // Star rating
        document.querySelectorAll('.star-rating i').forEach(star => {
            star.addEventListener('click', () => {
                const rating = star.dataset.rating;
                document.getElementById('post-rating').value = rating;
                document.querySelectorAll('.star-rating i').forEach((s, i) => {
                    if (i < rating) {
                        s.className = 'fas fa-star';
                    } else {
                        s.className = 'far fa-star';
                    }
                });
            });
        });
        
        // Add comment form
        document.getElementById('add-comment-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addComment();
        });
    }
    
    async login() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        if (!email.endsWith('@gmail.com')) {
            alert('Only Gmail addresses are allowed');
            return;
        }
        
        try {
            const response = await fetch('/api/users/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, device_id: this.deviceId })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('lako_user_id', data.id);
                this.currentUser = data;
                await this.loadUserPreferences();
                this.showMain();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }
    
    async register() {
        const fullName = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        
        if (!email.endsWith('@gmail.com')) {
            alert('Only Gmail addresses are allowed');
            return;
        }
        
        const interests = Array.from(document.querySelectorAll('#interest-preferences input:checked'))
            .map(cb => cb.value);
        
        if (interests.length > 5) {
            alert('Please select up to 5 street food interests');
            return;
        }
        
        const preferences = {
            interests: interests,
            theme: this.currentTheme,
            notifications: {
                posts: document.getElementById('reg-notify-posts')?.checked || false,
                comments: document.getElementById('reg-notify-comments')?.checked || false,
                suggestions: document.getElementById('reg-notify-suggestions')?.checked || false,
                promos: document.getElementById('reg-notify-promos')?.checked || false
            },
            radius: parseInt(document.getElementById('reg-radius')?.value || 10),
            feedContent: { reviews: true, questions: true, text: true }
        };
        
        try {
            const response = await fetch('/api/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    full_name: fullName, 
                    email, 
                    password, 
                    device_id: this.deviceId,
                    user_type: 'customer',
                    preferences: preferences
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Registration successful! Please login to discover street food.');
                this.showLogin();
            } else {
                alert(data.error || 'Registration failed');
            }
        } catch (error) {
            alert('Registration failed: ' + error.message);
        }
    }
    
    async forgotPassword() {
        const email = document.getElementById('forgot-email').value;
        alert('Password reset link sent to ' + email);
        this.showLogin();
    }
    
    async loadUser(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            const data = await response.json();
            if (response.ok) {
                this.currentUser = data;
                await this.loadUserPreferences();
                this.showMain();
            } else {
                this.showLanding();
            }
        } catch (error) {
            this.showLanding();
        }
    }
    
    async loadUserPreferences() {
        const savedPrefs = localStorage.getItem(`lako_prefs_${this.currentUser.id}`);
        if (savedPrefs) {
            const prefs = JSON.parse(savedPrefs);
            this.userPreferences = { ...this.userPreferences, ...prefs };
            if (prefs.theme) this.applyTheme(prefs.theme);
        }
    }
    
    saveUserPreferences() {
        if (this.currentUser) {
            const prefs = { ...this.userPreferences, theme: this.currentTheme };
            localStorage.setItem(`lako_prefs_${this.currentUser.id}`, JSON.stringify(prefs));
        }
    }
    
    async loadAllData() {
        await Promise.all([
            this.loadVendors(),
            this.loadPosts(),
            this.loadComments(),
            this.loadUserVotes(),
            this.loadUserActivities(),
            this.loadUserShortlist()
        ]);
        
        this.loadFeed();
        this.loadSuggestions();
        this.initMap();
        this.loadShortlist();
        this.loadActivities();
        this.updateProfileStats();
        this.loadSearchHistoryDisplay();
    }
    
    async loadVendors() {
        try {
            const response = await fetch('/api/vendors');
            this.vendors = await response.json();
            this.vendors.forEach(v => {
                if (!v.category) v.category = 'Street Food';
                if (!v.rating) v.rating = 0;
                if (!v.review_count) v.review_count = 0;
            });
        } catch (error) {
            console.error('Failed to load vendors:', error);
            this.vendors = [];
        }
    }
    
    async loadPosts() {
        try {
            const response = await fetch('/api/posts');
            this.posts = await response.json();
            this.posts.forEach(p => {
                p.score = (p.upvotes || 0) - (p.downvotes || 0);
            });
        } catch (error) {
            console.error('Failed to load posts:', error);
            this.posts = [];
        }
    }
    
    async loadComments() {
        try {
            const response = await fetch('/api/comments');
            this.comments = await response.json();
        } catch (error) {
            console.error('Failed to load comments:', error);
            this.comments = [];
        }
    }
    
    async loadUserVotes() {
        if (!this.currentUser) return;
        try {
            const response = await fetch(`/api/votes/user/${this.currentUser.id}`);
            this.votes = await response.json();
        } catch (error) {
            this.votes = [];
        }
    }
    
    async loadUserActivities() {
        if (!this.currentUser) return;
        try {
            const response = await fetch(`/api/activities/user/${this.currentUser.id}`);
            this.activities = await response.json();
        } catch (error) {
            this.activities = [];
        }
    }
    
    async loadUserShortlist() {
        if (!this.currentUser) return;
        try {
            const response = await fetch(`/api/shortlist/user/${this.currentUser.id}`);
            this.shortlist = await response.json();
        } catch (error) {
            this.shortlist = [];
        }
    }
    
    async loadFeed(reset = true) {
        if (reset) {
            this.currentPage = 0;
            this.hasMore = true;
            document.getElementById('feed-container').innerHTML = '';
        }
        
        if (this.loading || !this.hasMore) return;
        this.loading = true;
        
        const loadingDiv = document.getElementById('feed-loading');
        if (loadingDiv) loadingDiv.classList.remove('hidden');
        
        let filteredPosts = [...this.posts];
        
        filteredPosts = filteredPosts.filter(post => {
            if (post.post_type === 'review' && !this.userPreferences.feedContent.reviews) return false;
            if (post.post_type === 'question' && !this.userPreferences.feedContent.questions) return false;
            if (post.post_type === 'text' && !this.userPreferences.feedContent.text) return false;
            return true;
        });
        
        if (this.filters.category) {
            filteredPosts = filteredPosts.filter(post => {
                if (!post.vendor_id) return false;
                const vendor = this.vendors.find(v => v.id === post.vendor_id);
                return vendor && vendor.category === this.filters.category;
            });
        }
        
        if (this.filters.minRating > 0) {
            filteredPosts = filteredPosts.filter(post => {
                if (post.post_type !== 'review') return true;
                return (post.rating || 0) >= this.filters.minRating;
            });
        }
        
        if (this.currentSort === 'hot') {
            filteredPosts.sort((a, b) => (b.score + b.comment_count * 2) - (a.score + a.comment_count * 2));
        } else if (this.currentSort === 'new') {
            filteredPosts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        } else if (this.currentSort === 'top') {
            filteredPosts.sort((a, b) => b.score - a.score);
        } else if (this.currentSort === 'rising') {
            const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
            filteredPosts = filteredPosts.filter(p => new Date(p.created_at) > oneDayAgo);
            filteredPosts.sort((a, b) => (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes));
        }
        
        const start = this.currentPage * 10;
        const pagePosts = filteredPosts.slice(start, start + 10);
        
        if (pagePosts.length === 0) {
            this.hasMore = false;
        } else {
            this.currentPage++;
        }
        
        const container = document.getElementById('feed-container');
        for (const post of pagePosts) {
            const user = await this.getUser(post.user_id);
            const vendor = post.vendor_id ? this.vendors.find(v => v.id === post.vendor_id) : null;
            const userVote = this.votes.find(v => v.post_id === post.id);
            const foodIcon = this.getFoodIcon(post.title + ' ' + (vendor?.business_name || ''));
            
            const postHtml = `
                <div class="feed-card" data-post-id="${post.id}">
                    <div class="vote-section">
                        <button class="vote-up ${userVote?.vote_type === 1 ? 'voted' : ''}" data-post-id="${post.id}" data-vote="1"><i class="fas fa-arrow-up"></i></button>
                        <span class="vote-score" id="score-${post.id}">${post.score}</span>
                        <button class="vote-down ${userVote?.vote_type === -1 ? 'voted' : ''}" data-post-id="${post.id}" data-vote="-1"><i class="fas fa-arrow-down"></i></button>
                    </div>
                    <div class="post-content" onclick="app.showPostDetail(${post.id})">
                        <div class="post-meta">
                            <i class="fas fa-user-circle"></i> ${this.escapeHtml(user?.full_name || 'Foodie')}
                            <span class="post-time"> • ${this.formatTime(post.created_at)}</span>
                            ${vendor ? `<span class="post-vendor"> • <i class="fas fa-store"></i> ${this.escapeHtml(vendor.business_name)}</span>` : ''}
                            ${post.post_type === 'review' ? `<span class="post-badge"><i class="fas fa-star"></i> Food Review</span>` : ''}
                            ${post.post_type === 'question' ? `<span class="post-badge"><i class="fas fa-question-circle"></i> Food Question</span>` : ''}
                        </div>
                        <h3><i class="fas ${foodIcon}"></i> ${this.escapeHtml(post.title)}</h3>
                        <div class="post-content-text">${this.truncate(this.escapeHtml(post.content), 150)}</div>
                        ${post.rating ? `<div class="post-rating"><i class="fas fa-star"></i> ${post.rating}/5</div>` : ''}
                    </div>
                    <div class="post-actions">
                        <button class="comment-btn" data-post-id="${post.id}"><i class="fas fa-comment"></i> ${post.comment_count}</button>
                        <button class="share-btn" data-post-id="${post.id}"><i class="fas fa-share"></i> Share Food Find</button>
                        ${vendor ? `<button class="save-vendor-btn" data-vendor-id="${vendor.id}"><i class="fas fa-heart"></i> Save Food Spot</button>` : ''}
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', postHtml);
        }
        
        this.attachFeedEvents();
        
        if (loadingDiv) loadingDiv.classList.add('hidden');
        this.loading = false;
        
        window.onscroll = () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
                this.loadFeed(false);
            }
        };
    }
    
    getFoodIcon(text) {
        const lowerText = text.toLowerCase();
        if (lowerText.includes('bbq') || lowerText.includes('inihaw')) return 'fa-fire';
        if (lowerText.includes('fishball')) return 'fa-fish';
        if (lowerText.includes('isaw')) return 'fa-drumstick-bite';
        if (lowerText.includes('kwek') || lowerText.includes('tokneneng')) return 'fa-egg';
        if (lowerText.includes('turon') || lowerText.includes('banana')) return 'fa-apple-alt';
        if (lowerText.includes('siomai')) return 'fa-dumpling';
        if (lowerText.includes('burger')) return 'fa-hamburger';
        if (lowerText.includes('pancit') || lowerText.includes('noodle')) return 'fa-utensils';
        if (lowerText.includes('rice') || lowerText.includes('silog')) return 'fa-utensil-spoon';
        if (lowerText.includes('dessert') || lowerText.includes('halo')) return 'fa-ice-cream';
        if (lowerText.includes('milk tea') || lowerText.includes('beverage')) return 'fa-coffee';
        return 'fa-utensils';
    }
    
    attachFeedEvents() {
        document.querySelectorAll('.vote-up, .vote-down').forEach(btn => {
            btn.removeEventListener('click', this.handleVote);
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleVote(btn);
            });
        });
        
        document.querySelectorAll('.comment-btn').forEach(btn => {
            btn.removeEventListener('click', this.handleComment);
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showPostDetail(btn.dataset.postId);
            });
        });
        
        document.querySelectorAll('.share-btn').forEach(btn => {
            btn.removeEventListener('click', this.handleShare);
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.sharePost(btn.dataset.postId);
            });
        });
        
        document.querySelectorAll('.save-vendor-btn').forEach(btn => {
            btn.removeEventListener('click', this.handleSave);
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addToShortlist(btn.dataset.vendorId);
            });
        });
    }
    
    async handleVote(button) {
        const postId = button.dataset.postId;
        const voteType = parseInt(button.dataset.vote);
        const post = this.posts.find(p => p.id == parseInt(postId));
        if (!post) return;
        
        try {
            const response = await fetch('/api/votes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    post_id: postId,
                    vote_type: voteType
                })
            });
            
            if (response.ok) {
                await this.loadUserVotes();
                await this.loadPosts();
                const updatedPost = this.posts.find(p => p.id == parseInt(postId));
                const scoreSpan = document.getElementById(`score-${postId}`);
                if (scoreSpan) scoreSpan.textContent = updatedPost.score;
                
                const upBtn = document.querySelector(`.vote-up[data-post-id="${postId}"]`);
                const downBtn = document.querySelector(`.vote-down[data-post-id="${postId}"]`);
                const userVote = this.votes.find(v => v.post_id == parseInt(postId));
                
                if (upBtn) upBtn.classList.toggle('voted', userVote?.vote_type === 1);
                if (downBtn) downBtn.classList.toggle('voted', userVote?.vote_type === -1);
                
                await this.logActivity('vote', post.vendor_id, { post_id: postId });
            }
        } catch (error) {
            console.error('Vote failed:', error);
        }
    }
    
    async showPostDetail(postId) {
        const post = this.posts.find(p => p.id == postId);
        if (!post) return;
        
        this.currentPostId = postId;
        const user = await this.getUser(post.user_id);
        const vendor = post.vendor_id ? this.vendors.find(v => v.id === post.vendor_id) : null;
        const postComments = this.comments.filter(c => c.post_id == postId);
        
        const container = document.getElementById('post-detail-container');
        container.innerHTML = `
            <div class="post-detail">
                <div class="post-header">
                    <i class="fas fa-user-circle"></i> ${this.escapeHtml(user?.full_name || 'Foodie')}
                    <span>${this.formatTime(post.created_at)}</span>
                    ${vendor ? `<span><i class="fas fa-store"></i> ${this.escapeHtml(vendor.business_name)}</span>` : ''}
                </div>
                <h2><i class="fas ${this.getFoodIcon(post.title)}"></i> ${this.escapeHtml(post.title)}</h2>
                <div class="post-body">${this.escapeHtml(post.content).replace(/\n/g, '<br>')}</div>
                ${post.rating ? `<div class="post-rating-large"><i class="fas fa-star"></i> Rating: ${post.rating}/5</div>` : ''}
                <div class="post-stats">
                    <span><i class="fas fa-arrow-up"></i> ${post.upvotes}</span>
                    <span><i class="fas fa-arrow-down"></i> ${post.downvotes}</span>
                    <span><i class="fas fa-comment"></i> ${post.comment_count}</span>
                </div>
                ${vendor ? `<button onclick="app.addToShortlist(${vendor.id})" class="btn-secondary"><i class="fas fa-heart"></i> Save Food Spot</button>` : ''}
            </div>
        `;
        
        const commentsContainer = document.getElementById('comments-container');
        commentsContainer.innerHTML = this.renderComments(postComments);
        this.attachCommentEvents();
        
        document.getElementById('post-detail-modal').classList.remove('hidden');
        
        await this.logActivity('view_post', post.vendor_id, { post_id: postId });
    }
    
    renderComments(comments, parentId = null, depth = 0) {
        const filtered = comments.filter(c => c.parent_id === parentId);
        if (filtered.length === 0 && depth === 0) {
            return '<div class="no-comments"><i class="fas fa-comment-slash"></i> No food tips yet. Be the first to comment!</div>';
        }
        
        return filtered.map(comment => {
            const user = this.currentUser?.id === comment.user_id ? 'You' : 'Foodie';
            const childComments = this.renderComments(comments, comment.id, depth + 1);
            
            return `
                <div class="comment-thread" style="margin-left: ${depth * 20}px">
                    <div class="comment" data-comment-id="${comment.id}">
                        <div class="comment-header">
                            <strong><i class="fas fa-user-circle"></i> ${user}</strong>
                            <span class="comment-time">${this.formatTime(comment.created_at)}</span>
                        </div>
                        <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                        <div class="comment-actions">
                            <button class="comment-reply" data-id="${comment.id}"><i class="fas fa-reply"></i> Reply</button>
                        </div>
                    </div>
                    ${childComments}
                </div>
            `;
        }).join('');
    }
    
    attachCommentEvents() {
        document.querySelectorAll('.comment-reply').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showReplyForm(btn.dataset.id);
            });
        });
    }
    
    showReplyForm(commentId) {
        const commentDiv = document.querySelector(`.comment[data-comment-id="${commentId}"]`);
        if (!commentDiv) return;
        
        const existingForm = commentDiv.querySelector('.reply-form');
        if (existingForm) existingForm.remove();
        
        const formHtml = `
            <form class="reply-form" style="margin-top: 10px;">
                <textarea rows="2" placeholder="Share your food tip..." style="width:100%; padding:8px; border-radius:20px; border:1px solid #f0dbb4;"></textarea>
                <div style="display:flex; gap:8px; margin-top:8px;">
                    <button type="submit" class="btn-primary" style="padding:6px 12px; font-size:12px;">Post Food Tip</button>
                    <button type="button" class="cancel-reply btn-secondary" style="padding:6px 12px; font-size:12px;">Cancel</button>
                </div>
            </form>
        `;
        
        commentDiv.insertAdjacentHTML('beforeend', formHtml);
        
        const form = commentDiv.querySelector('.reply-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = form.querySelector('textarea').value;
            if (content.trim()) {
                await this.addCommentToPost(this.currentPostId, content, commentId);
                form.remove();
            }
        });
        
        form.querySelector('.cancel-reply').addEventListener('click', () => form.remove());
    }
    
    async addCommentToPost(postId, content, parentId = null) {
        try {
            const response = await fetch('/api/comments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_id: postId,
                    user_id: this.currentUser.id,
                    parent_id: parentId,
                    content: content
                })
            });
            
            if (response.ok) {
                await this.loadComments();
                await this.loadPosts();
                await this.showPostDetail(postId);
                document.getElementById('comment-content').value = '';
            }
        } catch (error) {
            console.error('Failed to add comment:', error);
        }
    }
    
    async addComment() {
        if (!this.currentPostId) return;
        const content = document.getElementById('comment-content').value;
        if (!content.trim()) return;
        await this.addCommentToPost(this.currentPostId, content);
    }
    
    async sharePost(postId) {
        const post = this.posts.find(p => p.id == postId);
        if (navigator.share) {
            navigator.share({ title: post.title, text: post.content });
        } else {
            prompt('Share this food find:', `${post.title}\n\n${post.content}`);
        }
        await this.logActivity('share', post.vendor_id, { post_id: postId });
    }
    
    async createPost() {
        const title = document.getElementById('post-title').value;
        const content = document.getElementById('post-content').value;
        const postType = document.getElementById('post-type').value;
        const vendorId = document.getElementById('post-vendor-id').value;
        const rating = parseInt(document.getElementById('post-rating').value);
        
        if (!title || !content) {
            alert('Please share what food you found!');
            return;
        }
        
        try {
            const response = await fetch('/api/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    vendor_id: vendorId || null,
                    title: title,
                    content: content,
                    post_type: postType,
                    rating: postType === 'review' ? rating : null
                })
            });
            
            if (response.ok) {
                await this.loadPosts();
                this.loadFeed(true);
                document.getElementById('create-post-modal').classList.add('hidden');
                document.getElementById('create-post-form').reset();
                
                if (vendorId) {
                    await this.logActivity('create_review', vendorId, { post_title: title });
                } else {
                    await this.logActivity('create_post', null, { post_title: title });
                }
                alert('Food review shared!');
            }
        } catch (error) {
            alert('Failed to share food review');
        }
    }
    
    showCreatePostModal() {
        const vendorSelect = document.getElementById('post-vendor-id');
        vendorSelect.innerHTML = '<option value="">Select a food vendor</option>' + 
            this.vendors.map(v => `<option value="${v.id}">${this.escapeHtml(v.business_name)}</option>`).join('');
        document.getElementById('create-post-modal').classList.remove('hidden');
    }
    
    showFeedFilters() {
        document.getElementById('filter-category').value = this.filters.category;
        document.getElementById('filter-rating').value = this.filters.minRating;
        document.getElementById('filter-time').value = this.filters.timeRange;
        document.getElementById('feed-filter-modal').classList.remove('hidden');
    }
    
    applyFeedFilters() {
        this.filters.category = document.getElementById('filter-category').value;
        this.filters.minRating = parseFloat(document.getElementById('filter-rating').value);
        this.filters.timeRange = document.getElementById('filter-time').value;
        this.currentPage = 0;
        this.hasMore = true;
        document.getElementById('feed-container').innerHTML = '';
        this.loadFeed();
        document.getElementById('feed-filter-modal').classList.add('hidden');
    }
    
    clearFeedFilters() {
        this.filters = { category: '', minRating: 0, timeRange: 'week' };
        this.currentPage = 0;
        this.hasMore = true;
        document.getElementById('feed-container').innerHTML = '';
        this.loadFeed();
        document.getElementById('feed-filter-modal').classList.add('hidden');
    }
    
    async initMap() {
        if (!this.map) {
            this.map = L.map('map').setView([13.9500, 121.3167], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(this.map);
        }
        await this.getLocation();
        await this.loadMapVendors();
    }
    
    async getLocation() {
        return new Promise((resolve) => {
            if (navigator.geolocation && this.userPreferences.privacy.shareLocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        this.currentLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                        resolve(this.currentLocation);
                    },
                    () => {
                        this.currentLocation = { lat: 13.9500, lng: 121.3167 };
                        resolve(this.currentLocation);
                    }
                );
            } else {
                this.currentLocation = { lat: 13.9500, lng: 121.3167 };
                resolve(this.currentLocation);
            }
        });
    }
    
    async centerMap() {
        if (this.map && this.currentLocation) {
            this.map.setView([this.currentLocation.lat, this.currentLocation.lng], 14);
        }
    }
    
    async loadMapVendors() {
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];
        
        let filteredVendors = [...this.vendors];
        if (this.mapFilters.category) {
            filteredVendors = filteredVendors.filter(v => v.category === this.mapFilters.category);
        }
        if (this.mapFilters.minRating > 0) {
            filteredVendors = filteredVendors.filter(v => (v.rating || 0) >= this.mapFilters.minRating);
        }
        
        if (this.mapRadius < 50) {
            filteredVendors = filteredVendors.filter(v => {
                if (v.latitude && v.longitude && this.currentLocation) {
                    const distance = this.calculateDistance(
                        this.currentLocation.lat, this.currentLocation.lng,
                        v.latitude, v.longitude
                    );
                    return distance <= this.mapRadius;
                }
                return true;
            });
        }
        
        filteredVendors.forEach(vendor => {
            if (vendor.latitude && vendor.longitude) {
                const foodIcon = this.getFoodIcon(vendor.business_name);
                const marker = L.marker([vendor.latitude, vendor.longitude])
                    .bindPopup(`
                        <div style="min-width:200px;">
                            <strong><i class="fas ${foodIcon}"></i> ${this.escapeHtml(vendor.business_name)}</strong><br>
                            <i class="fas fa-star"></i> ${vendor.rating || 0}<br>
                            <i class="fas fa-tag"></i> ${vendor.category || 'Street Food'}<br>
                            <button onclick="app.showVendorDetail(${vendor.id})" style="margin-top:8px; padding:4px 12px; background:var(--primary); color:white; border:none; border-radius:50px; cursor:pointer;">View Food Spot</button>
                        </div>
                    `).addTo(this.map);
                this.markers.push(marker);
            }
        });
    }
    
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    showRadiusModal() {
        document.getElementById('radius-slider').value = this.mapRadius;
        document.getElementById('radius-value').textContent = this.mapRadius;
        document.getElementById('radius-modal').classList.remove('hidden');
    }
    
    applyRadius() {
        this.mapRadius = parseInt(document.getElementById('radius-slider').value);
        this.loadMapVendors();
        document.getElementById('radius-modal').classList.add('hidden');
    }
    
    showMapFilters() {
        document.getElementById('map-filter-category').value = this.mapFilters.category;
        document.getElementById('map-filter-rating').value = this.mapFilters.minRating;
        document.getElementById('map-filter-modal').classList.remove('hidden');
    }
    
    applyMapFilters() {
        this.mapFilters.category = document.getElementById('map-filter-category').value;
        this.mapFilters.minRating = parseFloat(document.getElementById('map-filter-rating').value);
        this.loadMapVendors();
        document.getElementById('map-filter-modal').classList.add('hidden');
    }
    
    clearMapFilters() {
        this.mapFilters = { category: '', minRating: 0 };
        this.loadMapVendors();
        document.getElementById('map-filter-modal').classList.add('hidden');
    }
    
    async showTrafficAnalytics() {
        const trafficData = this.calculateTrafficData();
        document.getElementById('total-traffic').textContent = trafficData.total;
        document.getElementById('peak-traffic').textContent = trafficData.peakHour + ':00';
        document.getElementById('busiest-day').textContent = trafficData.busiestDay;
        
        const insightsList = document.getElementById('traffic-insights-list');
        insightsList.innerHTML = trafficData.insights.map(i => `<li><i class="fas fa-chart-line"></i> ${i}</li>`).join('');
        
        if (this.trafficChart) this.trafficChart.destroy();
        
        const ctx = document.getElementById('traffic-chart').getContext('2d');
        this.trafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Foodie Visits',
                    data: trafficData.weeklyData,
                    borderColor: 'var(--primary)',
                    backgroundColor: 'rgba(230,126,34,0.1)',
                    fill: true
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        document.getElementById('traffic-modal').classList.remove('hidden');
    }
    
    calculateTrafficData() {
        const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const weeklyData = [0, 0, 0, 0, 0, 0, 0];
        const hourlyData = Array(24).fill(0);
        
        this.activities.forEach(activity => {
            const date = new Date(activity.created_at);
            const day = date.getDay();
            const hour = date.getHours();
            if (day >= 0 && day <= 6) {
                weeklyData[day]++;
                hourlyData[hour]++;
            }
        });
        
        const total = weeklyData.reduce((a, b) => a + b, 0);
        const peakHour = hourlyData.indexOf(Math.max(...hourlyData));
        const busiestDayIndex = weeklyData.indexOf(Math.max(...weeklyData));
        const busiestDay = weekDays[busiestDayIndex];
        
        const insights = [];
        if (weeklyData[5] + weeklyData[6] > weeklyData[0] + weeklyData[1] + weeklyData[2] + weeklyData[3] + weeklyData[4]) {
            insights.push('Weekends are busiest for street food hunting!');
        }
        if (peakHour >= 17 && peakHour <= 21) {
            insights.push('Evenings are peak street food hours (5PM-9PM)');
        }
        if (peakHour >= 11 && peakHour <= 14) {
            insights.push('Lunch time also gets busy (11AM-2PM)');
        }
        
        return { total, peakHour, busiestDay, weeklyData, insights };
    }
    
    async showVendorDetail(vendorId) {
        const vendor = this.vendors.find(v => v.id === vendorId);
        if (!vendor) return;
        
        const vendorPosts = this.posts.filter(p => p.vendor_id === vendorId);
        const vendorReviews = vendorPosts.filter(p => p.post_type === 'review');
        const avgRating = vendorReviews.length ? 
            vendorReviews.reduce((sum, p) => sum + (p.rating || 0), 0) / vendorReviews.length : 
            vendor.rating;
        
        const isSaved = this.shortlist.some(s => s.id === vendorId);
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas ${this.getFoodIcon(vendor.business_name)}"></i> ${this.escapeHtml(vendor.business_name)}</h3>
                    <button class="close-modal" onclick="this.closest('.modal-overlay').remove()"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <p><i class="fas fa-star"></i> Rating: ${avgRating.toFixed(1)}/5 (${vendor.review_count || 0} foodie reviews)</p>
                    <p><i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(vendor.address || 'No address')}</p>
                    <p><i class="fas fa-tag"></i> ${vendor.category || 'Street Food'}</p>
                    <p><i class="fas fa-align-left"></i> ${this.escapeHtml(vendor.description || 'No description')}</p>
                    <div style="display:flex; gap:10px; margin-top:15px;">
                        <button onclick="app.chatWithVendor(${vendorId})" class="btn-primary"><i class="fab fa-facebook-messenger"></i> Ask About Food</button>
                        <button onclick="app.addToShortlist(${vendorId})" class="btn-secondary"><i class="fas fa-${isSaved ? 'heart' : 'heart-o'}"></i> ${isSaved ? 'Saved' : 'Save Food Spot'}</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        await this.logActivity('view_vendor', vendorId);
    }
    
    async addToShortlist(vendorId) {
        if (this.shortlist.some(s => s.id === vendorId)) {
            alert('Already in your favorite food spots!');
            return;
        }
        
        try {
            const response = await fetch('/api/shortlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.currentUser.id, vendor_id: vendorId })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.shortlist.push({ id: vendorId, shortlist_id: data.id });
                this.loadShortlist();
                this.updateProfileStats();
                await this.logActivity('save_vendor', vendorId);
                alert('Food spot saved to favorites!');
            }
        } catch (error) {
            console.error('Failed to save food spot:', error);
        }
    }
    
    async removeFromShortlist(vendorId) {
        const item = this.shortlist.find(s => s.id === vendorId);
        if (!item) return;
        
        try {
            await fetch(`/api/shortlist/${vendorId}/user/${this.currentUser.id}`, { method: 'DELETE' });
            this.shortlist = this.shortlist.filter(s => s.id !== vendorId);
            this.loadShortlist();
            this.updateProfileStats();
            await this.logActivity('unsave_vendor', vendorId);
        } catch (error) {
            console.error('Failed to remove:', error);
        }
    }
    
    chatWithVendor(vendorId) {
        const vendor = this.vendors.find(v => v.id === vendorId);
        if (vendor) {
            window.open(`https://m.me/?ref=lako_food_${vendorId}`, '_blank');
            this.logActivity('chat_start', vendorId);
        }
    }
    
    async loadSuggestions() {
        if (!this.currentUser) return;
        
        const viewedVendors = this.activities
            .filter(a => a.activity_type === 'view_vendor')
            .map(a => a.vendor_id)
            .filter((v, i, a) => a.indexOf(v) === i);
        
        const savedVendors = this.shortlist.map(s => s.id);
        
        let interestCategories = [...this.userPreferences.interests];
        
        const viewedVendorObjects = this.vendors.filter(v => viewedVendors.includes(v.id));
        viewedVendorObjects.forEach(v => {
            if (v.category && !interestCategories.includes(v.category)) {
                interestCategories.push(v.category);
            }
        });
        
        const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
        const recentActivities = this.activities.filter(a => new Date(a.created_at).getTime() > oneDayAgo);
        const trendingCounts = {};
        recentActivities.forEach(a => {
            if (a.vendor_id) {
                trendingCounts[a.vendor_id] = (trendingCounts[a.vendor_id] || 0) + 1;
            }
        });
        const trendingVendors = Object.keys(trendingCounts)
            .sort((a, b) => trendingCounts[b] - trendingCounts[a])
            .slice(0, 5)
            .map(id => this.vendors.find(v => v.id == id))
            .filter(v => v);
        
        let personalizedVendors = [];
        if (interestCategories.length > 0) {
            personalizedVendors = this.vendors
                .filter(v => interestCategories.includes(v.category) && 
                       !viewedVendors.includes(v.id) && 
                       !savedVendors.includes(v.id))
                .sort((a, b) => (b.rating || 0) - (a.rating || 0))
                .slice(0, 5);
        }
        
        const mostReviewed = [...this.vendors]
            .sort((a, b) => (b.review_count || 0) - (a.review_count || 0))
            .slice(0, 5);
        
        this.renderSuggestions('trending-container', trendingVendors, 'Trending Street Food');
        this.renderSuggestions('personalized-container', personalizedVendors, 'Recommended for You');
        this.renderSuggestions('most-reviewed-container', mostReviewed, 'Most Reviewed Food Spots');
    }
    
    renderSuggestions(containerId, vendors, title) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (vendors.length === 0) {
            container.innerHTML = '<p class="no-suggestions">No suggestions yet. Start exploring street food!</p>';
            return;
        }
        
        container.innerHTML = vendors.map(v => `
            <div class="suggestion-card" onclick="app.showVendorDetail(${v.id})">
                <div class="suggestion-icon"><i class="fas ${this.getFoodIcon(v.business_name)}"></i></div>
                <div class="suggestion-info">
                    <h4>${this.escapeHtml(v.business_name)}</h4>
                    <div class="rating"><i class="fas fa-star"></i> ${v.rating || 0}</div>
                    <div class="category"><i class="fas fa-tag"></i> ${v.category || 'Street Food'}</div>
                </div>
                <button class="save-suggestion" onclick="event.stopPropagation(); app.addToShortlist(${v.id})">
                    <i class="fas fa-heart-o"></i>
                </button>
            </div>
        `).join('');
    }
    
    loadSearchHistory() {
        const saved = localStorage.getItem('lako_search_history');
        if (saved) this.searchHistory = JSON.parse(saved);
    }
    
    saveSearchHistory() {
        localStorage.setItem('lako_search_history', JSON.stringify(this.searchHistory.slice(0, 10)));
    }
    
    addToSearchHistory(query) {
        if (!query.trim()) return;
        this.searchHistory = [query, ...this.searchHistory.filter(q => q !== query)];
        this.saveSearchHistory();
        this.loadSearchHistoryDisplay();
    }
    
    loadSearchHistoryDisplay() {
        const container = document.getElementById('recent-searches-list');
        if (container && this.searchHistory.length > 0) {
            container.innerHTML = this.searchHistory.map(q => `
                <button class="search-history-item" onclick="app.searchWithQuery('${this.escapeHtml(q)}')">
                    <i class="fas fa-clock"></i> ${this.escapeHtml(q)}
                </button>
            `).join('');
        } else if (container) {
            container.innerHTML = '<p class="no-history">No recent searches</p>';
        }
    }
    
    clearSearchHistory() {
        this.searchHistory = [];
        this.saveSearchHistory();
        this.loadSearchHistoryDisplay();
    }
    
    searchWithQuery(query) {
        document.getElementById('search-input').value = query;
        this.search();
    }
    
    async search() {
        const query = document.getElementById('search-input').value.toLowerCase().trim();
        if (!query) return;
        
        this.addToSearchHistory(query);
        const resultsContainer = document.getElementById('search-results');
        
        if (this.currentSearchTab === 'vendors') {
            const results = this.vendors.filter(v => 
                v.business_name.toLowerCase().includes(query) ||
                (v.category && v.category.toLowerCase().includes(query)) ||
                (v.address && v.address.toLowerCase().includes(query))
            );
            
            resultsContainer.innerHTML = results.map(v => `
                <div class="search-result" onclick="app.showVendorDetail(${v.id})">
                    <div class="search-result-icon"><i class="fas ${this.getFoodIcon(v.business_name)}"></i></div>
                    <div class="search-result-info">
                        <h4>${this.escapeHtml(v.business_name)}</h4>
                        <p><i class="fas fa-star"></i> ${v.rating || 0} | ${v.category || 'Street Food'}</p>
                        <p><i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(v.address || 'Location not specified')}</p>
                    </div>
                </div>
            `).join('') || '<p>No street food spots found</p>';
            
        } else if (this.currentSearchTab === 'posts') {
            const results = this.posts.filter(p => 
                p.title.toLowerCase().includes(query) || p.content.toLowerCase().includes(query)
            );
            
            resultsContainer.innerHTML = results.map(p => `
                <div class="search-result" onclick="app.showPostDetail(${p.id})">
                    <div class="search-result-icon"><i class="fas ${this.getFoodIcon(p.title)}"></i></div>
                    <div class="search-result-info">
                        <h4>${this.escapeHtml(p.title)}</h4>
                        <p>${this.truncate(this.escapeHtml(p.content), 80)}</p>
                        <p><i class="fas fa-clock"></i> ${this.formatTime(p.created_at)}</p>
                    </div>
                </div>
            `).join('') || '<p>No food reviews found</p>';
            
        } else if (this.currentSearchTab === 'categories') {
            const results = this.streetFoodTypes.filter(c => c.toLowerCase().includes(query));
            
            resultsContainer.innerHTML = results.map(c => `
                <div class="search-result" onclick="app.filterByCategory('${c}')">
                    <div class="search-result-icon"><i class="fas ${this.getFoodIcon(c)}"></i></div>
                    <div class="search-result-info">
                        <h4>${this.escapeHtml(c)}</h4>
                        <p>Find the best ${c} near you!</p>
                        <p><i class="fas fa-store"></i> ${this.vendors.filter(v => v.category === c).length} food spots</p>
                    </div>
                </div>
            `).join('') || '<p>No food categories found</p>';
        }
    }
    
    filterByCategory(category) {
        this.filters.category = category;
        this.switchTab('feed');
        this.loadFeed(true);
    }
    
    loadShortlist() {
        const container = document.getElementById('shortlist-container');
        if (!container) return;
        
        const shortlistedVendors = this.vendors.filter(v => this.shortlist.some(s => s.id === v.id));
        
        if (shortlistedVendors.length === 0) {
            container.innerHTML = '<p class="empty-state"><i class="fas fa-heart-o"></i> No saved food spots yet. Start exploring!</p>';
            return;
        }
        
        container.innerHTML = shortlistedVendors.map(v => `
            <div class="vendor-card" onclick="app.showVendorDetail(${v.id})">
                <div class="vendor-icon"><i class="fas ${this.getFoodIcon(v.business_name)}"></i></div>
                <div class="vendor-info">
                    <h4>${this.escapeHtml(v.business_name)}</h4>
                    <div class="rating"><i class="fas fa-star"></i> ${v.rating || 0}</div>
                </div>
                <button class="remove-shortlist" onclick="event.stopPropagation(); app.removeFromShortlist(${v.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }
    
    async logActivity(type, vendorId = null, metadata = {}) {
        if (!this.currentUser || !this.userPreferences.privacy.trackActivity) return;
        
        try {
            await fetch('/api/activities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    vendor_id: vendorId,
                    activity_type: type,
                    metadata: metadata
                })
            });
            await this.loadUserActivities();
            this.loadActivities();
            this.updateProfileStats();
        } catch (error) {
            console.error('Failed to log activity:', error);
        }
    }
    
    loadActivities() {
        const pastVendors = this.activities
            .filter(a => a.activity_type === 'view_vendor')
            .map(a => a.vendor_id)
            .filter((v, i, a) => a.indexOf(v) === i)
            .slice(0, 10);
        
        const pastVendorsContainer = document.getElementById('past-vendors-container');
        if (pastVendorsContainer) {
            const vendors = pastVendors.map(id => this.vendors.find(v => v.id === id)).filter(v => v);
            pastVendorsContainer.innerHTML = vendors.map(v => `
                <div class="activity-item" onclick="app.showVendorDetail(${v.id})">
                    <div><i class="fas ${this.getFoodIcon(v.business_name)}"></i> ${this.escapeHtml(v.business_name)}</div>
                    <button class="preview-btn" onclick="event.stopPropagation(); app.previewVendor(${v.id})"><i class="fas fa-eye"></i> Preview</button>
                </div>
            `).join('') || '<p>No past visits</p>';
        }
        
        const timeline = [...this.activities].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 20);
        const timelineContainer = document.getElementById('timeline-container');
        if (timelineContainer) {
            timelineContainer.innerHTML = timeline.map(a => {
                const vendor = this.vendors.find(v => v.id === a.vendor_id);
                const icon = this.getActivityIcon(a.activity_type);
                return `
                    <div class="timeline-item" onclick="app.showVendorDetail(${a.vendor_id})">
                        <div class="timeline-icon"><i class="fas fa-${icon}"></i></div>
                        <div class="timeline-content">
                            <div>${this.getActivityText(a.activity_type, vendor)}</div>
                            <div class="timeline-time">${this.formatTime(a.created_at)}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        const activitiesContainer = document.getElementById('activities-container');
        if (activitiesContainer) {
            const sorted = [...this.activities].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            activitiesContainer.innerHTML = sorted.map(a => {
                const vendor = this.vendors.find(v => v.id === a.vendor_id);
                return `
                    <div class="activity-item" onclick="app.showVendorDetail(${a.vendor_id})">
                        <div><i class="fas fa-${this.getActivityIcon(a.activity_type)}"></i> ${this.getActivityText(a.activity_type, vendor)}</div>
                        <div class="activity-time">${this.formatTime(a.created_at)}</div>
                    </div>
                `;
            }).join('') || '<p>No food adventures yet. Start exploring!</p>';
        }
    }
    
    getActivityIcon(type) {
        const icons = { 
            'view_vendor': 'eye', 
            'view_post': 'newspaper', 
            'create_post': 'plus-circle', 
            'create_review': 'star', 
            'vote': 'arrow-up', 
            'save_vendor': 'heart', 
            'chat_start': 'comments', 
            'share': 'share' 
        };
        return icons[type] || 'history';
    }
    
    getActivityText(type, vendor) {
        const texts = {
            'view_vendor': `Checked out ${vendor?.business_name || 'a food spot'}`,
            'view_post': 'Read a food review',
            'create_post': 'Shared a food find',
            'create_review': `Reviewed ${vendor?.business_name || 'a food spot'}`,
            'vote': 'Voted on a food review',
            'save_vendor': `Saved ${vendor?.business_name || 'a food spot'} to favorites`,
            'chat_start': `Asked about ${vendor?.business_name || 'a food spot'}`,
            'share': 'Shared a food find'
        };
        return texts[type] || 'Food activity';
    }
    
    previewVendor(vendorId) {
        const vendor = this.vendors.find(v => v.id === vendorId);
        if (!vendor) return;
        alert(`Preview: ${vendor.business_name}\nCategory: ${vendor.category}\nRating: ${vendor.rating}/5`);
    }
    
    async clearAllHistory() {
        if (!confirm('Clear your food journey history? This cannot be undone.')) return;
        
        for (const activity of this.activities) {
            try {
                await fetch(`/api/activities/${activity.id}`, { method: 'DELETE' });
            } catch (error) {
                console.error('Failed to delete activity:', error);
            }
        }
        
        await this.loadUserActivities();
        this.loadActivities();
        this.updateProfileStats();
        alert('Food journey history cleared');
    }
    
    updateProfileStats() {
        const myPosts = this.posts.filter(p => p.user_id === this.currentUser?.id).length;
        const myReviews = this.posts.filter(p => p.user_id === this.currentUser?.id && p.post_type === 'review').length;
        const myKarma = this.posts
            .filter(p => p.user_id === this.currentUser?.id)
            .reduce((sum, p) => sum + (p.score || 0), 0);
        const shortlistCount = this.shortlist.length;
        
        document.getElementById('post-count').textContent = myPosts;
        document.getElementById('review-count').textContent = myReviews;
        document.getElementById('karma-count').textContent = myKarma;
        document.getElementById('shortlist-count').textContent = shortlistCount;
        
        const profileInfo = document.getElementById('profile-info');
        if (profileInfo && this.currentUser) {
            profileInfo.innerHTML = `
                <div class="profile-card">
                    <i class="fas fa-user-circle fa-3x"></i>
                    <h3>${this.escapeHtml(this.currentUser.full_name)}</h3>
                    <p><i class="fas fa-envelope"></i> ${this.escapeHtml(this.currentUser.email)}</p>
                    <p><i class="fas fa-utensils"></i> Foodie since ${new Date(this.currentUser.created_at).toLocaleDateString()}</p>
                </div>
            `;
        }
    }
    
    async editProfile() {
        const newName = prompt('Enter your name:', this.currentUser.full_name);
        if (newName && newName !== this.currentUser.full_name) {
            try {
                const response = await fetch(`/api/users/${this.currentUser.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_name: newName })
                });
                
                if (response.ok) {
                    this.currentUser.full_name = newName;
                    this.updateProfileStats();
                    alert('Profile updated');
                }
            } catch (error) {
                alert('Failed to update profile');
            }
        }
    }
    
    async changePassword() {
        const currentPass = prompt('Enter current password:');
        if (!currentPass) return;
        
        const newPass = prompt('Enter new password:');
        if (!newPass) return;
        
        const confirmPass = prompt('Confirm new password:');
        if (newPass !== confirmPass) {
            alert('Passwords do not match');
            return;
        }
        
        try {
            const response = await fetch('/api/users/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    current_password: currentPass,
                    new_password: newPass
                })
            });
            
            if (response.ok) {
                alert('Password changed successfully');
            } else {
                alert('Current password is incorrect');
            }
        } catch (error) {
            alert('Failed to change password');
        }
    }
    
    async deleteAccount() {
        if (!confirm('Are you sure you want to delete your account? All your food reviews will be permanently deleted.')) return;
        if (!confirm('This action cannot be undone. Type "DELETE" to confirm.')) return;
        
        try {
            const response = await fetch(`/api/users/${this.currentUser.id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                localStorage.removeItem('lako_user_id');
                localStorage.removeItem(`lako_prefs_${this.currentUser.id}`);
                this.currentUser = null;
                this.showLanding();
                alert('Account deleted');
            }
        } catch (error) {
            alert('Failed to delete account');
        }
    }
    
    async logout() {
        if (confirm('Are you sure you want to logout?')) {
            localStorage.removeItem('lako_user_id');
            this.currentUser = null;
            this.showLanding();
        }
    }
    
    showPreferences() {
        const interestsGrid = document.getElementById('pref-interests');
        const allInterests = ['BBQ', 'Fishball', 'Isaw', 'Kwek-Kwek', 'Turon', 'Siomai', 'Burgers', 'Pancit', 'Rice Meals', 'Desserts', 'Beverages'];
        
        interestsGrid.innerHTML = allInterests.map(interest => `
            <label class="pref-option">
                <input type="checkbox" value="${interest}" ${this.userPreferences.interests.includes(interest) ? 'checked' : ''}>
                <i class="fas ${this.getFoodIcon(interest)}"></i> ${interest}
            </label>
        `).join('');
        
        document.getElementById('pref-radius').value = this.userPreferences.radius;
        
        document.getElementById('preferences-modal').classList.remove('hidden');
    }
    
    savePreferences() {
        const interests = Array.from(document.querySelectorAll('#pref-interests input:checked')).map(cb => cb.value);
        if (interests.length > 5) {
            alert('Select up to 5 street food favorites');
            return;
        }
        
        this.userPreferences.interests = interests;
        this.userPreferences.radius = parseInt(document.getElementById('pref-radius').value);
        
        this.saveUserPreferences();
        this.loadFeed(true);
        this.loadSuggestions();
        document.getElementById('preferences-modal').classList.add('hidden');
        alert('Food preferences saved');
    }
    
    showNotificationSettings() {
        document.getElementById('notif-new-posts').checked = this.userPreferences.notifications.posts;
        document.getElementById('notif-comments').checked = this.userPreferences.notifications.comments;
        document.getElementById('notif-suggestions').checked = this.userPreferences.notifications.suggestions;
        document.getElementById('notif-promos').checked = this.userPreferences.notifications.promos;
        
        document.getElementById('notification-modal').classList.remove('hidden');
    }
    
    saveNotificationSettings() {
        this.userPreferences.notifications = {
            posts: document.getElementById('notif-new-posts').checked,
            comments: document.getElementById('notif-comments').checked,
            suggestions: document.getElementById('notif-suggestions').checked,
            promos: document.getElementById('notif-promos').checked
        };
        
        this.saveUserPreferences();
        document.getElementById('notification-modal').classList.add('hidden');
        alert('Food alerts saved');
    }
    
    showPrivacySettings() {
        document.getElementById('privacy-location').checked = this.userPreferences.privacy.shareLocation;
        document.getElementById('privacy-activity').checked = this.userPreferences.privacy.trackActivity;
        
        document.getElementById('privacy-modal').classList.remove('hidden');
    }
    
    savePrivacySettings() {
        this.userPreferences.privacy = {
            shareLocation: document.getElementById('privacy-location').checked,
            trackActivity: document.getElementById('privacy-activity').checked
        };
        
        this.saveUserPreferences();
        document.getElementById('privacy-modal').classList.add('hidden');
        alert('Privacy settings saved');
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        if (tabName === 'map' && this.map) {
            setTimeout(() => this.map.invalidateSize(), 100);
        }
        if (tabName === 'suggestions') {
            this.loadSuggestions();
        }
        if (tabName === 'activities') {
            this.loadActivities();
        }
        if (tabName === 'shortlist') {
            this.loadShortlist();
        }
    }
    
    async getUser(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
        }
        return { full_name: 'Anonymous Foodie' };
    }
    
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    truncate(str, length) {
        if (!str) return '';
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    }
    
    formatTime(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
        return date.toLocaleDateString();
    }
}

// Initialize app
const app = new LakoCustomerApp();
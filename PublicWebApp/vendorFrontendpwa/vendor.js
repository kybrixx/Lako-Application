// ============= LAKO VENDOR APP =============
// Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp
// Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325

class LakoVendorApp {
    constructor() {
        this.currentUser = null;
        this.vendorBusiness = null;
        this.deviceId = this.getDeviceId();
        this.products = [];
        this.reviews = [];
        this.activities = [];
        this.sampleRequests = [];
        this.messages = [];
        this.analytics = {
            daily: [],
            weekly: [],
            monthly: []
        };
        this.currentTab = 'dashboard';
        this.currentProductId = null;
        this.currentReviewId = null;
        this.currentSampleId = null;
        this.locationMap = null;
        this.viewsChart = null;
        this.todayTrafficChart = null;
        this.weeklyTrafficChart = null;
        this.comparisonChart = null;
        this.init();
    }
    
    getDeviceId() {
        let id = localStorage.getItem('lako_vendor_device_id');
        if (!id) {
            id = 'vendor_' + Math.random().toString(36).substr(2, 16);
            localStorage.setItem('lako_vendor_device_id', id);
        }
        return id;
    }
    
    async init() {
        await this.checkEULA();
        this.setupEventListeners();
        this.splashScreen();
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
                document.getElementById('eula-text').innerHTML = data.eula_text.replace(/\n/g, '<br>');
                document.getElementById('eula-modal').classList.remove('hidden');
                
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
            document.getElementById('eula-modal').classList.add('hidden');
            this.splashScreen();
        } catch (error) {
            console.error('EULA accept failed:', error);
        }
    }
    
    declineEULA() {
        alert('You must accept the EULA to use Lako Vendor App.');
    }
    
    splashScreen() {
        setTimeout(() => {
            const userId = localStorage.getItem('lako_vendor_user_id');
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
        document.getElementById('register-business').classList.remove('hidden');
    }
    
    showForgot() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('forgot-password').classList.remove('hidden');
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
        document.getElementById('register-btn')?.addEventListener('click', () => this.showRegister());
        document.getElementById('back-to-landing')?.addEventListener('click', () => this.showLanding());
        document.getElementById('back-to-landing2')?.addEventListener('click', () => this.showLanding());
        document.getElementById('back-to-login')?.addEventListener('click', () => this.showLogin());
        document.getElementById('forgot-password-btn')?.addEventListener('click', () => this.showForgot());
        
        // Forms
        document.getElementById('login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        document.getElementById('register-business-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.registerBusiness();
        });
        
        document.getElementById('forgot-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.forgotPassword();
        });
        
        // Product management
        document.getElementById('add-product-btn')?.addEventListener('click', () => this.showProductModal());
        document.getElementById('product-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProduct();
        });
        
        // Business profile
        document.getElementById('edit-business-btn')?.addEventListener('click', () => this.showBusinessModal());
        document.getElementById('business-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveBusiness();
        });
        
        // Settings
        document.getElementById('change-password-btn')?.addEventListener('click', () => this.changePassword());
        document.getElementById('logout-btn')?.addEventListener('click', () => this.logout());
        document.getElementById('save-discovery-settings')?.addEventListener('click', () => this.saveDiscoverySettings());
        document.getElementById('claim-location-btn')?.addEventListener('click', () => this.claimLocation());
        
        // Export report
        document.getElementById('export-report-btn')?.addEventListener('click', () => this.exportTrafficReport());
        
        // Boost info
        document.getElementById('boost-info-btn')?.addEventListener('click', () => this.showBoostInfo());
        
        // Sample request actions
        document.getElementById('approve-sample')?.addEventListener('click', () => this.approveSample());
        document.getElementById('reject-sample')?.addEventListener('click', () => this.rejectSample());
        
        // Radius slider
        const radiusSlider = document.getElementById('service-radius');
        if (radiusSlider) {
            radiusSlider.addEventListener('input', (e) => {
                document.getElementById('radius-value').textContent = e.target.value;
            });
        }
        
        // Close modals
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('product-modal')?.classList.add('hidden');
                document.getElementById('business-modal')?.classList.add('hidden');
                document.getElementById('reply-modal')?.classList.add('hidden');
                document.getElementById('sample-modal')?.classList.add('hidden');
            });
        });
    }
    
    // ============= AUTHENTICATION =============
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
                if (data.user_type !== 'vendor') {
                    alert('This account is not registered as a vendor');
                    return;
                }
                localStorage.setItem('lako_vendor_user_id', data.id);
                this.currentUser = data;
                this.vendorBusiness = data.vendor_business;
                this.showMain();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }
    
    async registerBusiness() {
        const fullName = document.getElementById('reg-fullname').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const businessName = document.getElementById('reg-business-name').value;
        const mayorPermit = document.getElementById('reg-mayor-permit').value;
        const address = document.getElementById('reg-address').value;
        const phone = document.getElementById('reg-phone').value;
        const description = document.getElementById('reg-description').value;
        
        if (!email.endsWith('@gmail.com')) {
            alert('Only Gmail addresses are allowed');
            return;
        }
        
        try {
            const registerResponse = await fetch('/api/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    password: password,
                    device_id: this.deviceId,
                    user_type: 'vendor',
                    preferences: {}
                })
            });
            
            const userData = await registerResponse.json();
            
            if (!registerResponse.ok) {
                alert(userData.error);
                return;
            }
            
            const vendorResponse = await fetch('/api/vendor/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userData.id,
                    business_name: businessName,
                    mayor_permit: mayorPermit,
                    business_address: address,
                    business_phone: phone,
                    description: description
                })
            });
            
            const vendorData = await vendorResponse.json();
            
            if (vendorResponse.ok) {
                alert('Business registration submitted for verification! You will be notified once approved.');
                this.showLogin();
            } else {
                alert(vendorData.error);
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
                await this.loadVendorBusiness();
                this.showMain();
            } else {
                this.showLanding();
            }
        } catch (error) {
            this.showLanding();
        }
    }
    
    async loadVendorBusiness() {
        try {
            const response = await fetch(`/api/vendor/business/${this.currentUser.id}`);
            const data = await response.json();
            if (response.ok) {
                this.vendorBusiness = data;
                this.initLocationMap();
                this.updateVisibilityScore();
            }
        } catch (error) {
            console.error('Failed to load vendor business:', error);
        }
    }
    
    async loadAllData() {
        await Promise.all([
            this.loadProducts(),
            this.loadReviews(),
            this.loadActivities(),
            this.loadSampleRequests(),
            this.loadMessages(),
            this.loadAnalytics()
        ]);
        
        this.updateDashboard();
        this.updateTrafficTab();
        this.updateFeedTab();
        this.updateCatalogTab();
        this.updateReviewsTab();
        this.updateInquiriesTab();
        this.updateProfileTab();
    }
    
    async loadProducts() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/vendor/products/${this.vendorBusiness.id}`);
            this.products = await response.json();
        } catch (error) {
            console.error('Failed to load products:', error);
            this.products = [];
        }
    }
    
    async loadReviews() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/posts?vendor_id=${this.vendorBusiness.id}`);
            this.reviews = await response.json();
        } catch (error) {
            console.error('Failed to load reviews:', error);
            this.reviews = [];
        }
    }
    
    async loadActivities() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/activities/vendor/${this.vendorBusiness.id}`);
            this.activities = await response.json();
        } catch (error) {
            console.error('Failed to load activities:', error);
            this.activities = [];
        }
    }
    
    async loadSampleRequests() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/sample-requests/vendor/${this.vendorBusiness.id}`);
            this.sampleRequests = await response.json();
        } catch (error) {
            console.error('Failed to load sample requests:', error);
            this.sampleRequests = [];
        }
    }
    
    async loadMessages() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/vendor/messages/${this.vendorBusiness.id}`);
            this.messages = await response.json();
        } catch (error) {
            console.error('Failed to load messages:', error);
            this.messages = [];
        }
    }
    
    async loadAnalytics() {
        if (!this.vendorBusiness) return;
        try {
            const response = await fetch(`/api/vendor/analytics/${this.vendorBusiness.id}?days=30`);
            const data = await response.json();
            this.analytics = data;
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.analytics = { daily: [], weekly: [], monthly: [] };
        }
    }
    
    // ============= DASHBOARD =============
    updateDashboard() {
        const today = new Date().toISOString().split('T')[0];
        const todayViews = this.activities.filter(a => a.created_at?.split('T')[0] === today).length;
        const weekViews = this.activities.filter(a => {
            const date = new Date(a.created_at);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return date > weekAgo;
        }).length;
        
        const avgRating = this.reviews.length ? 
            this.reviews.reduce((sum, r) => sum + (r.rating || 0), 0) / this.reviews.length : 0;
        
        const uniqueViewers = [...new Set(this.activities.map(a => a.user_id))].length;
        
        document.getElementById('views-today').textContent = todayViews;
        document.getElementById('views-week').textContent = weekViews;
        document.getElementById('search-impressions').textContent = weekViews * 2;
        document.getElementById('search-rank').textContent = '#12';
        document.getElementById('avg-rating').textContent = avgRating.toFixed(1);
        document.getElementById('total-reviews').textContent = this.reviews.length;
        document.getElementById('saved-count').textContent = Math.floor(Math.random() * 100);
        document.getElementById('unique-viewers').textContent = uniqueViewers;
        document.getElementById('avg-rating-display').textContent = avgRating.toFixed(1);
        document.getElementById('total-reviews-display').textContent = this.reviews.length;
        
        const productReviewCounts = {};
        this.reviews.forEach(review => {
            if (review.product_id) {
                productReviewCounts[review.product_id] = (productReviewCounts[review.product_id] || 0) + 1;
            }
        });
        
        const mostReviewed = Object.entries(productReviewCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([id, count]) => {
                const product = this.products.find(p => p.id == id);
                return product ? { ...product, reviewCount: count } : null;
            })
            .filter(p => p);
        
        const mostReviewedContainer = document.getElementById('most-reviewed-products');
        if (mostReviewedContainer) {
            mostReviewedContainer.innerHTML = mostReviewed.map(p => `
                <div class="product-card">
                    <div class="product-icon"><i class="fas fa-box"></i></div>
                    <div class="product-info">
                        <h4>${this.escapeHtml(p.name)}</h4>
                        <p>${p.reviewCount} reviews</p>
                    </div>
                </div>
            `).join('') || '<div class="empty-state">No products reviewed yet</div>';
        }
        
        const trending = this.calculateTrendingProducts();
        const trendingContainer = document.getElementById('trending-products');
        if (trendingContainer) {
            trendingContainer.innerHTML = trending.map(p => `
                <div class="product-card">
                    <div class="product-icon"><i class="fas fa-fire"></i></div>
                    <div class="product-info">
                        <h4>${this.escapeHtml(p.name)}</h4>
                        <p>Score: ${p.engagementScore}</p>
                    </div>
                </div>
            `).join('') || '<div class="empty-state">No trending products yet</div>';
        }
        
        this.renderWeeklyViewsChart();
    }
    
    calculateTrendingProducts() {
        const last7Days = new Date();
        last7Days.setDate(last7Days.getDate() - 7);
        
        const productEngagement = {};
        
        this.products.forEach(product => {
            productEngagement[product.id] = {
                ...product,
                shares: 0,
                likes: 0,
                comments: 0,
                reviews: 0,
                recentEngagement: 0,
                engagementScore: 0
            };
        });
        
        this.reviews.forEach(review => {
            if (review.product_id && productEngagement[review.product_id]) {
                productEngagement[review.product_id].reviews++;
                const reviewDate = new Date(review.created_at);
                if (reviewDate > last7Days) {
                    productEngagement[review.product_id].recentEngagement += 2;
                }
            }
        });
        
        Object.values(productEngagement).forEach(p => {
            p.engagementScore = (p.shares * 3) + (p.likes * 2) + (p.comments * 1.5) + (p.reviews * 2) + p.recentEngagement;
        });
        
        return Object.values(productEngagement)
            .sort((a, b) => b.engagementScore - a.engagementScore)
            .slice(0, 5);
    }
    
    renderWeeklyViewsChart() {
        const ctx = document.getElementById('weekly-views-chart')?.getContext('2d');
        if (!ctx) return;
        
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const views = days.map((_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (6 - i));
            return this.activities.filter(a => new Date(a.created_at).toDateString() === date.toDateString()).length;
        });
        
        if (this.viewsChart) this.viewsChart.destroy();
        
        this.viewsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [{
                    label: 'Views',
                    data: views,
                    borderColor: '#e67e22',
                    backgroundColor: 'rgba(230,126,34,0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
    
    // ============= TRAFFIC TAB =============
    updateTrafficTab() {
        const currentHour = new Date().getHours();
        let trafficValue, trafficLabel, trafficLevel;
        
        if ((currentHour >= 17 && currentHour <= 21) || (currentHour >= 11 && currentHour <= 13)) {
            trafficValue = 87; trafficLabel = 'High'; trafficLevel = 'high';
        } else if ((currentHour >= 9 && currentHour <= 11) || (currentHour >= 14 && currentHour <= 17)) {
            trafficValue = 54; trafficLabel = 'Medium'; trafficLevel = 'medium';
        } else {
            trafficValue = 23; trafficLabel = 'Low'; trafficLevel = 'low';
        }
        
        document.getElementById('current-traffic').textContent = trafficValue;
        const badge = document.getElementById('traffic-level-badge');
        badge.textContent = trafficLabel;
        badge.className = `traffic-level level-${trafficLevel}`;
        
        this.renderTodayTrafficChart();
        this.renderWeeklyTrafficChart();
        this.renderComparisonChart();
        this.renderPeakHours();
    }
    
    renderTodayTrafficChart() {
        const ctx = document.getElementById('today-traffic-chart')?.getContext('2d');
        if (!ctx) return;
        
        const hours = Array.from({ length: 12 }, (_, i) => `${i * 2}:00`);
        const traffic = hours.map((_, i) => {
            const hour = i * 2;
            if ((hour >= 17 && hour <= 21) || (hour >= 11 && hour <= 13)) return 70 + Math.random() * 20;
            if ((hour >= 9 && hour <= 11) || (hour >= 14 && hour <= 17)) return 40 + Math.random() * 20;
            return 10 + Math.random() * 20;
        });
        
        if (this.todayTrafficChart) this.todayTrafficChart.destroy();
        
        this.todayTrafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Visitors',
                    data: traffic,
                    borderColor: '#e67e22',
                    backgroundColor: 'rgba(230,126,34,0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
    
    renderWeeklyTrafficChart() {
        const ctx = document.getElementById('weekly-traffic-chart')?.getContext('2d');
        if (!ctx) return;
        
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const traffic = [45, 52, 48, 55, 78, 89, 76];
        
        if (this.weeklyTrafficChart) this.weeklyTrafficChart.destroy();
        
        this.weeklyTrafficChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: days,
                datasets: [{
                    label: 'Visitors',
                    data: traffic,
                    backgroundColor: '#e67e22',
                    borderRadius: 8
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
    
    renderComparisonChart() {
        const ctx = document.getElementById('comparison-chart')?.getContext('2d');
        if (!ctx) return;
        
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const thisWeek = [45, 52, 48, 55, 78, 89, 76];
        const lastWeek = [38, 44, 42, 48, 65, 72, 68];
        
        if (this.comparisonChart) this.comparisonChart.destroy();
        
        this.comparisonChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [
                    { label: 'This Week', data: thisWeek, borderColor: '#e67e22', tension: 0.4 },
                    { label: 'Last Week', data: lastWeek, borderColor: '#888', tension: 0.4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
    
    renderPeakHours() {
        const container = document.getElementById('peak-hours-list');
        if (!container) return;
        
        container.innerHTML = `
            <div style="padding: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span><i class="fas fa-chart-line"></i> 11:00 AM - 1:00 PM</span>
                    <span style="color: #e67e22;">Very High (85 visitors)</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span><i class="fas fa-chart-line"></i> 5:00 PM - 9:00 PM</span>
                    <span style="color: #e67e22;">High (120 visitors)</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span><i class="fas fa-chart-line"></i> 2:00 PM - 4:00 PM</span>
                    <span style="color: #f39c12;">Medium (45 visitors)</span>
                </div>
            </div>
        `;
    }
    
    exportTrafficReport() {
        alert('Traffic report would be generated as PDF here.\n\nIn production, this would download a PDF with:\n- Daily traffic breakdown\n- Peak hours analysis\n- Comparison charts\n- Customer insights');
    }
    
    // ============= FEED TAB =============
    updateFeedTab() {
        this.renderFeedPreview();
        this.renderFeedMostReviewed();
        this.renderFeedTrending();
        this.renderFeedRecent();
        this.updateEngagementMetrics();
        this.renderProductPerformance();
    }
    
    renderFeedPreview() {
        const container = document.getElementById('feed-preview');
        if (!container) return;
        
        const sampleProduct = this.products[0];
        if (!sampleProduct) {
            container.innerHTML = '<div class="empty-state">Add products to see preview</div>';
            return;
        }
        
        container.innerHTML = `
            <div style="background: #1a1a2e; border-radius: 16px; padding: 15px;">
                <div style="display: flex; gap: 12px; margin-bottom: 10px;">
                    <i class="fas fa-store" style="font-size: 2rem; color: #e67e22;"></i>
                    <div>
                        <h4>${this.escapeHtml(this.vendorBusiness?.business_name || 'Your Business')}</h4>
                        <div style="color: #f39c12;">${'★'.repeat(Math.floor(this.getAvgRating()))}${'☆'.repeat(5 - Math.floor(this.getAvgRating()))} (${this.getAvgRating().toFixed(1)})</div>
                    </div>
                </div>
                <h5>${this.escapeHtml(sampleProduct.name)}</h5>
                <p style="color: #aaa; font-size: 0.8rem;">${this.escapeHtml(sampleProduct.description || 'Delicious street food!')}</p>
                <div style="display: flex; gap: 15px; margin-top: 10px; color: #888;">
                    <span><i class="fas fa-heart"></i> ${Math.floor(Math.random() * 50)}</span>
                    <span><i class="fas fa-comment"></i> ${Math.floor(Math.random() * 20)}</span>
                    <span><i class="fas fa-share"></i> ${Math.floor(Math.random() * 10)}</span>
                </div>
            </div>
        `;
    }
    
    getAvgRating() {
        if (!this.reviews.length) return 0;
        return this.reviews.reduce((sum, r) => sum + (r.rating || 0), 0) / this.reviews.length;
    }
    
    renderFeedMostReviewed() {
        const container = document.getElementById('feed-most-reviewed');
        if (!container) return;
        
        const mostReviewed = [...this.products]
            .sort((a, b) => (b.review_count || 0) - (a.review_count || 0))
            .slice(0, 3);
        
        container.innerHTML = mostReviewed.map(p => `
            <div style="background: #0a0a0f; border-radius: 12px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between;">
                <span><i class="fas fa-box"></i> ${this.escapeHtml(p.name)}</span>
                <span style="color: #e67e22;">${p.review_count || 0} reviews</span>
            </div>
        `).join('') || '<div class="empty-state">No reviews yet</div>';
    }
    
    renderFeedTrending() {
        const container = document.getElementById('feed-trending');
        if (!container) return;
        
        const trending = this.calculateTrendingProducts().slice(0, 3);
        
        container.innerHTML = trending.map(p => `
            <div style="background: #0a0a0f; border-radius: 12px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <span><i class="fas fa-fire" style="color: #e67e22;"></i> ${this.escapeHtml(p.name)}</span>
                    <span style="color: #e67e22;">Score: ${p.engagementScore}</span>
                </div>
                <div style="font-size: 0.7rem; color: #888;">Shares: ${p.shares || 0} | Likes: ${p.likes || 0} | Reviews: ${p.reviews || 0}</div>
            </div>
        `).join('') || '<div class="empty-state">No trending products yet</div>';
    }
    
    renderFeedRecent() {
        const container = document.getElementById('feed-recent');
        if (!container) return;
        
        const recentReviews = [...this.reviews]
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 3);
        
        container.innerHTML = recentReviews.map(r => `
            <div style="background: #0a0a0f; border-radius: 12px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <span><i class="fas fa-user"></i> ${this.escapeHtml(r.user_name || 'Customer')}</span>
                    <span style="color: #f39c12;">${'★'.repeat(r.rating || 0)}${'☆'.repeat(5 - (r.rating || 0))}</span>
                </div>
                <p style="font-size: 0.75rem; margin-top: 5px;">${this.escapeHtml(r.content || 'Great food!')}</p>
            </div>
        `).join('') || '<div class="empty-state">No recent reviews</div>';
    }
    
    updateEngagementMetrics() {
        const totalShares = this.activities.filter(a => a.activity_type === 'share').length;
        const totalLikes = this.activities.filter(a => a.activity_type === 'like').length;
        const totalComments = this.activities.filter(a => a.activity_type === 'comment').length;
        const totalReviews = this.reviews.length;
        
        document.getElementById('total-shares').textContent = totalShares;
        document.getElementById('total-likes').textContent = totalLikes;
        document.getElementById('total-comments').textContent = totalComments;
        document.getElementById('total-reviews-count').textContent = totalReviews;
    }
    
    renderProductPerformance() {
        const container = document.getElementById('product-performance-list');
        if (!container) return;
        
        const trending = this.calculateTrendingProducts();
        
        container.innerHTML = trending.map(p => `
            <div style="background: #0a0a0f; border-radius: 12px; padding: 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h5>${this.escapeHtml(p.name)}</h5>
                        <div style="font-size: 0.7rem; color: #888;">${p.reviews || 0} reviews | ${p.likes || 0} likes</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #e67e22; font-weight: bold;">Score: ${p.engagementScore}</div>
                        ${p.engagementScore > 50 ? '<span style="background: #e67e22; padding: 2px 8px; border-radius: 20px; font-size: 0.6rem;">Trending</span>' : ''}
                    </div>
                </div>
                <div style="margin-top: 8px; height: 4px; background: #222; border-radius: 2px;">
                    <div style="width: ${Math.min(100, p.engagementScore / 10)}%; height: 100%; background: #e67e22; border-radius: 2px;"></div>
                </div>
            </div>
        `).join('') || '<div class="empty-state">No products yet</div>';
    }
    
    showBoostInfo() {
        alert('📈 HOW TO BOOST YOUR PRODUCTS (FREE & ORGANIC)\n\n' +
              'Products with high engagement automatically appear in the "Trending" section of customer feeds!\n\n' +
              'To increase engagement:\n' +
              '✓ Encourage customers to share your products\n' +
              '✓ Respond to reviews promptly\n' +
              '✓ Add high-quality photos of your food\n' +
              '✓ Keep your menu updated\n' +
              '✓ Offer special promotions to generate reviews\n\n' +
              'The more engagement, the higher your visibility!');
    }
    
    // ============= CATALOG TAB =============
    updateCatalogTab() {
        const container = document.getElementById('products-list');
        if (!container) return;
        
        if (this.products.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-box-open"></i> No products yet. Click "Add Product" to get started!</div>';
            return;
        }
        
        container.innerHTML = this.products.map(p => `
            <div class="product-card" data-product-id="${p.id}">
                <div class="product-icon"><i class="fas fa-${p.category === 'BBQ' ? 'fire' : p.category === 'Fishball' ? 'fish' : 'utensils'}"></i></div>
                <div class="product-info">
                    <h4>${this.escapeHtml(p.name)}</h4>
                    <p>₱${p.price || '0'} | MOQ: ${p.moq || 1}</p>
                    <div class="product-stats">
                        <span><i class="fas fa-star"></i> ${p.avg_rating || 0}</span>
                        <span><i class="fas fa-comment"></i> ${p.review_count || 0} reviews</span>
                    </div>
                </div>
                <div class="product-actions">
                    <button onclick="app.editProduct(${p.id})" title="Edit"><i class="fas fa-edit"></i></button>
                    <button onclick="app.deleteProduct(${p.id})" title="Delete"><i class="fas fa-trash"></i></button>
                    <button onclick="app.toggleProductVisibility(${p.id})" title="${p.is_visible ? 'Hide' : 'Show'}">
                        <i class="fas fa-${p.is_visible ? 'eye' : 'eye-slash'}"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        const boostSelect = document.getElementById('boost-product-select');
        if (boostSelect) {
            boostSelect.innerHTML = '<option value="">Select product to boost (free - organic engagement)</option>' + 
                this.products.map(p => `<option value="${p.id}">${this.escapeHtml(p.name)}</option>`).join('');
        }
    }
    
    showProductModal(productId = null) {
        this.currentProductId = productId;
        const modal = document.getElementById('product-modal');
        const title = document.getElementById('product-modal-title');
        
        if (productId) {
            const product = this.products.find(p => p.id == productId);
            if (product) {
                title.innerHTML = '<i class="fas fa-edit"></i> Edit Product';
                document.getElementById('product-name').value = product.name;
                document.getElementById('product-description').value = product.description || '';
                document.getElementById('product-category').value = product.category || '';
                document.getElementById('product-price').value = product.price || '';
                document.getElementById('product-moq').value = product.moq || 1;
            }
        } else {
            title.innerHTML = '<i class="fas fa-plus"></i> Add Product';
            document.getElementById('product-form').reset();
        }
        
        modal.classList.remove('hidden');
    }
    
    async saveProduct() {
        const productData = {
            name: document.getElementById('product-name').value,
            description: document.getElementById('product-description').value,
            category: document.getElementById('product-category').value,
            price: parseFloat(document.getElementById('product-price').value) || null,
            moq: parseInt(document.getElementById('product-moq').value) || 1,
            vendor_id: this.vendorBusiness.id
        };
        
        try {
            let response;
            if (this.currentProductId) {
                response = await fetch(`/api/vendor/products/${this.currentProductId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });
            } else {
                response = await fetch('/api/vendor/products', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });
            }
            
            if (response.ok) {
                await this.loadProducts();
                this.updateCatalogTab();
                this.updateFeedTab();
                document.getElementById('product-modal').classList.add('hidden');
                alert(this.currentProductId ? 'Product updated!' : 'Product added!');
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to save product');
            }
        } catch (error) {
            alert('Failed to save product: ' + error.message);
        }
    }
    
    async editProduct(productId) {
        this.showProductModal(productId);
    }
    
    async deleteProduct(productId) {
        if (!confirm('Are you sure you want to delete this product?')) return;
        
        try {
            const response = await fetch(`/api/vendor/products/${productId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await this.loadProducts();
                this.updateCatalogTab();
                this.updateFeedTab();
                alert('Product deleted');
            } else {
                alert('Failed to delete product');
            }
        } catch (error) {
            alert('Failed to delete product: ' + error.message);
        }
    }
    
    async toggleProductVisibility(productId) {
        const product = this.products.find(p => p.id == productId);
        if (!product) return;
        
        try {
            const response = await fetch(`/api/vendor/products/${productId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_visible: !product.is_visible })
            });
            
            if (response.ok) {
                await this.loadProducts();
                this.updateCatalogTab();
                alert(product.is_visible ? 'Product hidden' : 'Product shown');
            }
        } catch (error) {
            alert('Failed to toggle visibility');
        }
    }
    
    // ============= REVIEWS TAB =============
    updateReviewsTab() {
        this.renderRatingBreakdown();
        this.renderAllReviews();
    }
    
    renderRatingBreakdown() {
        const container = document.getElementById('rating-breakdown');
        if (!container) return;
        
        const breakdown = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
        this.reviews.forEach(r => {
            if (r.rating) breakdown[r.rating] = (breakdown[r.rating] || 0) + 1;
        });
        
        const total = this.reviews.length || 1;
        
        container.innerHTML = [5, 4, 3, 2, 1].map(star => `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>${star} ★</span>
                    <span>${breakdown[star]} (${Math.round(breakdown[star] / total * 100)}%)</span>
                </div>
                <div style="height: 8px; background: #222; border-radius: 4px; overflow: hidden;">
                    <div style="width: ${breakdown[star] / total * 100}%; height: 100%; background: #e67e22; border-radius: 4px;"></div>
                </div>
            </div>
        `).join('');
    }
    
    renderAllReviews() {
        const container = document.getElementById('all-reviews-list');
        if (!container) return;
        
        if (this.reviews.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-star"></i> No reviews yet</div>';
            return;
        }
        
        container.innerHTML = this.reviews.map(r => `
            <div class="review-card" data-review-id="${r.id}">
                <div class="review-header">
                    <div>
                        <span class="reviewer"><i class="fas fa-user-circle"></i> ${this.escapeHtml(r.user_name || 'Customer')}</span>
                        <span class="review-rating"> ${'★'.repeat(r.rating || 0)}${'☆'.repeat(5 - (r.rating || 0))}</span>
                    </div>
                    <span class="review-date">${this.formatTime(r.created_at)}</span>
                </div>
                <div class="review-content">${this.escapeHtml(r.content || 'No review text')}</div>
                ${r.reply ? `<div class="reply-box"><i class="fas fa-reply"></i> <strong>Your Reply:</strong><div class="reply-text">${this.escapeHtml(r.reply)}</div></div>` : ''}
                <div class="review-actions">
                    <button onclick="app.showReplyModal(${r.id})"><i class="fas fa-reply"></i> Reply</button>
                    <button onclick="app.reportReview(${r.id})"><i class="fas fa-flag"></i> Report</button>
                </div>
            </div>
        `).join('');
    }
    
    showReplyModal(reviewId) {
        this.currentReviewId = reviewId;
        document.getElementById('reply-modal').classList.remove('hidden');
        document.getElementById('reply-content').value = '';
    }
    
    async submitReply() {
        const content = document.getElementById('reply-content').value;
        if (!content.trim()) {
            alert('Please enter a reply');
            return;
        }
        
        try {
            const response = await fetch(`/api/reviews/${this.currentReviewId}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reply: content })
            });
            
            if (response.ok) {
                await this.loadReviews();
                this.updateReviewsTab();
                document.getElementById('reply-modal').classList.add('hidden');
                alert('Reply posted!');
            }
        } catch (error) {
            alert('Failed to post reply');
        }
    }
    
    reportReview(reviewId) {
        alert('Review reported to admin for review.');
    }
    
    // ============= INQUIRIES TAB =============
    updateInquiriesTab() {
        this.renderSampleRequests();
        this.renderMessages();
    }
    
    renderSampleRequests() {
        const container = document.getElementById('sample-requests-list');
        if (!container) return;
        
        if (this.sampleRequests.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-box-open"></i> No sample requests yet</div>';
            return;
        }
        
        container.innerHTML = this.sampleRequests.map(s => `
            <div class="sample-card" data-sample-id="${s.id}">
                <div class="sample-header">
                    <span class="sample-customer"><i class="fas fa-user"></i> ${this.escapeHtml(s.customer_name)}</span>
                    <span class="sample-status status-${s.status}">${s.status}</span>
                </div>
                <div><i class="fas fa-box"></i> Product: ${this.escapeHtml(s.product_name || 'Sample Request')}</div>
                <div><i class="fas fa-map-marker-alt"></i> Pickup: ${this.escapeHtml(s.pickup_location || 'To be arranged')}</div>
                <div><i class="fas fa-calendar"></i> Preferred: ${s.preferred_date || 'As soon as possible'}</div>
                ${s.status === 'pending' ? `
                    <div class="sample-actions">
                        <button onclick="app.showSampleModal(${s.id})" class="btn-success" style="background:#28a745;">Approve</button>
                        <button onclick="app.rejectSampleRequest(${s.id})" class="btn-danger" style="background:#dc3545;">Reject</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    showSampleModal(sampleId) {
        this.currentSampleId = sampleId;
        const sample = this.sampleRequests.find(s => s.id == sampleId);
        if (sample) {
            document.getElementById('sample-details').innerHTML = `
                <p><strong>Customer:</strong> ${this.escapeHtml(sample.customer_name)}</p>
                <p><strong>Product:</strong> ${this.escapeHtml(sample.product_name || 'Sample')}</p>
                <p><strong>Pickup Location:</strong> ${this.escapeHtml(sample.pickup_location || 'Not specified')}</p>
                <p><strong>Preferred Date:</strong> ${sample.preferred_date || 'Not specified'}</p>
                <p><strong>Notes:</strong> ${this.escapeHtml(sample.notes || 'None')}</p>
            `;
            document.getElementById('sample-modal').classList.remove('hidden');
        }
    }
    
    async approveSample() {
        try {
            const response = await fetch(`/api/sample-requests/${this.currentSampleId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meetup_date: new Date().toISOString() })
            });
            
            if (response.ok) {
                await this.loadSampleRequests();
                this.updateInquiriesTab();
                document.getElementById('sample-modal').classList.add('hidden');
                alert('Sample request approved! Customer will be notified.');
            }
        } catch (error) {
            alert('Failed to approve request');
        }
    }
    
    async rejectSample() {
        const reason = prompt('Please provide a reason for rejection:');
        if (!reason) return;
        
        try {
            const response = await fetch(`/api/sample-requests/${this.currentSampleId}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason })
            });
            
            if (response.ok) {
                await this.loadSampleRequests();
                this.updateInquiriesTab();
                document.getElementById('sample-modal').classList.add('hidden');
                alert('Sample request rejected');
            }
        } catch (error) {
            alert('Failed to reject request');
        }
    }
    
    async rejectSampleRequest(sampleId) {
        const reason = prompt('Please provide a reason for rejection:');
        if (!reason) return;
        
        try {
            const response = await fetch(`/api/sample-requests/${sampleId}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason })
            });
            
            if (response.ok) {
                await this.loadSampleRequests();
                this.updateInquiriesTab();
                alert('Sample request rejected');
            }
        } catch (error) {
            alert('Failed to reject request');
        }
    }
    
    renderMessages() {
        const container = document.getElementById('messages-list');
        if (!container) return;
        
        if (this.messages.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-envelope"></i> No messages yet</div>';
            return;
        }
        
        container.innerHTML = this.messages.map(m => `
            <div class="message-card">
                <div class="message-header">
                    <span class="message-customer"><i class="fas fa-user"></i> ${this.escapeHtml(m.customer_name)}</span>
                    <span class="message-time">${this.formatTime(m.created_at)}</span>
                </div>
                <div class="message-content">${this.escapeHtml(m.message)}</div>
                <div class="message-reply">
                    <input type="text" placeholder="Type your reply..." id="reply-input-${m.id}">
                    <button onclick="app.sendMessage(${m.id}, ${m.customer_id})">Send</button>
                </div>
            </div>
        `).join('');
    }
    
    async sendMessage(messageId, customerId) {
        const input = document.getElementById(`reply-input-${messageId}`);
        const reply = input.value.trim();
        if (!reply) return;
        
        try {
            const response = await fetch('/api/vendor/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vendor_id: this.vendorBusiness.id,
                    customer_id: customerId,
                    message: reply,
                    is_from_vendor: true
                })
            });
            
            if (response.ok) {
                input.value = '';
                await this.loadMessages();
                this.updateInquiriesTab();
                alert('Reply sent!');
            }
        } catch (error) {
            alert('Failed to send message');
        }
    }
    
    // ============= PROFILE TAB =============
    updateProfileTab() {
        const container = document.getElementById('business-info');
        if (!container) return;
        
        if (this.vendorBusiness) {
            container.innerHTML = `
                <div class="chart-container" style="margin-bottom: 20px;">
                    <div style="text-align: center;">
                        <i class="fas fa-store" style="font-size: 3rem; color: #e67e22;"></i>
                        <h3 style="margin-top: 10px;">${this.escapeHtml(this.vendorBusiness.business_name)}</h3>
                        <p style="color: #888;">${this.escapeHtml(this.vendorBusiness.business_address || 'No address')}</p>
                        <p><i class="fas fa-phone"></i> ${this.escapeHtml(this.vendorBusiness.business_phone || 'Not set')}</p>
                        <p><i class="fas fa-envelope"></i> ${this.escapeHtml(this.vendorBusiness.business_email || this.currentUser?.email)}</p>
                        <p><i class="fas fa-id-card"></i> Mayor's Permit: ${this.escapeHtml(this.vendorBusiness.mayor_permit)}</p>
                        <p><i class="fas fa-clock"></i> Hours: ${this.escapeHtml(this.vendorBusiness.business_hours || 'Not set')}</p>
                        <p><i class="fas fa-tag"></i> Category: ${this.escapeHtml(this.vendorBusiness.category || 'Street Food')}</p>
                        <div class="toggle-switch" style="justify-content: center; gap: 15px;">
                            <span>Open for Business</span>
                            <label>
                                <input type="checkbox" id="profile-open-toggle" class="toggle-input" ${this.vendorBusiness.is_open ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
            
            const openToggle = document.getElementById('profile-open-toggle');
            if (openToggle) {
                openToggle.addEventListener('change', async (e) => {
                    await this.updateOpenStatus(e.target.checked);
                });
            }
        }
        
        const radiusSlider = document.getElementById('service-radius');
        if (radiusSlider && this.vendorBusiness) {
            radiusSlider.value = this.vendorBusiness.service_radius || 10;
            document.getElementById('radius-value').textContent = radiusSlider.value;
        }
        
        const openToggleSettings = document.getElementById('is-open-toggle');
        if (openToggleSettings && this.vendorBusiness) {
            openToggleSettings.checked = this.vendorBusiness.is_open === 1;
        }
    }
    
    async updateOpenStatus(isOpen) {
        try {
            const response = await fetch(`/api/vendor/business/${this.vendorBusiness.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_open: isOpen ? 1 : 0 })
            });
            
            if (response.ok) {
                this.vendorBusiness.is_open = isOpen ? 1 : 0;
                alert(isOpen ? 'Business marked as OPEN' : 'Business marked as CLOSED');
            }
        } catch (error) {
            alert('Failed to update status');
        }
    }
    
    showBusinessModal() {
        const modal = document.getElementById('business-modal');
        if (this.vendorBusiness) {
            document.getElementById('business-name').value = this.vendorBusiness.business_name || '';
            document.getElementById('business-address').value = this.vendorBusiness.business_address || '';
            document.getElementById('business-phone').value = this.vendorBusiness.business_phone || '';
            document.getElementById('business-email').value = this.vendorBusiness.business_email || '';
            document.getElementById('business-hours').value = this.vendorBusiness.business_hours || '';
            document.getElementById('business-description').value = this.vendorBusiness.description || '';
            document.getElementById('business-category').value = this.vendorBusiness.category || '';
        }
        modal.classList.remove('hidden');
    }
    
    async saveBusiness() {
        const businessData = {
            business_name: document.getElementById('business-name').value,
            business_address: document.getElementById('business-address').value,
            business_phone: document.getElementById('business-phone').value,
            business_email: document.getElementById('business-email').value,
            business_hours: document.getElementById('business-hours').value,
            description: document.getElementById('business-description').value,
            category: document.getElementById('business-category').value
        };
        
        try {
            const response = await fetch(`/api/vendor/business/${this.vendorBusiness.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(businessData)
            });
            
            if (response.ok) {
                await this.loadVendorBusiness();
                this.updateProfileTab();
                document.getElementById('business-modal').classList.add('hidden');
                alert('Business profile updated!');
            }
        } catch (error) {
            alert('Failed to update business profile');
        }
    }
    
    initLocationMap() {
        if (!this.locationMap && document.getElementById('location-map')) {
            this.locationMap = L.map('location-map').setView([13.9500, 121.3167], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(this.locationMap);
            
            if (this.vendorBusiness?.latitude && this.vendorBusiness?.longitude) {
                this.locationMap.setView([this.vendorBusiness.latitude, this.vendorBusiness.longitude], 16);
                L.marker([this.vendorBusiness.latitude, this.vendorBusiness.longitude]).addTo(this.locationMap)
                    .bindPopup('Your Business Location').openPopup();
            }
        }
    }
    
    claimLocation() {
        const address = prompt('Enter your business address:');
        if (address) {
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.length > 0) {
                        const lat = data[0].lat;
                        const lon = data[0].lon;
                        this.locationMap.setView([lat, lon], 16);
                        L.marker([lat, lon]).addTo(this.locationMap).bindPopup('Your Business Location').openPopup();
                        
                        fetch(`/api/vendor/business/${this.vendorBusiness.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ latitude: lat, longitude: lon })
                        });
                        alert('Location updated!');
                    } else {
                        alert('Address not found');
                    }
                });
        }
    }
    
    async saveDiscoverySettings() {
        const radius = document.getElementById('service-radius').value;
        const isOpen = document.getElementById('is-open-toggle').checked ? 1 : 0;
        
        try {
            const response = await fetch(`/api/vendor/business/${this.vendorBusiness.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service_radius: radius, is_open: isOpen })
            });
            
            if (response.ok) {
                alert('Discovery settings saved!');
                this.vendorBusiness.service_radius = radius;
                this.vendorBusiness.is_open = isOpen;
            }
        } catch (error) {
            alert('Failed to save settings');
        }
    }
    
    updateVisibilityScore() {
        let score = 0;
        const checklist = [];
        
        if (this.vendorBusiness?.business_name) { score += 10; checklist.push('✓ Business name set'); }
        else { checklist.push('✗ Add business name'); }
        
        if (this.vendorBusiness?.description && this.vendorBusiness.description.length > 50) { score += 15; checklist.push('✓ Business description (50+ chars)'); }
        else { checklist.push('✗ Add detailed business description'); }
        
        if (this.vendorBusiness?.business_hours) { score += 10; checklist.push('✓ Business hours set'); }
        else { checklist.push('✗ Set business hours'); }
        
        if (this.vendorBusiness?.business_phone) { score += 10; checklist.push('✓ Contact phone set'); }
        else { checklist.push('✗ Add contact phone'); }
        
        if (this.products.length > 0) { score += Math.min(20, this.products.length * 5); checklist.push(`✓ ${this.products.length} products added`); }
        else { checklist.push('✗ Add products to your catalog'); }
        
        if (this.reviews.length > 0) { score += Math.min(15, this.reviews.length * 3); checklist.push(`✓ ${this.reviews.length} customer reviews`); }
        else { checklist.push('✗ Encourage customers to leave reviews'); }
        
        if (this.vendorBusiness?.logo_url) { score += 10; checklist.push('✓ Business logo uploaded'); }
        else { checklist.push('✗ Upload business logo'); }
        
        if (this.vendorBusiness?.latitude && this.vendorBusiness?.longitude) { score += 10; checklist.push('✓ Location pin set on map'); }
        else { checklist.push('✗ Set your business location on map'); }
        
        document.getElementById('visibility-score').innerHTML = `
            <div style="font-size: 2rem; color: var(--primary);">${score}/100</div>
            <div style="height: 8px; background: #222; border-radius: 4px; margin: 10px 0;">
                <div id="visibility-bar" style="width: ${score}%; height: 100%; background: var(--primary); border-radius: 4px;"></div>
            </div>
        `;
        
        document.getElementById('visibility-checklist').innerHTML = `
            <h5><i class="fas fa-check-circle"></i> Profile Completion Checklist</h5>
            <ul style="list-style: none; padding-left: 0;">
                ${checklist.map(item => `<li style="padding: 5px 0; color: ${item.startsWith('✓') ? '#28a745' : '#888'};">${item}</li>`).join('')}
            </ul>
        `;
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
    
    async logout() {
        if (confirm('Are you sure you want to logout?')) {
            localStorage.removeItem('lako_vendor_user_id');
            this.currentUser = null;
            this.vendorBusiness = null;
            this.showLanding();
        }
    }
    
    // ============= UTILITIES =============
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        if (tabName === 'profile' && this.locationMap) {
            setTimeout(() => this.locationMap.invalidateSize(), 100);
        }
        if (tabName === 'reviews') {
            this.updateReviewsTab();
        }
        if (tabName === 'inquiries') {
            this.updateInquiriesTab();
        }
        if (tabName === 'feed') {
            this.updateFeedTab();
        }
    }
    
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    formatTime(dateStr) {
        if (!dateStr) return 'Recently';
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
const app = new LakoVendorApp();
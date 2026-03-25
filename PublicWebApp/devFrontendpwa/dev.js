// ============= LAKO DEV ADMIN APP =============
// Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp
// Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325

class LakoDevAdmin {
    constructor() {
        this.currentAdmin = null;
        this.deviceId = this.getDeviceId();
        this.pendingEmail = null;
        this.pendingPin = null;
        this.viewsChart = null;
        this.init();
    }
    
    getDeviceId() {
        let id = localStorage.getItem('lako_dev_device_id');
        if (!id) {
            id = 'dev_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now();
            localStorage.setItem('lako_dev_device_id', id);
        }
        return id;
    }
    
    async init() {
        this.setupEventListeners();
        this.splashScreen();
        await this.checkExistingSession();
    }
    
    splashScreen() {
        setTimeout(() => {
            this.showLogin();
        }, 2000);
    }
    
    showLogin() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('login-screen').classList.remove('hidden');
    }
    
    showRegister() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('register-screen').classList.remove('hidden');
    }
    
    showPinVerification() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('pin-screen').classList.remove('hidden');
        // Auto-focus first digit
        document.getElementById('pin-1').focus();
        this.setupPinInputs();
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
        
        // Login
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        // Register
        document.getElementById('register-btn').addEventListener('click', () => this.showRegister());
        document.getElementById('back-to-login').addEventListener('click', () => this.showLogin());
        document.getElementById('register-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });
        
        // PIN Verification
        document.getElementById('verify-pin-btn').addEventListener('click', () => this.verifyPin());
        document.getElementById('resend-pin-btn').addEventListener('click', () => this.resendPin());
        document.getElementById('resend-pin-verify-btn').addEventListener('click', () => this.resendPin());
        
        // Settings
        document.getElementById('update-password').addEventListener('click', () => this.updatePassword());
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        document.getElementById('revoke-all-devices').addEventListener('click', () => this.revokeAllDevices());
        
        // Auto-tab between PIN digits
        document.querySelectorAll('.pin-digit').forEach((input, index) => {
            input.addEventListener('keyup', (e) => {
                if (e.target.value.length === 1 && index < 5) {
                    document.getElementById(`pin-${index + 2}`).focus();
                }
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    document.getElementById(`pin-${index}`).focus();
                }
            });
        });
    }
    
    setupPinInputs() {
        // Clear all PIN inputs
        for (let i = 1; i <= 6; i++) {
            document.getElementById(`pin-${i}`).value = '';
        }
    }
    
    getPinCode() {
        let pin = '';
        for (let i = 1; i <= 6; i++) {
            pin += document.getElementById(`pin-${i}`).value;
        }
        return pin;
    }
    
    async checkExistingSession() {
        try {
            const response = await fetch('/api/dev/check', {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.authenticated) {
                this.currentAdmin = data;
                this.showMain();
                this.loadAllData();
            }
        } catch (error) {
            console.log('No active session');
        }
    }
    
    async login() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch('/api/dev/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username: email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.pendingEmail = email;
                // Generate and send PIN (simulated)
                this.pendingPin = Math.floor(100000 + Math.random() * 900000).toString();
                console.log('PIN for testing:', this.pendingPin); // In production, send via email/SMS
                alert(`PIN sent to ${email}\nDemo PIN: ${this.pendingPin}`);
                this.showPinVerification();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }
    
    async register() {
        const fullName = document.getElementById('reg-fullname').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirmPassword = document.getElementById('reg-confirm-password').value;
        
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        try {
            const response = await fetch('/api/dev/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: fullName, email, password, device_id: this.deviceId })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.pendingEmail = email;
                this.pendingPin = Math.floor(100000 + Math.random() * 900000).toString();
                console.log('PIN for testing:', this.pendingPin);
                alert(`Registration successful! PIN sent to ${email}\nDemo PIN: ${this.pendingPin}`);
                this.showPinVerification();
            } else {
                alert(data.error || 'Registration failed');
            }
        } catch (error) {
            alert('Registration failed: ' + error.message);
        }
    }
    
    async verifyPin() {
        const enteredPin = this.getPinCode();
        
        if (enteredPin.length !== 6) {
            alert('Please enter 6-digit PIN');
            return;
        }
        
        if (enteredPin !== this.pendingPin) {
            alert('Invalid PIN. Please try again.');
            return;
        }
        
        try {
            const response = await fetch('/api/dev/verify-device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    email: this.pendingEmail, 
                    device_id: this.deviceId,
                    pin: enteredPin 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentAdmin = data.admin;
                this.showMain();
                this.loadAllData();
            } else {
                alert(data.error || 'Verification failed');
            }
        } catch (error) {
            alert('Verification failed: ' + error.message);
        }
    }
    
    async resendPin() {
        if (!this.pendingEmail) {
            alert('Please login again');
            this.showLogin();
            return;
        }
        
        this.pendingPin = Math.floor(100000 + Math.random() * 900000).toString();
        console.log('New PIN:', this.pendingPin);
        alert(`New PIN sent to ${this.pendingEmail}\nDemo PIN: ${this.pendingPin}`);
    }
    
    async loadAllData() {
        await Promise.all([
            this.loadStats(),
            this.loadUsers(),
            this.loadVendors(),
            this.loadPosts(),
            this.loadDevices(),
            this.loadLogs(),
            this.loadAdminProfile()
        ]);
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/dev/stats', {
                credentials: 'include'
            });
            const stats = await response.json();
            
            document.getElementById('total-users').textContent = stats.total_users || 0;
            document.getElementById('total-vendors').textContent = stats.total_vendors || 0;
            document.getElementById('total-posts').textContent = stats.total_reviews || 0;
            document.getElementById('total-comments').textContent = stats.total_comments || 0;
            document.getElementById('active-devices').textContent = stats.active_devices || 0;
            document.getElementById('today-activity').textContent = stats.today_activity || 0;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    async loadUsers() {
        try {
            const response = await fetch('/api/dev/users', {
                credentials: 'include'
            });
            const users = await response.json();
            
            const tbody = document.getElementById('users-table-body');
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.id}</td>
                    <td>${this.escapeHtml(user.full_name)}</td>
                    <td>${this.escapeHtml(user.email)}</td>
                    <td><span class="status-badge ${user.user_type === 'vendor' ? 'status-active' : 'status-pending'}">${user.user_type}</span></td>
                    <td>${new Date(user.created_at).toLocaleDateString()}</td>
                    <td><button class="action-btn" onclick="app.deleteUser(${user.id})"><i class="fas fa-trash"></i></button></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }
    
    async loadVendors() {
        try {
            const response = await fetch('/api/dev/vendors', {
                credentials: 'include'
            });
            const vendors = await response.json();
            
            const tbody = document.getElementById('vendors-table-body');
            tbody.innerHTML = vendors.map(v => `
                <tr>
                    <td>${v.id}</td>
                    <td>${this.escapeHtml(v.business_name)}</td>
                    <td>${this.escapeHtml(v.owner_name || 'N/A')}</td>
                    <td>${this.escapeHtml(v.category || 'Street Food')}</td>
                    <td>${v.rating || 0} ★</td>
                    <td><span class="status-badge ${v.verification_status === 'approved' ? 'status-active' : 'status-pending'}">${v.verification_status || 'pending'}</span></td>
                    <td><button class="action-btn" onclick="app.deleteVendor(${v.id})"><i class="fas fa-trash"></i></button></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load vendors:', error);
        }
    }
    
    async loadPosts() {
        try {
            const response = await fetch('/api/dev/posts', {
                credentials: 'include'
            });
            const posts = await response.json();
            
            const tbody = document.getElementById('posts-table-body');
            tbody.innerHTML = posts.map(post => `
                <tr>
                    <td>${post.id}</td>
                    <td>${this.escapeHtml(post.author_name || 'Anonymous')}</td>
                    <td>${this.truncate(post.title, 30)}</td>
                    <td>${post.post_type}</td>
                    <td>${'★'.repeat(post.rating || 0)}</td>
                    <td>${new Date(post.created_at).toLocaleDateString()}</td>
                    <td><button class="action-btn" onclick="app.deletePost(${post.id})"><i class="fas fa-trash"></i></button></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load posts:', error);
        }
    }
    
    async loadDevices() {
        try {
            const response = await fetch('/api/dev/devices', {
                credentials: 'include'
            });
            const devices = await response.json();
            
            const container = document.getElementById('devices-list');
            container.innerHTML = devices.map(device => `
                <div class="device-item">
                    <div>
                        <i class="fas fa-${device.is_current ? 'check-circle' : 'mobile-alt'}"></i>
                        <strong>${this.escapeHtml(device.device_name || 'Unknown Device')}</strong>
                        <div style="font-size: 0.7rem; color: #888;">Last active: ${new Date(device.last_active).toLocaleString()}</div>
                    </div>
                    <div>
                        <span class="status-badge ${device.is_current ? 'status-active' : 'status-pending'}">
                            ${device.is_current ? 'Current Device' : 'Authorized'}
                        </span>
                        ${!device.is_current ? `<button class="action-btn" onclick="app.revokeDevice('${device.device_id}')"><i class="fas fa-times"></i></button>` : ''}
                    </div>
                </div>
            `).join('') || '<div class="empty-state">No authorized devices</div>';
        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    }
    
    async loadLogs() {
        try {
            const response = await fetch('/api/dev/logs', {
                credentials: 'include'
            });
            const logs = await response.json();
            
            const tbody = document.getElementById('logs-table-body');
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${new Date(log.created_at).toLocaleString()}</td>
                    <td>${this.escapeHtml(log.admin_name || 'System')}</td>
                    <td>${this.escapeHtml(log.action)}</td>
                    <td>${this.escapeHtml(log.target_type)} #${log.target_id}</td>
                    <td>${this.escapeHtml(log.details || '-')}</td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }
    
    async loadAdminProfile() {
        try {
            const response = await fetch('/api/dev/profile', {
                credentials: 'include'
            });
            const profile = await response.json();
            
            const container = document.getElementById('admin-profile');
            container.innerHTML = `
                <div style="background: #1a1a2e; padding: 15px; border-radius: 12px;">
                    <p><i class="fas fa-user"></i> <strong>${this.escapeHtml(profile.full_name)}</strong></p>
                    <p><i class="fas fa-envelope"></i> ${this.escapeHtml(profile.email)}</p>
                    <p><i class="fas fa-shield-alt"></i> Role: ${profile.role}</p>
                    <p><i class="fas fa-calendar"></i> Joined: ${new Date(profile.created_at).toLocaleDateString()}</p>
                    <p><i class="fas fa-mobile-alt"></i> Device ID: ${this.truncate(this.deviceId, 20)}</p>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }
    
    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
        
        try {
            const response = await fetch(`/api/dev/users/${userId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                alert('User deleted');
                this.loadUsers();
                this.loadStats();
            } else {
                alert('Failed to delete user');
            }
        } catch (error) {
            alert('Failed to delete user');
        }
    }
    
    async deleteVendor(vendorId) {
        if (!confirm('Are you sure you want to delete this vendor? All their products and reviews will be deleted.')) return;
        
        try {
            const response = await fetch(`/api/dev/vendors/${vendorId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                alert('Vendor deleted');
                this.loadVendors();
                this.loadStats();
            } else {
                alert('Failed to delete vendor');
            }
        } catch (error) {
            alert('Failed to delete vendor');
        }
    }
    
    async deletePost(postId) {
        if (!confirm('Are you sure you want to delete this post?')) return;
        
        try {
            const response = await fetch(`/api/dev/posts/${postId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                alert('Post deleted');
                this.loadPosts();
                this.loadStats();
            } else {
                alert('Failed to delete post');
            }
        } catch (error) {
            alert('Failed to delete post');
        }
    }
    
    async revokeDevice(deviceId) {
        if (!confirm('Revoke this device? It will need to re-authenticate.')) return;
        
        try {
            const response = await fetch(`/api/dev/revoke-device/${deviceId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                alert('Device revoked');
                this.loadDevices();
            } else {
                alert('Failed to revoke device');
            }
        } catch (error) {
            alert('Failed to revoke device');
        }
    }
    
    async revokeAllDevices() {
        if (!confirm('Revoke all other devices? You will remain logged in on this device.')) return;
        
        try {
            const response = await fetch('/api/dev/revoke-all-devices', {
                method: 'POST',
                credentials: 'include',
                body: JSON.stringify({ current_device_id: this.deviceId })
            });
            
            if (response.ok) {
                alert('All other devices revoked');
                this.loadDevices();
            } else {
                alert('Failed to revoke devices');
            }
        } catch (error) {
            alert('Failed to revoke devices');
        }
    }
    
    async updatePassword() {
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (!newPassword) {
            alert('Please enter a new password');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        try {
            const response = await fetch('/api/dev/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ new_password: newPassword })
            });
            
            if (response.ok) {
                alert('Password updated successfully');
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-password').value = '';
            } else {
                alert('Failed to update password');
            }
        } catch (error) {
            alert('Failed to update password');
        }
    }
    
    async logout() {
        if (!confirm('Are you sure you want to logout?')) return;
        
        try {
            const response = await fetch('/api/dev/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                localStorage.removeItem('lako_dev_device_id');
                this.currentAdmin = null;
                this.showLogin();
            }
        } catch (error) {
            alert('Logout failed');
        }
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Refresh data when switching tabs
        if (tabName === 'users') this.loadUsers();
        if (tabName === 'vendors') this.loadVendors();
        if (tabName === 'posts') this.loadPosts();
        if (tabName === 'devices') this.loadDevices();
        if (tabName === 'logs') this.loadLogs();
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
}

// Initialize app
const app = new LakoDevAdmin();
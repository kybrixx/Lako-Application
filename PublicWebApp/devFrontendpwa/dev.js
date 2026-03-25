// ============= LAKO DEV ADMIN APP =============
// Capstone Project: Lako: Passive GPS Proximity Discovery of Micro Retail Vendors
// Asian Institute of Technology and Education
// Developers: Kyle Brian M. Morillo & Alexander Collin Millicamp
// Headquarters: 196 Bula, Tiaong, Quezon, Philippines 4325

class LakoDevAdmin {
    constructor() {
        this.currentAdmin = null;
        this.deviceId = this.getDeviceId();
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
    
    showMain() {
        document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
        document.getElementById('main').classList.remove('hidden');
        this.loadAllData();
    }
    
    setupEventListeners() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        document.getElementById('login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        document.getElementById('update-password')?.addEventListener('click', () => this.updatePassword());
        document.getElementById('logout-btn')?.addEventListener('click', () => this.logout());
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
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch('/api/dev/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentAdmin = data;
                this.showMain();
                this.loadAllData();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }
    
    async loadAllData() {
        await Promise.all([
            this.loadStats(),
            this.loadUsers(),
            this.loadVendors(),
            this.loadPosts(),
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
            if (tbody) {
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
            }
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
            if (tbody) {
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
            }
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
            if (tbody) {
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
            }
        } catch (error) {
            console.error('Failed to load posts:', error);
        }
    }
    
    async loadLogs() {
        try {
            const response = await fetch('/api/dev/logs', {
                credentials: 'include'
            });
            const logs = await response.json();
            
            const tbody = document.getElementById('logs-table-body');
            if (tbody) {
                tbody.innerHTML = logs.map(log => `
                    <tr>
                        <td>${new Date(log.created_at).toLocaleString()}</td>
                        <td>${this.escapeHtml(log.admin_name || 'System')}</td>
                        <td>${this.escapeHtml(log.action)}</td>
                        <td>${this.escapeHtml(log.target_type)} #${log.target_id}</td>
                        <td>${this.escapeHtml(log.details || '-')}</td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }
    
    async loadAdminProfile() {
        if (this.currentAdmin) {
            const container = document.getElementById('admin-profile');
            if (container) {
                container.innerHTML = `
                    <div style="background: #1a1a2e; padding: 15px; border-radius: 12px;">
                        <p><i class="fas fa-user"></i> <strong>${this.escapeHtml(this.currentAdmin.full_name)}</strong></p>
                        <p><i class="fas fa-envelope"></i> ${this.escapeHtml(this.currentAdmin.username)}</p>
                        <p><i class="fas fa-shield-alt"></i> Role: ${this.currentAdmin.role}</p>
                    </div>
                `;
            }
        }
    }
    
    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user?')) return;
        try {
            const response = await fetch(`/api/dev/users/${userId}`, { method: 'DELETE', credentials: 'include' });
            if (response.ok) {
                alert('User deleted');
                this.loadUsers();
                this.loadStats();
            }
        } catch (error) {
            alert('Failed to delete user');
        }
    }
    
    async deleteVendor(vendorId) {
        if (!confirm('Are you sure you want to delete this vendor?')) return;
        try {
            const response = await fetch(`/api/dev/vendors/${vendorId}`, { method: 'DELETE', credentials: 'include' });
            if (response.ok) {
                alert('Vendor deleted');
                this.loadVendors();
                this.loadStats();
            }
        } catch (error) {
            alert('Failed to delete vendor');
        }
    }
    
    async deletePost(postId) {
        if (!confirm('Are you sure you want to delete this post?')) return;
        try {
            const response = await fetch(`/api/dev/posts/${postId}`, { method: 'DELETE', credentials: 'include' });
            if (response.ok) {
                alert('Post deleted');
                this.loadPosts();
                this.loadStats();
            }
        } catch (error) {
            alert('Failed to delete post');
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
            }
        } catch (error) {
            alert('Failed to update password');
        }
    }
    
    async logout() {
        if (!confirm('Are you sure you want to logout?')) return;
        try {
            await fetch('/api/dev/logout', { method: 'POST', credentials: 'include' });
            localStorage.removeItem('lako_dev_device_id');
            this.currentAdmin = null;
            this.showLogin();
        } catch (error) {
            alert('Logout failed');
        }
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        if (tabName === 'users') this.loadUsers();
        if (tabName === 'vendors') this.loadVendors();
        if (tabName === 'posts') this.loadPosts();
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

const app = new LakoDevAdmin();
// Developed by: Kyle Brian M. Morillo & Alexander Collin Millicamp
// Headquarters: 196 Bula, Tiaong, Quezon

class LakoCustomerApp {
    constructor() {
        this.deviceId = this.getDeviceId();
        this.currentUser = null;
        this.init();
    }
    
    getDeviceId() {
        let id = localStorage.getItem('lako_device_id');
        if (!id) {
            id = 'device_' + Math.random().toString(36).substr(2, 16);
            localStorage.setItem('lako_device_id', id);
        }
        return id;
    }
    
    async init() {
        console.log('App initializing...');
        await this.checkEULA();
    }
    
    async checkEULA() {
        console.log('Checking EULA...');
        
        try {
            const response = await fetch('/api/eula/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: this.deviceId })
            });
            
            console.log('EULA response status:', response.status);
            const data = await response.json();
            console.log('EULA data:', data);
            
            if (!data.accepted) {
                console.log('EULA not accepted, showing modal');
                this.showEULAModal(data);
            } else {
                console.log('EULA already accepted');
                this.splashScreen();
            }
        } catch (error) {
            console.error('EULA check failed:', error);
            this.splashScreen();
        }
    }
    
    showEULAModal(data) {
        // Remove any existing modal
        const existing = document.getElementById('eula-modal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.id = 'eula-modal';
        modal.innerHTML = `
            <div style="background: #1a1a2e; max-width: 600px; width: 90%; max-height: 80vh; border-radius: 20px; overflow: hidden;">
                <div style="background: #e67e22; padding: 20px; text-align: center; color: white;">
                    <h2>LAKO - End User License Agreement</h2>
                    <p>196 Bula, Tiaong, Quezon</p>

                    <p>Asian Institute of Technology and Education</p>
                </div>
                <div style="padding: 20px; overflow-y: auto; max-height: 50vh; color: #ccc; font-size: 12px; line-height: 1.5;">
                    ${(data.eula_text || 'Please accept the terms to continue.').replace(/\n/g, '<br>')}
                </div>
                <div style="padding: 15px; display: flex; gap: 10px; justify-content: center; border-top: 1px solid #333;">
                    <button id="accept-eula-btn" style="background: #e67e22; color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer;">I Accept</button>
                    <button id="decline-eula-btn" style="background: transparent; border: 1px solid #e67e22; color: #e67e22; padding: 10px 20px; border-radius: 25px; cursor: pointer;">Decline</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        document.getElementById('accept-eula-btn').onclick = () => this.acceptEULA(data.device_id);
        document.getElementById('decline-eula-btn').onclick = () => alert('You must accept the EULA to use Lako.');
    }
    
    async acceptEULA(deviceId) {
        try {
            await fetch('/api/eula/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: deviceId })
            });
            
            const modal = document.getElementById('eula-modal');
            if (modal) modal.remove();
            
            this.splashScreen();
        } catch (error) {
            console.error('Accept failed:', error);
        }
    }
    
    splashScreen() {
        console.log('Showing splash screen');
        
        const splash = document.createElement('div');
        splash.id = 'splash';
        splash.innerHTML = `
            <div>
                <h1 style="font-size: 3rem;">LAKO</h1>
                <p>Discover Street Food</p>
                <div class="loader"></div>
                <small>196 Bula, Tiaong, Quezon</small>
            </div>
        `;
        
        document.body.appendChild(splash);
        
        setTimeout(() => {
            splash.remove();
            this.showLanding();
        }, 2000);
    }
    
    showLanding() {
        console.log('Showing landing screen');
        
        const landing = document.createElement('div');
        landing.className = 'screen-container';
        landing.innerHTML = `
            <div class="container">
                <h1>LAKO</h1>
                <p class="tagline">Find the Best Street Food Near You</p>
                <button id="login-btn" class="btn-primary">Login</button>
                <button id="signup-btn" class="btn-secondary">Sign Up</button>
                <div class="dev-credit">
                    <p>Capstone Project - Asian Institute of Technology and Education</p>
                    <p>Kyle Brian M. Morillo & Alexander Collin Millicamp</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(landing);
        
        document.getElementById('login-btn').onclick = () => this.showLogin();
        document.getElementById('signup-btn').onclick = () => this.showRegister();
    }
    
    showLogin() {
        // Remove current screen
        const current = document.querySelector('.screen-container');
        if (current) current.remove();
        
        const loginScreen = document.createElement('div');
        loginScreen.className = 'screen-container';
        loginScreen.innerHTML = `
            <div class="container">
                <h2>Login</h2>
                <input type="email" id="login-email" placeholder="Gmail Address">
                <input type="password" id="login-password" placeholder="Password">
                <button id="do-login" class="btn-primary">Login</button>
                <button id="back-to-landing" class="link-btn">Back</button>
            </div>
        `;
        
        document.body.appendChild(loginScreen);
        
        document.getElementById('do-login').onclick = () => this.login();
        document.getElementById('back-to-landing').onclick = () => {
            loginScreen.remove();
            this.showLanding();
        };
    }
    
    showRegister() {
        // Remove current screen
        const current = document.querySelector('.screen-container');
        if (current) current.remove();
        
        const registerScreen = document.createElement('div');
        registerScreen.className = 'screen-container';
        registerScreen.innerHTML = `
            <div class="container">
                <h2>Sign Up</h2>
                <input type="text" id="reg-name" placeholder="Full Name">
                <input type="email" id="reg-email" placeholder="Gmail Address">
                <input type="password" id="reg-password" placeholder="Password">
                <button id="do-register" class="btn-primary">Sign Up</button>
                <button id="back-to-landing" class="link-btn">Back</button>
            </div>
        `;
        
        document.body.appendChild(registerScreen);
        
        document.getElementById('do-register').onclick = () => this.register();
        document.getElementById('back-to-landing').onclick = () => {
            registerScreen.remove();
            this.showLanding();
        };
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
        
        try {
            const response = await fetch('/api/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    full_name: fullName, 
                    email, 
                    password, 
                    device_id: this.deviceId,
                    user_type: 'customer'
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Registration successful! Please login.');
                // Go back to login
                const registerScreen = document.querySelector('.screen-container');
                if (registerScreen) registerScreen.remove();
                this.showLogin();
            } else {
                alert(data.error || 'Registration failed');
            }
        } catch (error) {
            alert('Registration failed: ' + error.message);
        }
    }
    
    showMain() {
        // Remove current screen
        const current = document.querySelector('.screen-container');
        if (current) current.remove();
        
        const mainScreen = document.createElement('div');
        mainScreen.className = 'screen-container';
        mainScreen.innerHTML = `
            <div class="container">
                <h1>Welcome to Lako!</h1>
                <p id="welcome-name" style="color: #e67e22; margin-bottom: 20px;">Welcome, ${this.currentUser.full_name}!</p>
                <button id="logout-btn" class="btn-secondary">Logout</button>
                <div style="margin-top: 30px;">
                    <h3>Vendors Near You</h3>
                    <div id="vendors-list"></div>
                </div>
                <div class="dev-credit">
                    <p>196 Bula, Tiaong, Quezon</p>
                    <p>Kyle Brian M. Morillo & Alexander Collin Millicamp</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(mainScreen);
        
        document.getElementById('logout-btn').onclick = () => this.logout();
        this.loadVendors();
    }
    
    async loadVendors() {
        try {
            const response = await fetch('/api/vendors');
            const vendors = await response.json();
            const container = document.getElementById('vendors-list');
            
            if (vendors.length === 0) {
                container.innerHTML = '<p style="color: #c7b59b;">No vendors found yet.</p>';
            } else {
                container.innerHTML = vendors.map(v => `
                    <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 15px; text-align: left; border: 1px solid #f0dbb4;">
                        <strong>${this.escapeHtml(v.business_name)}</strong><br>
                        ⭐ ${v.rating || 0} (${v.review_count || 0} reviews)<br>
                        <small>${v.category || 'Street Food'}</small>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load vendors:', error);
            document.getElementById('vendors-list').innerHTML = '<p>Error loading vendors</p>';
        }
    }
    
    logout() {
        localStorage.removeItem('lako_user_id');
        this.currentUser = null;
        
        const mainScreen = document.querySelector('.screen-container');
        if (mainScreen) mainScreen.remove();
        
        this.showLanding();
    }
    
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LakoCustomerApp();
});
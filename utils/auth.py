"""Role-Based Access Control for DataPulse AI"""

import streamlit as st
from datetime import datetime
import hashlib

# User roles and permissions
ROLES = {
    'admin': {
        'name': 'Administrator',
        'icon': '👑',
        'color': '#ef4444',
        'permissions': ['view_dashboard', 'view_analytics', 'view_reports', 'view_data', 
                       'edit_data', 'delete_data', 'manage_users', 'manage_settings', 
                       'view_ai_chat', 'manage_alerts', 'export_data', 'api_access']
    },
    'manager': {
        'name': 'Manager',
        'icon': '💼',
        'color': '#8b5cf6',
        'permissions': ['view_dashboard', 'view_analytics', 'view_reports', 'view_data',
                       'edit_data', 'view_ai_chat', 'manage_alerts', 'export_data']
    },
    'analyst': {
        'name': 'Analyst',
        'icon': '📊',
        'color': '#3b82f6',
        'permissions': ['view_dashboard', 'view_analytics', 'view_reports', 'view_data',
                       'view_ai_chat', 'export_data']
    },
    'viewer': {
        'name': 'Viewer',
        'icon': '👁️',
        'color': '#64748b',
        'permissions': ['view_dashboard', 'view_reports']
    }
}

# Default users (in production, this would be in a database)
DEFAULT_USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Admin User', 'email': 'admin@datapulse.ai'},
    'manager': {'password': 'manager123', 'role': 'manager', 'name': 'Manager User', 'email': 'manager@datapulse.ai'},
    'analyst': {'password': 'analyst123', 'role': 'analyst', 'name': 'Analyst User', 'email': 'analyst@datapulse.ai'},
    'viewer': {'password': 'viewer123', 'role': 'viewer', 'name': 'Viewer User', 'email': 'viewer@datapulse.ai'}
}


def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_auth():
    """Initialize authentication state"""
    if 'users' not in st.session_state:
        st.session_state.users = {
            username: {**data, 'password': hash_password(data['password'])}
            for username, data in DEFAULT_USERS.items()
        }
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0


def authenticate(username, password):
    """Authenticate user credentials"""
    users = st.session_state.get('users', {})
    hashed = hash_password(password)
    
    if username in users and users[username]['password'] == hashed:
        st.session_state.authenticated = True
        st.session_state.current_user = {
            'username': username,
            'role': users[username]['role'],
            'name': users[username]['name'],
            'email': users[username]['email'],
            'login_time': datetime.now()
        }
        st.session_state.login_attempts = 0
        return True
    
    st.session_state.login_attempts += 1
    return False


def logout():
    """Log out current user"""
    st.session_state.authenticated = False
    st.session_state.current_user = None


def get_current_user():
    """Get current logged in user"""
    return st.session_state.get('current_user', None)


def get_user_role():
    """Get current user's role"""
    user = get_current_user()
    return user['role'] if user else None


def has_permission(permission):
    """Check if current user has a specific permission"""
    user = get_current_user()
    if not user:
        return False
    role = user['role']
    return permission in ROLES.get(role, {}).get('permissions', [])


def require_permission(permission):
    """Check permission and show error if denied"""
    if not has_permission(permission):
        st.error("🚫 Access Denied: You don't have permission to access this feature.")
        st.info("Contact your administrator for access.")
        return False
    return True


def get_role_badge(role):
    """Get HTML badge for a role"""
    role_info = ROLES.get(role, ROLES['viewer'])
    return f"""
    <span style="display:inline-flex;align-items:center;gap:4px;
                 background:{role_info['color']}15;color:{role_info['color']};
                 padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;">
        {role_info['icon']} {role_info['name']}
    </span>
    """


def render_login_page():
    """Render the login page"""
    st.markdown("""
    <style>
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .login-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #64748b;
            font-size: 0.95rem;
        }
        .demo-credentials {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1.5rem;
        }
        .demo-title {
            font-weight: 600;
            color: #475569;
            font-size: 0.8rem;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .demo-user {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .demo-user:last-child {
            border-bottom: none;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div class="login-header">
            <div class="login-logo">⚡</div>
            <h1 class="login-title">DataPulse AI</h1>
            <p class="login-subtitle">Sign in to access your analytics dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                remember = st.checkbox("Remember me", value=True)
            
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if submitted:
                if authenticate(username, password):
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    attempts_left = 5 - st.session_state.login_attempts
                    if attempts_left > 0:
                        st.error(f"❌ Invalid credentials. {attempts_left} attempts remaining.")
                    else:
                        st.error("🔒 Account locked. Please contact administrator.")
        
        st.markdown("""
        <div class="demo-credentials">
            <div class="demo-title">Demo Credentials</div>
        """, unsafe_allow_html=True)
        
        demo_users = [
            ('admin', 'admin123', '👑 Admin'),
            ('manager', 'manager123', '💼 Manager'),
            ('analyst', 'analyst123', '📊 Analyst'),
            ('viewer', 'viewer123', '👁️ Viewer')
        ]
        
        for user, pwd, label in demo_users:
            st.markdown(f"""
            <div class="demo-user">
                <span style="color:#475569;">{label}</span>
                <code style="background:#e2e8f0;padding:2px 8px;border-radius:4px;font-size:0.75rem;">
                    {user} / {pwd}
                </code>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_user_menu():
    """Render user menu in sidebar"""
    user = get_current_user()
    if not user:
        return
    
    role_info = ROLES.get(user['role'], ROLES['viewer'])
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                padding:1.25rem;border-radius:16px;margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:44px;height:44px;border-radius:12px;
                        background:{role_info['color']};display:flex;
                        align-items:center;justify-content:center;font-size:1.25rem;">
                {role_info['icon']}
            </div>
            <div>
                <div style="color:white;font-weight:600;font-size:0.95rem;">{user['name']}</div>
                <div style="color:#94a3b8;font-size:0.75rem;">{role_info['name']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
        logout()
        st.rerun()

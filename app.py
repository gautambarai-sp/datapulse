"""DataPulse AI - E-commerce Analytics Dashboard"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Page config
st.set_page_config(
    page_title="DataPulse AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules
from utils.auth import (init_auth, render_login_page, render_user_menu, 
                        get_current_user, has_permission, logout, ROLES)
from utils.alerts import init_alerts, evaluate_alerts, get_active_alerts, render_alert_badge


def load_css():
    """Load custom CSS styles"""
    css_file = Path(__file__).parent / "assets" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Additional inline styles
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
    </style>
    """, unsafe_allow_html=True)

load_css()


def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'onboarding_step': 0,
        'onboarding_complete': False,
        'company_info': {},
        'data_store': {
            'orders': pd.DataFrame(),
            'order_items': pd.DataFrame(),
            'customers': pd.DataFrame(),
            'products': pd.DataFrame(),
            'inventory': pd.DataFrame(),
            'returns': pd.DataFrame(),
            'reviews': pd.DataFrame(),
            'website_traffic': pd.DataFrame(),
            'ads_meta': pd.DataFrame(),
            'ads_google': pd.DataFrame(),
            'ads_shopify': pd.DataFrame()
        },
        'column_mappings': {},
        'api_connections': {},
        'chat_history': [],
        'llm_provider': 'none'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def auto_map_columns_for_type(df, data_type):
    """Auto-map columns based on data type"""
    COLUMN_MAPPINGS = {
        'orders': {
            'product_name': ['product_name', 'product name', 'productname', 'item_name', 'item name', 
                            'lineitem_name', 'lineitem name', 'sku_name', 'product_title'],
            'customer_name': ['customer_name', 'customer name', 'customername', 'buyer_name', 'buyer name'],
            'order_id': ['order_id', 'order id', 'orderid', 'order_number', 'transaction_id'],
            'order_date': ['order_date', 'date', 'created_at', 'order date', 'transaction_date', 'purchase_date'],
            'customer_id': ['customer_id', 'customer id', 'customerid', 'user_id', 'buyer_id'],
            'category': ['category', 'product_category', 'product_type', 'item_category'],
            'quantity': ['quantity', 'qty', 'units', 'count', 'lineitem_quantity'],
            'total_amount': ['total_amount', 'amount', 'total', 'grand_total', 'order_value', 'subtotal', 'total_price'],
            'payment_method': ['payment_method', 'payment', 'payment_type', 'pay_method', 'payment_mode', 'gateway'],
            'order_status': ['order_status', 'status', 'delivery_status', 'fulfillment_status', 'financial_status'],
            'city': ['city', 'shipping_city', 'billing_city', 'customer_city', 'delivery_city'],
            'state': ['state', 'region', 'province', 'shipping_state', 'billing_state']
        },
        'customers': {
            'customer_id': ['customer_id', 'id', 'user_id', 'client_id'],
            'name': ['name', 'full_name', 'customer_name'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'mobile', 'contact', 'phone_number'],
            'city': ['city', 'location', 'address_city'],
            'total_orders': ['total_orders', 'order_count', 'orders'],
            'total_spent': ['total_spent', 'lifetime_value', 'ltv', 'revenue']
        },
        'products': {
            'product_id': ['product_id', 'id', 'sku', 'item_id'],
            'product_name': ['product_name', 'name', 'title', 'item_name'],
            'category': ['category', 'product_category', 'type'],
            'price': ['price', 'unit_price', 'selling_price', 'mrp'],
            'cost': ['cost', 'cost_price', 'purchase_price']
        }
    }
    
    mappings = COLUMN_MAPPINGS.get(data_type, {})
    column_map = {}
    
    for standard, variations in mappings.items():
        for col in df.columns:
            col_lower = col.lower().replace('_', ' ').strip()
            if col_lower in [v.lower().replace('_', ' ') for v in variations]:
                column_map[standard] = col
                break
    
    st.session_state.column_mappings[data_type] = column_map


def clean_dataframe_on_import(df, data_type):
    """Clean and preprocess dataframe during import"""
    cleaned_df = df.copy()
    cleaning_report = []
    
    # Remove empty rows
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.dropna(how='all')
    removed_empty = initial_rows - len(cleaned_df)
    if removed_empty > 0:
        cleaning_report.append(f"Removed {removed_empty} empty rows")
    
    # Remove duplicates
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates()
    removed_dupes = initial_rows - len(cleaned_df)
    if removed_dupes > 0:
        cleaning_report.append(f"Removed {removed_dupes} duplicate rows")
    
    # Clean column names
    cleaned_df.columns = [str(col).strip().replace('\n', ' ').replace('\r', '') for col in cleaned_df.columns]
    
    # Auto-detect and clean columns
    for col in cleaned_df.columns:
        col_lower = col.lower()
        
        if any(kw in col_lower for kw in ['amount', 'price', 'total', 'cost', 'revenue', 'value', 'spent', 'spend', 'sales']):
            try:
                cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[₹$€£,\s]', '', regex=True)
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
            except:
                pass
        
        elif any(kw in col_lower for kw in ['quantity', 'qty', 'stock', 'count', 'units']):
            try:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0).astype(int)
            except:
                pass
        
        elif any(kw in col_lower for kw in ['date', 'created', 'updated', 'time', 'day']):
            try:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], dayfirst=True, errors='coerce')
            except:
                pass
    
    return cleaned_df, cleaning_report


def format_inr(value):
    """Format number as INR"""
    if pd.isna(value) or value == 0:
        return "₹0"
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    return f"₹{value:,.0f}"


def render_progress_indicator(current_step):
    """Render the onboarding progress indicator"""
    steps = [("1", "Welcome"), ("2", "Company"), ("3", "Data"), ("4", "Dashboard")]
    
    html = '<div class="step-indicator">'
    for i, (num, label) in enumerate(steps):
        if i < current_step:
            status, icon = "step-completed", "✓"
        elif i == current_step:
            status, icon = "step-active", num
        else:
            status, icon = "step-pending", num
        
        color = "#10b981" if i < current_step else "#6366f1" if i == current_step else "#94a3b8"
        html += f'<div class="step {status}"><div class="step-number">{icon}</div>'
        html += f'<span style="font-weight:500;color:{color};">{label}</span></div>'
        if i < len(steps) - 1:
            html += f'<div class="step-line {"completed" if i < current_step else ""}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_intro_page():
    """Render the introductory landing page"""
    render_progress_indicator(0)
    
    st.markdown("""
    <div class="hero-section animate-fade-in">
        <h1 class="hero-title"><span class="gradient-text">DataPulse AI</span></h1>
        <p class="hero-subtitle">
            Transform your e-commerce data into actionable insights with AI-powered analytics. 
            Ask questions in natural language, get instant visualizations, and make data-driven decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("🤖", "AI Chatbot", "Ask questions in plain English and get instant insights", "icon-purple"),
        ("📊", "Smart Analytics", "Auto-detect patterns, trends, and anomalies", "icon-blue"),
        ("🔔", "Smart Alerts", "Get notified when metrics cross thresholds", "icon-green"),
        ("👥", "Team Roles", "Role-based access for your entire team", "icon-orange")
    ]
    
    for col, (icon, title, desc, color) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon {color}">{icon}</div>
                <h3 style="font-size:1.1rem;margin-bottom:0.5rem;color:#1e293b;">{title}</h3>
                <p style="color:#64748b;font-size:0.9rem;line-height:1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()


def render_company_setup():
    """Render company information setup page"""
    render_progress_indicator(1)
    
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 style="color:#1e293b;">🏢 Tell Us About Your Business</h1>
        <p style="color:#64748b;">This helps us customize your analytics experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        company_name = st.text_input("Company Name *", value=st.session_state.company_info.get('name', ''),
                                     placeholder="Enter your company name")
        
        c1, c2 = st.columns(2)
        with c1:
            industry = st.selectbox("Industry *", ["Select Industry", "Fashion & Apparel", "Electronics", 
                "Beauty & Personal Care", "Home & Living", "Food & Beverages", "Health & Wellness", "Other"])
        with c2:
            monthly_orders = st.selectbox("Monthly Orders *", ["Select Range", "0-100", "100-500", 
                "500-1K", "1K-5K", "5K-10K", "10K-50K", "50K+"])
        
        c1, c2 = st.columns(2)
        with c1:
            currency = st.selectbox("Primary Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP"])
        with c2:
            timezone = st.selectbox("Timezone", ["Asia/Kolkata (IST)", "America/New_York (EST)", 
                "Europe/London (GMT)", "Asia/Dubai (GST)"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.onboarding_step = 0
                st.rerun()
        with c2:
            if st.button("Continue →", type="primary", use_container_width=True):
                if company_name and industry != "Select Industry" and monthly_orders != "Select Range":
                    st.session_state.company_info = {
                        'name': company_name, 'industry': industry, 'monthly_orders': monthly_orders,
                        'currency': currency, 'timezone': timezone
                    }
                    st.session_state.onboarding_step = 2
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")


def render_data_connection():
    """Render data connection page"""
    render_progress_indicator(2)
    
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 style="color:#1e293b;">📊 Connect Your Data</h1>
        <p style="color:#64748b;">Upload your files to get started</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'uploaded_files_data' not in st.session_state:
        st.session_state.uploaded_files_data = {}
    
    def auto_detect_data_type(filename, df_columns):
        filename_lower = filename.lower()
        patterns = {
            'orders': ['order', 'sales', 'transactions'],
            'customers': ['customer', 'client', 'user'],
            'products': ['product', 'catalog', 'item'],
            'inventory': ['inventory', 'stock'],
            'ads_meta': ['meta', 'facebook', 'fb_ad'],
            'ads_google': ['google', 'gads', 'adwords']
        }
        
        for data_type, keywords in patterns.items():
            for kw in keywords:
                if kw in filename_lower:
                    return data_type
        return 'orders'
    
    uploaded_files = st.file_uploader(
        "Upload CSV or Excel files", 
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.uploaded_files_data:
                try:
                    file.seek(0)
                    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
                    detected_type = auto_detect_data_type(file.name, df.columns.tolist())
                    st.session_state.uploaded_files_data[file.name] = {
                        'df': df, 'data_type': detected_type, 'imported': False
                    }
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")
        
        st.markdown("### 📋 Uploaded Files")
        
        data_types = ['orders', 'customers', 'products', 'inventory', 'ads_meta', 'ads_google', 'ads_shopify']
        
        for idx, (filename, file_data) in enumerate(st.session_state.uploaded_files_data.items()):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**📄 {filename}** ({len(file_data['df']):,} rows)")
            
            with col2:
                selected_type = st.selectbox(
                    "Type", data_types, 
                    index=data_types.index(file_data['data_type']) if file_data['data_type'] in data_types else 0,
                    key=f"type_{filename}_{idx}", label_visibility="collapsed"
                )
                st.session_state.uploaded_files_data[filename]['data_type'] = selected_type
            
            with col3:
                st.success("✅") if file_data['imported'] else st.caption("⏳")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Import All Files", type="primary", use_container_width=True):
                for filename, file_data in st.session_state.uploaded_files_data.items():
                    data_type = file_data['data_type']
                    df, _ = clean_dataframe_on_import(file_data['df'].copy(), data_type)
                    
                    if len(st.session_state.data_store.get(data_type, pd.DataFrame())) > 0:
                        existing = st.session_state.data_store[data_type]
                        df = pd.concat([existing, df], ignore_index=True).drop_duplicates()
                    
                    st.session_state.data_store[data_type] = df
                    auto_map_columns_for_type(df, data_type)
                    st.session_state.uploaded_files_data[filename]['imported'] = True
                
                st.success("✅ All files imported successfully!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 📦 Connected Data")
    
    data_status = [f"✅ **{k.replace('_',' ').title()}**: {len(v):,} records" 
                   for k, v in st.session_state.data_store.items() if len(v) > 0]
    
    if data_status:
        for s in data_status:
            st.markdown(s)
    else:
        st.info("No data connected yet. Upload your files above.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.onboarding_step = 1
                st.rerun()
        with c2:
            has_data = any(len(df) > 0 for df in st.session_state.data_store.values())
            if st.button("Go to Dashboard →", type="primary", use_container_width=True, disabled=not has_data):
                st.session_state.onboarding_complete = True
                st.session_state.onboarding_step = 3
                st.rerun()


def render_sidebar():
    """Render the main dashboard sidebar"""
    with st.sidebar:
        # User menu
        render_user_menu()
        
        st.markdown("---")
        
        # Navigation with role-based filtering
        user = get_current_user()
        
        nav_items = []
        if has_permission('view_dashboard'):
            nav_items.append("📊 Dashboard")
        if has_permission('view_ai_chat'):
            nav_items.append("🤖 AI Chat")
        if has_permission('view_data'):
            nav_items.append("📁 Data Manager")
        if has_permission('view_analytics'):
            nav_items.append("📢 Ads Analytics")
        if has_permission('view_reports'):
            nav_items.append("📈 Reports")
        if has_permission('manage_alerts'):
            # Add alert badge
            alerts = get_active_alerts()
            alert_count = len(alerts) if alerts else 0
            alert_badge = f" ({alert_count})" if alert_count > 0 else ""
            nav_items.append(f"🔔 Alerts{alert_badge}")
        if has_permission('manage_settings'):
            nav_items.append("⚙️ Settings")
        if has_permission('manage_users'):
            nav_items.append("👥 User Management")
        
        page = st.radio("Navigation", nav_items, label_visibility="collapsed")
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("**📈 Quick Stats**")
        orders = st.session_state.data_store.get('orders', pd.DataFrame())
        if len(orders) > 0:
            mappings = st.session_state.column_mappings.get('orders', {})
            amount_col = mappings.get('total_amount')
            if amount_col and amount_col in orders.columns:
                revenue = orders[amount_col].sum()
                st.metric("Revenue", format_inr(revenue))
            st.metric("Orders", f"{len(orders):,}")
        else:
            st.caption("No data loaded")
        
        return page


def render_alerts_page():
    """Render alerts management page"""
    from utils.alerts import render_alerts_panel, render_alert_settings, evaluate_alerts
    
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🔔 Alerts & Notifications</h1>
        <p class="page-subtitle">Monitor key metrics and get notified when thresholds are crossed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Evaluate current alerts
    evaluate_alerts()
    
    tab1, tab2 = st.tabs(["📬 Active Alerts", "⚙️ Alert Settings"])
    
    with tab1:
        render_alerts_panel()
    
    with tab2:
        render_alert_settings()


def render_user_management():
    """Render user management page (admin only)"""
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">👥 User Management</h1>
        <p class="page-subtitle">Manage team members and their access levels</p>
    </div>
    """, unsafe_allow_html=True)
    
    users = st.session_state.get('users', {})
    
    # Display existing users
    st.markdown("### Current Users")
    
    for username, user_data in users.items():
        role_info = ROLES.get(user_data['role'], ROLES['viewer'])
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{user_data['name']}**")
            st.caption(f"@{username}")
        
        with col2:
            st.markdown(f"{role_info['icon']} {role_info['name']}")
        
        with col3:
            st.caption(user_data['email'])
        
        with col4:
            if username != 'admin':  # Can't delete admin
                if st.button("🗑️", key=f"del_{username}"):
                    del st.session_state.users[username]
                    st.rerun()
        
        st.markdown("---")
    
    # Add new user
    st.markdown("### ➕ Add New User")
    
    with st.form("add_user"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
        
        with col2:
            new_email = st.text_input("Email")
            new_role = st.selectbox("Role", ['viewer', 'analyst', 'manager', 'admin'])
        
        new_password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Add User", type="primary"):
            if new_username and new_name and new_email and new_password:
                from utils.auth import hash_password
                st.session_state.users[new_username] = {
                    'password': hash_password(new_password),
                    'role': new_role,
                    'name': new_name,
                    'email': new_email
                }
                st.success(f"✅ User {new_username} added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields")


def render_main_dashboard():
    """Render the main analytics dashboard"""
    page = render_sidebar()
    
    # Evaluate alerts on each page load
    evaluate_alerts()
    
    # Show alert banner if critical alerts exist
    alerts = get_active_alerts()
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    if critical_alerts and '🔔 Alerts' not in page:
        st.markdown(f"""
        <div class="alert-banner alert-critical">
            <span>🔴</span>
            <span><strong>{len(critical_alerts)} critical alert(s)</strong> require attention</span>
        </div>
        """, unsafe_allow_html=True)
    
    if "📊 Dashboard" in page:
        from views.dashboard import render_dashboard
        render_dashboard()
    elif "🤖 AI Chat" in page:
        from views.ai_chat import render_ai_chat
        render_ai_chat()
    elif "📁 Data Manager" in page:
        from views.data_manager import render_data_manager
        render_data_manager()
    elif "📢 Ads Analytics" in page:
        from views.ads_analytics import render_ads_analytics
        render_ads_analytics()
    elif "📈 Reports" in page:
        from views.reports import render_reports
        render_reports()
    elif "🔔 Alerts" in page:
        render_alerts_page()
    elif "⚙️ Settings" in page:
        from views.settings import render_settings
        render_settings()
    elif "👥 User Management" in page:
        render_user_management()


def main():
    """Main application entry point"""
    init_session_state()
    init_auth()
    init_alerts()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        render_login_page()
        return
    
    # Main app flow
    if not st.session_state.onboarding_complete:
        if st.session_state.onboarding_step == 0:
            render_intro_page()
        elif st.session_state.onboarding_step == 1:
            render_company_setup()
        elif st.session_state.onboarding_step == 2:
            render_data_connection()
        else:
            render_main_dashboard()
    else:
        render_main_dashboard()


if __name__ == "__main__":
    main()

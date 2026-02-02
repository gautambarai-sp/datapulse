"""DataPulse - AI-Powered E-commerce Analytics Platform"""

import streamlit as st
import pandas as pd
import numpy as np
import re

# Page config - MUST be first
st.set_page_config(
    page_title="DataPulse AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3, .st-emotion-cache-10trblm {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {display: none;}
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* Sidebar - Purple Gradient Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #c7d2fe !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #a5b4fc !important;
    }
    
    /* Main Content Area */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 24px;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 1rem;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: #64748b;
        max-width: 600px;
        margin: 0 auto 2rem;
        line-height: 1.6;
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        border-color: #6366f1;
    }
    
    .feature-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .icon-purple { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
    .icon-blue { background: linear-gradient(135deg, #3b82f6, #0ea5e9); }
    .icon-green { background: linear-gradient(135deg, #10b981, #14b8a6); }
    .icon-orange { background: linear-gradient(135deg, #f59e0b, #f97316); }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .metric-highlight-purple {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
    }
    .metric-highlight-purple * { color: white !important; }
    
    .metric-highlight-green {
        background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%) !important;
        border: none !important;
    }
    .metric-highlight-green * { color: white !important; }
    
    .metric-highlight-blue {
        background: linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%) !important;
        border: none !important;
    }
    .metric-highlight-blue * { color: white !important; }
    
    .metric-highlight-orange {
        background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%) !important;
        border: none !important;
    }
    .metric-highlight-orange * { color: white !important; }
    
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Buttons */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.4);
    }
    
    /* Input fields */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8fafc;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
        color: #64748b;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #6366f1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Progress Steps */
    .step-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .step-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .step-active .step-number {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
    }
    
    .step-completed .step-number {
        background: #10b981;
        color: white;
    }
    
    .step-pending .step-number {
        background: #e2e8f0;
        color: #94a3b8;
    }
    
    .step-line {
        width: 60px;
        height: 2px;
        background: #e2e8f0;
    }
    
    .step-line.completed {
        background: #10b981;
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #6366f1;
    }
    
    /* Chat styling */
    .chat-message {
        padding: 1rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
    }
    
    .chat-user {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        margin-left: 2rem;
    }
    
    .chat-ai {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-right: 2rem;
    }
    
    /* Data cards */
    .data-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .data-card:hover {
        border-color: #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        background: #f8fafc !important;
        border-radius: 10px !important;
    }
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
    """Auto-map columns based on data type - with strict matching to avoid confusion"""
    # Standard column mappings for each data type - ORDER MATTERS (more specific first)
    COLUMN_MAPPINGS = {
        'orders': {
            # Product columns - very specific patterns ONLY
            'product_name': ['product_name', 'product name', 'productname', 'item_name', 'item name', 
                            'lineitem_name', 'lineitem name', 'sku_name', 'product_title'],
            # Customer columns - specific patterns
            'customer_name': ['customer_name', 'customer name', 'customername', 'buyer_name', 'buyer name'],
            # Other columns
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
        },
        'inventory': {
            'product_id': ['product_id', 'sku', 'item_id', 'id'],
            'product_name': ['product_name', 'name', 'item_name'],
            'quantity': ['quantity', 'stock', 'available', 'on_hand', 'qty'],
            'warehouse': ['warehouse', 'location', 'store']
        },
        'returns': {
            'return_id': ['return_id', 'rma_number', 'id'],
            'order_id': ['order_id', 'original_order'],
            'return_date': ['return_date', 'date', 'created_at'],
            'return_reason': ['return_reason', 'reason', 'cause'],
            'refund_amount': ['refund_amount', 'refund', 'amount']
        },
        'reviews': {
            'review_id': ['review_id', 'id'],
            'product_id': ['product_id', 'sku', 'item_id'],
            'rating': ['rating', 'stars', 'score'],
            'review_text': ['review_text', 'review', 'comment', 'feedback'],
            'review_date': ['review_date', 'date', 'created_at']
        },
        'ads_meta': {
            'date': ['date', 'day', 'reporting_date'],
            'campaign_name': ['campaign_name', 'campaign', 'campaign_id'],
            'impressions': ['impressions', 'impr'],
            'clicks': ['clicks', 'link_clicks'],
            'spend': ['spend', 'amount_spent', 'cost'],
            'conversions': ['conversions', 'purchases', 'results'],
            'revenue': ['revenue', 'purchase_value', 'conversion_value']
        },
        'ads_google': {
            'date': ['date', 'day'],
            'campaign': ['campaign', 'campaign_name'],
            'impressions': ['impressions', 'impr'],
            'clicks': ['clicks'],
            'cost': ['cost', 'spend', 'amount'],
            'conversions': ['conversions', 'conv'],
            'conversion_value': ['conversion_value', 'revenue']
        },
        'ads_shopify': {
            'date': ['date', 'day'],
            'campaign_type': ['campaign_type', 'marketing_channel', 'channel'],
            'spend': ['spend', 'cost', 'amount'],
            'clicks': ['clicks', 'sessions'],
            'orders': ['orders', 'purchases', 'conversions'],
            'revenue': ['revenue', 'sales', 'total_sales']
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
    
    # Store the mapping
    st.session_state.column_mappings[data_type] = column_map


def clean_dataframe_on_import(df, data_type):
    """Clean and preprocess dataframe during import"""
    cleaned_df = df.copy()
    cleaning_report = []
    
    # 1. Remove completely empty rows
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.dropna(how='all')
    removed_empty = initial_rows - len(cleaned_df)
    if removed_empty > 0:
        cleaning_report.append(f"Removed {removed_empty} empty rows")
    
    # 2. Remove duplicate rows
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates()
    removed_dupes = initial_rows - len(cleaned_df)
    if removed_dupes > 0:
        cleaning_report.append(f"Removed {removed_dupes} duplicate rows")
    
    # 3. Clean column names (strip whitespace, remove newlines)
    cleaned_df.columns = [str(col).strip().replace('\n', ' ').replace('\r', '') for col in cleaned_df.columns]
    
    # 4. Auto-detect and clean columns based on name patterns
    for col in cleaned_df.columns:
        col_lower = col.lower()
        
        # Clean amount/price/revenue columns - convert to numeric
        if any(kw in col_lower for kw in ['amount', 'price', 'total', 'cost', 'revenue', 'value', 'spent', 'spend', 'sales']):
            try:
                # Remove currency symbols and commas
                cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[₹$€£,\s]', '', regex=True)
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                cleaning_report.append(f"Cleaned {col} (numeric)")
            except:
                pass
        
        # Clean quantity/count columns
        elif any(kw in col_lower for kw in ['quantity', 'qty', 'stock', 'count', 'units', 'impressions', 'clicks', 'conversions']):
            try:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0).astype(int)
            except:
                pass
        
        # Clean date columns
        elif any(kw in col_lower for kw in ['date', 'created', 'updated', 'time', 'day']):
            try:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], dayfirst=True, errors='coerce')
                cleaning_report.append(f"Parsed {col} as date")
            except:
                pass
        
        # Clean email columns
        elif 'email' in col_lower:
            cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
        
        # Clean phone columns
        elif any(kw in col_lower for kw in ['phone', 'mobile']):
            cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[^\d+]', '', regex=True)
    
    # 5. Standardize status columns
    for col in cleaned_df.columns:
        if any(kw in col.lower() for kw in ['status', 'state']):
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.title()
            # Standardize common status values
            status_map = {
                'Delivered': 'Delivered',
                'Completed': 'Delivered',
                'Complete': 'Delivered',
                'Success': 'Delivered',
                'Shipped': 'Shipped',
                'In Transit': 'Shipped',
                'Intransit': 'Shipped',
                'Processing': 'Processing',
                'Pending': 'Processing',
                'Confirmed': 'Processing',
                'Rto': 'RTO',
                'Returned': 'RTO',
                'Return': 'RTO',
                'Cancelled': 'Cancelled',
                'Canceled': 'Cancelled',
                'Cancel': 'Cancelled'
            }
            cleaned_df[col] = cleaned_df[col].replace(status_map)
    
    # 6. Standardize payment method columns
    for col in cleaned_df.columns:
        if any(kw in col.lower() for kw in ['payment', 'pay_method', 'payment_mode']):
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.upper()
            payment_map = {
                'UPI': 'UPI',
                'GPAY': 'UPI',
                'PHONEPE': 'UPI',
                'PAYTM': 'UPI',
                'COD': 'COD',
                'CASH ON DELIVERY': 'COD',
                'CASH': 'COD',
                'CARD': 'Card',
                'CREDIT CARD': 'Card',
                'DEBIT CARD': 'Card',
                'CC': 'Card',
                'DC': 'Card',
                'NETBANKING': 'NetBanking',
                'NET BANKING': 'NetBanking',
                'NB': 'NetBanking',
                'WALLET': 'Wallet',
                'PREPAID': 'Prepaid',
                'EMI': 'EMI'
            }
            cleaned_df[col] = cleaned_df[col].replace(payment_map)
    
    # 7. Fill missing values for critical columns based on data type
    if data_type == 'orders':
        for col in cleaned_df.columns:
            if 'status' in col.lower():
                cleaned_df[col] = cleaned_df[col].fillna('Unknown')
            if 'payment' in col.lower():
                cleaned_df[col] = cleaned_df[col].fillna('Unknown')
    
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
        ("🤖", "AI Chatbot", "Ask questions in plain English and get instant insights with charts", "icon-purple"),
        ("📊", "Smart Analytics", "Auto-detect patterns, trends, and anomalies in your data", "icon-blue"),
        ("🔌", "Easy Integration", "Connect Shopify, WooCommerce, Amazon, Meta Ads & more", "icon-green"),
        ("📈", "Real-time Insights", "Track revenue, RTO rates, ad performance & customer behavior", "icon-orange")
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
    
    st.markdown("""
    <div style="text-align:center;margin:2rem 0;">
        <h2 style="color:#1e293b;margin-bottom:1rem;">💬 Ask Anything About Your Data</h2>
        <p style="color:#64748b;">Our AI understands natural language queries</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    queries = [
        ["What's my total revenue this month?", "Show me top 10 products", "Breakdown sales by city"],
        ["What's my RTO rate?", "Compare COD vs Prepaid", "Which customers buy the most?"],
        ["How are my Meta ads performing?", "What's my ROAS?", "Show ad spend trends"]
    ]
    
    for col, qs in zip([col1, col2, col3], queries):
        with col:
            for q in qs:
                st.markdown(f"""
                <div style="background:#f8fafc;padding:0.75rem 1rem;border-radius:10px;margin-bottom:0.5rem;
                            border-left:3px solid #6366f1;font-size:0.9rem;color:#475569;">"{q}"</div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()
    
    st.markdown("""
    <div style="text-align:center;margin-top:3rem;padding:2rem;background:#f8fafc;border-radius:16px;">
        <p style="color:#64748b;margin-bottom:1rem;">Trusted by e-commerce brands</p>
        <div style="display:flex;justify-content:center;gap:3rem;flex-wrap:wrap;">
            <span style="color:#94a3b8;font-weight:600;">🔒 Secure Data</span>
            <span style="color:#94a3b8;font-weight:600;">⚡ Real-time Sync</span>
            <span style="color:#94a3b8;font-weight:600;">🎯 99.9% Accuracy</span>
            <span style="color:#94a3b8;font-weight:600;">💬 24/7 AI Support</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
        
        platforms = st.multiselect("E-commerce Platforms", 
            ["Shopify", "WooCommerce", "Amazon", "Flipkart", "Meesho", "Custom Website"])
        
        ad_platforms = st.multiselect("Advertising Platforms",
            ["Meta Ads (Facebook/Instagram)", "Google Ads", "Amazon Ads"])
    
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
                        'currency': currency, 'timezone': timezone, 'platforms': platforms, 'ad_platforms': ad_platforms
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
        <p style="color:#64748b;">Upload multiple files at once and assign them to datasets</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📁 Upload Files", "🔌 Connect APIs"])
    
    with tab1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#f0f9ff 0%,#e0f2fe 100%);padding:2rem;border-radius:16px;
                    text-align:center;margin-bottom:1.5rem;border:2px dashed #0ea5e9;">
            <p style="font-size:2rem;margin-bottom:0.5rem;">📤</p>
            <p style="color:#0369a1;font-weight:600;">Drag & drop multiple CSV or Excel files at once</p>
            <p style="color:#64748b;font-size:0.875rem;">Select all files from a folder or pick multiple files</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize uploaded_files_data in session state
        if 'uploaded_files_data' not in st.session_state:
            st.session_state.uploaded_files_data = {}
        
        def auto_detect_data_type(filename, df_columns):
            """Auto-detect data type based on filename and column patterns"""
            filename_lower = filename.lower()
            columns_lower = [c.lower() for c in df_columns]
            
            # Filename pattern matching (highest priority)
            filename_patterns = {
                'orders': ['order', 'sales', 'transactions', 'purchase'],
                'order_items': ['order_item', 'orderitem', 'line_item', 'lineitem', 'items'],
                'customers': ['customer', 'client', 'user', 'buyer'],
                'products': ['product', 'catalog', 'item', 'sku'],
                'inventory': ['inventory', 'stock', 'warehouse'],
                'returns': ['return', 'refund', 'rma'],
                'reviews': ['review', 'rating', 'feedback'],
                'website_traffic': ['traffic', 'analytics', 'pageview', 'session', 'visitor'],
                'ads_meta': ['meta_ad', 'facebook_ad', 'fb_ad', 'instagram_ad', 'meta-ad', 'fb-ad'],
                'ads_google': ['google_ad', 'gads', 'adwords', 'google-ad', 'googleads'],
                'ads_shopify': ['shopify_ad', 'shopify-ad']
            }
            
            # Check filename patterns
            for data_type, patterns in filename_patterns.items():
                for pattern in patterns:
                    if pattern in filename_lower:
                        return data_type
            
            # Column-based detection (fallback)
            column_signatures = {
                'orders': ['order_id', 'order_date', 'total_amount', 'order_status'],
                'order_items': ['order_id', 'product_id', 'quantity', 'unit_price'],
                'customers': ['customer_id', 'customer_name', 'email', 'phone'],
                'products': ['product_id', 'product_name', 'category', 'price'],
                'inventory': ['sku', 'stock', 'quantity', 'warehouse', 'reorder'],
                'returns': ['return_id', 'return_date', 'return_reason', 'refund'],
                'reviews': ['review_id', 'rating', 'review_text', 'stars'],
                'website_traffic': ['page_views', 'sessions', 'bounce_rate', 'visitors'],
                'ads_meta': ['campaign_name', 'spend', 'reach', 'frequency'],
                'ads_google': ['campaign', 'cost', 'clicks', 'cpc', 'ctr'],
                'ads_shopify': ['ad_spend', 'orders', 'acos', 'roas']
            }
            
            # Count matching columns for each type
            best_match = 'orders'
            best_score = 0
            
            for data_type, signature_cols in column_signatures.items():
                score = sum(1 for sig_col in signature_cols if any(sig_col in col for col in columns_lower))
                if score > best_score:
                    best_score = score
                    best_match = data_type
            
            return best_match
        
        uploaded_files = st.file_uploader(
            "Upload Data Files", 
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True, 
            label_visibility="collapsed",
            help="Select multiple files at once using Ctrl+Click or Cmd+Click"
        )
        
        if uploaded_files:
            # Process all uploaded files
            for file in uploaded_files:
                if file.name not in st.session_state.uploaded_files_data:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
                        
                        # Auto-detect data type based on filename and columns
                        detected_type = auto_detect_data_type(file.name, df.columns.tolist())
                        
                        st.session_state.uploaded_files_data[file.name] = {
                            'df': df,
                            'data_type': detected_type,
                            'imported': False,
                            'auto_detected': True
                        }
                    except Exception as e:
                        st.error(f"Error reading {file.name}: {e}")
            
            st.markdown("### 📋 Uploaded Files")
            st.markdown("*Assign each file to its dataset type, then import all at once*")
            st.markdown("---")
            
            # Data type options
            data_types = [
                ('orders', '📦 Orders'),
                ('order_items', '🧾 Order Items'),
                ('customers', '👥 Customers'),
                ('products', '🛍️ Products'),
                ('inventory', '📊 Inventory'),
                ('returns', '↩️ Returns'),
                ('reviews', '⭐ Reviews'),
                ('website_traffic', '🌐 Website Traffic'),
                ('ads_meta', '📘 Meta Ads'),
                ('ads_google', '🔍 Google Ads'),
                ('ads_shopify', '🛒 Shopify Ads')
            ]
            data_type_labels = {k: v for k, v in data_types}
            data_type_keys = [k for k, v in data_types]
            
            # Display all files in a grid format
            for idx, (filename, file_data) in enumerate(st.session_state.uploaded_files_data.items()):
                df = file_data['df']
                
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**📄 {filename}**")
                    auto_badge = " 🎯" if file_data.get('auto_detected') else ""
                    st.caption(f"{len(df):,} rows × {len(df.columns)} cols{auto_badge}")
                
                with col2:
                    # Get current data type index safely
                    current_type = file_data.get('data_type', 'orders')
                    try:
                        type_index = data_type_keys.index(current_type)
                    except ValueError:
                        type_index = 0  # Default to orders
                    
                    selected_type = st.selectbox(
                        "Select Data Type",
                        options=data_type_keys,
                        format_func=lambda x: data_type_labels.get(x, x),
                        key=f"type_{filename}_{idx}",
                        index=type_index,
                        label_visibility="collapsed"
                    )
                    st.session_state.uploaded_files_data[filename]['data_type'] = selected_type
                
                with col3:
                    if file_data['imported']:
                        st.success("✅")
                    else:
                        st.caption("⏳")
                
                with col4:
                    if st.button("🗑️", key=f"remove_{filename}_{idx}", help="Remove file"):
                        del st.session_state.uploaded_files_data[filename]
                        st.rerun()
                
                # Preview expander with column mapping
                with st.expander(f"Preview & Map Columns - {filename}", expanded=False):
                    st.dataframe(df.head(5), use_container_width=True, hide_index=True)
                    
                    # Show column mapping for orders data type
                    if selected_type == 'orders':
                        st.markdown("##### 🔗 Column Mapping (for accurate analysis)")
                        st.caption("Map your columns to standard fields for accurate AI analysis")
                        
                        # Initialize mapping in session state if not exists
                        if f'col_map_{filename}' not in st.session_state:
                            st.session_state[f'col_map_{filename}'] = {}
                        
                        map_cols = st.columns(3)
                        col_options = ['(Auto-detect)'] + list(df.columns)
                        
                        with map_cols[0]:
                            prod_col = st.selectbox(
                                "Product/Item Name", col_options,
                                key=f"prod_{filename}_{idx}",
                                help="Which column has the product/item name?"
                            )
                            if prod_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['product_name'] = prod_col
                            
                            cust_col = st.selectbox(
                                "Customer Name", col_options,
                                key=f"cust_{filename}_{idx}",
                                help="Which column has the customer name?"
                            )
                            if cust_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['customer_name'] = cust_col
                        
                        with map_cols[1]:
                            amt_col = st.selectbox(
                                "Order Amount/Total", col_options,
                                key=f"amt_{filename}_{idx}",
                                help="Which column has the order total?"
                            )
                            if amt_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['total_amount'] = amt_col
                            
                            date_col = st.selectbox(
                                "Order Date", col_options,
                                key=f"date_{filename}_{idx}",
                                help="Which column has the order date?"
                            )
                            if date_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['order_date'] = date_col
                        
                        with map_cols[2]:
                            status_col = st.selectbox(
                                "Order Status", col_options,
                                key=f"status_{filename}_{idx}",
                                help="Which column has order/delivery status?"
                            )
                            if status_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['order_status'] = status_col
                            
                            city_col = st.selectbox(
                                "City/Location", col_options,
                                key=f"city_{filename}_{idx}",
                                help="Which column has the city?"
                            )
                            if city_col != '(Auto-detect)':
                                st.session_state[f'col_map_{filename}']['city'] = city_col
                    else:
                        st.caption(f"Columns: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
                
                st.markdown("---")
            
            # Import all button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:1rem;margin-bottom:1rem;">
                    <p style="margin:0;color:#166534;font-size:0.9rem;">
                        ✨ <strong>Auto-cleaning enabled:</strong> Data will be cleaned automatically (remove duplicates, fix formats, standardize values)
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Import & Clean All Files", type="primary", use_container_width=True):
                    imported_count = 0
                    cleaning_summary = []
                    
                    for filename, file_data in st.session_state.uploaded_files_data.items():
                        data_type = file_data['data_type']
                        df = file_data['df'].copy()
                        
                        # Clean the data
                        df, report = clean_dataframe_on_import(df, data_type)
                        if report:
                            cleaning_summary.extend([f"{filename}: {r}" for r in report])
                        
                        # If there's existing data of same type, merge
                        if len(st.session_state.data_store.get(data_type, pd.DataFrame())) > 0:
                            existing = st.session_state.data_store[data_type]
                            df = pd.concat([existing, df], ignore_index=True)
                            # Remove duplicates after merge
                            df = df.drop_duplicates()
                        
                        st.session_state.data_store[data_type] = df
                        
                        # First apply manual column mappings if user specified them
                        manual_mapping = st.session_state.get(f'col_map_{filename}', {})
                        if manual_mapping:
                            # Merge manual mappings with existing (manual takes priority)
                            existing_map = st.session_state.column_mappings.get(data_type, {})
                            existing_map.update(manual_mapping)
                            st.session_state.column_mappings[data_type] = existing_map
                        else:
                            # Auto-map columns for this data type
                            auto_map_columns_for_type(df, data_type)
                        
                        st.session_state.uploaded_files_data[filename]['imported'] = True
                        imported_count += 1
                    
                    st.success(f"✅ Successfully imported and cleaned {imported_count} file(s)!")
                    if cleaning_summary:
                        with st.expander("📋 Cleaning Report"):
                            for item in cleaning_summary:
                                st.caption(f"• {item}")
                    st.rerun()
    
    with tab2:
        col1, col2 = st.columns(2)
        for col, (icon, name, desc, color, key) in zip([col1, col2, col1, col2], [
            ("🛒", "Shopify", "Connect your Shopify store", "icon-green", "shopify"),
            ("📘", "Meta Ads", "Sync Facebook & Instagram ads", "icon-blue", "meta"),
            ("🔍", "Google Ads", "Import Google Ads data", "icon-orange", "google"),
            ("🛍️", "WooCommerce", "Connect WooCommerce store", "icon-purple", "woo")
        ]):
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon {color}">{icon}</div>
                    <h3>{name}</h3>
                    <p style="color:#64748b;font-size:0.875rem;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Connect {name}", key=f"connect_{key}"):
                    st.info(f"🔗 {name} OAuth flow would open here in production")
    
    st.markdown("<br>", unsafe_allow_html=True)
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
        st.markdown("""
        <div style="padding:1rem 0;">
            <h1 style="font-size:1.5rem;margin:0;">
                <span style="background:linear-gradient(135deg,#6366f1,#a855f7);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                    ⚡ DataPulse
                </span>
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.company_info.get('name'):
            st.caption(f"📍 {st.session_state.company_info['name']}")
        
        st.markdown("---")
        
        page = st.radio("Navigation", ["📊 Dashboard", "🤖 AI Chat", "📁 Data Manager", 
                                       "📢 Ads Analytics", "📈 Reports", "⚙️ Settings"],
                        label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("**📈 Quick Stats**")
        
        orders = st.session_state.data_store.get('orders', pd.DataFrame())
        if len(orders) > 0:
            mappings = st.session_state.column_mappings.get('orders', {})
            amount_col = mappings.get('total_amount')
            status_col = mappings.get('order_status')
            
            if amount_col and amount_col in orders.columns:
                if status_col and status_col in orders.columns:
                    delivered = orders[orders[status_col].str.lower().str.contains('deliver|complete', na=False)]
                    revenue = delivered[amount_col].sum()
                else:
                    revenue = orders[amount_col].sum()
                st.metric("Revenue", format_inr(revenue))
            st.metric("Orders", f"{len(orders):,}")
        else:
            st.caption("No data loaded")
        
        return page


def render_main_dashboard():
    """Render the main analytics dashboard"""
    page = render_sidebar()
    
    if page == "📊 Dashboard":
        from views.dashboard import render_dashboard
        render_dashboard()
    elif page == "🤖 AI Chat":
        from views.ai_chat import render_ai_chat
        render_ai_chat()
    elif page == "📁 Data Manager":
        from views.data_manager import render_data_manager
        render_data_manager()
    elif page == "📢 Ads Analytics":
        from views.ads_analytics import render_ads_analytics
        render_ads_analytics()
    elif page == "📈 Reports":
        from views.reports import render_reports
        render_reports()
    elif page == "⚙️ Settings":
        from views.settings import render_settings
        render_settings()


def main():
    """Main application entry point"""
    init_session_state()
    
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

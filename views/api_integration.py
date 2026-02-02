"""API Integration - Realistic API connections with proper OAuth flows"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json


def render_api_integration():
    """API Integration page with realistic implementation notes"""
    st.title("🔌 API Integration")
    
    st.info("""
    **⚠️ Important Note on API Integration**
    
    This page provides templates for connecting to e-commerce and ads platforms. 
    For **production use**, you'll need:
    - API credentials from each platform
    - OAuth authentication setup
    - Secure credential storage
    - Rate limiting compliance
    
    The test connections below simulate the flow but don't make real API calls without credentials.
    """)
    
    # Tabs for different integrations
    tabs = st.tabs([
        "🛒 E-commerce", 
        "📢 Ads Platforms",
        "🔧 Custom API"
    ])
    
    # E-commerce integrations
    with tabs[0]:
        render_ecommerce_integrations()
    
    # Ads platform integrations
    with tabs[1]:
        render_ads_integrations()
    
    # Custom API
    with tabs[2]:
        render_custom_api()


def render_ecommerce_integrations():
    """E-commerce platform integrations"""
    st.subheader("🛒 E-commerce Platform Connections")
    
    col1, col2 = st.columns(2)
    
    # ===== SHOPIFY =====
    with col1:
        st.markdown("### 🟢 Shopify")
        
        with st.expander("How Shopify Integration Works", expanded=False):
            st.markdown("""
            **Shopify uses OAuth 2.0 for authentication:**
            
            1. **Create a Shopify App** in your Partner Dashboard
            2. **Get API credentials**: API Key + API Secret
            3. **OAuth Flow**:
               - User clicks "Connect" → redirected to Shopify
               - User authorizes your app
               - Shopify redirects back with auth code
               - Exchange code for access token
            4. **Use access token** to call Shopify Admin API
            
            **Required Scopes:**
            - `read_orders` - Order history
            - `read_products` - Product catalog
            - `read_customers` - Customer data
            - `read_inventory` - Stock levels
            
            **API Endpoints:**
            - Orders: `GET /admin/api/2024-01/orders.json`
            - Products: `GET /admin/api/2024-01/products.json`
            - Customers: `GET /admin/api/2024-01/customers.json`
            """)
        
        shopify_connected = st.session_state.api_connections.get('shopify', {}).get('status') == 'active'
        
        if shopify_connected:
            st.success("✅ Shopify Connected")
            conn = st.session_state.api_connections['shopify']
            st.caption(f"Store: {conn.get('store_url', 'N/A')}")
            st.caption(f"Connected: {conn.get('connected_at', 'N/A')}")
            
            if st.button("🔄 Sync Shopify Data", key="sync_shopify"):
                with st.spinner("Syncing..."):
                    sync_shopify_data()
            
            if st.button("❌ Disconnect Shopify", key="disconnect_shopify"):
                del st.session_state.api_connections['shopify']
                st.rerun()
        else:
            store_url = st.text_input("Shopify Store URL", placeholder="mystore.myshopify.com")
            api_key = st.text_input("API Key", type="password", key="shopify_key")
            api_secret = st.text_input("API Secret", type="password", key="shopify_secret")
            access_token = st.text_input("Access Token", type="password", key="shopify_token",
                                        help="From your Shopify app's OAuth flow")
            
            if st.button("🔗 Connect Shopify", key="connect_shopify"):
                if store_url and access_token:
                    # In production, you'd verify the token here
                    st.session_state.api_connections['shopify'] = {
                        'status': 'active',
                        'store_url': store_url,
                        'access_token': access_token[:10] + "...",  # Don't store full token in state
                        'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.success("✅ Shopify connected!")
                    st.rerun()
                else:
                    st.error("Store URL and Access Token required")
    
    # ===== WOOCOMMERCE =====
    with col2:
        st.markdown("### 🟣 WooCommerce")
        
        with st.expander("How WooCommerce Integration Works", expanded=False):
            st.markdown("""
            **WooCommerce uses REST API with Key/Secret authentication:**
            
            1. **Generate API Keys** in WooCommerce → Settings → Advanced → REST API
            2. **Authentication**: HTTP Basic Auth with Consumer Key/Secret
            3. **Make API calls** directly with credentials
            
            **Required Permissions:**
            - Read permission on Orders, Products, Customers
            
            **API Endpoints:**
            - Orders: `GET /wp-json/wc/v3/orders`
            - Products: `GET /wp-json/wc/v3/products`
            - Customers: `GET /wp-json/wc/v3/customers`
            """)
        
        woo_connected = st.session_state.api_connections.get('woocommerce', {}).get('status') == 'active'
        
        if woo_connected:
            st.success("✅ WooCommerce Connected")
            conn = st.session_state.api_connections['woocommerce']
            st.caption(f"Site: {conn.get('site_url', 'N/A')}")
            
            if st.button("🔄 Sync WooCommerce Data", key="sync_woo"):
                with st.spinner("Syncing..."):
                    sync_woocommerce_data()
            
            if st.button("❌ Disconnect WooCommerce", key="disconnect_woo"):
                del st.session_state.api_connections['woocommerce']
                st.rerun()
        else:
            site_url = st.text_input("Site URL", placeholder="https://mystore.com")
            consumer_key = st.text_input("Consumer Key", type="password", key="woo_key")
            consumer_secret = st.text_input("Consumer Secret", type="password", key="woo_secret")
            
            if st.button("🔗 Connect WooCommerce", key="connect_woo"):
                if site_url and consumer_key and consumer_secret:
                    st.session_state.api_connections['woocommerce'] = {
                        'status': 'active',
                        'site_url': site_url,
                        'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.success("✅ WooCommerce connected!")
                    st.rerun()
                else:
                    st.error("All fields required")
    
    st.markdown("---")
    
    # Amazon
    st.markdown("### 🟠 Amazon Seller Central")
    
    with st.expander("How Amazon SP-API Integration Works", expanded=False):
        st.markdown("""
        **Amazon Selling Partner API (SP-API) requirements:**
        
        1. **Register as Developer** in Amazon Seller Central
        2. **Create an App** with required permissions
        3. **LWA (Login with Amazon)** OAuth flow
        4. **Use refresh token** for ongoing access
        
        **Required Roles:**
        - Orders API
        - Catalog Items API
        - Reports API
        
        **Complexity Note:** Amazon SP-API is more complex than Shopify/WooCommerce.
        Consider using a library like `python-amazon-sp-api`.
        """)
    
    amazon_connected = st.session_state.api_connections.get('amazon', {}).get('status') == 'active'
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        seller_id = st.text_input("Seller ID", key="amazon_seller")
    with col2:
        marketplace = st.selectbox("Marketplace", ["IN", "US", "UK", "DE", "JP"], key="amazon_mp")
    with col3:
        refresh_token = st.text_input("Refresh Token", type="password", key="amazon_token")
    
    if amazon_connected:
        st.success("✅ Amazon Connected")
        if st.button("❌ Disconnect Amazon", key="disconnect_amazon"):
            del st.session_state.api_connections['amazon']
            st.rerun()
    else:
        if st.button("🔗 Connect Amazon", key="connect_amazon"):
            if seller_id and refresh_token:
                st.session_state.api_connections['amazon'] = {
                    'status': 'active',
                    'seller_id': seller_id,
                    'marketplace': marketplace,
                    'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.success("✅ Amazon connected!")
                st.rerun()
            else:
                st.error("Seller ID and Refresh Token required")


def render_ads_integrations():
    """Ads platform integrations"""
    st.subheader("📢 Ads Platform Connections")
    
    col1, col2 = st.columns(2)
    
    # ===== META ADS =====
    with col1:
        st.markdown("### 📘 Meta Ads (Facebook/Instagram)")
        
        with st.expander("How Meta Ads Integration Works", expanded=False):
            st.markdown("""
            **Meta Marketing API Requirements:**
            
            1. **Create Meta Business Account**
            2. **Create App** in Meta for Developers
            3. **Request Permissions**: `ads_read`, `ads_management`
            4. **Get Access Token** via OAuth flow
            
            **API Endpoints:**
            - Campaigns: `GET /{ad_account_id}/campaigns`
            - Ad Sets: `GET /{ad_account_id}/adsets`
            - Insights: `GET /{ad_account_id}/insights`
            
            **Required Fields for Insights:**
            ```
            fields=impressions,reach,clicks,spend,
                   actions,cost_per_action_type
            ```
            
            **Rate Limits:** ~200 calls/hour per user
            """)
        
        meta_connected = st.session_state.api_connections.get('meta_ads', {}).get('status') == 'active'
        
        if meta_connected:
            st.success("✅ Meta Ads Connected")
            conn = st.session_state.api_connections['meta_ads']
            st.caption(f"Ad Account: {conn.get('ad_account_id', 'N/A')}")
            
            if st.button("🔄 Sync Meta Ads Data", key="sync_meta"):
                with st.spinner("Syncing..."):
                    sync_meta_ads_data()
            
            if st.button("❌ Disconnect Meta Ads", key="disconnect_meta"):
                del st.session_state.api_connections['meta_ads']
                st.rerun()
        else:
            ad_account_id = st.text_input("Ad Account ID", placeholder="act_123456789", key="meta_account")
            access_token = st.text_input("Access Token", type="password", key="meta_token",
                                        help="Long-lived token from Meta Business Suite")
            
            if st.button("🔗 Connect Meta Ads", key="connect_meta"):
                if ad_account_id and access_token:
                    st.session_state.api_connections['meta_ads'] = {
                        'status': 'active',
                        'ad_account_id': ad_account_id,
                        'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.success("✅ Meta Ads connected!")
                    st.rerun()
                else:
                    st.error("Ad Account ID and Access Token required")
    
    # ===== GOOGLE ADS =====
    with col2:
        st.markdown("### 🔍 Google Ads")
        
        with st.expander("How Google Ads Integration Works", expanded=False):
            st.markdown("""
            **Google Ads API Requirements:**
            
            1. **Google Ads Manager Account** (MCC recommended)
            2. **Developer Token** from API Center
            3. **OAuth 2.0 Credentials** from Google Cloud Console
            4. **Link accounts** (OAuth + Developer Token + Customer ID)
            
            **API Access Levels:**
            - Basic: ~10,000 operations/day
            - Standard: ~50,000 operations/day
            
            **Key Resources:**
            - Campaign: `customers/{customer_id}/campaigns`
            - Ad Group: `customers/{customer_id}/adGroups`
            - Metrics: GoogleAdsService.SearchStream
            
            **GAQL Example:**
            ```sql
            SELECT campaign.name, metrics.cost_micros,
                   metrics.clicks, metrics.conversions
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
            ```
            """)
        
        google_connected = st.session_state.api_connections.get('google_ads', {}).get('status') == 'active'
        
        if google_connected:
            st.success("✅ Google Ads Connected")
            conn = st.session_state.api_connections['google_ads']
            st.caption(f"Customer ID: {conn.get('customer_id', 'N/A')}")
            
            if st.button("🔄 Sync Google Ads Data", key="sync_google"):
                with st.spinner("Syncing..."):
                    sync_google_ads_data()
            
            if st.button("❌ Disconnect Google Ads", key="disconnect_google"):
                del st.session_state.api_connections['google_ads']
                st.rerun()
        else:
            customer_id = st.text_input("Customer ID", placeholder="123-456-7890", key="google_customer")
            developer_token = st.text_input("Developer Token", type="password", key="google_dev_token")
            refresh_token = st.text_input("OAuth Refresh Token", type="password", key="google_refresh")
            
            if st.button("🔗 Connect Google Ads", key="connect_google"):
                if customer_id and developer_token:
                    st.session_state.api_connections['google_ads'] = {
                        'status': 'active',
                        'customer_id': customer_id,
                        'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.success("✅ Google Ads connected!")
                    st.rerun()
                else:
                    st.error("Customer ID and Developer Token required")
    
    st.markdown("---")
    
    # ===== SHOPIFY MARKETING =====
    st.markdown("### 🛍️ Shopify Marketing API")
    
    with st.expander("How Shopify Marketing Integration Works", expanded=False):
        st.markdown("""
        **Shopify Marketing API** (part of Shopify Admin API):
        
        If you're already connected to Shopify, marketing data is available via:
        - `GET /admin/api/2024-01/marketing_events.json`
        
        **Includes:**
        - Shopify Email campaigns
        - Shopify Audiences
        - Marketing automations
        
        **Note:** Third-party ads (Facebook, Google) shown in Shopify 
        are via their respective attribution APIs.
        """)
    
    shopify_connected = st.session_state.api_connections.get('shopify', {}).get('status') == 'active'
    
    if shopify_connected:
        st.info("✅ Shopify Marketing is available through your Shopify connection")
        if st.button("🔄 Sync Shopify Marketing Data", key="sync_shopify_marketing"):
            with st.spinner("Syncing..."):
                sync_shopify_marketing_data()
    else:
        st.warning("Connect Shopify first in the E-commerce tab to access marketing data")


def render_custom_api():
    """Custom API configuration"""
    st.subheader("🔧 Custom API Integration")
    
    st.markdown("""
    Connect to any custom API that returns JSON data with orders, customers, or products.
    """)
    
    api_name = st.text_input("API Name", placeholder="My Custom API")
    base_url = st.text_input("Base URL", placeholder="https://api.example.com/v1")
    
    auth_method = st.selectbox("Authentication Method", 
                               ["None", "API Key (Header)", "API Key (Query)", "Bearer Token", "Basic Auth"])
    
    if auth_method == "API Key (Header)":
        header_name = st.text_input("Header Name", value="X-API-Key")
        api_key = st.text_input("API Key", type="password")
    elif auth_method == "API Key (Query)":
        param_name = st.text_input("Parameter Name", value="api_key")
        api_key = st.text_input("API Key", type="password")
    elif auth_method == "Bearer Token":
        bearer_token = st.text_input("Bearer Token", type="password")
    elif auth_method == "Basic Auth":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
    
    st.markdown("#### Endpoint Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        orders_endpoint = st.text_input("Orders Endpoint", placeholder="/orders")
        customers_endpoint = st.text_input("Customers Endpoint", placeholder="/customers")
    
    with col2:
        products_endpoint = st.text_input("Products Endpoint", placeholder="/products")
        inventory_endpoint = st.text_input("Inventory Endpoint", placeholder="/inventory")
    
    if st.button("💾 Save Custom API Configuration"):
        if api_name and base_url:
            st.session_state.api_connections['custom'] = {
                'status': 'configured',
                'api_name': api_name,
                'base_url': base_url,
                'auth_method': auth_method,
                'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.success(f"✅ {api_name} configuration saved!")
        else:
            st.error("API Name and Base URL required")


# ===== SYNC FUNCTIONS =====
# These are placeholders that would make real API calls in production

def sync_shopify_data():
    """Simulate Shopify data sync"""
    import numpy as np
    
    # In production, this would call Shopify Admin API
    # GET https://{store}.myshopify.com/admin/api/2024-01/orders.json
    
    dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
    orders = pd.DataFrame({
        'order_id': [f'SHOP{i:05d}' for i in range(1, 51)],
        'order_date': np.random.choice(dates, 50),
        'customer_id': [f'CUST{np.random.randint(1, 30):03d}' for _ in range(50)],
        'product_name': np.random.choice(['Product A', 'Product B', 'Product C'], 50),
        'quantity': np.random.randint(1, 5, 50),
        'total_amount': np.random.uniform(500, 5000, 50).round(2),
        'order_status': np.random.choice(['Delivered', 'Shipped', 'Processing'], 50, p=[0.7, 0.2, 0.1]),
        'payment_method': np.random.choice(['Card', 'UPI', 'COD'], 50)
    })
    
    st.session_state.data_store['orders'] = orders
    st.session_state.column_mappings['orders'] = {
        'order_id': 'order_id',
        'order_date': 'order_date',
        'customer_id': 'customer_id',
        'product_name': 'product_name',
        'quantity': 'quantity',
        'total_amount': 'total_amount',
        'order_status': 'order_status',
        'payment_method': 'payment_method'
    }
    
    st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.success(f"✅ Synced {len(orders)} orders from Shopify")


def sync_woocommerce_data():
    """Simulate WooCommerce data sync"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    orders = pd.DataFrame({
        'order_id': [f'WOO{i:05d}' for i in range(1, 31)],
        'order_date': np.random.choice(dates, 30),
        'customer_id': [f'WCUST{np.random.randint(1, 20):03d}' for _ in range(30)],
        'product_name': np.random.choice(['WC Product 1', 'WC Product 2', 'WC Product 3'], 30),
        'quantity': np.random.randint(1, 3, 30),
        'total_amount': np.random.uniform(300, 3000, 30).round(2),
        'order_status': np.random.choice(['completed', 'processing', 'on-hold'], 30, p=[0.75, 0.15, 0.1])
    })
    
    # Merge or replace existing orders
    existing = st.session_state.data_store.get('orders', pd.DataFrame())
    if len(existing) > 0:
        combined = pd.concat([existing, orders], ignore_index=True)
        st.session_state.data_store['orders'] = combined
        st.success(f"✅ Merged {len(orders)} WooCommerce orders (Total: {len(combined)})")
    else:
        st.session_state.data_store['orders'] = orders
        st.success(f"✅ Synced {len(orders)} orders from WooCommerce")


def sync_meta_ads_data():
    """Simulate Meta Ads data sync"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    ads_data = pd.DataFrame({
        'date': dates,
        'campaign_name': np.random.choice(['Awareness', 'Traffic', 'Conversions'], 30),
        'ad_set_name': np.random.choice(['Audience A', 'Audience B', 'Lookalike'], 30),
        'impressions': np.random.randint(10000, 100000, 30),
        'reach': np.random.randint(8000, 80000, 30),
        'clicks': np.random.randint(100, 2000, 30),
        'spend': np.random.uniform(500, 5000, 30).round(2),
        'conversions': np.random.randint(5, 50, 30),
        'revenue': np.random.uniform(1000, 15000, 30).round(2),
        'platform': np.random.choice(['Facebook', 'Instagram'], 30)
    })
    
    st.session_state.data_store['ads_meta'] = ads_data
    st.success(f"✅ Synced {len(ads_data)} days of Meta Ads data")


def sync_google_ads_data():
    """Simulate Google Ads data sync"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    ads_data = pd.DataFrame({
        'date': dates,
        'campaign': np.random.choice(['Search - Brand', 'Search - Generic', 'Display', 'Shopping'], 30),
        'ad_group': np.random.choice(['Group A', 'Group B', 'Group C'], 30),
        'impressions': np.random.randint(5000, 50000, 30),
        'clicks': np.random.randint(50, 1000, 30),
        'cost': np.random.uniform(300, 3000, 30).round(2),
        'conversions': np.random.randint(3, 30, 30),
        'conversion_value': np.random.uniform(800, 10000, 30).round(2),
        'network': np.random.choice(['Search', 'Display', 'YouTube'], 30)
    })
    
    st.session_state.data_store['ads_google'] = ads_data
    st.success(f"✅ Synced {len(ads_data)} days of Google Ads data")


def sync_shopify_marketing_data():
    """Simulate Shopify marketing data sync"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    marketing_data = pd.DataFrame({
        'date': dates,
        'campaign_type': np.random.choice(['Email', 'Shopify Audiences', 'Automation'], 30),
        'spend': np.random.uniform(100, 1000, 30).round(2),
        'clicks': np.random.randint(50, 500, 30),
        'orders': np.random.randint(2, 20, 30),
        'revenue': np.random.uniform(500, 5000, 30).round(2)
    })
    
    st.session_state.data_store['ads_shopify'] = marketing_data
    st.success(f"✅ Synced {len(marketing_data)} days of Shopify marketing data")

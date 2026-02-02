"""Data Manager with cleaning and preprocessing capabilities"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re


# Data type detection patterns
DATA_TYPE_PATTERNS = {
    'orders': ['order', 'transaction', 'sale', 'purchase', 'invoice', 'shipment', 'delivery', 'cod', 'prepaid', 'rto'],
    'order_items': ['order_item', 'line_item', 'order_line', 'item_detail', 'basket', 'cart_item'],
    'customers': ['customer', 'client', 'user', 'member', 'subscriber', 'buyer', 'contact', 'email', 'phone'],
    'products': ['product', 'item', 'sku', 'catalog', 'merchandise', 'goods', 'variant', 'category'],
    'inventory': ['inventory', 'stock', 'warehouse', 'quantity', 'available', 'reserved', 'reorder'],
    'returns': ['return', 'refund', 'rma', 'exchange', 'reversal', 'cancellation', 'return_reason'],
    'reviews': ['review', 'rating', 'feedback', 'testimonial', 'comment', 'star', 'nps'],
    'website_traffic': ['traffic', 'session', 'pageview', 'visitor', 'bounce', 'analytics', 'utm', 'source', 'medium'],
    'ads_meta': ['facebook', 'instagram', 'meta', 'fb_', 'ig_', 'reach', 'cpm', 'ad_set', 'adset'],
    'ads_google': ['google_ads', 'google ads', 'adwords', 'search_term', 'quality_score', 'ad_group', 'ppc'],
    'ads_shopify': ['shopify_marketing', 'shop_campaign', 'shopify_ad', 'shopify ads', 'shopify_ads']
}

# Standard column mappings
COLUMN_MAPPINGS = {
    'orders': {
        'order_id': ['order_id', 'order id', 'orderid', 'id', 'order_number', 'transaction_id', 'invoice_id'],
        'order_date': ['order_date', 'date', 'created_at', 'order date', 'transaction_date', 'created', 'purchase_date'],
        'customer_name': ['customer_name', 'customer', 'name', 'buyer', 'client', 'customer name', 'full_name'],
        'customer_email': ['email', 'customer_email', 'buyer_email', 'contact_email'],
        'product_name': ['product_name', 'product', 'item', 'item_name', 'product name', 'sku_name'],
        'category': ['category', 'product_category', 'type', 'product_type', 'item_category'],
        'quantity': ['quantity', 'qty', 'units', 'count', 'amount_qty'],
        'total_amount': ['total_amount', 'amount', 'total', 'price', 'revenue', 'order_value', 'total_price', 'grand_total'],
        'payment_method': ['payment_method', 'payment', 'payment_type', 'pay_method', 'payment method', 'payment_mode'],
        'order_status': ['order_status', 'status', 'delivery_status', 'fulfillment_status', 'state', 'order status'],
        'city': ['city', 'customer_city', 'shipping_city', 'delivery_city', 'location'],
        'state': ['state', 'region', 'province', 'customer_state', 'shipping_state']
    },
    'customers': {
        'customer_id': ['customer_id', 'id', 'user_id', 'client_id', 'member_id'],
        'name': ['name', 'full_name', 'customer_name', 'display_name'],
        'email': ['email', 'email_address', 'contact_email'],
        'phone': ['phone', 'mobile', 'contact', 'phone_number', 'telephone'],
        'city': ['city', 'location', 'address_city'],
        'state': ['state', 'region', 'province'],
        'total_orders': ['total_orders', 'order_count', 'orders', 'purchase_count'],
        'total_spent': ['total_spent', 'lifetime_value', 'ltv', 'revenue', 'total_purchase'],
        'created_at': ['created_at', 'join_date', 'signup_date', 'registered_at', 'first_order_date'],
        'segment': ['segment', 'tier', 'type', 'customer_type', 'category']
    },
    'products': {
        'product_id': ['product_id', 'id', 'sku', 'item_id', 'sku_id'],
        'product_name': ['product_name', 'name', 'title', 'item_name', 'description'],
        'category': ['category', 'product_category', 'type', 'product_type'],
        'subcategory': ['subcategory', 'sub_category', 'sub_type'],
        'price': ['price', 'unit_price', 'selling_price', 'mrp', 'cost'],
        'cost': ['cost', 'cost_price', 'purchase_price', 'cogs'],
        'brand': ['brand', 'manufacturer', 'vendor'],
        'supplier': ['supplier', 'vendor', 'seller']
    },
    'inventory': {
        'product_id': ['product_id', 'sku', 'item_id', 'id'],
        'product_name': ['product_name', 'name', 'item_name', 'sku_name'],
        'quantity': ['quantity', 'stock', 'available', 'on_hand', 'qty'],
        'warehouse': ['warehouse', 'location', 'store', 'fulfillment_center'],
        'reorder_level': ['reorder_level', 'reorder_point', 'min_stock', 'safety_stock'],
        'last_updated': ['last_updated', 'updated_at', 'sync_date']
    },
    'order_items': {
        'order_id': ['order_id', 'order_number', 'transaction_id'],
        'item_id': ['item_id', 'line_item_id', 'id'],
        'product_id': ['product_id', 'sku', 'sku_id'],
        'product_name': ['product_name', 'name', 'item_name', 'title'],
        'quantity': ['quantity', 'qty', 'units'],
        'unit_price': ['unit_price', 'price', 'item_price', 'selling_price'],
        'discount': ['discount', 'discount_amount', 'promo_discount'],
        'total': ['total', 'line_total', 'item_total', 'amount']
    },
    'returns': {
        'return_id': ['return_id', 'rma_number', 'return_number', 'id'],
        'order_id': ['order_id', 'original_order', 'order_number'],
        'return_date': ['return_date', 'date', 'created_at', 'initiated_date'],
        'product_id': ['product_id', 'sku', 'item_id'],
        'product_name': ['product_name', 'item_name', 'product'],
        'quantity': ['quantity', 'qty', 'return_qty'],
        'return_reason': ['return_reason', 'reason', 'reason_code', 'cause'],
        'return_status': ['return_status', 'status', 'state'],
        'refund_amount': ['refund_amount', 'refund', 'amount', 'refund_value'],
        'return_type': ['return_type', 'type', 'exchange_or_refund']
    },
    'reviews': {
        'review_id': ['review_id', 'id', 'feedback_id'],
        'product_id': ['product_id', 'sku', 'item_id'],
        'product_name': ['product_name', 'product', 'item_name'],
        'customer_id': ['customer_id', 'user_id', 'reviewer_id'],
        'rating': ['rating', 'stars', 'score', 'star_rating'],
        'review_text': ['review_text', 'review', 'comment', 'feedback', 'text'],
        'review_date': ['review_date', 'date', 'created_at', 'submitted_at'],
        'verified_purchase': ['verified_purchase', 'verified', 'is_verified'],
        'helpful_votes': ['helpful_votes', 'helpful', 'upvotes', 'likes']
    },
    'website_traffic': {
        'date': ['date', 'day', 'session_date'],
        'sessions': ['sessions', 'visits', 'session_count'],
        'users': ['users', 'visitors', 'unique_visitors', 'unique_users'],
        'pageviews': ['pageviews', 'page_views', 'views'],
        'bounce_rate': ['bounce_rate', 'bounces', 'bounce'],
        'avg_session_duration': ['avg_session_duration', 'session_duration', 'time_on_site'],
        'source': ['source', 'traffic_source', 'utm_source'],
        'medium': ['medium', 'traffic_medium', 'utm_medium'],
        'campaign': ['campaign', 'utm_campaign', 'campaign_name'],
        'conversions': ['conversions', 'goals', 'goal_completions'],
        'revenue': ['revenue', 'transaction_revenue', 'ecommerce_revenue']
    },
    'ads_meta': {
        'date': ['date', 'day', 'reporting_date'],
        'campaign_name': ['campaign_name', 'campaign', 'campaign_id'],
        'ad_set_name': ['ad_set_name', 'adset', 'ad_set', 'adset_name'],
        'impressions': ['impressions', 'impr'],
        'reach': ['reach', 'unique_reach'],
        'clicks': ['clicks', 'link_clicks'],
        'spend': ['spend', 'amount_spent', 'cost'],
        'conversions': ['conversions', 'purchases', 'results'],
        'revenue': ['revenue', 'purchase_value', 'conversion_value'],
        'cpm': ['cpm', 'cost_per_1000_impressions'],
        'cpc': ['cpc', 'cost_per_click'],
        'platform': ['platform', 'publisher_platform']
    },
    'ads_google': {
        'date': ['date', 'day', 'reporting_date'],
        'campaign': ['campaign', 'campaign_name'],
        'ad_group': ['ad_group', 'adgroup', 'ad_group_name'],
        'impressions': ['impressions', 'impr'],
        'clicks': ['clicks'],
        'cost': ['cost', 'spend', 'amount'],
        'conversions': ['conversions', 'conv'],
        'conversion_value': ['conversion_value', 'conv_value', 'revenue'],
        'ctr': ['ctr', 'click_through_rate'],
        'cpc': ['cpc', 'avg_cpc', 'cost_per_click'],
        'network': ['network', 'ad_network_type']
    },
    'ads_shopify': {
        'date': ['date', 'day'],
        'campaign_type': ['campaign_type', 'marketing_channel', 'channel'],
        'spend': ['spend', 'cost', 'amount'],
        'clicks': ['clicks', 'sessions'],
        'orders': ['orders', 'purchases', 'conversions'],
        'revenue': ['revenue', 'sales', 'total_sales'],
        'roas': ['roas', 'return_on_ad_spend']
    }
}


def detect_data_type(df):
    """Auto-detect data type from columns"""
    columns_lower = [c.lower().replace('_', ' ') for c in df.columns]
    col_text = ' '.join(columns_lower)
    
    scores = {}
    for dtype, keywords in DATA_TYPE_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in col_text)
        scores[dtype] = score
    
    best_match = max(scores, key=scores.get)
    confidence = scores[best_match] / max(len(DATA_TYPE_PATTERNS[best_match]), 1)
    
    return best_match if confidence > 0.1 else 'orders', confidence


def auto_map_columns(df, data_type):
    """Auto-map columns based on data type"""
    mappings = COLUMN_MAPPINGS.get(data_type, {})
    column_map = {}
    
    for standard, variations in mappings.items():
        for col in df.columns:
            col_lower = col.lower().replace('_', ' ').strip()
            if col_lower in [v.lower() for v in variations]:
                column_map[standard] = col
                break
    
    return column_map


def clean_dataframe(df, data_type):
    """Clean and preprocess dataframe"""
    cleaned_df = df.copy()
    cleaning_report = []
    
    # 1. Remove completely empty rows
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.dropna(how='all')
    if len(cleaned_df) < initial_rows:
        cleaning_report.append(f"Removed {initial_rows - len(cleaned_df)} empty rows")
    
    # 2. Remove duplicate rows
    initial_rows = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates()
    if len(cleaned_df) < initial_rows:
        cleaning_report.append(f"Removed {initial_rows - len(cleaned_df)} duplicate rows")
    
    # 3. Clean column names
    cleaned_df.columns = [col.strip().replace('\n', ' ').replace('\r', '') for col in cleaned_df.columns]
    
    # 4. Auto-detect and clean numeric columns
    for col in cleaned_df.columns:
        col_lower = col.lower()
        
        # Clean amount/price columns
        if any(kw in col_lower for kw in ['amount', 'price', 'total', 'cost', 'revenue', 'value', 'spent']):
            cleaned_df[col] = pd.to_numeric(
                cleaned_df[col].astype(str).str.replace(r'[₹$,\s]', '', regex=True),
                errors='coerce'
            )
            cleaning_report.append(f"Converted {col} to numeric")
        
        # Clean quantity columns
        elif any(kw in col_lower for kw in ['quantity', 'qty', 'stock', 'count', 'units']):
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0).astype(int)
        
        # Clean date columns
        elif any(kw in col_lower for kw in ['date', 'created', 'updated', 'time']):
            try:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], dayfirst=True, errors='coerce')
                cleaning_report.append(f"Converted {col} to datetime")
            except:
                pass
        
        # Clean email columns
        elif 'email' in col_lower:
            cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
        
        # Clean phone columns
        elif any(kw in col_lower for kw in ['phone', 'mobile', 'contact']):
            cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[^\d+]', '', regex=True)
    
    # 5. Standardize status columns
    for col in cleaned_df.columns:
        if any(kw in col.lower() for kw in ['status', 'state']):
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.title()
    
    # 6. Fill missing values for critical columns
    mappings = auto_map_columns(cleaned_df, data_type)
    
    if data_type == 'orders':
        if 'order_status' in mappings and mappings['order_status'] in cleaned_df.columns:
            cleaned_df[mappings['order_status']] = cleaned_df[mappings['order_status']].fillna('Unknown')
        if 'payment_method' in mappings and mappings['payment_method'] in cleaned_df.columns:
            cleaned_df[mappings['payment_method']] = cleaned_df[mappings['payment_method']].fillna('Unknown')
    
    return cleaned_df, cleaning_report


def validate_data(df, data_type):
    """Validate data quality"""
    issues = []
    warnings = []
    mappings = auto_map_columns(df, data_type)
    
    # Check for required columns
    required_cols = {
        'orders': ['order_id', 'total_amount'],
        'customers': ['customer_id', 'email'],
        'products': ['product_id', 'product_name'],
        'inventory': ['product_id', 'quantity']
    }
    
    for req in required_cols.get(data_type, []):
        if req not in mappings:
            issues.append(f"Missing required column: {req}")
    
    # Check for data quality issues
    total_rows = len(df)
    
    # Check null percentages
    for col in df.columns:
        null_pct = df[col].isna().sum() / total_rows * 100
        if null_pct > 50:
            warnings.append(f"{col}: {null_pct:.1f}% missing values")
        elif null_pct > 20:
            warnings.append(f"{col}: {null_pct:.1f}% missing values")
    
    # Data type specific validations
    if data_type == 'orders' and 'total_amount' in mappings:
        amount_col = mappings['total_amount']
        if amount_col in df.columns:
            negative = (df[amount_col] < 0).sum()
            if negative > 0:
                warnings.append(f"{negative} orders with negative amounts")
            
            zeros = (df[amount_col] == 0).sum()
            if zeros > total_rows * 0.1:
                warnings.append(f"{zeros} orders with zero amounts")
    
    if data_type == 'inventory' and 'quantity' in mappings:
        qty_col = mappings['quantity']
        if qty_col in df.columns:
            negative = (df[qty_col] < 0).sum()
            if negative > 0:
                issues.append(f"{negative} items with negative stock")
    
    return issues, warnings


def get_data_quality_score(df, data_type):
    """Calculate data quality score"""
    score = 100
    mappings = auto_map_columns(df, data_type)
    
    # Deduct for missing required columns
    required_cols = {
        'orders': ['order_id', 'order_date', 'total_amount', 'order_status'],
        'customers': ['customer_id', 'email', 'name'],
        'products': ['product_id', 'product_name', 'price'],
        'inventory': ['product_id', 'quantity']
    }
    
    for req in required_cols.get(data_type, []):
        if req not in mappings:
            score -= 10
    
    # Deduct for null values
    avg_null_pct = df.isna().sum().sum() / (len(df) * len(df.columns)) * 100
    score -= min(avg_null_pct, 30)
    
    # Deduct for duplicates
    dup_pct = df.duplicated().sum() / len(df) * 100
    score -= min(dup_pct, 20)
    
    return max(0, min(100, score))


def render_data_manager():
    """Render data manager page"""
    st.markdown("""
    <div class="section-header">
        <h1 style="margin:0;color:#1e293b;">📁 Data Manager</h1>
        <p style="margin:0.5rem 0 0;color:#64748b;">View, manage, and add more data to your datasets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # First show currently loaded data
    st.markdown("### 📊 Your Connected Datasets")
    
    available_data = {k: v for k, v in st.session_state.data_store.items() if len(v) > 0}
    
    if available_data:
        # Dataset labels
        dataset_labels = {
            'orders': '📦 Orders',
            'order_items': '🧾 Order Items',
            'customers': '👥 Customers',
            'products': '🛍️ Products',
            'inventory': '📊 Inventory',
            'returns': '↩️ Returns',
            'reviews': '⭐ Reviews',
            'website_traffic': '🌐 Website Traffic',
            'ads_meta': '📘 Meta Ads',
            'ads_google': '🔍 Google Ads',
            'ads_shopify': '🛒 Shopify Ads'
        }
        
        cols = st.columns(3)
        for idx, (key, df) in enumerate(available_data.items()):
            with cols[idx % 3]:
                label = dataset_labels.get(key, key.replace('_', ' ').title())
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:1rem;border:1px solid #e2e8f0;margin-bottom:1rem;">
                    <p style="margin:0;font-size:0.875rem;color:#64748b;">{label}</p>
                    <p style="margin:0.25rem 0 0;font-size:1.5rem;font-weight:700;color:#1e293b;">{len(df):,}</p>
                    <p style="margin:0;font-size:0.75rem;color:#94a3b8;">records</p>
                </div>
                """, unsafe_allow_html=True)
        
        # View and manage data
        st.markdown("---")
        st.markdown("### 🔍 View & Manage Data")
        
        selected_dataset = st.selectbox(
            "Select dataset to view",
            list(available_data.keys()),
            format_func=lambda x: dataset_labels.get(x, x.replace('_', ' ').title())
        )
        
        if selected_dataset:
            df = st.session_state.data_store[selected_dataset]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rows", f"{len(df):,}")
            with col2:
                st.metric("Columns", f"{len(df.columns)}")
            with col3:
                st.metric("Null Values", f"{df.isna().sum().sum():,}")
            with col4:
                if st.button("🗑️ Clear Dataset", key=f"clear_{selected_dataset}"):
                    st.session_state.data_store[selected_dataset] = pd.DataFrame()
                    st.success(f"Cleared {selected_dataset}")
                    st.rerun()
            
            # Show data preview
            st.dataframe(df.head(100), use_container_width=True, hide_index=True)
            
            # Column mappings - EDITABLE
            st.markdown("#### 🔗 Column Mapping")
            st.caption("⚠️ **Important:** Correct column mapping ensures accurate AI analytics. Edit if needed.")
            
            mappings = st.session_state.column_mappings.get(selected_dataset, {})
            col_options = ['(Not Mapped)'] + list(df.columns)
            
            if selected_dataset == 'orders':
                mapping_fields = [
                    ('product_name', 'Product/Item Name', 'Which column has product names?'),
                    ('customer_name', 'Customer Name', 'Which column has customer names?'),
                    ('total_amount', 'Order Amount/Total', 'Which column has order totals?'),
                    ('order_date', 'Order Date', 'Which column has order dates?'),
                    ('order_status', 'Order Status', 'Which column has delivery/order status?'),
                    ('city', 'City/Location', 'Which column has city information?'),
                    ('payment_method', 'Payment Method', 'Which column has payment info?'),
                ]
                
                map_cols = st.columns(3)
                updated_mappings = {}
                
                for idx, (field, label, help_text) in enumerate(mapping_fields):
                    with map_cols[idx % 3]:
                        current_val = mappings.get(field, '(Not Mapped)')
                        if current_val not in col_options:
                            current_val = '(Not Mapped)'
                        
                        selected = st.selectbox(
                            label,
                            col_options,
                            index=col_options.index(current_val) if current_val in col_options else 0,
                            key=f"map_{selected_dataset}_{field}",
                            help=help_text
                        )
                        if selected != '(Not Mapped)':
                            updated_mappings[field] = selected
                
                if st.button("💾 Save Column Mappings", type="primary"):
                    st.session_state.column_mappings[selected_dataset] = updated_mappings
                    st.success("✅ Column mappings saved! AI analytics will now use these columns correctly.")
                    st.rerun()
            else:
                # Show existing mappings for other data types
                if mappings:
                    with st.expander("📋 Current Column Mappings"):
                        for standard, actual in mappings.items():
                            st.text(f"{standard} → {actual}")
    else:
        st.info("📁 No data loaded yet. Upload data below or go back to the onboarding to connect your data.")
    
    st.markdown("---")
    
    # Tabs for adding more data and cleaning
    tab1, tab2, tab3 = st.tabs(["➕ Add More Data", "🧹 Clean & Preprocess", "✅ Validate Data"])
    
    with tab1:
        st.subheader("Upload Additional Data")
        st.caption("Add more data files to your existing datasets")
        
        uploaded_files = st.file_uploader(
            "Drop CSV or Excel files here",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Upload one or more files. Data type will be auto-detected."
        )
        
        if uploaded_files:
            for file in uploaded_files:
                with st.expander(f"📄 {file.name}", expanded=True):
                    try:
                        file.seek(0)
                        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
                        st.info(f"📊 {len(df):,} rows × {len(df.columns)} columns")
                        
                        # Auto-detect type
                        detected_type, confidence = detect_data_type(df)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            data_types = [
                                'orders', 'order_items', 'customers', 'products', 'inventory',
                                'returns', 'reviews', 'website_traffic',
                                'ads_meta', 'ads_google', 'ads_shopify'
                            ]
                            data_type_labels = {
                                'orders': '📦 Orders',
                                'order_items': '🧾 Order Items',
                                'customers': '👥 Customers',
                                'products': '🛍️ Products',
                                'inventory': '📊 Inventory',
                                'returns': '↩️ Returns',
                                'reviews': '⭐ Reviews',
                                'website_traffic': '🌐 Website Traffic',
                                'ads_meta': '📘 Meta Ads',
                                'ads_google': '🔍 Google Ads',
                                'ads_shopify': '🛒 Shopify Ads'
                            }
                            data_type = st.selectbox(
                                "Data Type",
                                data_types,
                                format_func=lambda x: data_type_labels.get(x, x),
                                index=data_types.index(detected_type) if detected_type in data_types else 0,
                                key=f"type_{file.name}"
                            )
                        with col2:
                            st.metric("Detection Confidence", f"{confidence*100:.0f}%")
                        
                        # Show column mappings
                        mappings = auto_map_columns(df, data_type)
                        if mappings:
                            st.write("**Auto-mapped columns:**")
                            mapping_text = " | ".join([f"`{k}` → {v}" for k, v in mappings.items()])
                            st.caption(mapping_text)
                        
                        # Preview
                        st.dataframe(df.head(5), use_container_width=True, hide_index=True)
                        
                        # Import options
                        col1, col2 = st.columns(2)
                        with col1:
                            clean_on_import = st.checkbox("Clean data on import", value=True, key=f"clean_{file.name}")
                        with col2:
                            merge_existing = st.checkbox("Merge with existing", value=True, key=f"merge_{file.name}")
                        
                        if st.button(f"📥 Import as {data_type.replace('_', ' ').title()}", key=f"import_{file.name}", type="primary"):
                            # Clean if requested
                            if clean_on_import:
                                df, report = clean_dataframe(df, data_type)
                                if report:
                                    st.success("Cleaned: " + ", ".join(report))
                            
                            # Store mappings
                            st.session_state.column_mappings[data_type] = mappings
                            
                            # Merge or replace
                            existing = st.session_state.data_store[data_type]
                            if merge_existing and len(existing) > 0:
                                # Find ID column for deduplication
                                id_col = mappings.get(f'{data_type[:-1]}_id') or mappings.get('order_id') or mappings.get('product_id') or mappings.get('customer_id')
                                
                                df = pd.concat([existing, df], ignore_index=True)
                                if id_col and id_col in df.columns:
                                    df = df.drop_duplicates(subset=[id_col], keep='last')
                                else:
                                    df = df.drop_duplicates()
                                
                                st.success(f"✅ Merged! Total: {len(df):,} {data_type}")
                            else:
                                st.success(f"✅ Imported {len(df):,} {data_type}")
                            
                            st.session_state.data_store[data_type] = df
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("🧹 Data Cleaning & Preprocessing")
        
        # Select data to clean
        available_data = {k: v for k, v in st.session_state.data_store.items() if len(v) > 0}
        
        if not available_data:
            st.info("Upload data first to use cleaning features")
        else:
            data_type = st.selectbox("Select dataset", list(available_data.keys()), key="clean_select")
            df = st.session_state.data_store[data_type].copy()
            
            st.write(f"**Current size:** {len(df):,} rows × {len(df.columns)} columns")
            
            # Data quality score
            quality_score = get_data_quality_score(df, data_type)
            col1, col2, col3 = st.columns(3)
            with col1:
                color = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"
                st.metric("Quality Score", f"{color} {quality_score:.0f}/100")
            with col2:
                st.metric("Null Values", f"{df.isna().sum().sum():,}")
            with col3:
                st.metric("Duplicates", f"{df.duplicated().sum():,}")
            
            st.divider()
            
            # Cleaning options
            st.subheader("Cleaning Operations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Remove:**")
                remove_empty = st.checkbox("Empty rows", value=True)
                remove_duplicates = st.checkbox("Duplicate rows", value=True)
                remove_nulls = st.checkbox("Rows with >50% nulls", value=False)
            
            with col2:
                st.write("**Transform:**")
                standardize_text = st.checkbox("Standardize text (trim, title case)", value=True)
                fix_dates = st.checkbox("Fix date formats", value=True)
                fix_numbers = st.checkbox("Clean numeric columns", value=True)
            
            # Column-specific cleaning
            st.subheader("Column Operations")
            
            col_to_drop = st.multiselect("Drop columns", df.columns.tolist())
            
            col_to_fill = st.selectbox("Fill missing values in", ["None"] + df.columns.tolist())
            if col_to_fill != "None":
                fill_method = st.selectbox("Fill method", ["Mean", "Median", "Mode", "Custom value"])
                if fill_method == "Custom value":
                    fill_value = st.text_input("Custom fill value")
            
            if st.button("🧹 Apply Cleaning", type="primary"):
                report = []
                
                # Apply cleaning operations
                if remove_empty:
                    before = len(df)
                    df = df.dropna(how='all')
                    if len(df) < before:
                        report.append(f"Removed {before - len(df)} empty rows")
                
                if remove_duplicates:
                    before = len(df)
                    df = df.drop_duplicates()
                    if len(df) < before:
                        report.append(f"Removed {before - len(df)} duplicates")
                
                if remove_nulls:
                    before = len(df)
                    null_threshold = len(df.columns) * 0.5
                    df = df[df.isna().sum(axis=1) < null_threshold]
                    if len(df) < before:
                        report.append(f"Removed {before - len(df)} rows with >50% nulls")
                
                if standardize_text:
                    for col in df.select_dtypes(include=['object']).columns:
                        df[col] = df[col].astype(str).str.strip()
                    report.append("Standardized text columns")
                
                if fix_dates:
                    for col in df.columns:
                        if any(kw in col.lower() for kw in ['date', 'created', 'updated']):
                            try:
                                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                                report.append(f"Fixed dates in {col}")
                            except:
                                pass
                
                if fix_numbers:
                    for col in df.columns:
                        if any(kw in col.lower() for kw in ['amount', 'price', 'total', 'cost', 'quantity']):
                            df[col] = pd.to_numeric(
                                df[col].astype(str).str.replace(r'[₹$,\s]', '', regex=True),
                                errors='coerce'
                            )
                            report.append(f"Cleaned numbers in {col}")
                
                if col_to_drop:
                    df = df.drop(columns=col_to_drop)
                    report.append(f"Dropped columns: {', '.join(col_to_drop)}")
                
                if col_to_fill != "None":
                    if fill_method == "Mean":
                        df[col_to_fill] = df[col_to_fill].fillna(df[col_to_fill].mean())
                    elif fill_method == "Median":
                        df[col_to_fill] = df[col_to_fill].fillna(df[col_to_fill].median())
                    elif fill_method == "Mode":
                        df[col_to_fill] = df[col_to_fill].fillna(df[col_to_fill].mode().iloc[0] if len(df[col_to_fill].mode()) > 0 else None)
                    elif fill_method == "Custom value":
                        df[col_to_fill] = df[col_to_fill].fillna(fill_value)
                    report.append(f"Filled nulls in {col_to_fill}")
                
                # Save cleaned data
                st.session_state.data_store[data_type] = df
                
                # Show report
                st.success("✅ Cleaning complete!")
                for item in report:
                    st.write(f"• {item}")
                
                new_score = get_data_quality_score(df, data_type)
                st.metric("New Quality Score", f"{new_score:.0f}/100", delta=f"+{new_score - quality_score:.0f}")
                st.rerun()
    
    with tab3:
        st.subheader("✅ Data Validation")
        
        available_data = {k: v for k, v in st.session_state.data_store.items() if len(v) > 0}
        
        if not available_data:
            st.info("Upload data first to validate")
        else:
            for dtype, df in available_data.items():
                with st.expander(f"📊 {dtype.title()} Validation", expanded=True):
                    issues, warnings = validate_data(df, dtype)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        quality_score = get_data_quality_score(df, dtype)
                        color = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"
                        st.metric("Quality", f"{color} {quality_score:.0f}%")
                    with col2:
                        st.metric("Issues", len(issues))
                    with col3:
                        st.metric("Warnings", len(warnings))
                    
                    if issues:
                        st.error("**Issues (must fix):**")
                        for issue in issues:
                            st.write(f"❌ {issue}")
                    
                    if warnings:
                        st.warning("**Warnings:**")
                        for warn in warnings:
                            st.write(f"⚠️ {warn}")
                    
                    if not issues and not warnings:
                        st.success("✅ No issues found!")
                    
                    # Show data profile
                    st.write("**Data Profile:**")
                    profile = pd.DataFrame({
                        'Column': df.columns,
                        'Type': df.dtypes.astype(str),
                        'Non-Null': df.count().values,
                        'Null %': (df.isna().sum() / len(df) * 100).round(1).values,
                        'Unique': df.nunique().values
                    })
                    st.dataframe(profile, use_container_width=True, hide_index=True)

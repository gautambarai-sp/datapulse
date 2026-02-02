"""Enhanced Dashboard with beautiful UI and color scheme"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np


def format_inr(value):
    """Format number as INR"""
    if pd.isna(value) or value == 0:
        return "₹0"
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    return f"₹{value:,.0f}"


def auto_detect_columns(df):
    """Auto-detect column mappings based on column names"""
    mappings = {}
    col_patterns = {
        'order_id': ['order_id', 'order id', 'orderid', 'id', 'order_number', 'order no'],
        'order_date': ['order_date', 'date', 'created_at', 'order date', 'created', 'purchase_date', 'transaction_date'],
        'customer_id': ['customer_id', 'customer id', 'cust_id', 'user_id'],
        'customer_name': ['customer_name', 'customer', 'name', 'buyer', 'client'],
        'product_name': ['product_name', 'product', 'item', 'item_name', 'sku_name', 'lineitem_name'],
        'category': ['category', 'product_category', 'type', 'product_type'],
        'quantity': ['quantity', 'qty', 'units', 'count', 'lineitem_quantity'],
        'total_amount': ['total_amount', 'amount', 'total', 'price', 'revenue', 'order_value', 'grand_total', 'subtotal', 'total_price'],
        'payment_method': ['payment_method', 'payment', 'payment_type', 'pay_method', 'payment_mode', 'gateway'],
        'order_status': ['order_status', 'status', 'delivery_status', 'fulfillment_status', 'state', 'financial_status'],
        'city': ['city', 'customer_city', 'shipping_city', 'delivery_city', 'location', 'billing_city'],
        'state': ['state', 'region', 'province', 'customer_state', 'billing_province']
    }
    
    for standard, variations in col_patterns.items():
        for col in df.columns:
            col_lower = col.lower().replace('_', ' ').replace('-', ' ').strip()
            for var in variations:
                if var.replace('_', ' ') in col_lower or col_lower in var.replace('_', ' '):
                    mappings[standard] = col
                    break
            if standard in mappings:
                break
    
    return mappings


COLORS = {
    'primary': '#6366f1',
    'secondary': '#8b5cf6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'chart': ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#3b82f6', '#ec4899', '#14b8a6', '#f97316']
}


def render_dashboard():
    """Main dashboard render function"""
    has_data = any(len(st.session_state.data_store.get(k, pd.DataFrame())) > 0 
                   for k in st.session_state.data_store.keys())
    
    if not has_data:
        render_empty_state()
        return
    
    st.markdown("""
    <div class="section-header">
        <h1 style="margin:0;color:#1e293b;">📊 Analytics Dashboard</h1>
        <p style="margin:0.5rem 0 0;color:#64748b;">Real-time insights into your business performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    orders = st.session_state.data_store.get('orders', pd.DataFrame())
    mappings = st.session_state.column_mappings.get('orders', {})
    
    if len(orders) == 0:
        st.info("📁 No orders data loaded.")
        return
    
    # Auto-detect columns if not mapped
    if not mappings:
        mappings = auto_detect_columns(orders)
        st.session_state.column_mappings['orders'] = mappings
    
    # Date filter
    date_col = mappings.get('order_date')
    if date_col and date_col in orders.columns:
        orders[date_col] = pd.to_datetime(orders[date_col], errors='coerce')
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        with col1:
            date_range = st.selectbox("📅 Time Period", 
                ["Last 7 days", "Last 30 days", "Last 90 days", "This Month", "All Time"], 
                index=4, key="dashboard_time_filter")
        
        # Apply date filter
        today = pd.Timestamp.now().normalize()  # Use normalized timestamp (midnight)
        filtered_orders = orders.copy()
        
        # Remove NaT values for filtering
        valid_dates = filtered_orders[date_col].notna()
        
        if date_range == "Last 7 days":
            start_date = today - timedelta(days=7)
            filtered_orders = filtered_orders[valid_dates & (filtered_orders[date_col] >= start_date)]
        elif date_range == "Last 30 days":
            start_date = today - timedelta(days=30)
            filtered_orders = filtered_orders[valid_dates & (filtered_orders[date_col] >= start_date)]
        elif date_range == "Last 90 days":
            start_date = today - timedelta(days=90)
            filtered_orders = filtered_orders[valid_dates & (filtered_orders[date_col] >= start_date)]
        elif date_range == "This Month":
            filtered_orders = filtered_orders[valid_dates & 
                                              (filtered_orders[date_col].dt.month == today.month) & 
                                              (filtered_orders[date_col].dt.year == today.year)]
        # "All Time" - no filtering needed
        
        orders = filtered_orders
        
        # Show filter info
        with col4:
            if date_range != "All Time" and len(orders) > 0:
                min_date = orders[date_col].min().strftime('%d %b %Y') if pd.notna(orders[date_col].min()) else "N/A"
                max_date = orders[date_col].max().strftime('%d %b %Y') if pd.notna(orders[date_col].max()) else "N/A"
                st.caption(f"📆 Showing: {min_date} to {max_date} ({len(orders):,} orders)")
            elif date_range == "All Time":
                st.caption(f"📆 Showing all {len(orders):,} orders")
    
    amount_col = mappings.get('total_amount')
    status_col = mappings.get('order_status')
    qty_col = mappings.get('quantity')
    
    if status_col and status_col in orders.columns:
        orders['_status'] = orders[status_col].astype(str).str.lower()
        delivered = orders[orders['_status'].str.contains('deliver|complete|success', na=False)]
        rto = orders[orders['_status'].str.contains('rto|return', na=False)]
    else:
        delivered = orders
        rto = pd.DataFrame()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        revenue = delivered[amount_col].sum() if amount_col and amount_col in orders.columns and len(delivered) > 0 else 0
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px;padding:1.5rem;color:white;">
            <p style="margin:0;font-size:0.875rem;opacity:0.9;">💰 Revenue</p>
            <p style="margin:0.5rem 0 0;font-size:1.75rem;font-weight:700;font-family:'Space Grotesk',sans-serif;">{format_inr(revenue)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#3b82f6,#0ea5e9);border-radius:16px;padding:1.5rem;color:white;">
            <p style="margin:0;font-size:0.875rem;opacity:0.9;">📦 Orders</p>
            <p style="margin:0.5rem 0 0;font-size:1.75rem;font-weight:700;font-family:'Space Grotesk',sans-serif;">{len(orders):,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        aov = delivered[amount_col].mean() if amount_col and amount_col in orders.columns and len(delivered) > 0 else 0
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#10b981,#14b8a6);border-radius:16px;padding:1.5rem;color:white;">
            <p style="margin:0;font-size:0.875rem;opacity:0.9;">💵 AOV</p>
            <p style="margin:0.5rem 0 0;font-size:1.75rem;font-weight:700;font-family:'Space Grotesk',sans-serif;">{format_inr(aov)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        rto_base = len(delivered) + len(rto)
        rto_rate = len(rto) / rto_base * 100 if rto_base > 0 else 0
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#f59e0b,#f97316);border-radius:16px;padding:1.5rem;color:white;">
            <p style="margin:0;font-size:0.875rem;opacity:0.9;">🔄 RTO Rate</p>
            <p style="margin:0.5rem 0 0;font-size:1.75rem;font-weight:700;font-family:'Space Grotesk',sans-serif;">{rto_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        units = orders[qty_col].sum() if qty_col and qty_col in orders.columns else len(orders)
        st.markdown(f"""
        <div style="background:#f8fafc;border-radius:16px;padding:1.5rem;border:2px solid #e2e8f0;">
            <p style="margin:0;font-size:0.875rem;color:#64748b;">📊 Units Sold</p>
            <p style="margin:0.5rem 0 0;font-size:1.75rem;font-weight:700;color:#1e293b;font-family:'Space Grotesk',sans-serif;">{units:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Revenue Trend")
        if date_col and date_col in orders.columns and amount_col and amount_col in orders.columns:
            daily = orders.groupby(orders[date_col].dt.date)[amount_col].sum().reset_index()
            daily.columns = ['Date', 'Revenue']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily['Date'], y=daily['Revenue'], mode='lines+markers',
                line=dict(color=COLORS['primary'], width=3), marker=dict(size=6),
                fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
            ))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0),
                            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                            plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Date and amount columns needed")
    
    with col2:
        st.markdown("### 📊 Order Status")
        if status_col and status_col in orders.columns:
            status_counts = orders[status_col].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(status_counts, values='Count', names='Status',
                        color_discrete_sequence=COLORS['chart'], hole=0.4)
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0),
                            legend=dict(orientation='h', yanchor='bottom', y=-0.2))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Status column needed")
    
    col1, col2 = st.columns(2)
    product_col = mappings.get('product_name')
    payment_col = mappings.get('payment_method')
    
    with col1:
        st.markdown("### 🏆 Top Products")
        if product_col and product_col in orders.columns:
            if amount_col and amount_col in orders.columns:
                top_products = orders.groupby(product_col)[amount_col].sum().nlargest(8).reset_index()
                top_products.columns = ['Product', 'Revenue']
                y_col = 'Revenue'
            else:
                top_products = orders[product_col].value_counts().head(8).reset_index()
                top_products.columns = ['Product', 'Count']
                y_col = 'Count'
            
            fig = px.bar(top_products, x=y_col, y='Product', orientation='h',
                        color_discrete_sequence=[COLORS['secondary']])
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0),
                            xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                            yaxis=dict(showgrid=False), plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Product column needed")
    
    with col2:
        st.markdown("### 💳 Payment Methods")
        if payment_col and payment_col in orders.columns:
            pay_counts = orders[payment_col].value_counts().reset_index()
            pay_counts.columns = ['Method', 'Count']
            
            fig = px.bar(pay_counts, x='Method', y='Count', color='Method',
                        color_discrete_sequence=COLORS['chart'])
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0),
                            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                            plot_bgcolor='white', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Payment method column needed")
    
    # Geographic
    city_col = mappings.get('city')
    if city_col and city_col in orders.columns:
        st.markdown("### 🗺️ Geographic Distribution")
        city_data = orders[city_col].value_counts().head(10).reset_index()
        city_data.columns = ['City', 'Orders']
        
        fig = px.bar(city_data, x='City', y='Orders', color_discrete_sequence=[COLORS['info']])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    
    # Ads Summary
    ads_meta = st.session_state.data_store.get('ads_meta', pd.DataFrame())
    if len(ads_meta) > 0:
        st.markdown("---")
        st.markdown("### 📢 Ads Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        spend = ads_meta['spend'].sum() if 'spend' in ads_meta.columns else 0
        impressions = ads_meta['impressions'].sum() if 'impressions' in ads_meta.columns else 0
        clicks = ads_meta['clicks'].sum() if 'clicks' in ads_meta.columns else 0
        conversions = ads_meta['conversions'].sum() if 'conversions' in ads_meta.columns else 0
        ad_revenue = ads_meta['revenue'].sum() if 'revenue' in ads_meta.columns else 0
        
        with col1:
            st.metric("💸 Ad Spend", format_inr(spend))
        with col2:
            ctr = clicks / impressions * 100 if impressions > 0 else 0
            st.metric("🖱️ CTR", f"{ctr:.2f}%")
        with col3:
            st.metric("🎯 Conversions", f"{conversions:,.0f}")
        with col4:
            roas = ad_revenue / spend if spend > 0 else 0
            st.metric("📈 ROAS", f"{roas:.2f}x")


def render_empty_state():
    """Render empty state"""
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;">
        <p style="font-size:4rem;margin-bottom:1rem;">📊</p>
        <h2 style="color:#1e293b;margin-bottom:1rem;">Welcome to Your Dashboard</h2>
        <p style="color:#64748b;max-width:500px;margin:0 auto 2rem;">
            Upload your e-commerce data to see powerful analytics and insights.
        </p>
    </div>
    """, unsafe_allow_html=True)

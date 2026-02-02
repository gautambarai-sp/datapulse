"""Main dashboard page - Self-contained with all visualizations"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def format_inr(value):
    """Format number as Indian Rupees"""
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    elif value >= 1000:
        return f"₹{value/1000:.1f}K"
    return f"₹{value:,.0f}"


def normalize_status(status):
    """Normalize order status"""
    if pd.isna(status):
        return "unknown"
    s = str(status).lower().strip()
    if any(x in s for x in ["deliver", "complete", "success"]):
        return "delivered"
    elif any(x in s for x in ["rto", "return"]):
        return "rto"
    elif any(x in s for x in ["cancel"]):
        return "cancelled"
    elif any(x in s for x in ["ship", "transit"]):
        return "shipped"
    elif any(x in s for x in ["process", "pending", "confirm"]):
        return "processing"
    return "other"


def normalize_payment(payment):
    """Normalize payment method"""
    if pd.isna(payment):
        return "Other"
    p = str(payment).lower().strip()
    if "cod" in p or "cash" in p:
        return "COD"
    elif "upi" in p:
        return "UPI"
    elif "card" in p or "credit" in p or "debit" in p:
        return "Card"
    elif "net" in p or "bank" in p:
        return "Net Banking"
    elif "prepaid" in p or "wallet" in p:
        return "Prepaid"
    return "Other"


def render_dashboard():
    st.header("📊 Analytics Dashboard")
    
    # Check for data
    if not st.session_state.datasets or not st.session_state.active_dataset:
        st.info("📁 No data loaded. Go to **Data Manager** to upload your data.")
        return
    
    dataset = st.session_state.datasets.get(st.session_state.active_dataset)
    if not dataset:
        st.warning("Dataset not found")
        return
    
    df = dataset['df'].copy()
    mappings = dataset['mappings']
    
    # Get column names from mappings
    amount_col = mappings.get('total_amount')
    status_col = mappings.get('order_status')
    date_col = mappings.get('order_date')
    payment_col = mappings.get('payment_method')
    product_col = mappings.get('product_name')
    
    # Normalize status
    if status_col and status_col in df.columns:
        df['_status'] = df[status_col].apply(normalize_status)
    else:
        df['_status'] = 'unknown'
    
    # Normalize payment
    if payment_col and payment_col in df.columns:
        df['_payment'] = df[payment_col].apply(normalize_payment)
    else:
        df['_payment'] = 'Unknown'
    
    # Calculate metrics
    total_orders = len(df)
    delivered = df[df['_status'] == 'delivered']
    rto = df[df['_status'] == 'rto']
    
    if amount_col and amount_col in df.columns:
        total_revenue = delivered[amount_col].sum()
        aov = delivered[amount_col].mean() if len(delivered) > 0 else 0
    else:
        total_revenue = 0
        aov = 0
    
    rto_base = len(delivered) + len(rto)
    rto_rate = (len(rto) / rto_base * 100) if rto_base > 0 else 0
    
    # ============ KEY METRICS ============
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Total Revenue", format_inr(total_revenue), help="Revenue from delivered orders only")
    col2.metric("🛒 AOV", format_inr(aov), help="Average Order Value (delivered)")
    col3.metric("📦 Total Orders", f"{total_orders:,}")
    col4.metric("✅ Delivered", f"{len(delivered):,}")
    col5.metric("🔄 RTO Rate", f"{rto_rate:.1f}%", help="RTO / (Delivered + RTO)")
    
    st.divider()
    
    # ============ ROW 1: Revenue Trend + Order Status ============
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Revenue Trend")
        if date_col and date_col in df.columns and amount_col:
            try:
                df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
                delivered_with_date = delivered[delivered[date_col].notna()].copy()
                delivered_with_date['_date'] = pd.to_datetime(delivered_with_date[date_col], errors='coerce')
                
                trend = delivered_with_date.groupby(delivered_with_date['_date'].dt.date)[amount_col].sum().reset_index()
                trend.columns = ['Date', 'Revenue']
                
                fig = px.area(trend, x='Date', y='Revenue', 
                             color_discrete_sequence=['#6366f1'])
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
                fig.update_traces(fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.2)')
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("📅 Could not parse dates")
        else:
            st.info("📅 Date column not mapped")
    
    with col2:
        st.subheader("🥧 Orders by Status")
        status_counts = df['_status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        colors = {'delivered': '#22c55e', 'rto': '#ef4444', 'cancelled': '#f97316', 
                  'shipped': '#3b82f6', 'processing': '#eab308', 'other': '#94a3b8'}
        status_counts['Color'] = status_counts['Status'].map(colors).fillna('#94a3b8')
        
        fig = px.pie(status_counts, values='Count', names='Status',
                    color='Status', color_discrete_map=colors,
                    hole=0.4)
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # ============ ROW 2: Payment Methods + COD vs Prepaid ============
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Revenue by Payment Method")
        if amount_col:
            payment_rev = delivered.groupby('_payment')[amount_col].agg(['sum', 'count']).reset_index()
            payment_rev.columns = ['Payment', 'Revenue', 'Orders']
            payment_rev = payment_rev.sort_values('Revenue', ascending=True)
            
            fig = px.bar(payment_rev, y='Payment', x='Revenue', orientation='h',
                        color='Revenue', color_continuous_scale='Blues',
                        text=payment_rev['Revenue'].apply(format_inr))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            fig.update_traces(textposition='outside')
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Amount column not mapped")
    
    with col2:
        st.subheader("💰 COD vs Prepaid Analysis")
        # COD = COD, Prepaid = everything else
        df['_is_cod'] = df['_payment'] == 'COD'
        
        cod_delivered = delivered[delivered['_is_cod']]
        prepaid_delivered = delivered[~delivered['_is_cod']]
        cod_rto = rto[rto['_is_cod']]
        prepaid_rto = rto[~rto['_is_cod']]
        
        if amount_col:
            cod_rev = cod_delivered[amount_col].sum()
            prepaid_rev = prepaid_delivered[amount_col].sum()
            
            cod_rto_base = len(cod_delivered) + len(cod_rto)
            prepaid_rto_base = len(prepaid_delivered) + len(prepaid_rto)
            
            cod_rto_rate = (len(cod_rto) / cod_rto_base * 100) if cod_rto_base > 0 else 0
            prepaid_rto_rate = (len(prepaid_rto) / prepaid_rto_base * 100) if prepaid_rto_base > 0 else 0
            
            # Comparison chart
            fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "xy"}]],
                               subplot_titles=("Revenue Split", "RTO Rate Comparison"))
            
            fig.add_trace(go.Pie(labels=['COD', 'Prepaid'], values=[cod_rev, prepaid_rev],
                                marker_colors=['#f97316', '#22c55e'], hole=0.5), row=1, col=1)
            
            fig.add_trace(go.Bar(x=['COD', 'Prepaid'], y=[cod_rto_rate, prepaid_rto_rate],
                                marker_color=['#f97316', '#22c55e'],
                                text=[f'{cod_rto_rate:.1f}%', f'{prepaid_rto_rate:.1f}%'],
                                textposition='outside'), row=1, col=2)
            
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Insight
            if cod_rto_rate > prepaid_rto_rate:
                st.warning(f"⚠️ COD has {cod_rto_rate - prepaid_rto_rate:.1f}% higher RTO rate than Prepaid")
        else:
            st.info("Amount column not mapped")
    
    st.divider()
    
    # ============ ROW 3: Top Products + Category Breakdown ============
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Products by Revenue")
        if product_col and product_col in df.columns and amount_col:
            top_products = delivered.groupby(product_col)[amount_col].sum().nlargest(10).reset_index()
            top_products.columns = ['Product', 'Revenue']
            top_products = top_products.sort_values('Revenue', ascending=True)
            
            fig = px.bar(top_products, y='Product', x='Revenue', orientation='h',
                        color='Revenue', color_continuous_scale='Greens',
                        text=top_products['Revenue'].apply(format_inr))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_traces(textposition='outside')
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Product column not mapped")
    
    with col2:
        st.subheader("📊 Orders Over Time")
        if date_col and date_col in df.columns:
            try:
                df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
                daily_orders = df.groupby([df['_date'].dt.date, '_status']).size().reset_index()
                daily_orders.columns = ['Date', 'Status', 'Orders']
                
                fig = px.bar(daily_orders, x='Date', y='Orders', color='Status',
                            color_discrete_map={'delivered': '#22c55e', 'rto': '#ef4444', 
                                               'cancelled': '#f97316', 'shipped': '#3b82f6',
                                               'processing': '#eab308', 'other': '#94a3b8'})
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), barmode='stack')
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("📅 Could not parse dates")
        else:
            st.info("📅 Date column not mapped")
    
    # ============ ROW 4: Geographic + Heatmap ============
    if 'city' in [c.lower() for c in df.columns]:
        city_col = [c for c in df.columns if c.lower() == 'city'][0]
        
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗺️ Top Cities by Orders")
            city_orders = df.groupby(city_col).size().nlargest(10).reset_index()
            city_orders.columns = ['City', 'Orders']
            city_orders = city_orders.sort_values('Orders', ascending=True)
            
            fig = px.bar(city_orders, y='City', x='Orders', orientation='h',
                        color='Orders', color_continuous_scale='Purples')
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📍 City-wise RTO Rate")
            city_stats = df.groupby(city_col).apply(
                lambda x: pd.Series({
                    'Total': len(x),
                    'Delivered': len(x[x['_status'] == 'delivered']),
                    'RTO': len(x[x['_status'] == 'rto'])
                })
            ).reset_index()
            city_stats['Base'] = city_stats['Delivered'] + city_stats['RTO']
            city_stats['RTO Rate'] = (city_stats['RTO'] / city_stats['Base'] * 100).fillna(0)
            city_stats = city_stats[city_stats['Base'] >= 3].nlargest(10, 'Total')
            city_stats = city_stats.sort_values('RTO Rate', ascending=True)
            
            fig = px.bar(city_stats, y=city_col, x='RTO Rate', orientation='h',
                        color='RTO Rate', color_continuous_scale='Reds',
                        text=city_stats['RTO Rate'].apply(lambda x: f'{x:.1f}%'))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_traces(textposition='outside')
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # ============ DATA TABLE ============
    st.divider()
    st.subheader("📋 Recent Orders")
    display_cols = [c for c in [mappings.get('order_id'), mappings.get('order_date'), 
                                mappings.get('total_amount'), mappings.get('order_status'),
                                mappings.get('payment_method'), mappings.get('product_name')] 
                   if c and c in df.columns]
    if display_cols:
        st.dataframe(df[display_cols].head(20), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

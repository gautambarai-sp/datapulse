"""Reports Page with Export Options"""

import streamlit as st
import pandas as pd
from datetime import datetime


def format_inr(value):
    if pd.isna(value) or value == 0:
        return "₹0"
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    return f"₹{value:,.0f}"


def render_reports():
    """Render reports page"""
    st.markdown("""
    <div class="section-header">
        <h1 style="margin:0;color:#1e293b;">📈 Reports</h1>
        <p style="margin:0.5rem 0 0;color:#64748b;">Generate and export detailed business reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    orders = st.session_state.data_store.get('orders', pd.DataFrame())
    
    if len(orders) == 0:
        st.info("📁 No data available. Upload data to generate reports.")
        return
    
    # Report types
    report_type = st.selectbox("📋 Select Report Type", [
        "Sales Summary Report",
        "Product Performance Report",
        "Customer Analysis Report",
        "Payment Methods Report",
        "Geographic Report",
        "Ads Performance Report"
    ])
    
    st.markdown("---")
    
    mappings = st.session_state.column_mappings.get('orders', {})
    
    if report_type == "Sales Summary Report":
        st.markdown("### 📊 Sales Summary")
        
        amount_col = mappings.get('total_amount')
        status_col = mappings.get('order_status')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Orders", f"{len(orders):,}")
        with col2:
            if amount_col and amount_col in orders.columns:
                st.metric("Total Revenue", format_inr(orders[amount_col].sum()))
        with col3:
            if amount_col and amount_col in orders.columns:
                st.metric("Avg Order Value", format_inr(orders[amount_col].mean()))
        
        st.markdown("#### Order Details")
        st.dataframe(orders.head(100), use_container_width=True, hide_index=True)
    
    elif report_type == "Product Performance Report":
        st.markdown("### 🏆 Product Performance")
        
        product_col = mappings.get('product_name')
        amount_col = mappings.get('total_amount')
        qty_col = mappings.get('quantity')
        
        if product_col and product_col in orders.columns:
            agg_dict = {orders.columns[0]: 'count'}
            if amount_col and amount_col in orders.columns:
                agg_dict[amount_col] = 'sum'
            if qty_col and qty_col in orders.columns:
                agg_dict[qty_col] = 'sum'
            
            product_stats = orders.groupby(product_col).agg(agg_dict).reset_index()
            product_stats.columns = [product_col, 'Orders'] + (['Revenue'] if amount_col else []) + (['Units'] if qty_col else [])
            product_stats = product_stats.sort_values('Orders', ascending=False)
            
            st.dataframe(product_stats, use_container_width=True, hide_index=True)
        else:
            st.info("Product column not mapped")
    
    elif report_type == "Customer Analysis Report":
        st.markdown("### 👥 Customer Analysis")
        
        customer_col = mappings.get('customer_id')
        amount_col = mappings.get('total_amount')
        
        if customer_col and customer_col in orders.columns:
            agg_dict = {orders.columns[0]: 'count'}
            if amount_col and amount_col in orders.columns:
                agg_dict[amount_col] = 'sum'
            
            customer_stats = orders.groupby(customer_col).agg(agg_dict).reset_index()
            col_names = [customer_col, 'Orders']
            if amount_col and amount_col in orders.columns:
                col_names.append('Total Spent')
            customer_stats.columns = col_names
            customer_stats = customer_stats.sort_values('Orders', ascending=False)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Unique Customers", f"{len(customer_stats):,}")
            with col2:
                repeat = len(customer_stats[customer_stats['Orders'] > 1])
                st.metric("Repeat Customers", f"{repeat:,}")
            with col3:
                if 'Total Spent' in customer_stats.columns:
                    st.metric("Avg CLV", format_inr(customer_stats['Total Spent'].mean()))
            
            st.dataframe(customer_stats.head(50), use_container_width=True, hide_index=True)
        else:
            st.info("Customer ID column not mapped")
    
    elif report_type == "Payment Methods Report":
        st.markdown("### 💳 Payment Methods Analysis")
        
        payment_col = mappings.get('payment_method')
        amount_col = mappings.get('total_amount')
        
        if payment_col and payment_col in orders.columns:
            agg_dict = {orders.columns[0]: 'count'}
            if amount_col and amount_col in orders.columns:
                agg_dict[amount_col] = 'sum'
            
            payment_stats = orders.groupby(payment_col).agg(agg_dict).reset_index()
            col_names = [payment_col, 'Orders']
            if amount_col and amount_col in orders.columns:
                col_names.append('Revenue')
            payment_stats.columns = col_names
            payment_stats['% of Orders'] = (payment_stats['Orders'] / payment_stats['Orders'].sum() * 100).round(1)
            
            st.dataframe(payment_stats, use_container_width=True, hide_index=True)
        else:
            st.info("Payment method column not mapped")
    
    elif report_type == "Geographic Report":
        st.markdown("### 🗺️ Geographic Distribution")
        
        city_col = mappings.get('city')
        amount_col = mappings.get('total_amount')
        
        if city_col and city_col in orders.columns:
            agg_dict = {orders.columns[0]: 'count'}
            if amount_col and amount_col in orders.columns:
                agg_dict[amount_col] = 'sum'
            
            geo_stats = orders.groupby(city_col).agg(agg_dict).reset_index()
            col_names = [city_col, 'Orders']
            if amount_col and amount_col in orders.columns:
                col_names.append('Revenue')
            geo_stats.columns = col_names
            geo_stats = geo_stats.sort_values('Orders', ascending=False)
            
            st.dataframe(geo_stats, use_container_width=True, hide_index=True)
        else:
            st.info("City column not mapped")
    
    elif report_type == "Ads Performance Report":
        st.markdown("### 📢 Ads Performance")
        
        ads_meta = st.session_state.data_store.get('ads_meta', pd.DataFrame())
        
        if len(ads_meta) > 0:
            st.dataframe(ads_meta, use_container_width=True, hide_index=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Spend", format_inr(ads_meta['spend'].sum()) if 'spend' in ads_meta.columns else "N/A")
            with col2:
                st.metric("Total Clicks", f"{ads_meta['clicks'].sum():,}" if 'clicks' in ads_meta.columns else "N/A")
            with col3:
                st.metric("Conversions", f"{ads_meta['conversions'].sum():,}" if 'conversions' in ads_meta.columns else "N/A")
            with col4:
                if 'revenue' in ads_meta.columns and 'spend' in ads_meta.columns:
                    roas = ads_meta['revenue'].sum() / ads_meta['spend'].sum()
                    st.metric("ROAS", f"{roas:.2f}x")
        else:
            st.info("No ads data available")
    
    # Export option
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2 = st.columns(2)
    with col1:
        csv = orders.to_csv(index=False)
        st.download_button(
            "📥 Download Orders CSV",
            csv,
            f"orders_export_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

"""Ads Analytics - Meta, Google Ads, Shopify Ads analytics"""

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


def render_ads_analytics():
    """Main ads analytics page"""
    st.title("📢 Ads Analytics")
    st.caption("Analyze performance across Meta, Google, and Shopify Ads")
    
    # Get ads data
    ads_meta = st.session_state.data_store.get('ads_meta', pd.DataFrame())
    ads_google = st.session_state.data_store.get('ads_google', pd.DataFrame())
    ads_shopify = st.session_state.data_store.get('ads_shopify', pd.DataFrame())
    
    has_any_ads = len(ads_meta) > 0 or len(ads_google) > 0 or len(ads_shopify) > 0
    
    if not has_any_ads:
        render_ads_welcome()
        return
    
    # Platform selector
    platforms = []
    if len(ads_meta) > 0:
        platforms.append("Meta Ads")
    if len(ads_google) > 0:
        platforms.append("Google Ads")
    if len(ads_shopify) > 0:
        platforms.append("Shopify Ads")
    platforms.insert(0, "All Platforms")
    
    selected_platform = st.selectbox("Select Platform", platforms)
    
    st.markdown("---")
    
    # Render analytics based on selection
    if selected_platform == "All Platforms":
        render_cross_platform_analytics(ads_meta, ads_google, ads_shopify)
    elif selected_platform == "Meta Ads":
        render_meta_analytics(ads_meta)
    elif selected_platform == "Google Ads":
        render_google_analytics(ads_google)
    elif selected_platform == "Shopify Ads":
        render_shopify_analytics(ads_shopify)


def render_ads_welcome():
    """Welcome screen when no ads data"""
    st.info("📢 No ads data loaded yet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📁 Upload Ads Data
        
        Go to **Data Manager** and upload your ads export files:
        
        **Meta Ads Export** should include:
        - `date`, `campaign_name`, `ad_set_name`
        - `impressions`, `reach`, `clicks`
        - `spend`, `cpc`, `cpm`
        - `conversions`, `revenue`
        
        **Google Ads Export** should include:
        - `date`, `campaign`, `ad_group`
        - `impressions`, `clicks`, `cost`
        - `conversions`, `conversion_value`
        - `ctr`, `cpc`
        
        **Shopify Marketing Export** should include:
        - `date`, `campaign_type`
        - `spend`, `clicks`, `orders`
        - `revenue`, `roas`
        """)
    
    with col2:
        st.markdown("""
        ### 🔌 Connect Ads APIs
        
        Go to **API Integration** to connect:
        
        **Meta Marketing API**
        - Facebook & Instagram ads
        - Requires Business Manager access
        - OAuth authentication
        
        **Google Ads API**
        - Search & Display campaigns
        - YouTube ads
        - Requires Google Ads account
        
        **Shopify Marketing API**
        - Native Shopify campaigns
        - Marketing automations
        """)
    
    st.markdown("---")
    
    # Sample data loader
    if st.button("🎮 Load Sample Ads Data", use_container_width=True):
        load_sample_ads_data()
        st.rerun()


def load_sample_ads_data():
    """Load sample ads data for demonstration"""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Meta Ads sample
    meta_ads = pd.DataFrame({
        'date': dates,
        'campaign_name': np.random.choice(['Brand Awareness', 'Conversions', 'Retargeting', 'Lookalike'], 30),
        'ad_set_name': np.random.choice(['Age 25-34', 'Age 35-44', 'Interest: Fashion', 'Interest: Tech'], 30),
        'impressions': np.random.randint(10000, 100000, 30),
        'reach': np.random.randint(8000, 80000, 30),
        'clicks': np.random.randint(100, 2000, 30),
        'spend': np.random.uniform(500, 5000, 30).round(2),
        'conversions': np.random.randint(5, 50, 30),
        'revenue': np.random.uniform(1000, 15000, 30).round(2),
        'platform': np.random.choice(['Facebook', 'Instagram'], 30, p=[0.6, 0.4])
    })
    
    # Google Ads sample
    google_ads = pd.DataFrame({
        'date': dates,
        'campaign': np.random.choice(['Search - Brand', 'Search - Generic', 'Display', 'Shopping'], 30),
        'ad_group': np.random.choice(['Keywords A', 'Keywords B', 'Audience 1', 'Audience 2'], 30),
        'impressions': np.random.randint(5000, 50000, 30),
        'clicks': np.random.randint(50, 1000, 30),
        'cost': np.random.uniform(300, 3000, 30).round(2),
        'conversions': np.random.randint(3, 30, 30),
        'conversion_value': np.random.uniform(800, 10000, 30).round(2),
        'network': np.random.choice(['Search', 'Display', 'YouTube'], 30, p=[0.5, 0.3, 0.2])
    })
    
    st.session_state.data_store['ads_meta'] = meta_ads
    st.session_state.data_store['ads_google'] = google_ads
    
    st.success("✅ Sample ads data loaded!")


def render_cross_platform_analytics(ads_meta, ads_google, ads_shopify):
    """Cross-platform analytics view"""
    st.subheader("🌐 Cross-Platform Performance")
    
    # Aggregate metrics by platform
    platforms_data = []
    
    if len(ads_meta) > 0:
        meta_metrics = {
            'Platform': 'Meta Ads',
            'Spend': ads_meta['spend'].sum() if 'spend' in ads_meta.columns else 0,
            'Impressions': ads_meta['impressions'].sum() if 'impressions' in ads_meta.columns else 0,
            'Clicks': ads_meta['clicks'].sum() if 'clicks' in ads_meta.columns else 0,
            'Conversions': ads_meta['conversions'].sum() if 'conversions' in ads_meta.columns else 0,
            'Revenue': ads_meta['revenue'].sum() if 'revenue' in ads_meta.columns else 0
        }
        platforms_data.append(meta_metrics)
    
    if len(ads_google) > 0:
        google_metrics = {
            'Platform': 'Google Ads',
            'Spend': ads_google['cost'].sum() if 'cost' in ads_google.columns else 0,
            'Impressions': ads_google['impressions'].sum() if 'impressions' in ads_google.columns else 0,
            'Clicks': ads_google['clicks'].sum() if 'clicks' in ads_google.columns else 0,
            'Conversions': ads_google['conversions'].sum() if 'conversions' in ads_google.columns else 0,
            'Revenue': ads_google['conversion_value'].sum() if 'conversion_value' in ads_google.columns else 0
        }
        platforms_data.append(google_metrics)
    
    if len(ads_shopify) > 0:
        shopify_metrics = {
            'Platform': 'Shopify Ads',
            'Spend': ads_shopify['spend'].sum() if 'spend' in ads_shopify.columns else 0,
            'Impressions': ads_shopify.get('impressions', pd.Series([0])).sum(),
            'Clicks': ads_shopify['clicks'].sum() if 'clicks' in ads_shopify.columns else 0,
            'Conversions': ads_shopify['orders'].sum() if 'orders' in ads_shopify.columns else 0,
            'Revenue': ads_shopify['revenue'].sum() if 'revenue' in ads_shopify.columns else 0
        }
        platforms_data.append(shopify_metrics)
    
    platforms_df = pd.DataFrame(platforms_data)
    
    # Calculate derived metrics
    platforms_df['CTR'] = (platforms_df['Clicks'] / platforms_df['Impressions'] * 100).round(2)
    platforms_df['CPC'] = (platforms_df['Spend'] / platforms_df['Clicks']).round(2)
    platforms_df['ROAS'] = (platforms_df['Revenue'] / platforms_df['Spend']).round(2)
    platforms_df['CPA'] = (platforms_df['Spend'] / platforms_df['Conversions']).round(2)
    
    # Total metrics
    total_spend = platforms_df['Spend'].sum()
    total_revenue = platforms_df['Revenue'].sum()
    total_conversions = platforms_df['Conversions'].sum()
    total_clicks = platforms_df['Clicks'].sum()
    total_impressions = platforms_df['Impressions'].sum()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💸 Total Ad Spend", format_inr(total_spend))
    
    with col2:
        st.metric("💰 Total Revenue", format_inr(total_revenue))
    
    with col3:
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0
        st.metric("📈 Overall ROAS", f"{overall_roas:.2f}x")
    
    with col4:
        overall_cpa = total_spend / total_conversions if total_conversions > 0 else 0
        st.metric("🎯 Avg CPA", format_inr(overall_cpa))
    
    with col5:
        overall_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
        st.metric("🖱️ Overall CTR", f"{overall_ctr:.2f}%")
    
    st.markdown("---")
    
    # Platform comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Spend by platform
        fig = px.pie(platforms_df, values='Spend', names='Platform',
                    title="💸 Ad Spend by Platform",
                    color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ROAS comparison
        fig = px.bar(platforms_df, x='Platform', y='ROAS',
                    title="📈 ROAS by Platform",
                    color='Platform',
                    color_discrete_sequence=px.colors.qualitative.Set2)
        fig.add_hline(y=1, line_dash="dash", line_color="red", 
                      annotation_text="Break-even")
        st.plotly_chart(fig, use_container_width=True)
    
    # Efficiency comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(platforms_df, x='Platform', y='CPA',
                    title="🎯 CPA by Platform (Lower is Better)",
                    color='Platform',
                    color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(platforms_df, x='Platform', y='CTR',
                    title="🖱️ CTR by Platform",
                    color='Platform',
                    color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)
    
    # Time series - combine all platforms
    st.subheader("📈 Performance Over Time")
    
    combined_daily = []
    
    if len(ads_meta) > 0 and 'date' in ads_meta.columns:
        meta_daily = ads_meta.copy()
        meta_daily['date'] = pd.to_datetime(meta_daily['date'], errors='coerce')
        meta_daily = meta_daily.groupby(meta_daily['date'].dt.date).agg({
            'spend': 'sum',
            'conversions': 'sum'
        }).reset_index()
        meta_daily['Platform'] = 'Meta Ads'
        meta_daily.columns = ['Date', 'Spend', 'Conversions', 'Platform']
        combined_daily.append(meta_daily)
    
    if len(ads_google) > 0 and 'date' in ads_google.columns:
        google_daily = ads_google.copy()
        google_daily['date'] = pd.to_datetime(google_daily['date'], errors='coerce')
        # Use 'spend' column, fallback to 'cost' if exists
        spend_col = 'spend' if 'spend' in google_daily.columns else ('cost' if 'cost' in google_daily.columns else None)
        conv_col = 'conversions' if 'conversions' in google_daily.columns else None
        if spend_col and conv_col:
            google_daily = google_daily.groupby(google_daily['date'].dt.date).agg({
                spend_col: 'sum',
                conv_col: 'sum'
            }).reset_index()
            google_daily['Platform'] = 'Google Ads'
            google_daily.columns = ['Date', 'Spend', 'Conversions', 'Platform']
            combined_daily.append(google_daily)
    
    if combined_daily:
        all_daily = pd.concat(combined_daily, ignore_index=True)
        
        fig = px.line(all_daily, x='Date', y='Spend', color='Platform',
                     title="📈 Daily Ad Spend by Platform")
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance table
    st.subheader("📊 Platform Comparison")
    
    display_df = platforms_df.copy()
    display_df['Spend'] = display_df['Spend'].apply(format_inr)
    display_df['Revenue'] = display_df['Revenue'].apply(format_inr)
    display_df['CPC'] = display_df['CPC'].apply(lambda x: format_inr(x))
    display_df['CPA'] = display_df['CPA'].apply(lambda x: format_inr(x))
    display_df['CTR'] = display_df['CTR'].apply(lambda x: f"{x:.2f}%")
    display_df['ROAS'] = display_df['ROAS'].apply(lambda x: f"{x:.2f}x")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_meta_analytics(ads_meta):
    """Meta Ads specific analytics"""
    st.subheader("📘 Meta Ads Analytics")
    
    # Date filter
    if 'date' in ads_meta.columns:
        ads_meta['date'] = pd.to_datetime(ads_meta['date'], errors='coerce')
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", ads_meta['date'].min())
        with col2:
            end_date = st.date_input("End Date", ads_meta['date'].max())
        
        mask = (ads_meta['date'].dt.date >= start_date) & (ads_meta['date'].dt.date <= end_date)
        filtered = ads_meta[mask]
    else:
        filtered = ads_meta
    
    # Metrics
    spend = filtered['spend'].sum() if 'spend' in filtered.columns else 0
    impressions = filtered['impressions'].sum() if 'impressions' in filtered.columns else 0
    reach = filtered['reach'].sum() if 'reach' in filtered.columns else 0
    clicks = filtered['clicks'].sum() if 'clicks' in filtered.columns else 0
    conversions = filtered['conversions'].sum() if 'conversions' in filtered.columns else 0
    revenue = filtered['revenue'].sum() if 'revenue' in filtered.columns else 0
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("💸 Spend", format_inr(spend))
    with col2:
        st.metric("👁️ Impressions", f"{impressions:,.0f}")
    with col3:
        st.metric("👥 Reach", f"{reach:,.0f}")
    with col4:
        ctr = clicks / impressions * 100 if impressions > 0 else 0
        st.metric("🖱️ CTR", f"{ctr:.2f}%")
    with col5:
        st.metric("🎯 Conversions", f"{conversions:,.0f}")
    with col6:
        roas = revenue / spend if spend > 0 else 0
        st.metric("📈 ROAS", f"{roas:.2f}x")
    
    st.markdown("---")
    
    # Campaign performance
    if 'campaign_name' in filtered.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_perf = filtered.groupby('campaign_name').agg({
                'spend': 'sum',
                'conversions': 'sum',
                'revenue': 'sum'
            }).reset_index()
            campaign_perf['ROAS'] = campaign_perf['revenue'] / campaign_perf['spend']
            campaign_perf = campaign_perf.sort_values('spend', ascending=False)
            
            fig = px.bar(campaign_perf, x='campaign_name', y='spend',
                        title="💰 Spend by Campaign",
                        color_discrete_sequence=['#3b82f6'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(campaign_perf, x='campaign_name', y='ROAS',
                        title="📈 ROAS by Campaign",
                        color_discrete_sequence=['#10b981'])
            fig.add_hline(y=1, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
    
    # Platform breakdown (Facebook vs Instagram)
    if 'platform' in filtered.columns:
        st.subheader("📱 Platform Breakdown")
        
        platform_perf = filtered.groupby('platform').agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(platform_perf, values='spend', names='platform',
                        title="Spend by Platform",
                        color_discrete_sequence=['#3b82f6', '#ec4899'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(platform_perf, values='conversions', names='platform',
                        title="Conversions by Platform",
                        color_discrete_sequence=['#3b82f6', '#ec4899'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Trend
    if 'date' in filtered.columns:
        st.subheader("📈 Performance Trend")
        
        daily = filtered.groupby(filtered['date'].dt.date).agg({
            'spend': 'sum',
            'conversions': 'sum',
            'revenue': 'sum'
        }).reset_index()
        daily['ROAS'] = daily['revenue'] / daily['spend']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['spend'],
                                  name='Spend', line=dict(color='#ef4444')))
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['revenue'],
                                  name='Revenue', line=dict(color='#10b981')))
        fig.update_layout(title='Spend vs Revenue', height=350)
        st.plotly_chart(fig, use_container_width=True)


def render_google_analytics(ads_google):
    """Google Ads specific analytics"""
    st.subheader("🔍 Google Ads Analytics")
    
    # Date filter
    if 'date' in ads_google.columns:
        ads_google['date'] = pd.to_datetime(ads_google['date'], errors='coerce')
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", ads_google['date'].min(), key="gads_start")
        with col2:
            end_date = st.date_input("End Date", ads_google['date'].max(), key="gads_end")
        
        mask = (ads_google['date'].dt.date >= start_date) & (ads_google['date'].dt.date <= end_date)
        filtered = ads_google[mask]
    else:
        filtered = ads_google
    
    # Metrics
    cost = filtered['cost'].sum() if 'cost' in filtered.columns else 0
    impressions = filtered['impressions'].sum() if 'impressions' in filtered.columns else 0
    clicks = filtered['clicks'].sum() if 'clicks' in filtered.columns else 0
    conversions = filtered['conversions'].sum() if 'conversions' in filtered.columns else 0
    conv_value = filtered['conversion_value'].sum() if 'conversion_value' in filtered.columns else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💸 Cost", format_inr(cost))
    with col2:
        ctr = clicks / impressions * 100 if impressions > 0 else 0
        st.metric("🖱️ CTR", f"{ctr:.2f}%")
    with col3:
        cpc = cost / clicks if clicks > 0 else 0
        st.metric("💵 CPC", format_inr(cpc))
    with col4:
        cpa = cost / conversions if conversions > 0 else 0
        st.metric("🎯 CPA", format_inr(cpa))
    with col5:
        roas = conv_value / cost if cost > 0 else 0
        st.metric("📈 ROAS", f"{roas:.2f}x")
    
    st.markdown("---")
    
    # Campaign performance
    if 'campaign' in filtered.columns:
        col1, col2 = st.columns(2)
        
        # Determine which column to use for cost
        cost_col = 'spend' if 'spend' in filtered.columns else ('cost' if 'cost' in filtered.columns else None)
        
        if cost_col:
            with col1:
                agg_dict = {
                    cost_col: 'sum',
                    'clicks': 'sum',
                    'conversions': 'sum',
                }
                if 'conversion_value' in filtered.columns:
                    agg_dict['conversion_value'] = 'sum'
                
                campaign_perf = filtered.groupby('campaign').agg(agg_dict).reset_index()
                
                if 'conversion_value' in campaign_perf.columns:
                    campaign_perf['ROAS'] = campaign_perf['conversion_value'] / campaign_perf[cost_col]
                else:
                    campaign_perf['ROAS'] = 0
                
                fig = px.bar(campaign_perf, x='campaign', y=cost_col,
                            title="💰 Cost by Campaign",
                            color_discrete_sequence=['#4285f4'])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'ROAS' in campaign_perf.columns:
                    fig = px.bar(campaign_perf, x='campaign', y='ROAS',
                                title="📈 ROAS by Campaign",
                                color_discrete_sequence=['#34a853'])
                    fig.add_hline(y=1, line_dash="dash", line_color="red")
                    st.plotly_chart(fig, use_container_width=True)
    
    # Network breakdown
    if 'network' in filtered.columns:
        st.subheader("🌐 Network Performance")
        
        # Determine which column to use for cost
        cost_col = 'spend' if 'spend' in filtered.columns else ('cost' if 'cost' in filtered.columns else None)
        
        if cost_col:
            agg_dict = {
                cost_col: 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'conversions': 'sum'
            }
            
            network_perf = filtered.groupby('network').agg(agg_dict).reset_index()
            network_perf['CTR'] = network_perf['clicks'] / network_perf['impressions'] * 100
            network_perf['CPA'] = network_perf[cost_col] / network_perf['conversions'].replace(0, 1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(network_perf, values=cost_col, names='network',
                            title="Cost by Network",
                            color_discrete_sequence=['#4285f4', '#ea4335', '#fbbc05'])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(network_perf, x='network', y='CPA',
                            title="CPA by Network",
                            color_discrete_sequence=['#34a853'])
                st.plotly_chart(fig, use_container_width=True)


def render_shopify_analytics(ads_shopify):
    """Shopify Ads analytics"""
    st.subheader("🛍️ Shopify Marketing Analytics")
    
    if len(ads_shopify) == 0:
        st.info("No Shopify marketing data available")
        return
    
    # Basic metrics
    spend = ads_shopify['spend'].sum() if 'spend' in ads_shopify.columns else 0
    orders = ads_shopify['orders'].sum() if 'orders' in ads_shopify.columns else 0
    revenue = ads_shopify['revenue'].sum() if 'revenue' in ads_shopify.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💸 Marketing Spend", format_inr(spend))
    with col2:
        st.metric("📦 Orders", f"{orders:,.0f}")
    with col3:
        st.metric("💰 Revenue", format_inr(revenue))
    with col4:
        roas = revenue / spend if spend > 0 else 0
        st.metric("📈 ROAS", f"{roas:.2f}x")
    
    # Campaign type breakdown
    if 'campaign_type' in ads_shopify.columns:
        campaign_perf = ads_shopify.groupby('campaign_type').agg({
            'spend': 'sum',
            'orders': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        fig = px.bar(campaign_perf, x='campaign_type', y='revenue',
                    title="Revenue by Campaign Type",
                    color_discrete_sequence=['#96bf48'])
        st.plotly_chart(fig, use_container_width=True)

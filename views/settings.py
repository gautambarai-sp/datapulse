"""Settings Page for DataPulse AI"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path


def render_settings():
    """Render settings page"""
    st.markdown("""
    <div class="section-header">
        <h1 style="margin:0;color:#1e293b;">⚙️ Settings</h1>
        <p style="margin:0.5rem 0 0;color:#64748b;">Configure your DataPulse AI preferences</p>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["🏢 Company Info", "🤖 AI Settings", "📊 Data Management", "🎨 Preferences"])
    
    # Company Info Tab
    with tabs[0]:
        st.markdown("### Company Information")
        st.markdown("Update your business details")
        
        company_info = st.session_state.get('company_info', {})
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input(
                "Company Name",
                value=company_info.get('company_name', ''),
                key="settings_company_name"
            )
            industry = st.selectbox(
                "Industry",
                ["Fashion & Apparel", "Electronics", "Beauty & Personal Care", 
                 "Home & Kitchen", "Food & Beverages", "Health & Wellness",
                 "Sports & Outdoors", "Books & Media", "Toys & Games", "Other"],
                index=0 if not company_info.get('industry') else 
                      ["Fashion & Apparel", "Electronics", "Beauty & Personal Care", 
                       "Home & Kitchen", "Food & Beverages", "Health & Wellness",
                       "Sports & Outdoors", "Books & Media", "Toys & Games", "Other"].index(company_info.get('industry', 'Fashion & Apparel')),
                key="settings_industry"
            )
            website = st.text_input(
                "Website URL",
                value=company_info.get('website', ''),
                key="settings_website"
            )
        
        with col2:
            email = st.text_input(
                "Contact Email",
                value=company_info.get('email', ''),
                key="settings_email"
            )
            business_size = st.selectbox(
                "Business Size",
                ["Solo Entrepreneur", "Small (2-10)", "Medium (11-50)", "Large (50+)"],
                index=0 if not company_info.get('business_size') else
                      ["Solo Entrepreneur", "Small (2-10)", "Medium (11-50)", "Large (50+)"].index(company_info.get('business_size', 'Solo Entrepreneur')),
                key="settings_business_size"
            )
            currency_options = ["₹ INR", "$ USD", "€ EUR", "£ GBP"]
            stored_currency = company_info.get('currency', '₹ INR')
            currency_index = 0
            if stored_currency in currency_options:
                currency_index = currency_options.index(stored_currency)
            elif 'INR' in str(stored_currency) or '₹' in str(stored_currency):
                currency_index = 0
            elif 'USD' in str(stored_currency) or '$' in str(stored_currency):
                currency_index = 1
            elif 'EUR' in str(stored_currency) or '€' in str(stored_currency):
                currency_index = 2
            elif 'GBP' in str(stored_currency) or '£' in str(stored_currency):
                currency_index = 3
            currency = st.selectbox(
                "Currency",
                currency_options,
                index=currency_index,
                key="settings_currency"
            )
        
        if st.button("💾 Save Company Info", key="save_company_info", type="primary"):
            st.session_state.company_info = {
                'company_name': company_name,
                'industry': industry,
                'website': website,
                'email': email,
                'business_size': business_size,
                'currency': currency
            }
            st.success("✅ Company information saved successfully!")
    
    # AI Settings Tab
    with tabs[1]:
        st.markdown("### AI Assistant Configuration")
        
        llm_config = st.session_state.get('llm_config', {})
        
        provider = st.selectbox(
            "LLM Provider",
            ["OpenAI", "Groq"],
            index=["openai", "groq"].index(llm_config.get('provider', 'openai')) 
                  if llm_config.get('provider') in ["openai", "groq"] else 0,
            key="settings_provider"
        )
        
        provider_map = {"OpenAI": "openai", "Groq": "groq"}
        selected_provider = provider_map[provider]
        
        if selected_provider == "openai":
            api_key = st.text_input("OpenAI API Key", type="password", key="settings_openai_key")
            model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], key="settings_openai_model")
        else:
            api_key = st.text_input("Groq API Key", type="password", key="settings_groq_key")
            model = st.selectbox("Model", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"], key="settings_groq_model")
        
        st.markdown("#### AI Personality")
        tone = st.select_slider(
            "Response Tone",
            options=["Very Formal", "Formal", "Balanced", "Casual", "Very Casual"],
            value="Balanced",
            key="settings_tone"
        )
        
        if st.button("💾 Save AI Settings", key="save_ai_settings", type="primary"):
            config = {
                'provider': selected_provider,
                'model': model if selected_provider == "ollama" else model,
                'tone': tone
            }
            if selected_provider in ["openai", "groq"]:
                config['api_key'] = api_key
            st.session_state.llm_config = config
            st.success("✅ AI settings saved successfully!")
    
    # Data Management Tab
    with tabs[2]:
        st.markdown("### Data Management")
        
        # Show current data status
        data_store = st.session_state.get('data_store', {})
        
        st.markdown("#### 📁 Loaded Datasets")
        
        datasets = {
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
        
        for key, label in datasets.items():
            df = data_store.get(key, pd.DataFrame())
            if len(df) > 0:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{label}**")
                with col2:
                    st.markdown(f"`{len(df):,} rows`")
                with col3:
                    if st.button("🗑️ Clear", key=f"clear_{key}"):
                        st.session_state.data_store[key] = pd.DataFrame()
                        st.rerun()
        
        st.markdown("---")
        
        # Clear all data
        st.markdown("#### ⚠️ Danger Zone")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Data", type="secondary", key="clear_all_data"):
                st.session_state.data_store = {}
                st.session_state.column_mappings = {}
                st.success("All data cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset Onboarding", type="secondary", key="reset_onboarding"):
                st.session_state.onboarding_complete = False
                st.session_state.onboarding_step = 0
                st.session_state.company_info = {}
                st.success("Onboarding reset! Refreshing...")
                st.rerun()
    
    # Preferences Tab
    with tabs[3]:
        st.markdown("### Display Preferences")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📅 Date Format")
            date_format = st.selectbox(
                "Preferred Date Format",
                ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
                key="settings_date_format"
            )
            
            st.markdown("#### 💰 Number Format")
            number_format = st.selectbox(
                "Number Format",
                ["Indian (12,34,567)", "International (1,234,567)"],
                key="settings_number_format"
            )
        
        with col2:
            st.markdown("#### 📊 Chart Preferences")
            chart_theme = st.selectbox(
                "Chart Color Theme",
                ["DataPulse Purple", "Ocean Blue", "Forest Green", "Sunset Orange"],
                key="settings_chart_theme"
            )
            
            st.markdown("#### 🔔 Notifications")
            email_reports = st.toggle("Email Weekly Reports", value=False, key="settings_email_reports")
        
        if st.button("💾 Save Preferences", key="save_preferences", type="primary"):
            st.session_state.preferences = {
                'date_format': date_format,
                'number_format': number_format,
                'chart_theme': chart_theme,
                'email_reports': email_reports
            }
            st.success("✅ Preferences saved successfully!")
        
        st.markdown("---")
        
        # App info
        st.markdown("### ℹ️ About DataPulse AI")
        st.markdown("""
        <div style="background:linear-gradient(135deg,#f8fafc,#f1f5f9);border-radius:12px;padding:1.5rem;border:1px solid #e2e8f0;">
            <p style="margin:0;color:#64748b;font-size:0.875rem;">
                <strong style="color:#1e293b;">DataPulse AI</strong> v1.0.0<br><br>
                🚀 AI-powered e-commerce analytics platform<br>
                📊 Real-time insights and reporting<br>
                🤖 Smart chatbot for data queries<br>
                📢 Multi-platform ads analytics<br><br>
                <em>Built with ❤️ for modern e-commerce businesses</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

"""Navigation sidebar"""

import streamlit as st
from datetime import datetime


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span style="font-size: 2.5rem;">📊</span>
            <h1>DataPulse</h1>
            <p style="color: #64748b; font-size: 0.8rem;">E-Commerce Analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📁 Data Manager", "🤖 AI Chat", "📈 Reports", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if st.session_state.datasets:
            st.markdown("**📂 Active Dataset**")
            names = list(st.session_state.datasets.keys())
            current_index = names.index(st.session_state.active_dataset) if st.session_state.active_dataset in names else 0
            
            selected = st.selectbox("Dataset", names, index=current_index, label_visibility="collapsed")
            
            if selected != st.session_state.active_dataset:
                st.session_state.active_dataset = selected
                st.rerun()
            
            ds = st.session_state.datasets[selected]
            st.caption(f"📋 {len(ds['df']):,} rows | 🔗 {len(ds['mappings'])} fields")
            
            st.divider()
            
            live = st.toggle("🔴 Live Mode", st.session_state.live_mode)
            if live != st.session_state.live_mode:
                st.session_state.live_mode = live
            
            if st.session_state.live_mode:
                st.markdown('<div class="live-badge"><div class="live-dot"></div>Auto-refreshing</div>', unsafe_allow_html=True)
        else:
            st.info("📁 No data loaded")
        
        st.divider()
        st.caption("DataPulse v1.0")
    
    return page

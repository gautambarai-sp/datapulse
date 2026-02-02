"""KPI metric components"""

import streamlit as st


def insight_box(message: str, type: str = "info") -> None:
    icons = {'positive': '✅', 'warning': '⚠️', 'negative': '🚨', 'info': '💡'}
    icon = icons.get(type, '💡')
    
    if type == 'warning':
        st.warning(f"{icon} {message}")
    elif type == 'negative':
        st.error(f"{icon} {message}")
    elif type == 'positive':
        st.success(f"{icon} {message}")
    else:
        st.info(f"{icon} {message}")

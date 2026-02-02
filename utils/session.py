"""Session state management"""

import streamlit as st
from datetime import datetime


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'datasets': {},
        'active_dataset': None,
        'chat_messages': [],
        'live_mode': False,
        'currency': 'INR',
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_dataset():
    """Get currently active dataset or None."""
    if st.session_state.active_dataset:
        return st.session_state.datasets.get(st.session_state.active_dataset)
    return None


def add_dataset(name, df, mappings, stats):
    """Add a new dataset."""
    st.session_state.datasets[name] = {
        'df': df,
        'mappings': mappings,
        'stats': stats,
        'uploaded_at': datetime.now()
    }
    st.session_state.active_dataset = name


def remove_dataset(name):
    """Remove a dataset."""
    if name in st.session_state.datasets:
        del st.session_state.datasets[name]
        if st.session_state.active_dataset == name:
            names = list(st.session_state.datasets.keys())
            st.session_state.active_dataset = names[0] if names else None


def add_chat_message(role, content, data=None, chart=None, insight=None):
    """Add message to chat history."""
    st.session_state.chat_messages.append({
        'role': role,
        'content': content,
        'data': data,
        'chart': chart,
        'insight': insight,
        'timestamp': datetime.now()
    })


def clear_chat():
    """Clear chat history."""
    st.session_state.chat_messages = []

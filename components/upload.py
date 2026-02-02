"""File upload component"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple


def show_file_preview(df: pd.DataFrame, rows: int = 10) -> None:
    with st.expander("📋 Data Preview", expanded=True):
        st.dataframe(df.head(rows), use_container_width=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            st.metric("Size", f"{memory_mb:.1f} MB")


def column_mapping_form(df: pd.DataFrame, detected: Dict[str, str]) -> Tuple[Dict[str, str], str]:
    columns = [''] + list(df.columns)
    
    def get_idx(field: str) -> int:
        col = detected.get(field, '')
        return list(df.columns).index(col) + 1 if col in df.columns else 0
    
    st.markdown("### 🔗 Column Mapping")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        order_id = st.selectbox("Order ID *", columns, index=get_idx('order_id'))
    with col2:
        amount = st.selectbox("Order Amount *", columns, index=get_idx('total_amount'))
    with col3:
        status = st.selectbox("Order Status *", columns, index=get_idx('order_status'))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date = st.selectbox("Order Date", columns, index=get_idx('order_date'))
    with col2:
        payment = st.selectbox("Payment Method", columns, index=get_idx('payment_method'))
    with col3:
        customer = st.selectbox("Customer Name", columns, index=get_idx('customer_name'))
    with col4:
        category = st.selectbox("Category", columns, index=get_idx('category'))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        product = st.selectbox("Product Name", columns, index=get_idx('product_name'))
    with col2:
        city = st.selectbox("City", columns, index=get_idx('city'))
    with col3:
        email = st.selectbox("Customer Email", columns, index=get_idx('customer_email'))
    with col4:
        qty = st.selectbox("Quantity", columns, index=get_idx('quantity'))
    
    name = st.text_input("Dataset Name", st.session_state.get('_uploaded_filename', 'My Dataset'))
    
    mappings = {}
    if order_id: mappings['order_id'] = order_id
    if amount: mappings['total_amount'] = amount
    if status: mappings['order_status'] = status
    if date: mappings['order_date'] = date
    if payment: mappings['payment_method'] = payment
    if customer: mappings['customer_name'] = customer
    if category: mappings['category'] = category
    if product: mappings['product_name'] = product
    if city: mappings['city'] = city
    if email: mappings['customer_email'] = email
    if qty: mappings['quantity'] = qty
    
    return mappings, name

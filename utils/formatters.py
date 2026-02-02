"""Formatting utilities for currency and numbers"""

import pandas as pd


def format_currency(value, currency='INR'):
    """Format as Indian Rupees with Lakhs/Crores."""
    if pd.isna(value) or value is None:
        return "₹0"
    
    value = float(value)
    
    if currency == 'INR':
        if abs(value) >= 10000000:
            return f"₹{value/10000000:.2f}Cr"
        elif abs(value) >= 100000:
            return f"₹{value/100000:.2f}L"
        elif abs(value) >= 1000:
            return f"₹{value:,.0f}"
        else:
            return f"₹{value:.0f}"
    return f"${value:,.2f}"


def format_number(value):
    """Format large numbers with K/M suffix."""
    if pd.isna(value):
        return "0"
    value = float(value)
    if abs(value) >= 1000000:
        return f"{value/1000000:.1f}M"
    elif abs(value) >= 1000:
        return f"{value/1000:.1f}K"
    return f"{value:,.0f}"


def format_percentage(value, decimals=1):
    """Format as percentage."""
    if pd.isna(value):
        return "0%"
    return f"{float(value):.{decimals}f}%"

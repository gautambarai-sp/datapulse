"""Data cleaning and processing"""

import pandas as pd
import re
from typing import Dict, Tuple


class DataProcessor:
    """Handles data cleaning and column detection."""
    
    STATUS_MAP = {
        'delivered': 'Delivered', 'completed': 'Delivered', 'fulfilled': 'Delivered',
        'success': 'Delivered', 'successful': 'Delivered',
        'cancelled': 'Cancelled', 'canceled': 'Cancelled', 'refunded': 'Cancelled',
        'rto': 'RTO', 'returned': 'RTO', 'return': 'RTO', 'undelivered': 'RTO',
        'return to origin': 'RTO', 'failed delivery': 'RTO', 'failed': 'RTO',
        'processing': 'Processing', 'pending': 'Processing', 'confirmed': 'Processing',
        'new': 'Processing', 'placed': 'Processing',
        'shipped': 'Shipped', 'in transit': 'Shipped', 'dispatched': 'Shipped',
    }
    
    PAYMENT_MAP = {
        'cod': 'COD', 'cash on delivery': 'COD', 'cash': 'COD',
        'upi': 'UPI', 'gpay': 'UPI', 'phonepe': 'UPI', 'paytm': 'UPI',
        'credit card': 'Card', 'debit card': 'Card', 'card': 'Card',
        'net banking': 'Net Banking', 'netbanking': 'Net Banking',
        'prepaid': 'Prepaid', 'online': 'Prepaid', 'wallet': 'Prepaid',
    }
    
    COLUMN_PATTERNS = {
        'order_id': [r'order[_\s]?id', r'order[_\s]?no', r'^id$', r'invoice'],
        'total_amount': [r'total', r'amount', r'value', r'price', r'revenue', r'sale'],
        'order_status': [r'status', r'state', r'delivery.*status'],
        'order_date': [r'date', r'created', r'placed', r'time'],
        'payment_method': [r'payment', r'pay.*method', r'pay.*mode'],
        'customer_name': [r'customer.*name', r'^name$', r'buyer'],
        'customer_email': [r'email', r'mail'],
        'city': [r'^city$', r'customer.*city', r'shipping.*city'],
        'product_name': [r'product', r'item', r'sku.*name'],
        'category': [r'category', r'type', r'department'],
        'quantity': [r'qty', r'quantity', r'units'],
    }
    
    @classmethod
    def detect_columns(cls, df: pd.DataFrame) -> Dict[str, str]:
        """Auto-detect column mappings."""
        detected = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            for field, patterns in cls.COLUMN_PATTERNS.items():
                if field not in detected:
                    for pattern in patterns:
                        if re.search(pattern, col_lower):
                            detected[field] = col
                            break
        return detected
    
    @classmethod
    def standardize_status(cls, status: str) -> str:
        if pd.isna(status):
            return 'Unknown'
        status_lower = str(status).lower().strip()
        return cls.STATUS_MAP.get(status_lower, status.title())
    
    @classmethod
    def standardize_payment(cls, payment: str) -> str:
        if pd.isna(payment):
            return 'Unknown'
        payment_lower = str(payment).lower().strip()
        return cls.PAYMENT_MAP.get(payment_lower, payment.title())
    
    @classmethod
    def clean_dataframe(cls, df: pd.DataFrame, mappings: Dict[str, str]) -> Tuple[pd.DataFrame, Dict]:
        """Clean and standardize the DataFrame."""
        df = df.copy()
        stats = {'original_rows': len(df), 'duplicates_removed': 0, 'test_orders_removed': 0}
        
        # Remove duplicates
        order_id_col = mappings.get('order_id')
        if order_id_col and order_id_col in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=[order_id_col])
            stats['duplicates_removed'] = before - len(df)
        
        # Clean status
        status_col = mappings.get('order_status')
        if status_col and status_col in df.columns:
            df[status_col] = df[status_col].apply(cls.standardize_status)
        
        # Clean payment method
        payment_col = mappings.get('payment_method')
        if payment_col and payment_col in df.columns:
            df[payment_col] = df[payment_col].apply(cls.standardize_payment)
        
        # Clean amount
        amount_col = mappings.get('total_amount')
        if amount_col and amount_col in df.columns:
            df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$,Rs\.\s]', '', regex=True)
            df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        
        # Clean date
        date_col = mappings.get('order_date')
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Remove test orders
        for col in [mappings.get('customer_email'), mappings.get('customer_name')]:
            if col and col in df.columns:
                before = len(df)
                mask = ~df[col].astype(str).str.lower().str.contains('test|demo|sample|dummy', na=False)
                df = df[mask]
                stats['test_orders_removed'] += before - len(df)
        
        stats['final_rows'] = len(df)
        return df, stats

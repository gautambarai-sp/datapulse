"""Core analytics engine with accurate business logic"""

import pandas as pd
from typing import Dict, Any, Optional


class AnalyticsEngine:
    """Analytics engine with CORRECT business logic."""
    
    def __init__(self, df: pd.DataFrame, mappings: Dict[str, str]):
        self.df = df
        self.mappings = mappings
    
    def _col(self, field: str) -> Optional[str]:
        return self.mappings.get(field)
    
    def _delivered(self) -> pd.DataFrame:
        status_col = self._col('order_status')
        if status_col and status_col in self.df.columns:
            return self.df[self.df[status_col] == 'Delivered']
        return self.df
    
    def _shipped(self) -> pd.DataFrame:
        status_col = self._col('order_status')
        if status_col and status_col in self.df.columns:
            return self.df[self.df[status_col].isin(['Delivered', 'RTO'])]
        return self.df
    
    def total_revenue(self) -> Dict[str, Any]:
        amount_col = self._col('total_amount')
        delivered = self._delivered()
        value = delivered[amount_col].sum() if amount_col and amount_col in delivered.columns else 0
        return {'value': value, 'orders': len(delivered)}
    
    def aov(self) -> Dict[str, Any]:
        amount_col = self._col('total_amount')
        delivered = self._delivered()
        value = delivered[amount_col].mean() if amount_col and amount_col in delivered.columns and len(delivered) > 0 else 0
        return {'value': value, 'orders': len(delivered)}
    
    def total_orders(self) -> Dict[str, Any]:
        status_col = self._col('order_status')
        breakdown = self.df[status_col].value_counts().to_dict() if status_col and status_col in self.df.columns else {}
        return {'value': len(self.df), 'breakdown': breakdown}
    
    def rto_rate(self) -> Dict[str, Any]:
        status_col = self._col('order_status')
        if not status_col or status_col not in self.df.columns:
            return {'value': 0, 'rto_orders': 0, 'shipped': 0}
        
        shipped = self._shipped()
        rto_count = len(shipped[shipped[status_col] == 'RTO'])
        shipped_count = len(shipped)
        rate = (rto_count / shipped_count * 100) if shipped_count > 0 else 0
        return {'value': rate, 'rto_orders': rto_count, 'shipped': shipped_count}
    
    def status_breakdown(self) -> pd.DataFrame:
        status_col = self._col('order_status')
        if not status_col or status_col not in self.df.columns:
            return pd.DataFrame()
        df = self.df.groupby(status_col).size().reset_index(name='Orders')
        df.columns = ['Status', 'Orders']
        df['Percentage'] = (df['Orders'] / df['Orders'].sum() * 100).round(1)
        return df.sort_values('Orders', ascending=False)
    
    def payment_breakdown(self) -> pd.DataFrame:
        payment_col = self._col('payment_method')
        amount_col = self._col('total_amount')
        if not payment_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered()
        if len(delivered) == 0:
            return pd.DataFrame()
        df = delivered.groupby(payment_col).agg(
            Revenue=(amount_col, 'sum'),
            Orders=(amount_col, 'count'),
            AOV=(amount_col, 'mean')
        ).reset_index()
        df.columns = ['Payment Method', 'Revenue', 'Orders', 'AOV']
        return df.sort_values('Revenue', ascending=False)
    
    def category_breakdown(self) -> pd.DataFrame:
        category_col = self._col('category')
        amount_col = self._col('total_amount')
        if not category_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered()
        if len(delivered) == 0:
            return pd.DataFrame()
        df = delivered.groupby(category_col).agg(
            Revenue=(amount_col, 'sum'),
            Orders=(amount_col, 'count')
        ).reset_index()
        df.columns = ['Category', 'Revenue', 'Orders']
        return df.sort_values('Revenue', ascending=False)
    
    def top_products(self, n: int = 10) -> pd.DataFrame:
        product_col = self._col('product_name')
        amount_col = self._col('total_amount')
        if not product_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered()
        if len(delivered) == 0:
            return pd.DataFrame()
        df = delivered.groupby(product_col).agg(
            Revenue=(amount_col, 'sum'),
            Orders=(amount_col, 'count')
        ).reset_index()
        df.columns = ['Product', 'Revenue', 'Orders']
        return df.sort_values('Revenue', ascending=False).head(n)
    
    def top_customers(self, n: int = 10) -> pd.DataFrame:
        customer_col = self._col('customer_name') or self._col('customer_email')
        amount_col = self._col('total_amount')
        if not customer_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered()
        if len(delivered) == 0:
            return pd.DataFrame()
        df = delivered.groupby(customer_col).agg(
            TotalSpent=(amount_col, 'sum'),
            Orders=(amount_col, 'count'),
            AOV=(amount_col, 'mean')
        ).reset_index()
        df.columns = ['Customer', 'Total Spent', 'Orders', 'AOV']
        return df.sort_values('Total Spent', ascending=False).head(n)
    
    def city_breakdown(self, n: int = 10) -> pd.DataFrame:
        city_col = self._col('city')
        amount_col = self._col('total_amount')
        if not city_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered()
        if len(delivered) == 0:
            return pd.DataFrame()
        df = delivered.groupby(city_col).agg(
            Revenue=(amount_col, 'sum'),
            Orders=(amount_col, 'count')
        ).reset_index()
        df.columns = ['City', 'Revenue', 'Orders']
        return df.sort_values('Revenue', ascending=False).head(n)
    
    def revenue_trend(self, period: str = 'D') -> pd.DataFrame:
        date_col = self._col('order_date')
        amount_col = self._col('total_amount')
        if not date_col or not amount_col:
            return pd.DataFrame()
        delivered = self._delivered().copy()
        delivered = delivered[delivered[date_col].notna()]
        if len(delivered) == 0:
            return pd.DataFrame()
        delivered['Period'] = delivered[date_col].dt.to_period(period).astype(str)
        df = delivered.groupby('Period')[amount_col].sum().reset_index()
        df.columns = ['Period', 'Revenue']
        return df
    
    def rto_by_payment(self) -> pd.DataFrame:
        status_col = self._col('order_status')
        payment_col = self._col('payment_method')
        if not status_col or not payment_col:
            return pd.DataFrame()
        shipped = self._shipped()
        if len(shipped) == 0:
            return pd.DataFrame()
        
        def calc_rto(group):
            rto = len(group[group[status_col] == 'RTO'])
            total = len(group)
            return pd.Series({
                'Shipped': total,
                'RTO Orders': rto,
                'RTO Rate': round(rto / total * 100, 2) if total > 0 else 0
            })
        
        df = shipped.groupby(payment_col).apply(calc_rto).reset_index()
        df.columns = ['Payment Method', 'Shipped', 'RTO Orders', 'RTO Rate']
        return df.sort_values('RTO Rate', ascending=False)
    
    def rto_by_city(self, n: int = 10, min_orders: int = 5) -> pd.DataFrame:
        status_col = self._col('order_status')
        city_col = self._col('city')
        if not status_col or not city_col:
            return pd.DataFrame()
        shipped = self._shipped()
        if len(shipped) == 0:
            return pd.DataFrame()
        
        city_counts = shipped[city_col].value_counts()
        valid_cities = city_counts[city_counts >= min_orders].index
        shipped = shipped[shipped[city_col].isin(valid_cities)]
        
        if len(shipped) == 0:
            return pd.DataFrame()
        
        def calc_rto(group):
            rto = len(group[group[status_col] == 'RTO'])
            total = len(group)
            return pd.Series({
                'Shipped': total,
                'RTO Orders': rto,
                'RTO Rate': round(rto / total * 100, 2) if total > 0 else 0
            })
        
        df = shipped.groupby(city_col).apply(calc_rto).reset_index()
        df.columns = ['City', 'Shipped', 'RTO Orders', 'RTO Rate']
        return df.sort_values('RTO Rate', ascending=False).head(n)
    
    def cod_vs_prepaid(self) -> Dict[str, Dict]:
        payment_col = self._col('payment_method')
        amount_col = self._col('total_amount')
        status_col = self._col('order_status')
        
        if not all([payment_col, amount_col, status_col]):
            return {}
        
        df = self.df.copy()
        df['PaymentType'] = df[payment_col].apply(lambda x: 'COD' if x == 'COD' else 'Prepaid')
        
        result = {}
        for ptype in ['COD', 'Prepaid']:
            subset = df[df['PaymentType'] == ptype]
            delivered = subset[subset[status_col] == 'Delivered']
            shipped = subset[subset[status_col].isin(['Delivered', 'RTO'])]
            
            rto_count = len(shipped[shipped[status_col] == 'RTO'])
            shipped_count = len(shipped)
            
            result[ptype] = {
                'total_orders': len(subset),
                'delivered_orders': len(delivered),
                'revenue': delivered[amount_col].sum() if len(delivered) > 0 else 0,
                'aov': delivered[amount_col].mean() if len(delivered) > 0 else 0,
                'rto_rate': round(rto_count / shipped_count * 100, 2) if shipped_count > 0 else 0,
                'rto_orders': rto_count,
                'shipped_orders': shipped_count
            }
        
        return result
    
    def repeat_customers(self) -> Dict[str, Any]:
        customer_col = self._col('customer_name') or self._col('customer_email')
        if not customer_col or customer_col not in self.df.columns:
            return {'value': 0, 'repeat_count': 0, 'total_customers': 0}
        delivered = self._delivered()
        if len(delivered) == 0:
            return {'value': 0, 'repeat_count': 0, 'total_customers': 0}
        customer_orders = delivered.groupby(customer_col).size()
        total_customers = len(customer_orders)
        repeat_customers = len(customer_orders[customer_orders > 1])
        rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
        return {'value': rate, 'repeat_count': repeat_customers, 'total_customers': total_customers}

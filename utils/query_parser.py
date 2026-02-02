"""Natural language query parser"""

import re
from typing import Tuple, Dict, Any
from utils.analytics import AnalyticsEngine
from utils.formatters import format_currency, format_percentage


class QueryParser:
    
    PATTERNS = {
        'total_revenue': [r'total revenue', r'^revenue$', r'how much.*made', r'total sales', r'gmv'],
        'aov': [r'average order value', r'\baov\b', r'avg.*order', r'basket.*size'],
        'order_count': [r'how many orders', r'total orders', r'order count'],
        'rto_rate': [r'rto rate', r'return.*rate', r'\brto\b', r'returns'],
        'status_breakdown': [r'status breakdown', r'orders by status', r'status wise'],
        'category_breakdown': [r'revenue by category', r'category.*revenue', r'by category'],
        'top_products': [r'top.*product', r'best.*product', r'best sell'],
        'top_customers': [r'top.*customer', r'best.*customer', r'vip'],
        'cod_vs_prepaid': [r'cod.*prepaid', r'prepaid.*cod', r'cod.*vs', r'compare.*payment'],
        'rto_by_payment': [r'rto.*payment', r'rto.*cod', r'payment.*rto'],
        'rto_by_city': [r'rto.*city', r'city.*rto'],
        'revenue_trend': [r'revenue trend', r'revenue.*time', r'monthly revenue'],
        'city_breakdown': [r'revenue.*city', r'city.*revenue', r'top.*city'],
        'payment_breakdown': [r'payment.*breakdown', r'by.*payment'],
        'summary': [r'summary', r'overview', r'dashboard', r'\bkpi\b'],
    }
    
    @classmethod
    def parse(cls, query: str) -> Tuple[str, Dict]:
        query_lower = query.lower().strip()
        params = {}
        match = re.search(r'top\s*(\d+)', query_lower)
        if match:
            params['limit'] = int(match.group(1))
        
        for query_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type, params
        return 'unknown', params
    
    @classmethod
    def execute(cls, engine: AnalyticsEngine, query: str) -> Dict[str, Any]:
        query_type, params = cls.parse(query)
        response = {'content': '', 'data': None, 'chart_data': None, 'chart_type': None, 'insight': None}
        
        if query_type == 'total_revenue':
            result = engine.total_revenue()
            response['content'] = f"**Total Revenue: {format_currency(result['value'])}**\n\nFrom {result['orders']:,} delivered orders."
        
        elif query_type == 'aov':
            result = engine.aov()
            response['content'] = f"**Average Order Value: {format_currency(result['value'])}**\n\nBased on {result['orders']:,} delivered orders."
        
        elif query_type == 'order_count':
            result = engine.total_orders()
            lines = [f"**Total Orders: {result['value']:,}**\n"]
            if result['breakdown']:
                lines.append("**By Status:**")
                for status, count in sorted(result['breakdown'].items(), key=lambda x: -x[1]):
                    pct = count / result['value'] * 100
                    lines.append(f"- {status}: {count:,} ({pct:.1f}%)")
            response['content'] = '\n'.join(lines)
        
        elif query_type == 'rto_rate':
            result = engine.rto_rate()
            response['content'] = f"**RTO Rate: {format_percentage(result['value'])}**\n\n{result['rto_orders']:,} returns out of {result['shipped']:,} shipped orders."
            response['insight'] = "RTO Rate = RTO / (Delivered + RTO), not all orders."
        
        elif query_type == 'status_breakdown':
            df = engine.status_breakdown()
            response['content'] = "**Orders by Status:**"
            response['data'] = df
            response['chart_data'] = df
            response['chart_type'] = 'pie'
        
        elif query_type == 'category_breakdown':
            df = engine.category_breakdown()
            if not df.empty:
                display_df = df.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(format_currency)
                response['content'] = "**Revenue by Category:**"
                response['data'] = display_df
                response['chart_data'] = df
                response['chart_type'] = 'bar'
            else:
                response['content'] = "Category column not available."
        
        elif query_type == 'top_products':
            limit = params.get('limit', 10)
            df = engine.top_products(limit)
            if not df.empty:
                display_df = df.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(format_currency)
                response['content'] = f"**Top {limit} Products:**"
                response['data'] = display_df
                response['chart_data'] = df
                response['chart_type'] = 'horizontal_bar'
            else:
                response['content'] = "Product column not available."
        
        elif query_type == 'top_customers':
            limit = params.get('limit', 10)
            df = engine.top_customers(limit)
            if not df.empty:
                display_df = df.copy()
                display_df['Total Spent'] = display_df['Total Spent'].apply(format_currency)
                response['content'] = f"**Top {limit} Customers:**"
                response['data'] = display_df
            else:
                response['content'] = "Customer column not available."
        
        elif query_type == 'cod_vs_prepaid':
            result = engine.cod_vs_prepaid()
            if result:
                cod = result['COD']
                prepaid = result['Prepaid']
                response['content'] = f"""**COD vs Prepaid Comparison:**

| Metric | COD | Prepaid |
|--------|-----|---------|
| Revenue | {format_currency(cod['revenue'])} | {format_currency(prepaid['revenue'])} |
| Orders | {cod['delivered_orders']:,} | {prepaid['delivered_orders']:,} |
| AOV | {format_currency(cod['aov'])} | {format_currency(prepaid['aov'])} |
| RTO Rate | {cod['rto_rate']}% | {prepaid['rto_rate']}% |"""
                if cod['rto_rate'] > prepaid['rto_rate']:
                    diff = cod['rto_rate'] - prepaid['rto_rate']
                    response['insight'] = f"⚠️ COD has {diff:.1f}% higher RTO rate than Prepaid."
                response['chart_data'] = result
                response['chart_type'] = 'comparison'
            else:
                response['content'] = "Payment method column not available."
        
        elif query_type == 'rto_by_payment':
            df = engine.rto_by_payment()
            if not df.empty:
                response['content'] = "**RTO Rate by Payment Method:**"
                response['data'] = df
                response['chart_data'] = df
                response['chart_type'] = 'bar'
            else:
                response['content'] = "Required columns not available."
        
        elif query_type == 'rto_by_city':
            limit = params.get('limit', 10)
            df = engine.rto_by_city(limit)
            if not df.empty:
                response['content'] = f"**Top {limit} Cities by RTO Rate:**"
                response['data'] = df
                response['chart_data'] = df
                response['chart_type'] = 'bar'
                response['insight'] = f"🚨 {df.iloc[0]['City']} has highest RTO at {df.iloc[0]['RTO Rate']}%"
            else:
                response['content'] = "Required columns not available."
        
        elif query_type == 'revenue_trend':
            df = engine.revenue_trend()
            if not df.empty:
                response['content'] = "**Revenue Trend:**"
                response['chart_data'] = df
                response['chart_type'] = 'area'
            else:
                response['content'] = "Date column not available."
        
        elif query_type == 'city_breakdown':
            limit = params.get('limit', 10)
            df = engine.city_breakdown(limit)
            if not df.empty:
                display_df = df.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(format_currency)
                response['content'] = f"**Top {limit} Cities:**"
                response['data'] = display_df
                response['chart_data'] = df
                response['chart_type'] = 'horizontal_bar'
            else:
                response['content'] = "City column not available."
        
        elif query_type == 'payment_breakdown':
            df = engine.payment_breakdown()
            if not df.empty:
                display_df = df.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(format_currency)
                display_df['AOV'] = display_df['AOV'].apply(format_currency)
                response['content'] = "**Revenue by Payment Method:**"
                response['data'] = display_df
                response['chart_data'] = df
                response['chart_type'] = 'bar'
            else:
                response['content'] = "Payment column not available."
        
        elif query_type == 'summary':
            revenue = engine.total_revenue()
            aov_data = engine.aov()
            orders = engine.total_orders()
            rto = engine.rto_rate()
            response['content'] = f"""**📊 Business Summary:**

| Metric | Value |
|--------|-------|
| Total Revenue | {format_currency(revenue['value'])} |
| Average Order Value | {format_currency(aov_data['value'])} |
| Total Orders | {orders['value']:,} |
| RTO Rate | {format_percentage(rto['value'])} |"""
        
        else:
            response['content'] = """I'm not sure what you're asking. Try:
- "What is my total revenue?"
- "How many orders?"
- "RTO rate by payment method"
- "Top 10 products"
- "COD vs Prepaid"
- "Show me a summary"
"""
        
        return response

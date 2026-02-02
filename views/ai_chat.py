"""Enhanced AI Chatbot with LLM integration and intelligent visualizations"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# Import LLM providers
try:
    from views.llm_provider import (
        OllamaProvider, OpenAIProvider, GroqProvider, 
        DataAnalysisLLM, get_llm_provider
    )
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def format_inr(value):
    """Format as INR"""
    if pd.isna(value) or value == 0:
        return "₹0"
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    return f"₹{value:,.0f}"


def get_colors():
    """Get color palette"""
    return ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#22c55e', '#3b82f6', '#14b8a6', '#ef4444']


class DataAnalyzer:
    """Intelligent data analyzer for natural language queries"""
    
    def __init__(self):
        self.orders = st.session_state.data_store.get('orders', pd.DataFrame())
        self.customers = st.session_state.data_store.get('customers', pd.DataFrame())
        self.products = st.session_state.data_store.get('products', pd.DataFrame())
        self.inventory = st.session_state.data_store.get('inventory', pd.DataFrame())
        self.ads_meta = st.session_state.data_store.get('ads_meta', pd.DataFrame())
        self.ads_google = st.session_state.data_store.get('ads_google', pd.DataFrame())
        self.ads_shopify = st.session_state.data_store.get('ads_shopify', pd.DataFrame())
        self.order_mappings = st.session_state.column_mappings.get('orders', {})
        self.customer_mappings = st.session_state.column_mappings.get('customers', {})
        self.product_mappings = st.session_state.column_mappings.get('products', {})
        self.inventory_mappings = st.session_state.column_mappings.get('inventory', {})
        
        # Build lookup tables for IDs to names
        self._product_id_to_name = self._build_product_lookup()
        self._customer_id_to_name = self._build_customer_lookup()
    
    def _build_product_lookup(self):
        """Build product ID to name lookup from products dataset"""
        lookup = {}
        if len(self.products) > 0:
            # Find ID column
            id_col = None
            name_col = None
            for col in self.products.columns:
                col_lower = col.lower()
                if 'product_id' in col_lower or col_lower == 'id' or col_lower == 'sku':
                    id_col = col
                if 'product_name' in col_lower or 'name' in col_lower or 'title' in col_lower:
                    if 'customer' not in col_lower:
                        name_col = col
            
            if id_col and name_col:
                for _, row in self.products.iterrows():
                    lookup[str(row[id_col])] = str(row[name_col])
        return lookup
    
    def _build_customer_lookup(self):
        """Build customer ID to name lookup from customers dataset"""
        lookup = {}
        if len(self.customers) > 0:
            # Find ID column
            id_col = None
            name_col = None
            for col in self.customers.columns:
                col_lower = col.lower()
                if 'customer_id' in col_lower or col_lower == 'id':
                    id_col = col
                if 'customer_name' in col_lower or 'name' in col_lower or 'full_name' in col_lower:
                    name_col = col
            
            if id_col and name_col:
                for _, row in self.customers.iterrows():
                    lookup[str(row[id_col])] = str(row[name_col])
        return lookup
    
    def _enrich_with_names(self, df, column, entity_type='product'):
        """Enrich a dataframe column with names if it contains IDs
        
        Args:
            df: DataFrame to enrich
            column: Column name that might contain IDs
            entity_type: 'product' or 'customer'
        
        Returns:
            Tuple of (enriched_df, display_column_name)
        """
        df = df.copy()
        lookup = self._product_id_to_name if entity_type == 'product' else self._customer_id_to_name
        
        if not lookup:
            return df, column
        
        # Check if the column contains IDs by seeing if values exist in lookup
        sample_values = df[column].dropna().astype(str).head(20).tolist()
        matches = sum(1 for v in sample_values if v in lookup)
        
        if matches >= len(sample_values) * 0.3:  # At least 30% match = likely IDs
            # Create a new column with names
            name_col = f'{entity_type.title()} Name'
            df[name_col] = df[column].astype(str).map(lookup).fillna(df[column])
            return df, name_col
        
        return df, column
    
    def _find_best_display_column(self, df, entity_type='product'):
        """Find the best column to display for an entity (name over ID)
        
        Args:
            df: DataFrame to search
            entity_type: 'product', 'customer', 'city', etc.
        
        Returns:
            Column name or None
        """
        cols = df.columns.tolist()
        
        if entity_type == 'product':
            # Priority: product_name > lineitem_name > item_name > product > item > sku > product_id
            name_patterns = [
                ('product_name', True), ('product name', True), ('lineitem_name', True),
                ('item_name', True), ('product_title', True), ('product', False),
                ('item', False), ('sku', False)
            ]
            exclude_patterns = ['customer', 'id', 'quantity', 'price', 'amount']
            
            for pattern, exact in name_patterns:
                for col in cols:
                    col_lower = col.lower().replace('_', ' ').strip()
                    if exact:
                        if col_lower == pattern.replace('_', ' '):
                            return col
                    else:
                        if pattern in col_lower and not any(ex in col_lower for ex in exclude_patterns):
                            return col
            
            # Last resort: if there's product_id, try to enrich it
            for col in cols:
                if 'product_id' in col.lower() or 'product id' in col.lower():
                    return col  # Will be enriched later
                    
        elif entity_type == 'customer':
            # Priority: customer_name > name > customer > customer_id
            name_patterns = [
                ('customer_name', True), ('customer name', True), ('buyer_name', True),
                ('full_name', True), ('name', False), ('customer', False)
            ]
            exclude_patterns = ['product', 'id', 'email', 'phone', 'address']
            
            for pattern, exact in name_patterns:
                for col in cols:
                    col_lower = col.lower().replace('_', ' ').strip()
                    if exact:
                        if col_lower == pattern.replace('_', ' '):
                            return col
                    else:
                        if pattern in col_lower and not any(ex in col_lower for ex in exclude_patterns):
                            return col
            
            # Last resort: customer_id
            for col in cols:
                if 'customer_id' in col.lower() or 'customer id' in col.lower():
                    return col
        
        return None
    
    def has_data(self, dtype='orders'):
        return len(st.session_state.data_store.get(dtype, [])) > 0
    
    def _no_data_response(self, data_type, analysis_type):
        """Generate helpful response when data is not available"""
        data_labels = {
            'orders': '📦 Orders',
            'customers': '👥 Customers', 
            'products': '🛍️ Products',
            'inventory': '📊 Inventory',
            'ads_meta': '📘 Meta Ads',
            'ads_google': '🔍 Google Ads',
            'ads_shopify': '🛒 Shopify Ads'
        }
        
        available_data = []
        for dtype, label in data_labels.items():
            if self.has_data(dtype):
                count = len(st.session_state.data_store.get(dtype, []))
                available_data.append(f"- {label}: {count:,} records")
        
        available_str = '\n'.join(available_data) if available_data else "- No data uploaded yet"
        
        return {
            'content': f"""## ℹ️ {analysis_type.title()} Not Available

❌ **{data_labels.get(data_type, data_type)} data is required** for this analysis but is not currently loaded.

### 📁 Your Current Data:
{available_str}

### 💡 How to Add Data:
1. Go to **Data Manager** in the sidebar
2. Click **Add More Data**
3. Upload your {data_type} file (CSV or Excel)

Once uploaded, come back and ask your question again!""",
            'charts': [],
            'tables': []
        }
    
    def _column_not_found_response(self, column_type, df, suggestion=None):
        """Generate helpful response when a column is not found"""
        available_cols = ', '.join(df.columns[:20].tolist())
        if len(df.columns) > 20:
            available_cols += f"... and {len(df.columns) - 20} more"
        
        tip = suggestion if suggestion else f"Check if your data has a column for {column_type}"
        
        return {
            'content': f"""## ⚠️ Column Not Found

❌ **Could not find a {column_type} column** in your data.

### 📋 Available Columns:
{available_cols}

### 💡 Tip:
{tip}

You can also go to **Settings** to manually map your columns.""",
            'charts': [],
            'tables': []
        }
    
    def get_orders_with_helpers(self):
        """Get orders with calculated helper columns"""
        if not self.has_data('orders'):
            return pd.DataFrame()
        
        df = self.orders.copy()
        status_col = self.order_mappings.get('order_status')
        payment_col = self.order_mappings.get('payment_method')
        
        if status_col and status_col in df.columns:
            df['_status'] = df[status_col].astype(str).str.lower()
            df['_is_delivered'] = df['_status'].str.contains('deliver|complete|success', na=False)
            df['_is_rto'] = df['_status'].str.contains('rto|return', na=False)
            df['_is_pending'] = df['_status'].str.contains('pending|process|transit', na=False)
        
        if payment_col and payment_col in df.columns:
            df['_is_cod'] = df[payment_col].astype(str).str.lower().str.contains('cod|cash', na=False)
            df['_is_prepaid'] = ~df['_is_cod']
        
        return df
    
    def analyze_query(self, query):
        """Analyze query intent and extract parameters"""
        query_lower = query.lower()
        
        # Detect intent
        intents = {
            'revenue': ['revenue', 'sales', 'income', 'earning', 'money', 'total amount'],
            'orders': ['order', 'transaction', 'purchase'],
            'rto': ['rto', 'return', 'returned', 'rto rate'],
            'cod': ['cod', 'cash on delivery', 'cash payment'],
            'prepaid': ['prepaid', 'online payment', 'paid online'],
            'products': ['product', 'item', 'sku', 'best selling', 'top product'],
            'customers': ['customer', 'buyer', 'client', 'user'],
            'inventory': ['inventory', 'stock', 'available', 'warehouse'],
            'payment': ['payment', 'payment method', 'payment type'],
            'status': ['status', 'delivery status', 'order status'],
            'city': ['city', 'location', 'region', 'area', 'geographic'],
            'state': ['state', 'province'],
            'category': ['category', 'categories'],
            'trend': ['trend', 'over time', 'daily', 'weekly', 'monthly', 'growth'],
            'compare': ['compare', 'vs', 'versus', 'comparison'],
            'top': ['top', 'best', 'highest', 'most'],
            'bottom': ['bottom', 'worst', 'lowest', 'least'],
            'average': ['average', 'avg', 'mean', 'aov'],
            'summary': ['summary', 'overview', 'dashboard', 'all data'],
            'breakdown': ['breakdown', 'break down', 'split', 'by', 'segment', 'group'],
            # Ads intents
            'ads': ['ad', 'ads', 'advertising', 'campaign', 'marketing'],
            'meta_ads': ['meta', 'facebook', 'instagram', 'fb ads'],
            'google_ads': ['google ads', 'google', 'search ads', 'ppc'],
            'spend': ['spend', 'cost', 'budget', 'ad spend', 'advertising cost'],
            'roas': ['roas', 'return on ad spend', 'ad return'],
            'ctr': ['ctr', 'click through', 'click rate'],
            'cpc': ['cpc', 'cost per click'],
            'cpa': ['cpa', 'cost per acquisition', 'cost per conversion'],
            'impressions': ['impression', 'views', 'reach'],
            'conversions': ['conversion', 'converted', 'purchase from ad']
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(kw in query_lower for kw in keywords):
                detected_intents.append(intent)
        
        # Detect time filters
        time_filter = None
        if 'today' in query_lower:
            time_filter = 'today'
        elif 'yesterday' in query_lower:
            time_filter = 'yesterday'
        elif 'this week' in query_lower or 'week' in query_lower:
            time_filter = 'week'
        elif 'this month' in query_lower or 'month' in query_lower:
            time_filter = 'month'
        elif 'last 7 days' in query_lower:
            time_filter = '7days'
        elif 'last 30 days' in query_lower:
            time_filter = '30days'
        
        # Detect number
        numbers = re.findall(r'\d+', query)
        limit = int(numbers[0]) if numbers else 10
        
        return {
            'intents': detected_intents,
            'time_filter': time_filter,
            'limit': limit,
            'raw_query': query
        }
    
    def process_query(self, query):
        """Process query and return response with visualization"""
        analysis = self.analyze_query(query)
        intents = analysis['intents']
        
        if not intents:
            return self.general_response()
        
        # Route to appropriate handler - check for ads and breakdown queries first
        if any(intent in intents for intent in ['ads', 'meta_ads', 'google_ads', 'spend', 'roas', 'ctr', 'cpc', 'cpa', 'impressions', 'conversions']):
            return self.get_ads_analysis(analysis)
        elif 'breakdown' in intents:
            return self.get_breakdown_analysis(analysis)
        elif 'summary' in intents:
            return self.get_summary()
        elif 'revenue' in intents and 'trend' in intents:
            return self.get_revenue_trend(analysis)
        elif 'revenue' in intents and 'city' in intents:
            return self.get_breakdown_analysis(analysis)  # Revenue by city
        elif 'revenue' in intents:
            return self.get_revenue_analysis(analysis)
        elif 'rto' in intents:
            return self.get_rto_analysis(analysis)
        elif 'cod' in intents or 'prepaid' in intents:
            return self.get_payment_analysis(analysis)
        elif 'products' in intents and ('top' in intents or 'best' in intents):
            return self.get_top_products(analysis)
        elif 'products' in intents:
            return self.get_product_analysis(analysis)
        elif 'customers' in intents and 'top' in intents:
            return self.get_top_customers(analysis)
        elif 'customers' in intents:
            return self.get_customer_analysis(analysis)
        elif 'inventory' in intents:
            return self.get_inventory_analysis(analysis)
        elif 'city' in intents:
            return self.get_city_analysis(analysis)
        elif 'state' in intents:
            return self.get_state_analysis(analysis)
        elif 'category' in intents:
            return self.get_category_analysis(analysis)
        elif 'payment' in intents:
            return self.get_payment_breakdown(analysis)
        elif 'status' in intents:
            return self.get_status_analysis(analysis)
        elif 'trend' in intents:
            return self.get_orders_trend(analysis)
        elif 'orders' in intents:
            return self.get_orders_analysis(analysis)
        else:
            return self.general_response()
    
    def get_breakdown_analysis(self, analysis):
        """Handle breakdown queries like 'breakdown sales by city' with ID-to-name enrichment"""
        if not self.has_data('orders'):
            return self._no_data_response('orders', 'breakdown analysis')
        
        df = self.get_orders_with_helpers()
        amount_col = self.order_mappings.get('total_amount')
        intents = analysis['intents']
        limit = analysis.get('limit', 15)
        
        # Auto-detect amount column
        if not amount_col or amount_col not in df.columns:
            amount_patterns = ['amount', 'total', 'price', 'revenue', 'value', 'subtotal']
            for col in df.columns:
                if any(p in col.lower() for p in amount_patterns):
                    try:
                        if pd.to_numeric(df[col], errors='coerce').notna().sum() > 0:
                            amount_col = col
                            break
                    except:
                        pass
        
        # Determine what dimension to break down by
        dimension = None
        dimension_col = None
        entity_type = None  # For enrichment
        
        # Auto-detect patterns for each dimension
        dimension_patterns = {
            'city': (['city', 'location', 'shipping_city', 'billing_city', 'town'], 'City', None),
            'state': (['state', 'region', 'province', 'shipping_state', 'billing_state'], 'State', None),
            'category': (['category', 'product_category', 'type', 'product_type'], 'Category', None),
            'products': (['product', 'item', 'sku', 'product_name', 'item_name', 'lineitem_name'], 'Product', 'product'),
            'payment': (['payment', 'payment_method', 'pay_method', 'gateway'], 'Payment Method', None),
            'status': (['status', 'order_status', 'fulfillment', 'delivery_status'], 'Status', None),
            'customers': (['customer', 'customer_name', 'buyer', 'client'], 'Customer', 'customer')
        }
        
        for intent_key, (patterns, dim_name, enrich_type) in dimension_patterns.items():
            if intent_key in intents:
                dimension = dim_name
                entity_type = enrich_type
                # First try mapped column
                mapped_col = self.order_mappings.get(intent_key) or self.order_mappings.get(intent_key.rstrip('s'))
                if mapped_col and mapped_col in df.columns:
                    dimension_col = mapped_col
                else:
                    # Use helper for product/customer to find best display column
                    if enrich_type:
                        dimension_col = self._find_best_display_column(df, enrich_type)
                    
                    # Fallback: Auto-detect
                    if not dimension_col:
                        for col in df.columns:
                            if any(p in col.lower() for p in patterns):
                                dimension_col = col
                                break
                break
        
        # If still no dimension, try to extract from query
        if not dimension_col:
            query_lower = analysis['raw_query'].lower()
            for col in df.columns:
                col_lower = col.lower().replace('_', ' ')
                if col_lower in query_lower or any(word in col_lower for word in query_lower.split()):
                    dimension_col = col
                    dimension = col.replace('_', ' ').title()
                    break
        
        if not dimension_col or dimension_col not in df.columns:
            available_cols = ', '.join(df.columns[:15].tolist())
            return {
                'content': f"""## ⚠️ Could Not Determine Breakdown Dimension

I couldn't identify which column to use for the breakdown.

**Available columns:** {available_cols}

💡 **Try asking more specifically**, like:
- "Show revenue by city"
- "Breakdown orders by payment method"
- "Sales by category"
- "Orders by status" """,
                'charts': [], 
                'tables': []
            }
        
        # Get delivered orders for revenue calculation
        if '_is_delivered' in df.columns:
            delivered = df[df['_is_delivered']]
            if len(delivered) == 0:
                delivered = df
        else:
            delivered = df
        
        # Enrich IDs with names if applicable
        display_col = dimension_col
        if entity_type:
            delivered, display_col = self._enrich_with_names(delivered, dimension_col, entity_type)
        
        try:
            # Create breakdown using named aggregation to avoid duplicate column issues
            if amount_col and amount_col in df.columns:
                delivered = delivered.copy()
                delivered[amount_col] = pd.to_numeric(delivered[amount_col], errors='coerce').fillna(0)
                
                breakdown = delivered.groupby(display_col, as_index=False).agg(
                    **{'Total Revenue': (amount_col, 'sum'),
                       'Avg Order Value': (amount_col, 'mean'),
                       'Order Count': (amount_col, 'count')}
                )
                breakdown = breakdown.rename(columns={display_col: dimension})
                breakdown = breakdown.sort_values('Total Revenue', ascending=False).head(limit)
                
                # Calculate percentages
                total_revenue = breakdown['Total Revenue'].sum()
                breakdown['% of Revenue'] = (breakdown['Total Revenue'] / total_revenue * 100).round(1)
                
                # Format for display
                breakdown_display = breakdown.copy()
                breakdown_display['Total Revenue'] = breakdown_display['Total Revenue'].apply(format_inr)
                breakdown_display['Avg Order Value'] = breakdown_display['Avg Order Value'].apply(format_inr)
            else:
                breakdown = delivered[display_col].value_counts().head(limit).reset_index()
                breakdown.columns = [dimension, 'Order Count']
                breakdown['% of Orders'] = (breakdown['Order Count'] / breakdown['Order Count'].sum() * 100).round(1)
                breakdown_display = breakdown.copy()
                total_revenue = 0
            
            response = f"""## 📊 Sales Breakdown by {dimension}

### Top {len(breakdown)} {dimension}s by {'Revenue' if amount_col and amount_col in df.columns else 'Orders'}

"""
            
            if amount_col and amount_col in df.columns:
                response += f"**Total Revenue Analyzed:** {format_inr(total_revenue)}\n\n"
            
            # Create visualization
            charts = []
            
            # Bar chart
            fig = px.bar(
                breakdown.head(15), 
                x=dimension, 
                y='Total Revenue' if 'Total Revenue' in breakdown.columns else 'Order Count',
                title=f'Sales by {dimension}',
                color='Total Revenue' if 'Total Revenue' in breakdown.columns else 'Order Count',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            charts.append(fig)
            
            # Pie chart for top 10
            if len(breakdown) > 1:
                pie_data = breakdown.head(10).copy()
                fig2 = px.pie(
                    pie_data, 
                    values='Total Revenue' if 'Total Revenue' in breakdown.columns else 'Order Count',
                    names=dimension,
                    title=f'Top 10 {dimension}s Distribution',
                    hole=0.4,
                    color_discrete_sequence=get_colors()
                )
                fig2.update_layout(height=400)
                charts.append(fig2)
            
            return {'content': response, 'charts': charts, 'tables': [breakdown_display]}
            
        except Exception as e:
            return {
                'content': f"## ⚠️ Error in Breakdown Analysis\n\nCould not complete the analysis: {str(e)}\n\n💡 Please check your data format.",
                'charts': [],
                'tables': []
            }
    
    def get_state_analysis(self, analysis):
        """State-wise analysis"""
        if not self.has_data('orders'):
            return self._no_data_response('orders', 'state analysis')
        
        df = self.get_orders_with_helpers()
        state_col = self.order_mappings.get('state')
        amount_col = self.order_mappings.get('total_amount')
        
        # Auto-detect state column
        if not state_col or state_col not in df.columns:
            state_patterns = ['state', 'region', 'province', 'shipping_state', 'billing_state']
            for col in df.columns:
                if any(p in col.lower() for p in state_patterns):
                    state_col = col
                    break
        
        if not state_col or state_col not in df.columns:
            return self._column_not_found_response('state/region', df, "Check if your data has a state or region column")
        
        # Use all orders if delivered is empty
        if '_is_delivered' in df.columns:
            delivered = df[df['_is_delivered']]
            if len(delivered) == 0:
                delivered = df
        else:
            delivered = df
        
        try:
            if amount_col and amount_col in df.columns:
                delivered = delivered.copy()
                delivered[amount_col] = pd.to_numeric(delivered[amount_col], errors='coerce').fillna(0)
                
                state_data = delivered.groupby(state_col, as_index=False).agg(
                    Revenue=(amount_col, 'sum'),
                    Orders=(amount_col, 'count'),
                    AOV=(amount_col, 'mean')
                )
                state_data = state_data.rename(columns={state_col: 'State'})
                state_data = state_data.sort_values('Revenue', ascending=False)
            else:
                state_data = delivered[state_col].value_counts().reset_index()
                state_data.columns = ['State', 'Orders']
            
            response = f"""## 🗺️ State-wise Analysis

### Overview
- **States with orders:** {len(state_data)}
"""
            
            fig = px.bar(state_data.head(15), x='State', y='Revenue' if 'Revenue' in state_data.columns else 'Orders',
                        title='Sales by State', color='Revenue' if 'Revenue' in state_data.columns else 'Orders',
                        color_continuous_scale='Viridis')
            fig.update_layout(height=400, xaxis_tickangle=-45)
            
            display_data = state_data.head(15).copy()
            if 'Revenue' in display_data.columns:
                display_data['Revenue'] = display_data['Revenue'].apply(format_inr)
                display_data['AOV'] = display_data['AOV'].apply(format_inr)
            
            return {'content': response, 'charts': [fig], 'tables': [display_data]}
            
        except Exception as e:
            return {
                'content': f"## ⚠️ Error in State Analysis\n\nCould not complete the analysis: {str(e)}",
                'charts': [],
                'tables': []
            }
    
    def get_category_analysis(self, analysis):
        """Category-wise analysis"""
        if not self.has_data('orders'):
            return self._no_data_response('orders', 'category analysis')
        
        df = self.get_orders_with_helpers()
        category_col = self.order_mappings.get('category')
        amount_col = self.order_mappings.get('total_amount')
        
        # Auto-detect category column
        if not category_col or category_col not in df.columns:
            cat_patterns = ['category', 'product_category', 'type', 'product_type', 'item_type']
            for col in df.columns:
                if any(p in col.lower() for p in cat_patterns):
                    category_col = col
                    break
        
        if not category_col or category_col not in df.columns:
            return self._column_not_found_response('category', df, "Check if your data has a category or product_type column")
        
        # Use all orders if delivered is empty
        if '_is_delivered' in df.columns:
            delivered = df[df['_is_delivered']]
            if len(delivered) == 0:
                delivered = df
        else:
            delivered = df
        
        try:
            if amount_col and amount_col in df.columns:
                delivered = delivered.copy()
                delivered[amount_col] = pd.to_numeric(delivered[amount_col], errors='coerce').fillna(0)
                
                cat_data = delivered.groupby(category_col, as_index=False).agg(
                    Revenue=(amount_col, 'sum'),
                    Orders=(amount_col, 'count'),
                    AOV=(amount_col, 'mean')
                )
                cat_data = cat_data.rename(columns={category_col: 'Category'})
                cat_data = cat_data.sort_values('Revenue', ascending=False)
            else:
                cat_data = delivered[category_col].value_counts().reset_index()
                cat_data.columns = ['Category', 'Orders']
            
            response = f"""## 📂 Category Analysis

### Overview
- **Total Categories:** {len(cat_data)}
"""
            
            charts = []
            
            # Bar chart
            fig = px.bar(cat_data, x='Category', y='Revenue' if 'Revenue' in cat_data.columns else 'Orders',
                        title='Sales by Category', color='Revenue' if 'Revenue' in cat_data.columns else 'Orders',
                        color_continuous_scale='Viridis')
            fig.update_layout(height=400)
            charts.append(fig)
            
            # Pie chart
            fig2 = px.pie(cat_data, values='Revenue' if 'Revenue' in cat_data.columns else 'Orders',
                         names='Category', title='Category Distribution', hole=0.4,
                         color_discrete_sequence=get_colors())
            fig2.update_layout(height=400)
            charts.append(fig2)
            
            display_data = cat_data.copy()
            if 'Revenue' in display_data.columns:
                display_data['Revenue'] = display_data['Revenue'].apply(format_inr)
                display_data['AOV'] = display_data['AOV'].apply(format_inr)
            
            return {'content': response, 'charts': charts, 'tables': [display_data]}
            
        except Exception as e:
            return {
                'content': f"## ⚠️ Error in Category Analysis\n\nCould not complete the analysis: {str(e)}",
                'charts': [],
                'tables': []
            }
    
    def get_summary(self):
        """Get complete data summary"""
        response = "## 📊 Complete Data Summary\n\n"
        charts = []
        tables = []
        
        # Orders summary
        if self.has_data('orders'):
            df = self.get_orders_with_helpers()
            amount_col = self.order_mappings.get('total_amount')
            
            delivered = df[df['_is_delivered']] if '_is_delivered' in df.columns else df
            rto = df[df['_is_rto']] if '_is_rto' in df.columns else pd.DataFrame()
            
            response += "### 📦 Orders\n"
            response += f"- **Total Orders:** {len(df):,}\n"
            response += f"- **Delivered:** {len(delivered):,}\n"
            response += f"- **RTO:** {len(rto):,}\n"
            
            if amount_col and amount_col in df.columns:
                revenue = delivered[amount_col].sum()
                aov = delivered[amount_col].mean()
                response += f"- **Revenue:** {format_inr(revenue)}\n"
                response += f"- **AOV:** {format_inr(aov)}\n"
            
            rto_base = len(delivered) + len(rto)
            rto_rate = (len(rto) / rto_base * 100) if rto_base > 0 else 0
            response += f"- **RTO Rate:** {rto_rate:.1f}%\n\n"
            
            # Create pie chart
            status_col = self.order_mappings.get('order_status')
            if status_col and status_col in df.columns:
                status_dist = df[status_col].value_counts().reset_index()
                status_dist.columns = ['Status', 'Count']
                fig = px.pie(status_dist, values='Count', names='Status', 
                            title='Order Status Distribution', hole=0.4,
                            color_discrete_sequence=get_colors())
                charts.append(fig)
        
        # Customers summary
        if self.has_data('customers'):
            response += f"### 👥 Customers\n"
            response += f"- **Total Customers:** {len(self.customers):,}\n\n"
        
        # Products summary
        if self.has_data('products'):
            response += f"### 🏷️ Products\n"
            response += f"- **Total Products:** {len(self.products):,}\n\n"
        
        # Inventory summary
        if self.has_data('inventory'):
            qty_col = self.inventory_mappings.get('quantity')
            response += f"### 📊 Inventory\n"
            response += f"- **Total SKUs:** {len(self.inventory):,}\n"
            if qty_col and qty_col in self.inventory.columns:
                response += f"- **Total Stock:** {self.inventory[qty_col].sum():,}\n"
                response += f"- **Low Stock Items:** {(self.inventory[qty_col] < 10).sum():,}\n\n"
        
        return {'content': response, 'charts': charts, 'tables': tables}
    
    def get_revenue_analysis(self, analysis):
        """Revenue analysis"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        amount_col = self.order_mappings.get('total_amount')
        
        if not amount_col or amount_col not in df.columns:
            return {'content': "❌ Amount column not found in orders", 'charts': [], 'tables': []}
        
        delivered = df[df['_is_delivered']] if '_is_delivered' in df.columns else df
        
        revenue = delivered[amount_col].sum()
        aov = delivered[amount_col].mean()
        max_order = delivered[amount_col].max()
        min_order = delivered[amount_col].min()
        
        response = f"""## 💰 Revenue Analysis

### Key Metrics
| Metric | Value |
|--------|-------|
| **Total Revenue** | {format_inr(revenue)} |
| **Average Order Value** | {format_inr(aov)} |
| **Highest Order** | {format_inr(max_order)} |
| **Lowest Order** | {format_inr(min_order)} |
| **Delivered Orders** | {len(delivered):,} |

> 💡 Revenue is calculated from **delivered orders only** to give accurate business performance.
"""
        
        # Revenue by payment method chart
        charts = []
        payment_col = self.order_mappings.get('payment_method')
        if payment_col and payment_col in df.columns:
            rev_by_payment = delivered.groupby(payment_col)[amount_col].sum().reset_index()
            rev_by_payment.columns = ['Payment Method', 'Revenue']
            rev_by_payment = rev_by_payment.sort_values('Revenue', ascending=False)
            
            fig = px.bar(rev_by_payment, x='Payment Method', y='Revenue',
                        title='Revenue by Payment Method',
                        color='Revenue', color_continuous_scale='Viridis')
            fig.update_layout(height=400)
            charts.append(fig)
        
        return {'content': response, 'charts': charts, 'tables': []}
    
    def get_revenue_trend(self, analysis):
        """Revenue trend over time"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        amount_col = self.order_mappings.get('total_amount')
        date_col = self.order_mappings.get('order_date')
        
        if not date_col or date_col not in df.columns:
            return {'content': "❌ Date column not found", 'charts': [], 'tables': []}
        
        delivered = df[df['_is_delivered']] if '_is_delivered' in df.columns else df
        
        temp = delivered.copy()
        temp['_date'] = pd.to_datetime(temp[date_col], dayfirst=True, errors='coerce')
        temp = temp.dropna(subset=['_date'])
        
        daily = temp.groupby(temp['_date'].dt.date)[amount_col].sum().reset_index()
        daily.columns = ['Date', 'Revenue']
        
        response = f"""## 📈 Revenue Trend

### Daily Revenue Statistics
- **Average Daily Revenue:** {format_inr(daily['Revenue'].mean())}
- **Best Day:** {format_inr(daily['Revenue'].max())}
- **Total Days:** {len(daily)}
"""
        
        fig = px.line(daily, x='Date', y='Revenue', title='Daily Revenue Trend',
                     markers=True, color_discrete_sequence=['#6366f1'])
        fig.update_layout(height=400)
        
        # Add trend line
        fig.add_trace(go.Scatter(
            x=daily['Date'], y=daily['Revenue'].rolling(7).mean(),
            mode='lines', name='7-day Moving Avg',
            line=dict(dash='dash', color='#ef4444')
        ))
        
        return {'content': response, 'charts': [fig], 'tables': []}
    
    def get_rto_analysis(self, analysis):
        """RTO analysis"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        
        if '_is_rto' not in df.columns:
            return {'content': "❌ Status column not found for RTO analysis", 'charts': [], 'tables': []}
        
        delivered = df[df['_is_delivered']]
        rto = df[df['_is_rto']]
        
        rto_base = len(delivered) + len(rto)
        rto_rate = (len(rto) / rto_base * 100) if rto_base > 0 else 0
        
        response = f"""## 🔄 RTO Analysis

### Overview
| Metric | Value |
|--------|-------|
| **RTO Rate** | {rto_rate:.1f}% |
| **RTO Orders** | {len(rto):,} |
| **Delivered Orders** | {len(delivered):,} |
| **RTO Base** | {rto_base:,} |

> 📊 **Formula:** RTO Rate = RTO / (Delivered + RTO) × 100
"""
        
        charts = []
        
        # RTO by payment method
        payment_col = self.order_mappings.get('payment_method')
        if payment_col and payment_col in df.columns:
            rto_by_payment = []
            for payment in df[payment_col].unique():
                p_df = df[df[payment_col] == payment]
                p_del = p_df[p_df['_is_delivered']]
                p_rto = p_df[p_df['_is_rto']]
                p_base = len(p_del) + len(p_rto)
                p_rate = (len(p_rto) / p_base * 100) if p_base > 0 else 0
                rto_by_payment.append({
                    'Payment Method': payment,
                    'RTO Rate': p_rate,
                    'RTO Orders': len(p_rto),
                    'Total': p_base
                })
            
            rto_df = pd.DataFrame(rto_by_payment)
            
            fig = px.bar(rto_df, x='Payment Method', y='RTO Rate',
                        title='RTO Rate by Payment Method',
                        color='RTO Rate', color_continuous_scale='Reds')
            fig.update_layout(height=400)
            charts.append(fig)
            
            response += "\n### RTO by Payment Method\n"
            response += f"- **COD RTO Rate:** {rto_df[rto_df['Payment Method'].str.lower().str.contains('cod|cash')]['RTO Rate'].mean():.1f}%" if len(rto_df[rto_df['Payment Method'].str.lower().str.contains('cod|cash')]) > 0 else ""
            response += f"\n- **Prepaid RTO Rate:** {rto_df[~rto_df['Payment Method'].str.lower().str.contains('cod|cash')]['RTO Rate'].mean():.1f}%" if len(rto_df[~rto_df['Payment Method'].str.lower().str.contains('cod|cash')]) > 0 else ""
        
        return {'content': response, 'charts': charts, 'tables': []}
    
    def get_payment_analysis(self, analysis):
        """COD vs Prepaid analysis"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        
        if '_is_cod' not in df.columns:
            return {'content': "❌ Payment method column not found", 'charts': [], 'tables': []}
        
        cod = df[df['_is_cod']]
        prepaid = df[df['_is_prepaid']]
        amount_col = self.order_mappings.get('total_amount')
        
        response = f"""## 💳 COD vs Prepaid Analysis

### Order Distribution
| Type | Orders | Percentage |
|------|--------|------------|
| **COD** | {len(cod):,} | {len(cod)/len(df)*100:.1f}% |
| **Prepaid** | {len(prepaid):,} | {len(prepaid)/len(df)*100:.1f}% |
"""
        
        if amount_col and amount_col in df.columns:
            cod_rev = cod[cod['_is_delivered']][amount_col].sum() if '_is_delivered' in df.columns else cod[amount_col].sum()
            prepaid_rev = prepaid[prepaid['_is_delivered']][amount_col].sum() if '_is_delivered' in df.columns else prepaid[amount_col].sum()
            
            response += f"""
### Revenue Distribution
| Type | Revenue | Percentage |
|------|---------|------------|
| **COD** | {format_inr(cod_rev)} | {cod_rev/(cod_rev+prepaid_rev)*100:.1f}% |
| **Prepaid** | {format_inr(prepaid_rev)} | {prepaid_rev/(cod_rev+prepaid_rev)*100:.1f}% |
"""
        
        # Pie chart
        data = pd.DataFrame({
            'Type': ['COD', 'Prepaid'],
            'Orders': [len(cod), len(prepaid)]
        })
        
        fig = px.pie(data, values='Orders', names='Type',
                    title='COD vs Prepaid Distribution', hole=0.4,
                    color_discrete_sequence=['#f59e0b', '#6366f1'])
        fig.update_layout(height=400)
        
        return {'content': response, 'charts': [fig], 'tables': []}
    
    def get_top_products(self, analysis):
        """Top products analysis with ID-to-name enrichment"""
        limit = analysis.get('limit', 10)
        
        if self.has_data('orders'):
            df = self.get_orders_with_helpers()
            product_col = self.order_mappings.get('product_name')
            amount_col = self.order_mappings.get('total_amount')
            
            # Use helper to find best product display column
            if not product_col or product_col not in df.columns:
                product_col = self._find_best_display_column(df, 'product')
            
            # If still not found, look for ID columns as last resort
            if not product_col or product_col not in df.columns:
                for col in df.columns:
                    col_lower = col.lower()
                    if 'product_id' in col_lower or (col_lower == 'product' and 'name' not in col_lower):
                        product_col = col
                        break
            
            # Auto-detect amount column if not mapped
            if not amount_col or amount_col not in df.columns:
                amount_patterns = ['total_amount', 'total amount', 'amount', 'total', 'grand_total', 
                                   'subtotal', 'total_price', 'order_value', 'revenue', 'price']
                for col in df.columns:
                    col_lower = col.lower().replace('_', ' ').strip()
                    if col_lower in [p.replace('_', ' ') for p in amount_patterns]:
                        try:
                            test_numeric = pd.to_numeric(df[col], errors='coerce')
                            if test_numeric.notna().sum() > 0:
                                amount_col = col
                                break
                        except:
                            pass
            
            if not product_col or product_col not in df.columns:
                available_cols = ', '.join(df.columns.tolist()[:20])
                return {
                    'content': f"""## ⚠️ Product Column Not Found

❌ **Could not identify a product column** in your orders data.

**Your columns:** {available_cols}

### 💡 How to Fix:
1. Go to **Data Manager** → **Column Mapping**
2. Map your product column manually
3. Or rename your product column to include 'product' or 'item'

**Expected column names:** product_name, item_name, product, item, sku_name""",
                    'charts': [], 
                    'tables': []
                }
            
            # Use all orders if delivered filter results in empty or no status column
            if '_is_delivered' in df.columns:
                delivered = df[df['_is_delivered']]
                if len(delivered) == 0:
                    delivered = df
            else:
                delivered = df
            
            # Enrich product IDs with names if possible
            delivered, display_col = self._enrich_with_names(delivered, product_col, 'product')
            
            if amount_col and amount_col in df.columns:
                delivered = delivered.copy()
                delivered[amount_col] = pd.to_numeric(delivered[amount_col], errors='coerce').fillna(0)
                
                # Group by the display column (enriched name or original)
                products = delivered.groupby(display_col, as_index=False).agg(
                    Revenue=(amount_col, 'sum'),
                    Orders=(amount_col, 'count')
                )
                products = products.rename(columns={display_col: 'Product'})
                products = products.nlargest(limit, 'Revenue')
                
                total_revenue = products['Revenue'].sum()
                
                response = f"""## 🏆 Top {limit} Products by Revenue

| Rank | Product | Revenue | Orders |
|------|---------|---------|--------|
"""
                for idx, row in enumerate(products.itertuples(), 1):
                    prod_name = str(row.Product)[:50] + ('...' if len(str(row.Product)) > 50 else '')
                    response += f"| {idx} | {prod_name} | {format_inr(row.Revenue)} | {int(row.Orders):,} |\n"
                
                response += f"\n**Total Revenue from Top {limit}:** {format_inr(total_revenue)}"
            else:
                products = delivered[display_col].value_counts().head(limit).reset_index()
                products.columns = ['Product', 'Orders']
                
                response = f"""## 🏆 Top {limit} Products by Order Count

| Rank | Product | Orders |
|------|---------|--------|
"""
                for i, row in enumerate(products.itertuples(), 1):
                    response += f"| {i} | {str(row.Product)[:50]}{'...' if len(str(row.Product)) > 50 else ''} | {int(row.Orders):,} |\n"
            
            fig = px.bar(products, x='Product', y='Revenue' if 'Revenue' in products.columns else 'Orders',
                        title=f'Top {limit} Products',
                        color='Revenue' if 'Revenue' in products.columns else 'Orders',
                        color_continuous_scale='Viridis')
            fig.update_layout(height=400, xaxis_tickangle=-45)
            
            return {'content': response, 'charts': [fig], 'tables': [products]}
        
        return {'content': "❌ No orders data available. Please upload your orders data first.", 'charts': [], 'tables': []}
    
    def get_product_analysis(self, analysis):
        """General product analysis"""
        if self.has_data('products'):
            df = self.products.copy()
            category_col = self.product_mappings.get('category')
            price_col = self.product_mappings.get('price')
            
            response = f"""## 🏷️ Product Analysis

### Overview
- **Total Products:** {len(df):,}
"""
            
            charts = []
            
            if category_col and category_col in df.columns:
                response += f"- **Categories:** {df[category_col].nunique():,}\n"
                
                cat_dist = df[category_col].value_counts().reset_index()
                cat_dist.columns = ['Category', 'Products']
                
                fig = px.pie(cat_dist, values='Products', names='Category',
                            title='Products by Category', hole=0.4,
                            color_discrete_sequence=get_colors())
                fig.update_layout(height=400)
                charts.append(fig)
            
            if price_col and price_col in df.columns:
                response += f"- **Average Price:** {format_inr(df[price_col].mean())}\n"
                response += f"- **Price Range:** {format_inr(df[price_col].min())} - {format_inr(df[price_col].max())}\n"
            
            return {'content': response, 'charts': charts, 'tables': []}
        
        return self.get_top_products(analysis)
    
    def get_top_customers(self, analysis):
        """Top customers analysis with ID-to-name enrichment"""
        limit = analysis.get('limit', 10)
        
        if self.has_data('customers'):
            df = self.customers.copy()
            spent_col = self.customer_mappings.get('total_spent')
            name_col = self.customer_mappings.get('name')
            
            # Auto-detect name column
            if not name_col or name_col not in df.columns:
                name_col = self._find_best_display_column(df, 'customer')
            
            if spent_col and spent_col in df.columns and name_col and name_col in df.columns:
                top = df.nlargest(limit, spent_col)[[name_col, spent_col]].copy()
                top.columns = ['Customer', 'Total Spent']
                
                fig = px.bar(top, x='Customer', y='Total Spent',
                            title=f'Top {limit} Customers by Lifetime Value',
                            color='Total Spent', color_continuous_scale='Purples')
                fig.update_layout(height=400)
                
                response = f"## 🏆 Top {limit} Customers\n\nRanked by total lifetime value:"
                
                return {'content': response, 'charts': [fig], 'tables': [top]}
        
        # Try from orders
        if self.has_data('orders'):
            df = self.get_orders_with_helpers()
            name_col = self.order_mappings.get('customer_name')
            amount_col = self.order_mappings.get('total_amount')
            
            # Auto-detect customer column
            if not name_col or name_col not in df.columns:
                name_col = self._find_best_display_column(df, 'customer')
            
            # If still not found, check for ID column as last resort
            if not name_col or name_col not in df.columns:
                for col in df.columns:
                    col_lower = col.lower()
                    if 'customer_id' in col_lower:
                        name_col = col
                        break
            
            if name_col and name_col in df.columns and amount_col:
                delivered = df[df['_is_delivered']] if '_is_delivered' in df.columns else df
                
                # Enrich customer IDs with names if possible
                delivered, display_col = self._enrich_with_names(delivered, name_col, 'customer')
                
                customers = delivered.groupby(display_col)[amount_col].sum().nlargest(limit).reset_index()
                customers.columns = ['Customer', 'Total Spent']
                
                fig = px.bar(customers, x='Customer', y='Total Spent',
                            title=f'Top {limit} Customers',
                            color='Total Spent', color_continuous_scale='Purples')
                fig.update_layout(height=400, xaxis_tickangle=-45)
                
                return {'content': f"## 🏆 Top {limit} Customers\n\nBased on orders data:", 'charts': [fig], 'tables': [customers]}
        
        return {'content': "❌ No customer data available", 'charts': [], 'tables': []}
    
    def get_customer_analysis(self, analysis):
        """General customer analysis"""
        if self.has_data('customers'):
            df = self.customers.copy()
            spent_col = self.customer_mappings.get('total_spent')
            segment_col = self.customer_mappings.get('segment')
            
            response = f"""## 👥 Customer Analysis

### Overview
- **Total Customers:** {len(df):,}
"""
            
            charts = []
            
            if spent_col and spent_col in df.columns:
                response += f"- **Average LTV:** {format_inr(df[spent_col].mean())}\n"
                response += f"- **Total Value:** {format_inr(df[spent_col].sum())}\n"
            
            if segment_col and segment_col in df.columns:
                seg_dist = df[segment_col].value_counts().reset_index()
                seg_dist.columns = ['Segment', 'Customers']
                
                fig = px.pie(seg_dist, values='Customers', names='Segment',
                            title='Customer Segments', hole=0.4,
                            color_discrete_sequence=get_colors())
                fig.update_layout(height=400)
                charts.append(fig)
            
            return {'content': response, 'charts': charts, 'tables': []}
        
        # From orders
        if self.has_data('orders'):
            df = self.orders.copy()
            name_col = self.order_mappings.get('customer_name')
            
            if name_col and name_col in df.columns:
                unique_customers = df[name_col].nunique()
                return {
                    'content': f"## 👥 Customer Analysis\n\n- **Unique Customers:** {unique_customers:,}\n- *Upload customer data for detailed analysis*",
                    'charts': [],
                    'tables': []
                }
        
        return {'content': "❌ No customer data available", 'charts': [], 'tables': []}
    
    def get_inventory_analysis(self, analysis):
        """Inventory analysis"""
        if not self.has_data('inventory'):
            return {'content': "❌ No inventory data available. Upload inventory CSV or connect via API.", 'charts': [], 'tables': []}
        
        df = self.inventory.copy()
        qty_col = self.inventory_mappings.get('quantity')
        product_col = self.inventory_mappings.get('product_name') or self.inventory_mappings.get('product_id')
        
        if not qty_col or qty_col not in df.columns:
            return {'content': "❌ Quantity column not found in inventory", 'charts': [], 'tables': []}
        
        total_stock = df[qty_col].sum()
        out_of_stock = (df[qty_col] == 0).sum()
        low_stock = (df[qty_col] < 10).sum()
        
        response = f"""## 📊 Inventory Analysis

### Stock Overview
| Metric | Value |
|--------|-------|
| **Total SKUs** | {len(df):,} |
| **Total Stock** | {total_stock:,} units |
| **Out of Stock** | {out_of_stock:,} |
| **Low Stock (<10)** | {low_stock:,} |

> ⚠️ {low_stock} items need attention!
"""
        
        # Stock level distribution
        df['Stock Level'] = pd.cut(df[qty_col], bins=[-1, 0, 10, 50, float('inf')],
                                   labels=['Out of Stock', 'Low', 'Medium', 'High'])
        stock_dist = df['Stock Level'].value_counts().reset_index()
        stock_dist.columns = ['Level', 'Count']
        
        fig = px.pie(stock_dist, values='Count', names='Level',
                    title='Stock Level Distribution',
                    color='Level',
                    color_discrete_map={
                        'Out of Stock': '#ef4444',
                        'Low': '#f59e0b',
                        'Medium': '#3b82f6',
                        'High': '#22c55e'
                    })
        fig.update_layout(height=400)
        
        return {'content': response, 'charts': [fig], 'tables': []}
    
    def get_city_analysis(self, analysis):
        """City/Geographic analysis"""
        if not self.has_data('orders'):
            return self._no_data_response("orders", "city/geographic analysis")
        
        df = self.get_orders_with_helpers()
        city_col = self.order_mappings.get('city')
        amount_col = self.order_mappings.get('total_amount')
        
        # Auto-detect city column if not mapped
        if not city_col or city_col not in df.columns:
            city_patterns = ['city', 'location', 'shipping_city', 'billing_city', 'customer_city', 'town']
            for col in df.columns:
                if any(p in col.lower() for p in city_patterns):
                    city_col = col
                    break
        
        # Auto-detect amount column if not mapped
        if not amount_col or amount_col not in df.columns:
            amount_patterns = ['amount', 'total', 'price', 'revenue', 'value', 'subtotal', 'total_price']
            for col in df.columns:
                if any(p in col.lower() for p in amount_patterns):
                    if pd.api.types.is_numeric_dtype(df[col]) or df[col].dtype == 'object':
                        try:
                            if pd.to_numeric(df[col], errors='coerce').notna().sum() > 0:
                                amount_col = col
                                break
                        except:
                            pass
        
        if not city_col or city_col not in df.columns:
            available_cols = ', '.join(df.columns[:15].tolist())
            return {
                'content': f"""## 🗺️ City Analysis Not Available

❌ **Could not find a city/location column** in your orders data.

**Available columns:** {available_cols}

💡 **Tip:** Make sure your data has a column for city, location, or shipping address.""",
                'charts': [], 
                'tables': []
            }
        
        # Use all orders if delivered filter results in empty
        if '_is_delivered' in df.columns:
            delivered = df[df['_is_delivered']]
            if len(delivered) == 0:
                delivered = df
        else:
            delivered = df
        
        try:
            if amount_col and amount_col in df.columns:
                delivered = delivered.copy()
                delivered[amount_col] = pd.to_numeric(delivered[amount_col], errors='coerce').fillna(0)
                
                city_data = delivered.groupby(city_col, as_index=False).agg(
                    Revenue=(amount_col, 'sum'),
                    Orders=(amount_col, 'count')
                )
                city_data = city_data.rename(columns={city_col: 'City'})
                city_data = city_data.nlargest(15, 'Revenue')
                
                total_rev = city_data['Revenue'].sum()
                city_data['% Revenue'] = (city_data['Revenue'] / total_rev * 100).round(1)
            else:
                city_data = delivered[city_col].value_counts().head(15).reset_index()
                city_data.columns = ['City', 'Orders']
                city_data['% Orders'] = (city_data['Orders'] / city_data['Orders'].sum() * 100).round(1)
            
            response = f"""## 🗺️ Revenue by City

### Top {len(city_data)} Cities

| Rank | City | {'Revenue | Orders | % Revenue' if 'Revenue' in city_data.columns else 'Orders | % Orders'} |
|------|------|{'---------|--------|----------' if 'Revenue' in city_data.columns else '--------|----------'}|
"""
            for idx, row in enumerate(city_data.itertuples(), 1):
                if 'Revenue' in city_data.columns:
                    response += f"| {idx} | {row.City} | {format_inr(row.Revenue)} | {int(row.Orders):,} | {row._4:.1f}% |\n"
                else:
                    response += f"| {idx} | {row.City} | {int(row.Orders):,} | {row._3:.1f}% |\n"
            
            if 'Revenue' in city_data.columns:
                response += f"\n**Total Revenue (Top 15):** {format_inr(total_rev)}"
            
            fig = px.bar(city_data, x='City', y='Revenue' if 'Revenue' in city_data.columns else 'Orders',
                        title='Revenue by City',
                        color='Revenue' if 'Revenue' in city_data.columns else 'Orders',
                        color_continuous_scale='Viridis')
            fig.update_layout(height=400, xaxis_tickangle=-45)
            
            # Add pie chart for top 10
            charts = [fig]
            if len(city_data) > 1:
                pie_data = city_data.head(10)
                fig2 = px.pie(pie_data, values='Revenue' if 'Revenue' in city_data.columns else 'Orders',
                             names='City', title='Top 10 Cities Distribution', hole=0.4,
                             color_discrete_sequence=get_colors())
                fig2.update_layout(height=400)
                charts.append(fig2)
            
            # Format for display
            display_data = city_data.copy()
            if 'Revenue' in display_data.columns:
                display_data['Revenue'] = display_data['Revenue'].apply(format_inr)
            
            return {'content': response, 'charts': charts, 'tables': [display_data]}
            
        except Exception as e:
            return {
                'content': f"## ⚠️ Error in City Analysis\n\nCould not complete the analysis: {str(e)}\n\n💡 Please check your data format.",
                'charts': [],
                'tables': []
            }
    
    def get_payment_breakdown(self, analysis):
        """Payment method breakdown"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        payment_col = self.order_mappings.get('payment_method')
        amount_col = self.order_mappings.get('total_amount')
        
        if not payment_col or payment_col not in df.columns:
            return {'content': "❌ Payment method column not found", 'charts': [], 'tables': []}
        
        pay_data = df.groupby(payment_col).size().reset_index(name='Orders')
        
        response = f"""## 💳 Payment Methods Breakdown

### Distribution
"""
        
        fig = px.pie(pay_data, values='Orders', names=payment_col,
                    title='Orders by Payment Method', hole=0.4,
                    color_discrete_sequence=get_colors())
        fig.update_layout(height=400)
        
        return {'content': response, 'charts': [fig], 'tables': [pay_data]}
    
    def get_status_analysis(self, analysis):
        """Order status analysis"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.orders.copy()
        status_col = self.order_mappings.get('order_status')
        
        if not status_col or status_col not in df.columns:
            return {'content': "❌ Status column not found", 'charts': [], 'tables': []}
        
        status_data = df[status_col].value_counts().reset_index()
        status_data.columns = ['Status', 'Count']
        status_data['Percentage'] = (status_data['Count'] / len(df) * 100).round(1)
        
        response = f"""## 📊 Order Status Analysis

### Current Status Distribution
"""
        
        fig = px.pie(status_data, values='Count', names='Status',
                    title='Order Status Distribution', hole=0.4,
                    color_discrete_sequence=get_colors())
        fig.update_layout(height=400)
        
        return {'content': response, 'charts': [fig], 'tables': [status_data]}
    
    def get_orders_trend(self, analysis):
        """Orders trend over time"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.orders.copy()
        date_col = self.order_mappings.get('order_date')
        
        if not date_col or date_col not in df.columns:
            return {'content': "❌ Date column not found", 'charts': [], 'tables': []}
        
        temp = df.copy()
        temp['_date'] = pd.to_datetime(temp[date_col], dayfirst=True, errors='coerce')
        temp = temp.dropna(subset=['_date'])
        
        daily = temp.groupby(temp['_date'].dt.date).size().reset_index(name='Orders')
        daily.columns = ['Date', 'Orders']
        
        response = f"""## 📈 Orders Trend

### Daily Statistics
- **Average Daily Orders:** {daily['Orders'].mean():.0f}
- **Best Day:** {daily['Orders'].max()} orders
- **Total Days:** {len(daily)}
"""
        
        fig = px.line(daily, x='Date', y='Orders', title='Daily Orders Trend',
                     markers=True, color_discrete_sequence=['#6366f1'])
        fig.update_layout(height=400)
        
        return {'content': response, 'charts': [fig], 'tables': []}
    
    def get_orders_analysis(self, analysis):
        """General orders analysis"""
        if not self.has_data('orders'):
            return {'content': "❌ No orders data available", 'charts': [], 'tables': []}
        
        df = self.get_orders_with_helpers()
        amount_col = self.order_mappings.get('total_amount')
        
        delivered = df[df['_is_delivered']] if '_is_delivered' in df.columns else df
        rto = df[df['_is_rto']] if '_is_rto' in df.columns else pd.DataFrame()
        
        rto_base = len(delivered) + len(rto)
        rto_rate = (len(rto) / rto_base * 100) if rto_base > 0 else 0
        
        response = f"""## 📦 Orders Analysis

### Overview
| Metric | Value |
|--------|-------|
| **Total Orders** | {len(df):,} |
| **Delivered** | {len(delivered):,} |
| **RTO** | {len(rto):,} |
| **RTO Rate** | {rto_rate:.1f}% |
"""
        
        if amount_col and amount_col in df.columns:
            response += f"| **Revenue** | {format_inr(delivered[amount_col].sum())} |\n"
            response += f"| **AOV** | {format_inr(delivered[amount_col].mean())} |\n"
        
        charts = []
        
        status_col = self.order_mappings.get('order_status')
        if status_col and status_col in df.columns:
            status_dist = df[status_col].value_counts().reset_index()
            status_dist.columns = ['Status', 'Count']
            
            fig = px.pie(status_dist, values='Count', names='Status',
                        title='Order Status Distribution', hole=0.4,
                        color_discrete_sequence=get_colors())
            fig.update_layout(height=400)
            charts.append(fig)
        
        return {'content': response, 'charts': charts, 'tables': []}
    
    def get_ads_analysis(self, analysis):
        """Analyze ads performance across platforms"""
        intents = analysis['intents']
        charts = []
        tables = []
        
        # Check for ads data
        has_meta = len(self.ads_meta) > 0
        has_google = len(self.ads_google) > 0
        has_shopify = len(self.ads_shopify) > 0
        
        if not has_meta and not has_google and not has_shopify:
            return {
                'content': """## 📢 No Ads Data Available

I don't see any ads data loaded. To analyze your advertising performance:

1. **Upload Ads Data**: Go to **📁 Data Manager** and upload your ads export files
2. **Connect Ads APIs**: Go to **🔌 API Integration** to connect:
   - Meta Ads (Facebook/Instagram)
   - Google Ads
   - Shopify Marketing

Or load sample data from the **Ads Analytics** page to explore!
""",
                'charts': [],
                'tables': []
            }
        
        # Aggregate metrics
        total_spend = 0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        total_revenue = 0
        
        if has_meta:
            if 'spend' in self.ads_meta.columns:
                total_spend += self.ads_meta['spend'].sum()
            if 'impressions' in self.ads_meta.columns:
                total_impressions += self.ads_meta['impressions'].sum()
            if 'clicks' in self.ads_meta.columns:
                total_clicks += self.ads_meta['clicks'].sum()
            if 'conversions' in self.ads_meta.columns:
                total_conversions += self.ads_meta['conversions'].sum()
            if 'revenue' in self.ads_meta.columns:
                total_revenue += self.ads_meta['revenue'].sum()
        
        if has_google:
            if 'cost' in self.ads_google.columns:
                total_spend += self.ads_google['cost'].sum()
            if 'impressions' in self.ads_google.columns:
                total_impressions += self.ads_google['impressions'].sum()
            if 'clicks' in self.ads_google.columns:
                total_clicks += self.ads_google['clicks'].sum()
            if 'conversions' in self.ads_google.columns:
                total_conversions += self.ads_google['conversions'].sum()
            if 'conversion_value' in self.ads_google.columns:
                total_revenue += self.ads_google['conversion_value'].sum()
        
        # Calculate derived metrics
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = total_spend / total_clicks if total_clicks > 0 else 0
        cpa = total_spend / total_conversions if total_conversions > 0 else 0
        roas = total_revenue / total_spend if total_spend > 0 else 0
        
        # Build response based on specific intent
        if 'roas' in intents:
            response = f"""## 📈 ROAS Analysis

**Overall ROAS: {roas:.2f}x**

For every ₹1 spent on ads, you're generating ₹{roas:.2f} in revenue.

| Metric | Value |
|--------|-------|
| Total Ad Spend | {format_inr(total_spend)} |
| Total Revenue | {format_inr(total_revenue)} |
| ROAS | {roas:.2f}x |

{"✅ **Great!** ROAS > 3x is typically profitable" if roas >= 3 else "⚠️ **Note:** ROAS below 3x may need optimization"}
"""
        elif 'ctr' in intents:
            response = f"""## 🖱️ CTR Analysis

**Overall CTR: {ctr:.2f}%**

| Metric | Value |
|--------|-------|
| Total Impressions | {total_impressions:,.0f} |
| Total Clicks | {total_clicks:,.0f} |
| CTR | {ctr:.2f}% |

{"✅ **Good CTR!** Above industry average" if ctr >= 2 else "⚠️ CTR below 2% - consider testing new ad creatives"}
"""
        elif 'cpc' in intents:
            response = f"""## 💵 CPC Analysis

**Average CPC: {format_inr(cpc)}**

| Metric | Value |
|--------|-------|
| Total Spend | {format_inr(total_spend)} |
| Total Clicks | {total_clicks:,.0f} |
| CPC | {format_inr(cpc)} |
"""
        elif 'cpa' in intents:
            response = f"""## 🎯 CPA Analysis

**Cost Per Acquisition: {format_inr(cpa)}**

| Metric | Value |
|--------|-------|
| Total Spend | {format_inr(total_spend)} |
| Total Conversions | {total_conversions:,.0f} |
| CPA | {format_inr(cpa)} |
"""
        elif 'spend' in intents:
            response = f"""## 💸 Ad Spend Analysis

**Total Ad Spend: {format_inr(total_spend)}**

"""
            if has_meta and has_google:
                meta_spend = self.ads_meta['spend'].sum() if 'spend' in self.ads_meta.columns else 0
                google_spend = self.ads_google['cost'].sum() if 'cost' in self.ads_google.columns else 0
                response += f"""
| Platform | Spend | % of Total |
|----------|-------|------------|
| Meta Ads | {format_inr(meta_spend)} | {meta_spend/total_spend*100:.1f}% |
| Google Ads | {format_inr(google_spend)} | {google_spend/total_spend*100:.1f}% |
"""
        else:
            # General ads overview
            response = f"""## 📢 Advertising Performance Overview

### Key Metrics
| Metric | Value |
|--------|-------|
| 💸 Total Ad Spend | {format_inr(total_spend)} |
| 👁️ Impressions | {total_impressions:,.0f} |
| 🖱️ Clicks | {total_clicks:,.0f} |
| 📊 CTR | {ctr:.2f}% |
| 💵 CPC | {format_inr(cpc)} |
| 🎯 Conversions | {total_conversions:,.0f} |
| 🎯 CPA | {format_inr(cpa)} |
| 💰 Revenue | {format_inr(total_revenue)} |
| 📈 ROAS | {roas:.2f}x |

### Platforms
"""
            if has_meta:
                response += f"- ✅ Meta Ads: {len(self.ads_meta)} days of data\n"
            if has_google:
                response += f"- ✅ Google Ads: {len(self.ads_google)} days of data\n"
            if has_shopify:
                response += f"- ✅ Shopify Marketing: {len(self.ads_shopify)} days of data\n"
        
        # Create charts
        # Platform comparison
        if has_meta or has_google:
            platform_data = []
            if has_meta:
                meta_spend = self.ads_meta['spend'].sum() if 'spend' in self.ads_meta.columns else 0
                meta_conv = self.ads_meta['conversions'].sum() if 'conversions' in self.ads_meta.columns else 0
                meta_rev = self.ads_meta['revenue'].sum() if 'revenue' in self.ads_meta.columns else 0
                platform_data.append({
                    'Platform': 'Meta Ads',
                    'Spend': meta_spend,
                    'Conversions': meta_conv,
                    'Revenue': meta_rev
                })
            if has_google:
                google_spend = self.ads_google['cost'].sum() if 'cost' in self.ads_google.columns else 0
                google_conv = self.ads_google['conversions'].sum() if 'conversions' in self.ads_google.columns else 0
                google_rev = self.ads_google['conversion_value'].sum() if 'conversion_value' in self.ads_google.columns else 0
                platform_data.append({
                    'Platform': 'Google Ads',
                    'Spend': google_spend,
                    'Conversions': google_conv,
                    'Revenue': google_rev
                })
            
            if platform_data:
                platform_df = pd.DataFrame(platform_data)
                
                # Spend by platform pie chart
                fig = px.pie(platform_df, values='Spend', names='Platform',
                            title='💸 Ad Spend by Platform',
                            color_discrete_sequence=['#3b82f6', '#4285f4', '#96bf48'])
                charts.append(fig)
                
                # ROAS by platform
                platform_df['ROAS'] = platform_df['Revenue'] / platform_df['Spend']
                fig = px.bar(platform_df, x='Platform', y='ROAS',
                            title='📈 ROAS by Platform',
                            color='Platform',
                            color_discrete_sequence=['#3b82f6', '#4285f4', '#96bf48'])
                fig.add_hline(y=1, line_dash="dash", line_color="red", 
                              annotation_text="Break-even")
                charts.append(fig)
        
        # Time series if available
        if has_meta and 'date' in self.ads_meta.columns:
            daily = self.ads_meta.copy()
            daily['date'] = pd.to_datetime(daily['date'], errors='coerce')
            daily = daily.groupby(daily['date'].dt.date).agg({
                'spend': 'sum',
                'conversions': 'sum'
            }).reset_index()
            daily.columns = ['Date', 'Spend', 'Conversions']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Spend'],
                                      name='Spend', line=dict(color='#ef4444')))
            fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Conversions'] * 50,
                                      name='Conversions (x50)', line=dict(color='#10b981')))
            fig.update_layout(title='📈 Daily Performance Trend', height=350)
            charts.append(fig)
        
        return {'content': response, 'charts': charts, 'tables': tables}
    
    def general_response(self):
        """General response when query not understood"""
        has_data = any(len(df) > 0 for df in st.session_state.data_store.values())
        
        # Get available data info
        data_info = []
        for dtype, label in [('orders', '📦 Orders'), ('customers', '👥 Customers'), 
                            ('products', '🛍️ Products'), ('inventory', '📊 Inventory'),
                            ('ads_meta', '📘 Meta Ads'), ('ads_google', '🔍 Google Ads')]:
            if self.has_data(dtype):
                df = st.session_state.data_store.get(dtype)
                data_info.append(f"- {label}: {len(df):,} records")
        
        # Get column info from orders if available
        column_info = ""
        if self.has_data('orders'):
            cols = list(self.orders.columns)[:15]
            column_info = f"\n\n**Your orders columns:** {', '.join(cols)}"
            if len(self.orders.columns) > 15:
                column_info += f"... and {len(self.orders.columns) - 15} more"
        
        if has_data:
            return {
                'content': f"""## 🤔 I couldn't understand that query

Let me help you with what I can analyze:

### 📁 Your Data
{chr(10).join(data_info) if data_info else "No data loaded yet"}
{column_info}

### 💬 Try These Questions:
| Category | Example Questions |
|----------|-------------------|
| 💰 **Revenue** | "Show total revenue", "Revenue by city", "Sales breakdown" |
| 📦 **Orders** | "Order summary", "Orders by status", "Orders trend" |
| 🏆 **Top Items** | "Top 10 products", "Best selling items", "Top customers" |
| 🗺️ **Geography** | "Revenue by city", "Orders by state", "Location analysis" |
| 📊 **Trends** | "Revenue trend", "Daily orders", "Monthly sales" |
| 💳 **Payments** | "COD vs prepaid", "Payment breakdown" |
| 🔄 **Returns** | "RTO rate", "Return analysis" |

### 💡 Tips:
- Be specific: "top 10 products by revenue" works better than just "products"
- Mention the column if needed: "breakdown by shipping_city"
- Use numbers: "top 5 customers" or "last 30 days"
""",
                'charts': [],
                'tables': []
            }
        else:
            return {
                'content': """## 👋 Welcome to DataPulse AI!

I don't see any data loaded yet. Here's how to get started:

### 📤 Upload Your Data:
1. Go to **📁 Data Manager** in the sidebar
2. Click **Add More Data**
3. Upload your CSV or Excel files

### 📊 Supported Data Types:
- **Orders** - Sales transactions
- **Customers** - Customer information
- **Products** - Product catalog
- **Inventory** - Stock levels
- **Ads** - Meta/Google/Shopify ad data

Once you upload data, I can help you analyze:
- Revenue and sales trends
- Top products and customers
- Geographic performance
- RTO rates and delivery
- And much more!
""",
                'charts': [],
                'tables': []
            }


def render_ai_chat():
    """Render AI chat interface"""
    
    # Header with refresh button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.header("🤖 AI Analytics Assistant")
    with col2:
        if st.button("🔄 New Chat", key="refresh_chat", help="Clear chat history and start fresh"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # LLM Configuration Section
    with st.expander("⚙️ AI Model Settings", expanded=False):
        render_llm_settings()
    
    # Check LLM status
    llm_provider = get_llm_provider() if LLM_AVAILABLE else None
    
    if llm_provider:
        st.success(f"🤖 AI Model: **{st.session_state.get('llm_provider', 'none').title()}** connected")
    else:
        st.info("💡 Configure an AI model above for advanced natural language queries, or use quick insights below")
    
    # Quick actions
    st.subheader("⚡ Quick Insights")
    
    cols = st.columns(4)
    quick_actions = [
        ("📊 Summary", "Give me a complete summary of all my data"),
        ("💰 Revenue", "Show me revenue analysis with charts"),
        ("🔄 RTO Analysis", "Analyze my RTO rates by payment method"),
        ("🏆 Top Products", "What are my top 10 best selling products?"),
        ("👥 Top Customers", "Show me my top 10 customers by value"),
        ("📈 Trends", "Show me revenue trend over time"),
        ("🗺️ Geography", "Analyze orders by city"),
        ("💳 Payments", "Show payment method breakdown")
    ]
    
    for i, (label, query) in enumerate(quick_actions):
        with cols[i % 4]:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                st.session_state.pending_query = query
    
    st.divider()
    
    # Chat input
    query = st.chat_input("Ask me anything about your data...")
    
    # Check for pending query from quick actions
    if 'pending_query' in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query
    
    if query:
        # Add user message
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query
        })
        
        # Check if LLM is configured
        llm_provider = get_llm_provider() if LLM_AVAILABLE else None
        
        if llm_provider:
            # Use LLM for advanced queries
            with st.spinner("🤖 AI is thinking..."):
                llm_analyzer = DataAnalysisLLM(llm_provider)
                llm_result = llm_analyzer.process(query)
                
                # Also get visualization from rule-based analyzer
                analyzer = DataAnalyzer()
                viz_result = analyzer.process_query(query)
                
                # Combine LLM response with visualizations
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': llm_result['response'],
                    'charts': viz_result.get('charts', []),
                    'tables': [llm_result['data']] if llm_result.get('data') is not None else viz_result.get('tables', []),
                    'llm_used': True
                })
        else:
            # Use rule-based analyzer
            analyzer = DataAnalyzer()
            result = analyzer.process_query(query)
            
            # Add assistant response
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': result['content'],
                'charts': result.get('charts', []),
                'tables': result.get('tables', []),
                'llm_used': False
            })
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            
            # Show LLM indicator
            if msg.get('llm_used'):
                st.caption("🤖 Powered by AI")
            
            # Display charts
            if msg.get('charts'):
                for chart in msg['charts']:
                    st.plotly_chart(chart, use_container_width=True)
            
            # Display tables
            if msg.get('tables'):
                for table in msg['tables']:
                    if isinstance(table, pd.DataFrame) and len(table) > 0:
                        st.dataframe(table, use_container_width=True, hide_index=True)
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()


def render_llm_settings():
    """Render LLM configuration settings"""
    
    st.write("**Select AI Provider:**")
    
    # Get current provider, defaulting to 'none'
    current_provider = st.session_state.get('llm_provider', 'none')
    if current_provider == 'ollama':
        current_provider = 'none'  # Reset if it was ollama
    
    provider = st.selectbox(
        "Provider",
        ["none", "openai", "groq"],
        index=["none", "openai", "groq"].index(current_provider) if current_provider in ["none", "openai", "groq"] else 0,
        format_func=lambda x: {
            'none': '🚫 None (Rule-based only)',
            'openai': '🤖 OpenAI (Cloud - Paid)',
            'groq': '⚡ Groq (Cloud - Free tier)'
        }.get(x, x),
        label_visibility="collapsed"
    )
    
    st.session_state.llm_provider = provider
    
    if provider == 'openai':
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get('openai_api_key', ''),
            placeholder="sk-..."
        )
        st.session_state.openai_api_key = api_key
        
        st.session_state.openai_model = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0
        )
        
        if api_key:
            st.success("✅ API key configured")
        else:
            st.info("Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)")
    
    elif provider == 'groq':
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.get('groq_api_key', ''),
            placeholder="gsk_..."
        )
        st.session_state.groq_api_key = api_key
        
        st.session_state.groq_model = st.selectbox(
            "Model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            index=0
        )
        
        if api_key:
            st.success("✅ API key configured")
        else:
            st.info("Get your FREE API key from [Groq Console](https://console.groq.com/keys)")

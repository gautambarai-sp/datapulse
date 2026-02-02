"""LLM Provider Integration for DataPulse AI Chat"""

import streamlit as st
import pandas as pd
import json
import re
from typing import Optional, Dict, Any
import requests


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self):
        """Get system prompt with data context"""
        return """You are DataPulse AI, an expert e-commerce analytics assistant. You help users analyze their business data including orders, customers, products, and inventory.

Your capabilities:
1. Answer questions about sales, revenue, RTO rates, and business metrics
2. Generate data analysis queries
3. Provide insights and recommendations
4. Help users understand their e-commerce performance

Business Logic Rules:
- Revenue = Sum of delivered orders only (not pending/RTO)
- RTO Rate = RTO orders / (Delivered + RTO) × 100
- AOV (Average Order Value) = Revenue / Delivered orders
- COD = Cash on Delivery orders
- Prepaid = Online payment orders

When analyzing data, always:
1. Be specific with numbers and metrics
2. Provide actionable insights
3. Suggest visualizations when relevant
4. Explain calculations clearly

Response Format:
- Use markdown formatting
- Include relevant metrics in tables when appropriate
- Be concise but thorough
- If you need to generate code for analysis, output it in a code block with ```python
"""
    
    def _get_data_context(self) -> str:
        """Get current data context for the LLM"""
        context_parts = []
        
        # Orders context
        orders = st.session_state.data_store.get('orders', pd.DataFrame())
        if len(orders) > 0:
            order_mappings = st.session_state.column_mappings.get('orders', {})
            
            context_parts.append(f"""
ORDERS DATA:
- Total rows: {len(orders)}
- Columns: {', '.join(orders.columns.tolist())}
- Column mappings: {json.dumps(order_mappings)}
- Sample data (first 3 rows): 
{orders.head(3).to_string()}
""")
            
            # Add summary stats
            amount_col = order_mappings.get('total_amount')
            status_col = order_mappings.get('order_status')
            
            if amount_col and amount_col in orders.columns:
                context_parts.append(f"- Total amount sum: {orders[amount_col].sum()}")
                context_parts.append(f"- Average amount: {orders[amount_col].mean():.2f}")
            
            if status_col and status_col in orders.columns:
                context_parts.append(f"- Status distribution: {orders[status_col].value_counts().to_dict()}")
        
        # Customers context
        customers = st.session_state.data_store.get('customers', pd.DataFrame())
        if len(customers) > 0:
            context_parts.append(f"""
CUSTOMERS DATA:
- Total rows: {len(customers)}
- Columns: {', '.join(customers.columns.tolist())}
""")
        
        # Products context
        products = st.session_state.data_store.get('products', pd.DataFrame())
        if len(products) > 0:
            context_parts.append(f"""
PRODUCTS DATA:
- Total rows: {len(products)}
- Columns: {', '.join(products.columns.tolist())}
""")
        
        # Inventory context
        inventory = st.session_state.data_store.get('inventory', pd.DataFrame())
        if len(inventory) > 0:
            context_parts.append(f"""
INVENTORY DATA:
- Total rows: {len(inventory)}
- Columns: {', '.join(inventory.columns.tolist())}
""")
        
        if not context_parts:
            return "NO DATA LOADED - User needs to upload data first."
        
        return "\n".join(context_parts)
    
    def generate(self, prompt: str) -> str:
        """Generate response - to be implemented by subclasses"""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        super().__init__()
        self.model = model
        self.base_url = base_url
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> list:
        """Get available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        return []
    
    def generate(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            data_context = self._get_data_context()
            
            full_prompt = f"""{self.system_prompt}

CURRENT DATA CONTEXT:
{data_context}

USER QUERY: {prompt}

Provide a helpful, data-driven response. If the query requires specific data analysis, explain what you found and provide insights."""
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1024
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('response', 'No response generated')
            else:
                return f"Error: {response.status_code} - {response.text}"
        
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to Ollama. Please make sure Ollama is running (`ollama serve`)"
        except Exception as e:
            return f"❌ Error: {str(e)}"


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            data_context = self._get_data_context()
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"DATA CONTEXT:\n{data_context}"},
                {"role": "user", "content": prompt}
            ]
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.json().get('error', {}).get('message', 'Unknown error')}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"


class GroqProvider(LLMProvider):
    """Groq API provider (fast inference)"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate(self, prompt: str) -> str:
        """Generate response using Groq"""
        try:
            data_context = self._get_data_context()
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"DATA CONTEXT:\n{data_context}"},
                {"role": "user", "content": prompt}
            ]
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.json().get('error', {}).get('message', 'Unknown error')}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"


class DataAnalysisLLM:
    """Main LLM handler with data analysis capabilities"""
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query and determine if it needs data operations"""
        query_lower = query.lower()
        
        # Detect analysis intent
        analysis_keywords = {
            'breakdown': ['breakdown', 'break down', 'split', 'segment', 'by'],
            'compare': ['compare', 'vs', 'versus', 'difference'],
            'trend': ['trend', 'over time', 'daily', 'weekly', 'monthly'],
            'top': ['top', 'best', 'highest', 'most'],
            'bottom': ['bottom', 'worst', 'lowest', 'least'],
            'filter': ['where', 'only', 'filter', 'specific'],
            'aggregate': ['total', 'sum', 'average', 'count', 'mean']
        }
        
        detected_ops = []
        for op, keywords in analysis_keywords.items():
            if any(kw in query_lower for kw in keywords):
                detected_ops.append(op)
        
        # Detect dimensions
        dimensions = {
            'city': ['city', 'cities', 'location', 'geographic'],
            'state': ['state', 'region', 'province'],
            'product': ['product', 'item', 'sku'],
            'category': ['category', 'type'],
            'payment': ['payment', 'cod', 'prepaid', 'payment method'],
            'status': ['status', 'delivery', 'delivered', 'rto'],
            'customer': ['customer', 'buyer', 'client'],
            'date': ['date', 'day', 'week', 'month', 'time']
        }
        
        detected_dims = []
        for dim, keywords in dimensions.items():
            if any(kw in query_lower for kw in keywords):
                detected_dims.append(dim)
        
        return {
            'operations': detected_ops,
            'dimensions': detected_dims,
            'needs_data': len(detected_ops) > 0 or len(detected_dims) > 0
        }
    
    def execute_data_query(self, query: str, analysis: Dict) -> Optional[pd.DataFrame]:
        """Execute data query based on analysis"""
        orders = st.session_state.data_store.get('orders', pd.DataFrame())
        if len(orders) == 0:
            return None
        
        order_mappings = st.session_state.column_mappings.get('orders', {})
        df = orders.copy()
        
        # Add helper columns
        status_col = order_mappings.get('order_status')
        if status_col and status_col in df.columns:
            df['_status'] = df[status_col].astype(str).str.lower()
            df['_is_delivered'] = df['_status'].str.contains('deliver|complete|success', na=False)
            df['_is_rto'] = df['_status'].str.contains('rto|return', na=False)
        
        # Handle breakdown queries
        if 'breakdown' in analysis['operations']:
            amount_col = order_mappings.get('total_amount')
            
            for dim in analysis['dimensions']:
                dim_col = order_mappings.get(dim) or order_mappings.get(f'{dim}_name')
                
                # Try to find the column
                if not dim_col:
                    for col in df.columns:
                        if dim.lower() in col.lower():
                            dim_col = col
                            break
                
                if dim_col and dim_col in df.columns:
                    # Aggregate by dimension
                    if amount_col and amount_col in df.columns:
                        result = df.groupby(dim_col).agg({
                            amount_col: ['sum', 'mean', 'count']
                        }).reset_index()
                        result.columns = [dim_col, 'Total Revenue', 'Avg Order', 'Order Count']
                        result = result.sort_values('Total Revenue', ascending=False)
                        return result
                    else:
                        result = df[dim_col].value_counts().reset_index()
                        result.columns = [dim_col, 'Count']
                        return result
        
        return None
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process user query with LLM and data analysis"""
        
        # Analyze query
        analysis = self.analyze_query(query)
        
        # Execute data query if needed
        data_result = None
        if analysis['needs_data']:
            data_result = self.execute_data_query(query, analysis)
        
        # Generate LLM response
        enhanced_query = query
        if data_result is not None:
            enhanced_query = f"""{query}

I have already executed the data query. Here are the results:
{data_result.to_string()}

Please analyze these results and provide insights."""
        
        llm_response = self.provider.generate(enhanced_query)
        
        return {
            'response': llm_response,
            'data': data_result,
            'analysis': analysis
        }


def get_llm_provider():
    """Get configured LLM provider from session state"""
    provider_type = st.session_state.get('llm_provider', 'none')
    
    if provider_type == 'ollama':
        model = st.session_state.get('ollama_model', 'llama3.2')
        return OllamaProvider(model=model)
    
    elif provider_type == 'openai':
        api_key = st.session_state.get('openai_api_key', '')
        model = st.session_state.get('openai_model', 'gpt-4o-mini')
        if api_key:
            return OpenAIProvider(api_key=api_key, model=model)
    
    elif provider_type == 'groq':
        api_key = st.session_state.get('groq_api_key', '')
        model = st.session_state.get('groq_model', 'llama-3.3-70b-versatile')
        if api_key:
            return GroqProvider(api_key=api_key, model=model)
    
    return None

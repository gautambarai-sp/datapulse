"""Alert System for DataPulse AI"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


# Default alert rules
DEFAULT_ALERT_RULES = [
    {
        'id': 'high_rto',
        'name': 'High RTO Rate',
        'metric': 'rto_rate',
        'condition': 'greater_than',
        'threshold': 15,
        'unit': '%',
        'severity': 'critical',
        'enabled': True,
        'description': 'RTO rate exceeds 15%'
    },
    {
        'id': 'low_revenue',
        'name': 'Revenue Drop',
        'metric': 'daily_revenue',
        'condition': 'less_than',
        'threshold': 10000,
        'unit': '₹',
        'severity': 'warning',
        'enabled': True,
        'description': 'Daily revenue below ₹10,000'
    },
    {
        'id': 'high_cancellation',
        'name': 'High Cancellation',
        'metric': 'cancellation_rate',
        'condition': 'greater_than',
        'threshold': 10,
        'unit': '%',
        'severity': 'warning',
        'enabled': True,
        'description': 'Cancellation rate exceeds 10%'
    },
    {
        'id': 'low_stock',
        'name': 'Low Stock Alert',
        'metric': 'low_stock_products',
        'condition': 'greater_than',
        'threshold': 5,
        'unit': 'products',
        'severity': 'info',
        'enabled': True,
        'description': 'More than 5 products have low stock'
    },
    {
        'id': 'high_ad_spend',
        'name': 'High Ad Spend',
        'metric': 'daily_ad_spend',
        'condition': 'greater_than',
        'threshold': 50000,
        'unit': '₹',
        'severity': 'info',
        'enabled': True,
        'description': 'Daily ad spend exceeds ₹50,000'
    },
    {
        'id': 'low_roas',
        'name': 'Low ROAS',
        'metric': 'roas',
        'condition': 'less_than',
        'threshold': 2.0,
        'unit': 'x',
        'severity': 'warning',
        'enabled': True,
        'description': 'ROAS below 2x'
    }
]

SEVERITY_CONFIG = {
    'critical': {'icon': '🔴', 'color': '#ef4444', 'bg': '#fef2f2', 'border': '#fecaca'},
    'warning': {'icon': '🟡', 'color': '#f59e0b', 'bg': '#fffbeb', 'border': '#fed7aa'},
    'info': {'icon': '🔵', 'color': '#3b82f6', 'bg': '#eff6ff', 'border': '#bfdbfe'},
    'success': {'icon': '🟢', 'color': '#22c55e', 'bg': '#f0fdf4', 'border': '#bbf7d0'}
}


def init_alerts():
    """Initialize alert system in session state"""
    if 'alert_rules' not in st.session_state:
        st.session_state.alert_rules = DEFAULT_ALERT_RULES.copy()
    if 'active_alerts' not in st.session_state:
        st.session_state.active_alerts = []
    if 'alert_history' not in st.session_state:
        st.session_state.alert_history = []
    if 'alerts_dismissed' not in st.session_state:
        st.session_state.alerts_dismissed = set()


def calculate_metrics():
    """Calculate current metrics for alert evaluation"""
    metrics = {}
    data_store = st.session_state.get('data_store', {})
    orders = data_store.get('orders', pd.DataFrame())
    mappings = st.session_state.get('column_mappings', {}).get('orders', {})
    
    if len(orders) > 0:
        # Get column mappings
        status_col = mappings.get('order_status')
        amount_col = mappings.get('total_amount')
        date_col = mappings.get('order_date')
        
        # Calculate RTO rate
        if status_col and status_col in orders.columns:
            total = len(orders)
            rto = len(orders[orders[status_col].astype(str).str.lower().str.contains('rto|return', na=False)])
            metrics['rto_rate'] = (rto / total * 100) if total > 0 else 0
            
            cancelled = len(orders[orders[status_col].astype(str).str.lower().str.contains('cancel', na=False)])
            metrics['cancellation_rate'] = (cancelled / total * 100) if total > 0 else 0
        
        # Calculate daily revenue
        if amount_col and amount_col in orders.columns:
            if date_col and date_col in orders.columns:
                try:
                    orders_copy = orders.copy()
                    orders_copy[date_col] = pd.to_datetime(orders_copy[date_col], errors='coerce')
                    today = orders_copy[date_col].max()
                    if pd.notna(today):
                        today_orders = orders_copy[orders_copy[date_col].dt.date == today.date()]
                        metrics['daily_revenue'] = today_orders[amount_col].sum()
                except:
                    metrics['daily_revenue'] = orders[amount_col].sum() / max(1, len(orders.groupby(date_col if date_col else orders.index)))
            else:
                metrics['daily_revenue'] = orders[amount_col].sum()
    
    # Inventory metrics
    inventory = data_store.get('inventory', pd.DataFrame())
    if len(inventory) > 0:
        qty_cols = [c for c in inventory.columns if any(q in c.lower() for q in ['quantity', 'stock', 'qty'])]
        if qty_cols:
            low_stock = len(inventory[inventory[qty_cols[0]] < 10])
            metrics['low_stock_products'] = low_stock
    
    # Ads metrics
    for ads_key in ['ads_meta', 'ads_google', 'ads_shopify']:
        ads = data_store.get(ads_key, pd.DataFrame())
        if len(ads) > 0:
            spend_cols = [c for c in ads.columns if any(s in c.lower() for s in ['spend', 'cost'])]
            rev_cols = [c for c in ads.columns if any(r in c.lower() for r in ['revenue', 'value', 'sales'])]
            
            if spend_cols:
                total_spend = ads[spend_cols[0]].sum()
                metrics['daily_ad_spend'] = metrics.get('daily_ad_spend', 0) + total_spend
                
                if rev_cols:
                    total_rev = ads[rev_cols[0]].sum()
                    if total_spend > 0:
                        metrics['roas'] = total_rev / total_spend
    
    return metrics


def evaluate_alerts():
    """Evaluate alert rules against current metrics"""
    metrics = calculate_metrics()
    active_alerts = []
    
    for rule in st.session_state.get('alert_rules', []):
        if not rule.get('enabled', True):
            continue
        
        metric_value = metrics.get(rule['metric'])
        if metric_value is None:
            continue
        
        threshold = rule['threshold']
        condition = rule['condition']
        triggered = False
        
        if condition == 'greater_than' and metric_value > threshold:
            triggered = True
        elif condition == 'less_than' and metric_value < threshold:
            triggered = True
        elif condition == 'equals' and metric_value == threshold:
            triggered = True
        
        if triggered:
            alert = {
                'id': rule['id'],
                'name': rule['name'],
                'description': rule['description'],
                'severity': rule['severity'],
                'metric': rule['metric'],
                'current_value': metric_value,
                'threshold': threshold,
                'unit': rule['unit'],
                'timestamp': datetime.now()
            }
            active_alerts.append(alert)
    
    st.session_state.active_alerts = active_alerts
    return active_alerts


def dismiss_alert(alert_id):
    """Dismiss an alert"""
    st.session_state.alerts_dismissed.add(alert_id)


def get_active_alerts():
    """Get list of active, non-dismissed alerts"""
    dismissed = st.session_state.get('alerts_dismissed', set())
    return [a for a in st.session_state.get('active_alerts', []) if a['id'] not in dismissed]


def render_alert_badge():
    """Render alert count badge for sidebar"""
    alerts = get_active_alerts()
    if not alerts:
        return ""
    
    critical = len([a for a in alerts if a['severity'] == 'critical'])
    warning = len([a for a in alerts if a['severity'] == 'warning'])
    
    if critical > 0:
        color = '#ef4444'
        count = critical
    elif warning > 0:
        color = '#f59e0b'
        count = warning
    else:
        color = '#3b82f6'
        count = len(alerts)
    
    return f"""
    <span style="background:{color};color:white;padding:2px 8px;border-radius:10px;
                 font-size:0.7rem;font-weight:600;margin-left:8px;">{count}</span>
    """


def render_alerts_panel():
    """Render the alerts notification panel"""
    alerts = get_active_alerts()
    
    if not alerts:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#64748b;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">✅</div>
            <div>All systems normal. No active alerts.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for alert in sorted(alerts, key=lambda x: {'critical': 0, 'warning': 1, 'info': 2}.get(x['severity'], 3)):
        config = SEVERITY_CONFIG.get(alert['severity'], SEVERITY_CONFIG['info'])
        
        st.markdown(f"""
        <div style="background:{config['bg']};border:1px solid {config['border']};
                    border-radius:12px;padding:1rem;margin-bottom:0.75rem;
                    border-left:4px solid {config['color']};">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div>
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.25rem;">
                        <span>{config['icon']}</span>
                        <strong style="color:{config['color']};">{alert['name']}</strong>
                    </div>
                    <div style="color:#475569;font-size:0.875rem;">{alert['description']}</div>
                    <div style="color:#64748b;font-size:0.75rem;margin-top:0.5rem;">
                        Current: <strong>{alert['current_value']:.1f}{alert['unit']}</strong> 
                        (Threshold: {alert['threshold']}{alert['unit']})
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Dismiss", key=f"dismiss_{alert['id']}", use_container_width=True):
                dismiss_alert(alert['id'])
                st.rerun()


def render_alert_settings():
    """Render alert configuration settings"""
    st.markdown("### ⚙️ Alert Rules")
    st.markdown("Configure when you want to be notified")
    
    rules = st.session_state.get('alert_rules', DEFAULT_ALERT_RULES)
    
    for i, rule in enumerate(rules):
        config = SEVERITY_CONFIG.get(rule['severity'], SEVERITY_CONFIG['info'])
        
        with st.expander(f"{config['icon']} {rule['name']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{rule['description']}**")
                
                new_threshold = st.number_input(
                    f"Threshold ({rule['unit']})",
                    value=float(rule['threshold']),
                    key=f"threshold_{rule['id']}"
                )
                
                new_severity = st.selectbox(
                    "Severity",
                    ['critical', 'warning', 'info'],
                    index=['critical', 'warning', 'info'].index(rule['severity']),
                    key=f"severity_{rule['id']}"
                )
            
            with col2:
                enabled = st.toggle("Enabled", value=rule['enabled'], key=f"enabled_{rule['id']}")
            
            # Update rule
            st.session_state.alert_rules[i]['threshold'] = new_threshold
            st.session_state.alert_rules[i]['severity'] = new_severity
            st.session_state.alert_rules[i]['enabled'] = enabled
    
    st.markdown("---")
    
    # Add new rule
    st.markdown("### ➕ Add Custom Rule")
    
    with st.form("new_alert_rule"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Rule Name", placeholder="My Custom Alert")
            new_metric = st.selectbox("Metric", [
                'rto_rate', 'cancellation_rate', 'daily_revenue', 
                'low_stock_products', 'daily_ad_spend', 'roas'
            ])
        
        with col2:
            new_condition = st.selectbox("Condition", ['greater_than', 'less_than', 'equals'])
            new_thresh = st.number_input("Threshold", value=0.0)
        
        if st.form_submit_button("Add Rule", type="primary"):
            if new_name:
                new_rule = {
                    'id': f"custom_{len(rules)}_{datetime.now().timestamp()}",
                    'name': new_name,
                    'metric': new_metric,
                    'condition': new_condition,
                    'threshold': new_thresh,
                    'unit': '%' if 'rate' in new_metric else '₹',
                    'severity': 'warning',
                    'enabled': True,
                    'description': f"{new_name} alert"
                }
                st.session_state.alert_rules.append(new_rule)
                st.success(f"✅ Added alert rule: {new_name}")
                st.rerun()

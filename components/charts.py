"""Chart builders using Plotly"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Optional

COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'gradient': ['#667eea', '#764ba2', '#ec4899', '#f59e0b', '#22c55e'],
    'status': {
        'Delivered': '#22c55e',
        'Processing': '#3b82f6',
        'Shipped': '#8b5cf6',
        'RTO': '#ef4444',
        'Cancelled': '#64748b',
    }
}


def create_area_chart(df: pd.DataFrame, x: str, y: str, height: int = 350) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y],
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)',
        line=dict(color=COLORS['primary'], width=2.5),
        hovertemplate='<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(showgrid=False, showline=True, linecolor='#e2e8f0'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', showline=False)
    )
    return fig


def create_bar_chart(df: pd.DataFrame, x: str, y: str, horizontal: bool = False, color: Optional[str] = None, height: int = 350) -> go.Figure:
    bar_color = color or COLORS['primary']
    
    if horizontal:
        fig = go.Figure(go.Bar(y=df[x], x=df[y], orientation='h', marker_color=bar_color))
        fig.update_layout(yaxis=dict(categoryorder='total ascending'))
    else:
        fig = go.Figure(go.Bar(x=df[x], y=df[y], marker_color=bar_color))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        showlegend=False
    )
    return fig


def create_pie_chart(df: pd.DataFrame, values: str, names: str, height: int = 350) -> go.Figure:
    colors = [COLORS['status'].get(n, COLORS['gradient'][i % 5]) for i, n in enumerate(df[names])]
    
    fig = go.Figure(go.Pie(
        values=df[values], labels=df[names],
        hole=0.4, marker_colors=colors,
        textinfo='percent+label', textposition='outside'
    ))
    fig.update_layout(
        margin=dict(l=40, r=40, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=height
    )
    return fig


def create_comparison_chart(data: Dict[str, Dict], height: int = 350) -> go.Figure:
    fig = make_subplots(rows=1, cols=3, subplot_titles=['Revenue', 'AOV', 'RTO Rate'])
    colors = [COLORS['warning'], COLORS['primary']]
    
    fig.add_trace(go.Bar(x=['COD', 'Prepaid'], y=[data['COD']['revenue'], data['Prepaid']['revenue']], marker_color=colors, showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=['COD', 'Prepaid'], y=[data['COD']['aov'], data['Prepaid']['aov']], marker_color=colors, showlegend=False), row=1, col=2)
    
    rto_colors = [COLORS['danger'], COLORS['success']]
    fig.add_trace(go.Bar(x=['COD', 'Prepaid'], y=[data['COD']['rto_rate'], data['Prepaid']['rto_rate']], marker_color=rto_colors, showlegend=False), row=1, col=3)
    
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20), height=height, paper_bgcolor='rgba(0,0,0,0)')
    return fig

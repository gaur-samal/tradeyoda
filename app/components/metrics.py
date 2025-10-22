"""Metrics and KPI components."""
import streamlit as st
from typing import List, Dict

def display_metric_card(title: str, value: str, delta: str = None, icon: str = "📊"):
    """Display a styled metric card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    ">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{value}</div>
        {f'<div style="font-size: 0.8rem;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

def calculate_trade_metrics(trades: List[Dict]) -> Dict:
    """Calculate trading performance metrics."""
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'avg_confluence': 0
        }
    
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum([t.get('pnl', 0) for t in trades])
    
    avg_win = sum([t['pnl'] for t in winning_trades]) / len(winning_trades) if winning_trades else 0
    avg_loss = sum([t['pnl'] for t in losing_trades]) / len(losing_trades) if losing_trades else 0
    
    total_wins = sum([t['pnl'] for t in winning_trades])
    total_losses = abs(sum([t['pnl'] for t in losing_trades]))
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    # NEW: Calculate average confluence score
    confluence_scores = [t.get('confluence_count', 0) for t in trades]
    avg_confluence = sum(confluence_scores) / len(confluence_scores) if confluence_scores else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'avg_confluence': avg_confluence
    }

def display_performance_dashboard(trades: List[Dict]):
    """Display comprehensive performance metrics."""
    metrics = calculate_trade_metrics(trades)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Trades", metrics['total_trades'])
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
    
    with col2:
        st.metric("Winning Trades", metrics['winning_trades'])
        st.metric("Losing Trades", metrics['losing_trades'])
    
    with col3:
        st.metric("Total P&L", f"₹{metrics['total_pnl']:,.2f}")
        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
    
    with col4:
        st.metric("Avg Win", f"₹{metrics['avg_win']:,.2f}")
        st.metric("Avg Loss", f"₹{metrics['avg_loss']:,.2f}")
    
    with col5:
        st.metric("Avg Confluence", f"{metrics['avg_confluence']:.1f}")
        st.caption("Average number of confirming indicators per trade")


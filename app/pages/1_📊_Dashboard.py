"""Dashboard page for real-time trading view."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.helpers import format_price, format_percentage

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Live Trading Dashboard")

# Check if orchestrator exists
if 'orchestrator' not in st.session_state or st.session_state.orchestrator is None:
    st.warning("⚠️ Please start the agent from the main page first")
    st.stop()

orchestrator = st.session_state.orchestrator

# Auto-refresh
if st.session_state.get('running', False):
    refresh_interval = st.sidebar.slider("Auto-refresh (seconds)", 5, 60, 10)
    st.sidebar.caption(f"Next refresh in {refresh_interval}s")

# Key Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    status = "🟢 ACTIVE" if st.session_state.get('running', False) else "🔴 STOPPED"
    st.metric("System Status", status)

with col2:
    active_trades = len([t for t in st.session_state.get('trades', []) if t.get('status') == 'ACTIVE'])
    st.metric("Active Trades", active_trades)

with col3:
    total_trades = len(st.session_state.get('trades', []))
    st.metric("Total Trades", total_trades)

with col4:
    total_pnl = sum([t.get('pnl', 0) for t in st.session_state.get('trades', [])])
    st.metric("Total P&L", format_price(total_pnl), delta=format_price(total_pnl))

with col5:
    if st.session_state.get('trades'):
        wins = len([t for t in st.session_state.trades if t.get('pnl', 0) > 0])
        win_rate = (wins / len(st.session_state.trades)) * 100 if st.session_state.trades else 0
    else:
        win_rate = 0
    st.metric("Win Rate", f"{win_rate:.1f}%")

st.divider()

# Live Price and Analysis
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Nifty 50 - Live Price")
    
    # Get live quote
    if orchestrator.data_agent.latest_data:
        nifty_data = orchestrator.data_agent.get_live_quote(orchestrator.config.NIFTY_SECURITY_ID)
        
        if nifty_data:
            price_col1, price_col2, price_col3, price_col4 = st.columns(4)
            
            with price_col1:
                ltp = nifty_data.get('LTP', 0)
                st.metric("LTP", format_price(ltp))
            
            with price_col2:
                change = nifty_data.get('change', 0)
                change_pct = nifty_data.get('change_pct', 0)
                st.metric("Change", f"{change:+.2f}", delta=f"{change_pct:+.2f}%")
            
            with price_col3:
                high = nifty_data.get('high', 0)
                st.metric("High", format_price(high))
            
            with price_col4:
                low = nifty_data.get('low', 0)
                st.metric("Low", format_price(low))
            
            # Volume bar
            volume = nifty_data.get('volume', 0)
            st.caption(f"Volume: {volume:,}")
            st.progress(min(volume / 10000000, 1.0))
        else:
            st.info("Waiting for live data...")
    else:
        st.info("📡 Connecting to market feed...")

with col2:
    st.subheader("🎯 Market Analysis")
    
    if orchestrator.analysis_cache:
        cache = orchestrator.analysis_cache
        llm_analysis = cache.get('llm_analysis', {})
        
        bias = llm_analysis.get('market_bias', 'Neutral')
        bias_color = {
            'Bullish': '🟢',
            'Bearish': '🔴',
            'Neutral': '🟡'
        }.get(bias, '⚪')
        
        st.markdown(f"### {bias_color} {bias}")
        
        context = cache.get('market_context', {})
        trend = context.get('trend', 'N/A')
        st.caption(f"**Trend:** {trend}")
        
        timestamp = cache.get('timestamp')
        if timestamp:
            age = (datetime.now() - timestamp).seconds
            st.caption(f"Updated {age}s ago")
    else:
        st.info("Run analysis to see market bias")

st.divider()

# Supply/Demand Zones Visualization
st.subheader("🎯 Supply & Demand Zones")

if orchestrator.analysis_cache:
    zones = orchestrator.analysis_cache['zones']
    current_price = zones.get('current_price', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 Demand Zones")
        demand_zones = zones.get('demand_zones', [])[:5]
        
        if demand_zones:
            for idx, zone in enumerate(demand_zones, 1):
                confidence = zone['confidence']
                
                with st.expander(f"Zone {idx} - Confidence: {confidence:.0f}%", expanded=(idx==1)):
                    st.progress(confidence / 100)
                    
                    zone_col1, zone_col2 = st.columns(2)
                    with zone_col1:
                        st.metric("Top", format_price(zone['zone_top']))
                        st.metric("Bottom", format_price(zone['zone_bottom']))
                    
                    with zone_col2:
                        st.metric("Distance", f"{zone['distance_from_price']:.2f}%")
                        st.caption(f"Factors: {', '.join(zone['factors'])}")
        else:
            st.info("No demand zones identified")
    
    with col2:
        st.markdown("#### 🔴 Supply Zones")
        supply_zones = zones.get('supply_zones', [])[:5]
        
        if supply_zones:
            for idx, zone in enumerate(supply_zones, 1):
                confidence = zone['confidence']
                
                with st.expander(f"Zone {idx} - Confidence: {confidence:.0f}%", expanded=(idx==1)):
                    st.progress(confidence / 100)
                    
                    zone_col1, zone_col2 = st.columns(2)
                    with zone_col1:
                        st.metric("Top", format_price(zone['zone_top']))
                        st.metric("Bottom", format_price(zone['zone_bottom']))
                    
                    with zone_col2:
                        st.metric("Distance", f"{zone['distance_from_price']:.2f}%")
                        st.caption(f"Factors: {', '.join(zone['factors'])}")
        else:
            st.info("No supply zones identified")

st.divider()

# Volume Profile
if orchestrator.analysis_cache:
    vp_data = orchestrator.analysis_cache.get('vp_data', {})
    
    if vp_data:
        st.subheader("📊 Volume Profile")
        
        vp_col1, vp_col2, vp_col3 = st.columns(3)
        
        with vp_col1:
            st.metric("POC (Point of Control)", format_price(vp_data.get('poc', 0)))
        
        with vp_col2:
            st.metric("VAH (Value Area High)", format_price(vp_data.get('vah', 0)))
        
        with vp_col3:
            st.metric("VAL (Value Area Low)", format_price(vp_data.get('val', 0)))
        
        # High Volume Nodes
        st.caption("**High Volume Nodes:**")
        hvn = vp_data.get('high_volume_nodes', [])
        if hvn:
            hvn_df = pd.DataFrame(hvn, columns=['Price', 'Volume'])
            st.dataframe(hvn_df, use_container_width=True)

# Refresh button
if st.button("🔄 Refresh Dashboard", use_container_width=True):
    st.rerun()


"""Active trades monitoring page."""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.helpers import format_price, format_percentage

st.set_page_config(page_title="Active Trades - Trade Yoda", page_icon="🎯", layout="wide")

st.title("🎯 Active Trades Monitor")

# Check orchestrator
if 'orchestrator' not in st.session_state or st.session_state.orchestrator is None:
    st.warning("⚠️ Please start Trade Yoda from the main page first")
    st.stop()

# Filters
st.sidebar.header("Filters")

status_options = ['ALL', 'ACTIVE', 'PENDING', 'CLOSED', 'PAPER']
selected_status = st.sidebar.multiselect(
    "Trade Status",
    options=status_options,
    default=['ACTIVE', 'PENDING']
)

direction_filter = st.sidebar.multiselect(
    "Direction",
    options=['CALL', 'PUT'],
    default=['CALL', 'PUT']
)

# Date range
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now().date(), datetime.now().date())
)

# Get trades
all_trades = st.session_state.get('trades', [])

if not all_trades:
    st.info("📭 No trades executed yet. Run trade identification cycle to start.")
    st.stop()

# Apply filters
filtered_trades = all_trades

if 'ALL' not in selected_status:
    filtered_trades = [t for t in filtered_trades if t.get('status') in selected_status]

if direction_filter:
    filtered_trades = [t for t in filtered_trades if t.get('direction') in direction_filter]

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Trades", len(filtered_trades))

with col2:
    active = len([t for t in filtered_trades if t.get('status') == 'ACTIVE'])
    st.metric("Active", active)

with col3:
    total_pnl = sum([t.get('pnl', 0) for t in filtered_trades])
    st.metric("Total P&L", format_price(total_pnl), delta=format_price(total_pnl))

with col4:
    if filtered_trades:
        avg_prob = sum([t.get('probability', 0) for t in filtered_trades]) / len(filtered_trades)
    else:
        avg_prob = 0
    st.metric("Avg Probability", f"{avg_prob:.1f}%")

st.divider()

# Trades table
st.subheader("Trade History")

# Convert to DataFrame
if filtered_trades:
    trades_data = []
    for idx, trade in enumerate(reversed(filtered_trades), 1):
        trades_data.append({
            'ID': idx,
            'Time': trade.get('timestamp', datetime.now()).strftime('%H:%M:%S'),
            'Direction': trade.get('direction', 'N/A'),
            'Entry': format_price(trade.get('entry_price', 0)),
            'Target': format_price(trade.get('target_price', 0)),
            'SL': format_price(trade.get('stop_loss', 0)),
            'RR': f"{trade.get('risk_reward', 0):.2f}",
            'Probability': f"{trade.get('probability', 0):.0f}%",
            'Status': trade.get('status', 'UNKNOWN'),
            'P&L': format_price(trade.get('pnl', 0))
        })
    
    df = pd.DataFrame(trades_data)
    
    # Style the dataframe
    def highlight_pnl(val):
        if 'P&L' in str(val):
            return ''
        try:
            num = float(val.replace('₹', '').replace(',', ''))
            if num > 0:
                return 'background-color: #d4edda'
            elif num < 0:
                return 'background-color: #f8d7da'
        except:
            pass
        return ''
    
    st.dataframe(df, width="stretch", height=400)
    
    st.divider()
    
    # Detailed trade cards
    st.subheader("Trade Details")
    
    for idx, trade in enumerate(reversed(filtered_trades[:10]), 1):
        status = trade.get('status', 'UNKNOWN')
        pnl = trade.get('pnl', 0)
        
        # Determine card style
        if status == 'ACTIVE':
            status_color = '🟡'
            card_style = 'background-color: #fff3cd; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'
        elif pnl > 0:
            status_color = '🟢'
            card_style = 'background-color: #d4edda; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'
        elif pnl < 0:
            status_color = '🔴'
            card_style = 'background-color: #f8d7da; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'
        else:
            status_color = '⚪'
            card_style = 'background-color: #e9ecef; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'
        
        with st.container():
            st.markdown(f'<div style="{card_style}">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.markdown(f"**Trade #{idx}** {status_color}")
                timestamp = trade.get('timestamp', datetime.now())
                st.caption(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            
            with col2:
                direction = trade.get('direction', 'N/A')
                entry = trade.get('entry_price', 0)
                st.markdown(f"**{direction}**")
                st.caption(f"Entry: {format_price(entry)}")
            
            with col3:
                target = trade.get('target_price', 0)
                sl = trade.get('stop_loss', 0)
                st.caption(f"Target: {format_price(target)}")
                st.caption(f"SL: {format_price(sl)}")
            
            with col4:
                st.markdown(f"**{status}**")
                st.markdown(f"**{format_price(pnl)}**")
            
            # Expandable details
            with st.expander("📋 View Full Details"):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**Trade Setup:**")
                    st.caption(f"Risk-Reward: {trade.get('risk_reward', 0):.2f}")
                    st.caption(f"Probability: {trade.get('probability', 0):.0f}%")
                    st.caption(f"Confidence: {trade.get('confidence', 0):.0f}%")
                    st.caption(f"Confluence: {trade.get('confluence_count', 0)} indicators")
                
                with detail_col2:
                    st.markdown("**LLM Analysis:**")
                    reasoning = trade.get('reasoning', 'N/A')
                    st.caption(reasoning[:200] + "..." if len(reasoning) > 200 else reasoning)
            
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("No trades match the selected filters")

# Export functionality
if filtered_trades:
    st.divider()
    
    if st.button("📥 Export to CSV"):
        df_export = pd.DataFrame(trades_data)
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.caption("🧙‍♂️ Trade Yoda - Powered by NeuralVectors Technologies LLP")


"""Main Streamlit application for AI Trading Agent."""
import streamlit as st
import pandas as pd
import asyncio
import nest_asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from orchestrator import TradingOrchestrator
from src.utils.logger import log
from src.utils.helpers import format_price, format_percentage

# Allow nested event loops for Streamlit
nest_asyncio.apply()

# Page config
st.set_page_config(
    page_title="AI Trading Agent - Nifty 50",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .trade-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 5px solid;
    }
    .trade-success {
        background-color: #d4edda;
        border-color: #28a745;
    }
    .trade-pending {
        background-color: #fff3cd;
        border-color: #ffc107;
    }
    .trade-failed {
        background-color: #f8d7da;
        border-color: #dc3545;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'config_updated' not in st.session_state:
    st.session_state.config_updated = False

# Header
st.markdown('<div class="main-header">🤖 AI Trading Agent - Nifty 50 Options</div>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
   
    with st.expander("🔐 API Credentials", expanded=not st.session_state.config_updated):
        dhan_client_id = st.text_input(
            "Dhan Client ID",
            value=config.DHAN_CLIENT_ID,
            type="password",
            help="Your Dhan Client ID from DhanHQ portal"
        )
        dhan_access_token = st.text_input(
            "Dhan Access Token",
            value=config.DHAN_ACCESS_TOKEN,
            type="password",
            help="Your Dhan Access Token"
        )
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=config.OPENAI_API_KEY,
            type="password",
            help="OpenAI API key for GPT-4"
        )
    
    use_sandbox = st.checkbox(
        "🧪 Use Sandbox Environment",
        value=config.USE_SANDBOX,
        help="Enable for paper trading (no real money)"
    )
    
    st.divider()

    # ─────────────── NEW FEATURE FLAGS ───────────────
    st.subheader("🧪 Experimental Features")

    # Backtest mode toggle
    cfg_backtest = st.checkbox(
        "🧪 Enable Backtest Mode",
        value=getattr(config, "USE_BACKTEST_MODE", False),
        help="Load historical candles instead of live‑market data for strategy testing."
    )
    config.USE_BACKTEST_MODE = cfg_backtest

    if cfg_backtest:
        from datetime import date
        c1, c2 = st.columns(2)
        with c1:
            config.BACKTEST_FROM = st.date_input(
                "From Date", value=date(2025, 10, 1))
        with c2:
            config.BACKTEST_TO = st.date_input(
                "To Date", value=date(2025, 10, 5))
        st.info(
            "Backtest mode will bypass market‑hour checks and use Historical Data API"
        )

    # No‑trades‑on‑expiry toggle
    cfg_no_expiry = st.checkbox(
        "🚫 No Trades on Expiry (Tuesday)",
        value=getattr(config, "NO_TRADES_ON_EXPIRY", True),
        help="When enabled, the algo skips any new positions on weekly expiry (Tuesday)."
    )
    config.NO_TRADES_ON_EXPIRY = cfg_no_expiry
    # ───────────────────────────────────────────────
    
    st.subheader("📊 Trading Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_reward = st.number_input(
            "Risk:Reward",
            min_value=1.0,
            max_value=5.0,
            value=config.RISK_REWARD_RATIO,
            step=0.5,
            help="Target risk-reward ratio"
        )
    
    with col2:
        max_risk = st.number_input(
            "Max Risk %",
            min_value=0.5,
            max_value=5.0,
            value=config.MAX_RISK_PERCENTAGE,
            step=0.5,
            help="Maximum risk per trade"
        )
    
    min_probability = st.slider(
        "Min Probability %",
        min_value=50,
        max_value=95,
        value=int(config.MIN_PROBABILITY_THRESHOLD),
        step=5,
        help="Minimum probability threshold for trade execution"
    )
    
    st.divider()
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button(
            "▶️ Start",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.running
        )
    
    with col2:
        stop_button = st.button(
            "⏹️ Stop",
            use_container_width=True,
            disabled=not st.session_state.running
        )
    
    if start_button:
        if dhan_client_id and dhan_access_token and openai_api_key:
            try:
                # Update config
                config.DHAN_CLIENT_ID = dhan_client_id
                config.DHAN_ACCESS_TOKEN = dhan_access_token
                config.OPENAI_API_KEY = openai_api_key
                config.USE_SANDBOX = use_sandbox
                config.RISK_REWARD_RATIO = risk_reward
                config.MAX_RISK_PERCENTAGE = max_risk
                config.MIN_PROBABILITY_THRESHOLD = min_probability
                
                # Initialize orchestrator
                st.session_state.orchestrator = TradingOrchestrator(config)
                st.session_state.orchestrator.start()
                st.session_state.running = True
                st.session_state.config_updated = True
                
                st.success("✅ Agent Started!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to start: {str(e)}")
                log.error(f"Startup error: {str(e)}")
        else:
            st.error("❌ Please provide all API credentials")
    
    if stop_button:
        if st.session_state.orchestrator:
            st.session_state.orchestrator.shutdown()
        st.session_state.running = False
        st.warning("⚠️ Agent Stopped")
        st.rerun()
    
    st.divider()
    
    # System info
    st.subheader("ℹ️ System Info")
    st.caption(f"**Mode:** {'Sandbox' if use_sandbox else 'Production'}")
    st.caption(f"**Status:** {'🟢 Running' if st.session_state.running else '🔴 Stopped'}")
    st.caption(f"**Active Trades:** {len([t for t in st.session_state.trades if t.get('status') == 'ACTIVE'])}")

# Main content
if st.session_state.orchestrator is None:
    # Welcome screen
    st.info("👆 Configure API credentials in the sidebar and click **Start** to begin")
    
    st.markdown("---")
    
    # Features
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Technical Analysis")
        st.markdown("""
        - **Volume Profile** (Fixed & Session)
        - **Order Blocks** Detection
        - **Fair Value Gap** Analysis
        - **Supply/Demand** Zones
        - Multi-timeframe Analysis
        """)
    
    with col2:
        st.markdown("### 🤖 AI-Powered")
        st.markdown("""
        - **GPT-4** Intelligence
        - **Multi-Agent** Architecture
        - **80%** Probability Threshold
        - Real-time Analysis
        - Risk Management
        """)
    
    with col3:
        st.markdown("### 🎯 Auto Execution")
        st.markdown("""
        - Automated Order Placement
        - **Bracket Orders** (SL + Target)
        - Real-time Monitoring
        - **Paper Trading** Support
        - WebSocket Feeds
        """)
    
    st.markdown("---")
    
    # Quick start guide
    with st.expander("📖 Quick Start Guide", expanded=True):
        st.markdown("""
        ### Getting Started
        
        1. **Get API Credentials:**
           - Dhan: Visit [DhanHQ Portal](https://dhanhq.co/docs/v2/)
           - OpenAI: Get key from [OpenAI Platform](https://platform.openai.com)
        
        2. **Configure Settings:**
           - Enter credentials in sidebar
           - Enable Sandbox for paper trading
           - Set risk parameters
        
        3. **Start Trading:**
           - Click "Start" button
           - Monitor dashboard in real-time
           - Review trades and analysis
        
        4. **Safety:**
           - Always start with Sandbox mode
           - Verify all parameters
           - Monitor actively during live trading
        """)

else:
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Dashboard",
        "🎯 Active Trades",
        "📊 Analysis",
        "📋 System Logs"
    ])
    
    with tab1:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_class = "status-running" if st.session_state.running else "status-stopped"
            status_text = "🟢 Running" if st.session_state.running else "🔴 Stopped"
            st.markdown(f'<p class="{status_class}">{status_text}</p>', unsafe_allow_html=True)
        
        with col2:
            active_count = len([t for t in st.session_state.trades if t.get('status') == 'ACTIVE'])
            st.metric("Active Trades", active_count)
        
        with col3:
            total_pnl = sum([t.get('pnl', 0) for t in st.session_state.trades])
            st.metric("Total P&L", format_price(total_pnl), delta=format_price(total_pnl))
        
        with col4:
            if st.session_state.trades:
                wins = len([t for t in st.session_state.trades if t.get('pnl', 0) > 0])
                win_rate = (wins / len(st.session_state.trades)) * 100
            else:
                win_rate = 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        st.divider()
        
        # Analysis controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🔍 Run Zone Analysis (15-min)", use_container_width=True):
                with st.spinner("Analyzing zones..."):
                    try:
                        result = asyncio.run(
                            st.session_state.orchestrator.run_zone_identification_cycle()
                        )
                        if result:
                            st.session_state.last_analysis = result
                            st.success("✅ Zone analysis complete!")
                        else:
                            st.warning("⚠️ No zones identified")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("🎯 Identify Trade (3-min)", use_container_width=True):
                with st.spinner("Identifying trades..."):
                    try:
                        result = asyncio.run(
                            st.session_state.orchestrator.run_trade_identification_cycle()
                        )
                        if result:
                            st.session_state.trades.append(result)
                            st.success(f"✅ Trade identified: {result['trade_setup']['direction']}")
                        else:
                            st.info("ℹ️ No trade opportunities found")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col3:
            if st.button("🔄", use_container_width=True, help="Refresh"):
                st.rerun()
        
        st.divider()
        
        # Current analysis display
        if st.session_state.last_analysis:
            analysis = st.session_state.last_analysis
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Demand Zones")
                demand_zones = analysis['zones'].get('demand_zones', [])[:5]
                
                if demand_zones:
                    for idx, zone in enumerate(demand_zones, 1):
                        st.markdown(f"""
                        **Zone {idx}** - Confidence: {zone['confidence']:.0f}%
                        - Range: {format_price(zone['zone_bottom'])} - {format_price(zone['zone_top'])}
                        - Distance: {zone['distance_from_price']:.2f}%
                        - Factors: {', '.join(zone['factors'])}
                        """)
                        st.progress(zone['confidence'] / 100)
                else:
                    st.info("No demand zones identified")
            
            with col2:
                st.subheader("🎯 Supply Zones")
                supply_zones = analysis['zones'].get('supply_zones', [])[:5]
                
                if supply_zones:
                    for idx, zone in enumerate(supply_zones, 1):
                        st.markdown(f"""
                        **Zone {idx}** - Confidence: {zone['confidence']:.0f}%
                        - Range: {format_price(zone['zone_bottom'])} - {format_price(zone['zone_top'])}
                        - Distance: {zone['distance_from_price']:.2f}%
                        - Factors: {', '.join(zone['factors'])}
                        """)
                        st.progress(zone['confidence'] / 100)
                else:
                    st.info("No supply zones identified")
        else:
            st.info("📊 Run zone analysis to see results")
    
    with tab2:
        st.subheader("🎯 Active Trades")
        
        if st.session_state.trades:
            # Filter controls
            status_filter = st.multiselect(
                "Filter by status",
                options=['ACTIVE', 'CLOSED', 'PAPER', 'PENDING'],
                default=['ACTIVE', 'PENDING']
            )
            
            filtered_trades = [
                t for t in st.session_state.trades
                if t.get('status') in status_filter
            ]
            
            for idx, trade in enumerate(reversed(filtered_trades[-20:]), 1):
                status = trade.get('status', 'UNKNOWN')
                
                if status == 'ACTIVE':
                    card_class = 'trade-pending'
                elif trade.get('pnl', 0) > 0:
                    card_class = 'trade-success'
                else:
                    card_class = 'trade-failed'
                
                with st.container():
                    st.markdown(f'<div class="trade-card {card_class}">', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**Trade #{len(filtered_trades) - idx + 1}**")
                        timestamp = trade.get('timestamp', datetime.now())
                        st.caption(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                    
                    with col2:
                        direction = trade.get('direction', 'N/A')
                        entry = trade.get('entry_price', 0)
                        st.markdown(f"**Direction:** {direction}")
                        st.caption(f"Entry: {format_price(entry)}")
                    
                    with col3:
                        pnl = trade.get('pnl', 0)
                        probability = trade.get('probability', 0)
                        st.markdown(f"**P&L:** {format_price(pnl)}")
                        st.caption(f"Probability: {probability:.0f}%")
                    
                    with col4:
                        status_emoji = {
                            'ACTIVE': '🟡',
                            'CLOSED': '🔵',
                            'PAPER': '📝',
                            'PENDING': '⏳'
                        }.get(status, '❓')
                        st.markdown(f"{status_emoji} **{status}**")
                    
                    # Expandable details
                    with st.expander("View Details"):
                        detail_col1, detail_col2 = st.columns(2)
                        
                        with detail_col1:
                            st.markdown("**Trade Setup:**")
                            st.json(trade.get('trade_setup', {}))
                        
                        with detail_col2:
                            st.markdown("**LLM Evaluation:**")
                            reasoning = trade.get('reasoning', 'N/A')
                            st.markdown(f"_{reasoning}_")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()
        else:
            st.info("📭 No trades executed yet")
    
    with tab3:
        st.subheader("📊 Latest Analysis")
        
        if st.session_state.orchestrator.analysis_cache:
            cache = st.session_state.orchestrator.analysis_cache
            
            # Analysis timestamp
            timestamp = cache.get('timestamp')
            if timestamp:
                st.caption(f"Last updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### Volume Profile")
                vp = cache.get('vp_data', {})
                if vp:
                    st.metric("POC", format_price(vp.get('poc', 0)))
                    st.metric("VAH", format_price(vp.get('vah', 0)))
                    st.metric("VAL", format_price(vp.get('val', 0)))
            
            with col2:
                st.markdown("### Market Context")
                context = cache.get('market_context', {})
                if context:
                    st.metric("Current Price", format_price(context.get('current_price', 0)))
                    st.metric("Trend", context.get('trend', 'N/A'))
                    vol = context.get('volatility', 0)
                    st.metric("Volatility", f"{vol:.4f}")
            
            with col3:
                st.markdown("### LLM Analysis")
                llm = cache.get('llm_analysis', {})
                if llm:
                    bias = llm.get('market_bias', 'N/A')
                    st.metric("Market Bias", bias)
                    
                    st.markdown("**Summary:**")
                    summary = llm.get('analysis_summary', 'N/A')
                    st.info(summary[:200] + "..." if len(summary) > 200 else summary)
            
            st.divider()
            
            # Detailed analysis
            with st.expander("📋 Full Analysis Details"):
                st.json(cache)
        else:
            st.info("📊 Run analysis cycle to see results")
    
    with tab4:
        st.subheader("📋 System Logs")
        
        # Log file viewer
        log_file = config.LOG_FILE
        
        if log_file.exists():
            log_lines = st.slider("Number of log lines", 10, 200, 50)
            
            if st.button("🔄 Refresh Logs"):
                st.rerun()
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_logs = ''.join(lines[-log_lines:])
                    st.code(recent_logs, language='log')
            except Exception as e:
                st.error(f"Error reading logs: {str(e)}")
        else:
            st.warning("Log file not found")

# Footer
st.markdown("---")
st.caption("🤖 AI Trading Agent v1.0.0 | Built with Streamlit | ⚠️ For educational purposes only")


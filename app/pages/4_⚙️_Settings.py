"""Settings and configuration page."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config

st.set_page_config(page_title="Settings - Trade Yoda", page_icon="⚙️", layout="wide")

st.title("⚙️ System Settings")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔐 API Configuration",
    "📊 Trading Parameters",
    "🔔 Alerts",
    "📝 Logs"
])

with tab1:
    st.subheader("API Configuration")
    
    with st.form("api_config_form"):
        st.markdown("#### Dhan API")
        dhan_client_id = st.text_input(
            "Client ID",
            value=config.DHAN_CLIENT_ID,
            type="password"
        )
        dhan_access_token = st.text_input(
            "Access Token",
            value=config.DHAN_ACCESS_TOKEN,
            type="password"
        )
        
        st.markdown("#### OpenAI API")
        openai_key = st.text_input(
            "API Key",
            value=config.OPENAI_API_KEY,
            type="password"
        )
        openai_model = st.selectbox(
            "Model",
            options=["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
            index=0
        )
        
        submitted = st.form_submit_button("💾 Save API Configuration")
        
        if submitted:
            config.DHAN_CLIENT_ID = dhan_client_id
            config.DHAN_ACCESS_TOKEN = dhan_access_token
            config.OPENAI_API_KEY = openai_key
            config.OPENAI_MODEL = openai_model
            
            st.success("✅ API configuration saved!")
            st.info("⚠️ Restart Trade Yoda for changes to take effect")

with tab2:
    st.subheader("Trading Parameters")
    
    with st.form("trading_params_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Risk Management")
            risk_reward = st.number_input(
                "Risk:Reward Ratio",
                min_value=1.0,
                max_value=10.0,
                value=float(config.RISK_REWARD_RATIO),
                step=0.5
            )
            max_risk = st.number_input(
                "Max Risk per Trade (%)",
                min_value=0.5,
                max_value=10.0,
                value=float(config.MAX_RISK_PERCENTAGE),
                step=0.5
            )
            min_probability = st.slider(
                "Min Probability Threshold (%)",
                min_value=50,
                max_value=95,
                value=int(config.MIN_PROBABILITY_THRESHOLD),
                step=5
            )
        
        with col2:
            st.markdown("#### Analysis Settings")
            zone_timeframe = st.number_input(
                "Zone Identification Timeframe (minutes)",
                min_value=5,
                max_value=60,
                value=config.ZONE_TIMEFRAME,
                step=5
            )
            trade_timeframe = st.number_input(
                "Trade Identification Timeframe (minutes)",
                min_value=1,
                max_value=15,
                value=config.TRADE_TIMEFRAME,
                step=1
            )
            vp_value_area = st.slider(
                "Volume Profile Value Area (%)",
                min_value=60,
                max_value=80,
                value=int(config.VP_VALUE_AREA),
                step=5
            )
        
        st.markdown("#### Technical Indicators - Classic")
        col3, col4 = st.columns(2)
        
        with col3:
            ob_lookback = st.number_input(
                "Order Block Lookback Period",
                min_value=10,
                max_value=50,
                value=config.OB_LOOKBACK,
                step=5
            )
        
        with col4:
            fvg_min_size = st.number_input(
                "Fair Value Gap Min Size (%)",
                min_value=0.001,
                max_value=1.0,
                value=config.FVG_MIN_SIZE,
                step=0.001,
                format="%.3f"
            )
        
        st.markdown("#### Technical Indicators - RSI & Bollinger Bands")
        col5, col6 = st.columns(2)
        
        with col5:
            rsi_period = st.number_input(
                "RSI Period",
                min_value=5,
                max_value=30,
                value=getattr(config, 'RSI_PERIOD', 14),
                step=1
            )
            rsi_overbought = st.number_input(
                "RSI Overbought Level",
                min_value=60.0,
                max_value=90.0,
                value=float(getattr(config, 'RSI_OVERBOUGHT', 70)),
                step=5.0
            )
            rsi_oversold = st.number_input(
                "RSI Oversold Level",
                min_value=10.0,
                max_value=40.0,
                value=float(getattr(config, 'RSI_OVERSOLD', 30)),
                step=5.0
            )
        
        with col6:
            bb_period = st.number_input(
                "Bollinger Bands Period",
                min_value=10,
                max_value=50,
                value=getattr(config, 'BB_PERIOD', 20),
                step=5
            )
            bb_std_dev = st.number_input(
                "Bollinger Bands Std Deviation",
                min_value=1.0,
                max_value=3.0,
                value=float(getattr(config, 'BB_STD_DEV', 2.0)),
                step=0.5
            )
        
        st.markdown("#### Pattern Detection")
        col7, col8 = st.columns(2)
        
        with col7:
            enable_candle_patterns = st.checkbox(
                "Enable Candlestick Patterns",
                value=getattr(config, 'ENABLE_CANDLESTICK_PATTERNS', True)
            )
        
        with col8:
            enable_chart_patterns = st.checkbox(
                "Enable Chart Patterns",
                value=getattr(config, 'ENABLE_CHART_PATTERNS', True)
            )
        
        min_pattern_confidence = st.slider(
            "Minimum Pattern Confidence (%)",
            min_value=50,
            max_value=90,
            value=int(getattr(config, 'MIN_PATTERN_CONFIDENCE', 70)),
            step=5
        )
        
        submitted = st.form_submit_button("💾 Save Trading Parameters")
        
        if submitted:
            config.RISK_REWARD_RATIO = risk_reward
            config.MAX_RISK_PERCENTAGE = max_risk
            config.MIN_PROBABILITY_THRESHOLD = min_probability
            config.ZONE_TIMEFRAME = zone_timeframe
            config.TRADE_TIMEFRAME = trade_timeframe
            config.VP_VALUE_AREA = vp_value_area
            config.OB_LOOKBACK = ob_lookback
            config.FVG_MIN_SIZE = fvg_min_size
            
            # NEW parameters
            config.RSI_PERIOD = rsi_period
            config.RSI_OVERBOUGHT = rsi_overbought
            config.RSI_OVERSOLD = rsi_oversold
            config.BB_PERIOD = bb_period
            config.BB_STD_DEV = bb_std_dev
            config.ENABLE_CANDLESTICK_PATTERNS = enable_candle_patterns
            config.ENABLE_CHART_PATTERNS = enable_chart_patterns
            config.MIN_PATTERN_CONFIDENCE = min_pattern_confidence
            
            st.success("✅ Trading parameters saved!")

with tab3:
    st.subheader("Alert Configuration")
    
    st.info("🚧 Alert system coming soon!")
    
    st.markdown("#### Planned Features:")
    st.markdown("""
    - 📧 Email notifications
    - 📱 Telegram alerts
    - 🔔 Discord webhooks
    - 📊 Trade execution alerts
    - ⚠️ Risk warnings
    - 🎯 Zone proximity alerts
    - 📈 RSI overbought/oversold alerts
    - 📊 Bollinger Band breakout alerts
    - 🕯️ Candlestick pattern alerts
    """)

with tab4:
    st.subheader("System Logs")
    
    log_level = st.selectbox(
        "Log Level",
        options=["DEBUG", "INFO", "WARNING", "ERROR"],
        index=1
    )
    
    log_lines = st.slider("Number of log lines to display", 10, 500, 100)
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    # Display logs
    log_file = config.LOG_FILE
    
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
                # Filter by log level if needed
                filtered_lines = [l for l in lines if log_level in l] if log_level != "INFO" else lines
                
                recent_logs = ''.join(filtered_lines[-log_lines:])
                st.code(recent_logs, language='log', line_numbers=True)
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")
    else:
        st.warning("Log file not found")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Logs", use_container_width=True):
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                st.download_button(
                    label="Download",
                    data=log_content,
                    file_name=f"logs_{log_file.stem}.log",
                    mime="text/plain"
                )
    
    with col2:
        if st.button("🗑️ Clear Logs", use_container_width=True):
            if log_file.exists():
                with open(log_file, 'w') as f:
                    f.write("")
                st.success("✅ Logs cleared!")

# Footer
st.markdown("---")
st.caption("🧙‍♂️ Trade Yoda - Powered by NeuralVectors Technologies LLP")


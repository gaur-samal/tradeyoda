"""Analysis and insights page."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.helpers import format_price

st.set_page_config(page_title="Analysis - Trade Yoda", page_icon="📈", layout="wide")

st.title("📈 Market Analysis & Insights")

# Check orchestrator
if 'orchestrator' not in st.session_state or st.session_state.orchestrator is None:
    st.warning("⚠️ Please start Trade Yoda from the main page first")
    st.stop()

orchestrator = st.session_state.orchestrator

# Analysis cache
if not orchestrator.analysis_cache:
    st.info("📊 No analysis data available. Run analysis cycle from main dashboard.")
    st.stop()

cache = orchestrator.analysis_cache

# Tabs for different analysis
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Volume Profile",
    "📦 Order Blocks",
    "⚡ Fair Value Gaps",
    "📈 RSI & Bollinger Bands",
    "🕯️ Patterns",
    "🤖 LLM Analysis"
])

with tab1:
    st.subheader("Volume Profile Analysis")
    
    vp_data = cache.get('vp_data', {})
    
    if vp_data:
        # Key levels
        col1, col2, col3 = st.columns(3)
        
        with col1:
            poc = vp_data.get('poc', 0)
            st.metric("POC (Point of Control)", format_price(poc))
            st.caption("Price level with highest trading volume")
        
        with col2:
            vah = vp_data.get('vah', 0)
            st.metric("VAH (Value Area High)", format_price(vah))
            st.caption("Upper boundary of 70% volume area")
        
        with col3:
            val = vp_data.get('val', 0)
            st.metric("VAL (Value Area Low)", format_price(val))
            st.caption("Lower boundary of 70% volume area")
        
        st.divider()
        
        # High and Low Volume Nodes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔊 High Volume Nodes")
            hvn = vp_data.get('high_volume_nodes', [])
            if hvn:
                hvn_data = []
                for price, volume in hvn:
                    hvn_data.append({
                        'Price': format_price(price),
                        'Volume': f"{volume:,.0f}",
                        'Type': 'Support/Resistance'
                    })
                st.dataframe(pd.DataFrame(hvn_data), width="stretch")
                st.caption("High volume areas often act as strong support/resistance")
        
        with col2:
            st.markdown("#### 🔇 Low Volume Nodes")
            lvn = vp_data.get('low_volume_nodes', [])
            if lvn:
                lvn_data = []
                for price, volume in lvn:
                    lvn_data.append({
                        'Price': format_price(price),
                        'Volume': f"{volume:,.0f}",
                        'Type': 'Low Interest'
                    })
                st.dataframe(pd.DataFrame(lvn_data), width="stretch")
                st.caption("Low volume areas may see quick price movement")
        
        st.divider()
        
        # Volume Profile visualization
        st.markdown("#### 📊 Volume Distribution")
        volume_profile = vp_data.get('volume_profile', {})
        
        if volume_profile:
            vp_df = pd.DataFrame([
                {'Price': price, 'Volume': volume}
                for price, volume in sorted(volume_profile.items())
            ])
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=vp_df['Volume'],
                y=vp_df['Price'],
                orientation='h',
                marker_color='rgba(102, 126, 234, 0.6)'
            ))
            
            # Add POC line
            fig.add_hline(y=poc, line_dash="dash", line_color="red",
                         annotation_text="POC", annotation_position="right")
            
            # Add VAH/VAL lines
            fig.add_hline(y=vah, line_dash="dot", line_color="green",
                         annotation_text="VAH", annotation_position="right")
            fig.add_hline(y=val, line_dash="dot", line_color="green",
                         annotation_text="VAL", annotation_position="right")
            
            fig.update_layout(
                title="Volume Profile Distribution",
                xaxis_title="Volume",
                yaxis_title="Price",
                height=500
            )
            
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("No volume profile data available")

with tab2:
    st.subheader("Order Blocks Analysis")
    
    zones = cache.get('zones', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 Bullish Order Blocks (Demand)")
        demand_zones = zones.get('demand_zones', [])
        
        if demand_zones:
            for idx, zone in enumerate(demand_zones, 1):
                with st.expander(f"Zone {idx} - Confidence: {zone['confidence']:.0f}%"):
                    st.progress(zone['confidence'] / 100)
                    
                    zone_col1, zone_col2 = st.columns(2)
                    with zone_col1:
                        st.metric("Zone Top", format_price(zone['zone_top']))
                        st.metric("Zone Bottom", format_price(zone['zone_bottom']))
                    
                    with zone_col2:
                        st.metric("Distance from Price", f"{zone['distance_from_price']:.2f}%")
                        st.caption(f"**Factors:** {', '.join(zone['factors'])}")
                    
                    st.markdown("**Analysis:**")
                    st.info(f"This demand zone has {zone['confidence']:.0f}% confidence based on {len(zone['factors'])} confirming factors.")
        else:
            st.info("No bullish order blocks identified")
    
    with col2:
        st.markdown("#### 🔴 Bearish Order Blocks (Supply)")
        supply_zones = zones.get('supply_zones', [])
        
        if supply_zones:
            for idx, zone in enumerate(supply_zones, 1):
                with st.expander(f"Zone {idx} - Confidence: {zone['confidence']:.0f}%"):
                    st.progress(zone['confidence'] / 100)
                    
                    zone_col1, zone_col2 = st.columns(2)
                    with zone_col1:
                        st.metric("Zone Top", format_price(zone['zone_top']))
                        st.metric("Zone Bottom", format_price(zone['zone_bottom']))
                    
                    with zone_col2:
                        st.metric("Distance from Price", f"{zone['distance_from_price']:.2f}%")
                        st.caption(f"**Factors:** {', '.join(zone['factors'])}")
                    
                    st.markdown("**Analysis:**")
                    st.info(f"This supply zone has {zone['confidence']:.0f}% confidence based on {len(zone['factors'])} confirming factors.")
        else:
            st.info("No bearish order blocks identified")

with tab3:
    st.subheader("Fair Value Gaps (FVG)")
    
    st.markdown("""
    Fair Value Gaps represent price imbalances where price moved too quickly,
    leaving gaps that often get filled later.
    """)
    
    # This would need FVG data from cache
    st.info("Fair Value Gap visualization - Implementation pending")

with tab4:
    st.subheader("📈 RSI & Bollinger Bands Analysis")
    
    tech_indicators = cache.get('technical_indicators', {})
    
    if tech_indicators:
        # RSI Section
        st.markdown("### RSI (Relative Strength Index)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rsi = tech_indicators.get('latest_rsi')
            if rsi:
                st.metric("Current RSI", f"{rsi:.2f}")
        
        with col2:
            rsi_signal = tech_indicators.get('rsi_signal', 'NEUTRAL')
            st.metric("Signal", rsi_signal)
        
        with col3:
            if rsi:
                if rsi > 70:
                    st.error("⚠️ Overbought Zone")
                elif rsi < 30:
                    st.success("✅ Oversold Zone")
                else:
                    st.info("📊 Neutral Zone")
        
        st.markdown("""
        **RSI Interpretation:**
        - **Above 70:** Overbought - potential reversal down
        - **Below 30:** Oversold - potential reversal up
        - **50-70:** Bullish momentum
        - **30-50:** Bearish momentum
        """)
        
        st.divider()
        
        # Bollinger Bands Section
        st.markdown("### Bollinger Bands")
        
        bb_data = tech_indicators.get('bollinger_bands', {})
        bb_position = tech_indicators.get('bb_position', 'N/A')
        
        if bb_data:
            bb_col1, bb_col2 = st.columns(2)
            
            with bb_col1:
                st.metric("Current Position", bb_position)
                
                if bb_position == 'ABOVE_UPPER':
                    st.warning("⚠️ Price above upper band - Potential reversal or strong trend")
                elif bb_position == 'BELOW_LOWER':
                    st.success("✅ Price below lower band - Potential bounce or strong decline")
                else:
                    st.info("📊 Price within bands - Normal range")
            
            with bb_col2:
                st.markdown("**Band Levels:**")
                if not bb_data.get('upper_band').empty:
                    upper = bb_data['upper_band'].iloc[-1]
                    middle = bb_data['middle_band'].iloc[-1]
                    lower = bb_data['lower_band'].iloc[-1]
                    bandwidth = bb_data['bandwidth'].iloc[-1]
                    
                    st.caption(f"Upper Band: {format_price(upper)}")
                    st.caption(f"Middle Band (SMA): {format_price(middle)}")
                    st.caption(f"Lower Band: {format_price(lower)}")
                    st.caption(f"Bandwidth: {bandwidth:.2f}%")
        
        st.markdown("""
        **Bollinger Bands Interpretation:**
        - **Price at Upper Band:** Potential overbought, watch for reversal
        - **Price at Lower Band:** Potential oversold, watch for bounce
        - **Squeeze (Narrow Bands):** Low volatility, potential breakout coming
        - **Expansion (Wide Bands):** High volatility, strong trend in progress
        """)
    else:
        st.info("No RSI or Bollinger Bands data available")

with tab5:
    st.subheader("🕯️ Candlestick & Chart Patterns")
    
    tech_indicators = cache.get('technical_indicators', {})
    
    if tech_indicators:
        pattern_col1, pattern_col2 = st.columns(2)
        
        with pattern_col1:
            st.markdown("### 🕯️ Candlestick Patterns")
            
            candle_patterns = tech_indicators.get('candlestick_patterns', [])
            
            if candle_patterns:
                st.caption(f"**Found {len(candle_patterns)} patterns**")
                
                for pattern in candle_patterns[-10:]:  # Show last 10
                    signal_emoji = {
                        'BULLISH': '🟢',
                        'BEARISH': '🔴',
                        'NEUTRAL': '🟡'
                    }.get(pattern['signal'], '⚪')
                    
                    with st.expander(f"{signal_emoji} {pattern['pattern']} - {pattern['confidence']}%"):
                        st.caption(f"**Signal:** {pattern['signal']}")
                        st.caption(f"**Confidence:** {pattern['confidence']}%")
                        st.caption(f"**Time:** {pattern['timestamp']}")
                        st.progress(pattern['confidence'] / 100)
                
                st.markdown("""
                **Common Patterns:**
                - **Bullish Engulfing:** Strong bullish reversal
                - **Bearish Engulfing:** Strong bearish reversal
                - **Hammer:** Bullish reversal at support
                - **Shooting Star:** Bearish reversal at resistance
                - **Doji:** Indecision, potential reversal
                - **Morning Star:** Strong bullish reversal (3-candle)
                - **Evening Star:** Strong bearish reversal (3-candle)
                """)
            else:
                st.info("No candlestick patterns detected")
        
        with pattern_col2:
            st.markdown("### 📈 Chart Patterns")
            
            chart_patterns = tech_indicators.get('chart_patterns', [])
            
            if chart_patterns:
                st.caption(f"**Found {len(chart_patterns)} patterns**")
                
                for pattern in chart_patterns[-10:]:  # Show last 10
                    signal_emoji = {
                        'BULLISH': '🟢',
                        'BEARISH': '🔴',
                        'NEUTRAL': '🟡'
                    }.get(pattern['signal'], '⚪')
                    
                    with st.expander(f"{signal_emoji} {pattern['pattern']} - {pattern['confidence']}%"):
                        st.caption(f"**Signal:** {pattern['signal']}")
                        st.caption(f"**Confidence:** {pattern['confidence']}%")
                        st.caption(f"**Time:** {pattern['timestamp']}")
                        
                        if 'resistance' in pattern:
                            st.caption(f"**Resistance:** {format_price(pattern['resistance'])}")
                        if 'support' in pattern:
                            st.caption(f"**Support:** {format_price(pattern['support'])}")
                        if 'neckline' in pattern:
                            st.caption(f"**Neckline:** {format_price(pattern['neckline'])}")
                        
                        st.progress(pattern['confidence'] / 100)
                
                st.markdown("""
                **Common Chart Patterns:**
                - **Double Top:** Bearish reversal at resistance
                - **Double Bottom:** Bullish reversal at support
                - **Head & Shoulders:** Strong bearish reversal
                - **Inverse H&S:** Strong bullish reversal
                - **Triangle:** Continuation pattern, breakout expected
                """)
            else:
                st.info("No chart patterns detected")
    else:
        st.info("No pattern data available")

with tab6:
    st.subheader("🤖 GPT-4 Analysis")
    
    llm_analysis = cache.get('llm_analysis', {})
    
    if llm_analysis:
        # Market Bias
        bias = llm_analysis.get('market_bias', 'Neutral')
        bias_emoji = {'Bullish': '🟢', 'Bearish': '🔴', 'Neutral': '🟡'}.get(bias, '⚪')
        
        st.markdown(f"### Market Bias: {bias_emoji} {bias}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Primary Zones")
            
            demand_zone = llm_analysis.get('primary_demand_zone', {})
            if demand_zone:
                st.markdown("**Demand Zone:**")
                st.metric("Top", format_price(demand_zone.get('top', 0)))
                st.metric("Bottom", format_price(demand_zone.get('bottom', 0)))
                st.progress(demand_zone.get('confidence', 0) / 100)
            
            supply_zone = llm_analysis.get('primary_supply_zone', {})
            if supply_zone:
                st.markdown("**Supply Zone:**")
                st.metric("Top", format_price(supply_zone.get('top', 0)))
                st.metric("Bottom", format_price(supply_zone.get('bottom', 0)))
                st.progress(supply_zone.get('confidence', 0) / 100)
        
        with col2:
            st.markdown("#### ⚠️ Risk Factors")
            risk_factors = llm_analysis.get('risk_factors', [])
            if risk_factors:
                for risk in risk_factors:
                    st.warning(f"• {risk}")
            else:
                st.success("No significant risk factors identified")
        
        st.divider()
        
        # NEW: Additional LLM insights
        st.markdown("#### 🎯 Multi-Indicator Confluence")
        
        conf_col1, conf_col2, conf_col3 = st.columns(3)
        
        with conf_col1:
            rsi_impact = llm_analysis.get('rsi_impact', 'neutral')
            st.metric("RSI Impact", rsi_impact)
        
        with conf_col2:
            bb_impact = llm_analysis.get('bb_impact', 'neutral')
            st.metric("BB Impact", bb_impact)
        
        with conf_col3:
            pattern_conf = llm_analysis.get('pattern_confluence', 'weak')
            st.metric("Pattern Confluence", pattern_conf)
        
        st.divider()
        
        # Entry Signals
        st.markdown("#### 🎯 Entry Signals")
        entry_signals = llm_analysis.get('entry_signals', [])
        if entry_signals:
            for signal in entry_signals:
                st.info(f"✅ {signal}")
        
        st.divider()
        
        # Analysis Summary
        st.markdown("#### 📝 Analysis Summary")
        summary = llm_analysis.get('analysis_summary', 'No summary available')
        st.markdown(summary)
        
        # Market Context
        st.divider()
        st.markdown("#### 📈 Market Context")
        
        context = cache.get('market_context', {})
        context_col1, context_col2, context_col3 = st.columns(3)
        
        with context_col1:
            st.metric("Current Price", format_price(context.get('current_price', 0)))
        
        with context_col2:
            st.metric("Trend", context.get('trend', 'N/A'))
        
        with context_col3:
            volatility = context.get('volatility', 0)
            st.metric("Volatility", f"{volatility:.4f}")
    else:
        st.info("No LLM analysis available")

# Refresh button
st.divider()
if st.button("🔄 Refresh Analysis", width="stretch"):
    st.rerun()

# Footer
st.markdown("---")
st.caption("🧙‍♂️ Trade Yoda - Powered by NeuralVectors Technologies LLP")



"""LLM-powered analysis agent for intelligent decision making."""
from openai import OpenAI
from typing import Dict, Callable, List
import pandas as pd
import numpy as np
import json
from src.utils.logger import log
from src.config import config


class LLMAnalysisAgent:
    """Agent using GPT-4 for market analysis and trade decisions."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = config.OPENAI_MODEL
    
    def analyze_zones(self, technical_data: Dict, market_context: Dict) -> Dict:
        """
        Use LLM to analyze and validate demand/supply zones.
        
        Args:
            technical_data: Technical analysis results
            market_context: Current market conditions
        
        Returns:
            dict: LLM analysis results
        """
        prompt = f"""
You are an expert market analyst specializing in technical analysis for Nifty 50/BankNifty Futures and options trading.

Analyze the following technical data and provide your assessment:

VOLUME PROFILE DATA:
- Point of Control (POC): {technical_data.get('poc')}
- Value Area High (VAH): {technical_data.get('vah')}
- Value Area Low (VAL): {technical_data.get('val')}

DEMAND ZONES (with confidence):
{json.dumps(technical_data.get('demand_zones', [])[:3], indent=2)}

SUPPLY ZONES (with confidence):
{json.dumps(technical_data.get('supply_zones', [])[:3], indent=2)}

CURRENT MARKET CONTEXT:
- Current Price: {technical_data.get('current_price')}
- Trend: {market_context.get('trend', 'Unknown')}
- Market Volatility: {market_context.get('volatility', 'Unknown')}
- RSI: {market_context.get('rsi', 'N/A')} ({market_context.get('rsi_signal', 'N/A')})
- Bollinger Band Position: {market_context.get('bb_position', 'N/A')}

RECENT CANDLESTICK PATTERNS:
{json.dumps(market_context.get('recent_candlestick_patterns', []), indent=2, default=str)}

RECENT CHART PATTERNS:
{json.dumps(market_context.get('recent_chart_patterns', []), indent=2, default=str)}

Consider the following in your analysis:
1. Validate the strongest demand and supply zones
2. Assess confluence of multiple indicators (Volume Profile + Order Blocks + FVG + RSI + Bollinger Bands)
3. Evaluate candlestick patterns for entry/exit confirmation
4. Consider chart patterns for trend continuation or reversal signals
5. RSI overbought/oversold conditions and divergences
6. Price position relative to Bollinger Bands (potential reversal signals)
7. Identify the highest probability trading opportunities
8. Rate your confidence in each zone (0-100%)

Respond in JSON format with:
{{
    "primary_demand_zone": {{"top": float, "bottom": float, "confidence": float}},
    "primary_supply_zone": {{"top": float, "bottom": float, "confidence": float}},
    "market_bias": "bullish|bearish|neutral",
    "rsi_impact": "supports bias|contradicts bias|neutral",
    "bb_impact": "expansion|contraction|neutral",
    "pattern_confluence": "strong|moderate|weak",
    "analysis_summary": "detailed explanation including all technical factors",
    "risk_factors": ["list of risks"],
    "entry_signals": ["list of bullish/bearish signals present"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional trading analyst specializing in multi-indicator confluence analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            log.info(f"LLM Zone Analysis: Bias={analysis.get('market_bias')}, "
                    f"RSI Impact={analysis.get('rsi_impact')}, "
                    f"Pattern Confluence={analysis.get('pattern_confluence')}")
            return analysis
            
        except Exception as e:
            log.error(f"LLM analysis error: {str(e)}")
            return {
                "market_bias": "neutral",
                "rsi_impact": "neutral",
                "bb_impact": "neutral",
                "pattern_confluence": "weak",
                "analysis_summary": "Analysis failed",
                "risk_factors": ["LLM analysis unavailable"]
            }

    def validate_and_enhance_zones(
        self,
        candidate_zones: Dict,
        price_data: pd.DataFrame,
        technical_indicators: Dict,
        market_context: Dict
    ) -> Dict:
        """
        LLM validates rule-based zones and provides enhanced analysis.
        
        This is the hybrid approach:
        1. Rule-based system finds zone candidates
        2. LLM validates quality and ranks by strength
        3. LLM provides reasoning for each zone
        """
        try:
            # Prepare data for LLM
            current_price = float(price_data['close'].iloc[-1])
            recent_action = self._format_recent_price_action(price_data)
            
            # Get swing points for reference
            swing_highs = self._find_swing_points(price_data, 'high')
            swing_lows = self._find_swing_points(price_data, 'low')
            
            prompt = f"""You are an expert technical analyst for Nifty/BankNifty Futures intraday trading.

CURRENT MARKET STATE:
- Current Price: {current_price:.2f}
- Timeframe: 15-minute
- Trend: {market_context.get('trend', 'Unknown')}
- Volatility: {market_context.get('volatility', 0):.4f}
- RSI: {technical_indicators.get('latest_rsi', 'N/A')} ({technical_indicators.get('rsi_signal', 'N/A')})
- Bollinger Band Position: {technical_indicators.get('bb_position', 'N/A')}

RECENT PRICE ACTION (Last 20 candles):
{recent_action}

SWING HIGHS (Potential Resistance):
{json.dumps(swing_highs, indent=2)}

SWING LOWS (Potential Support):
{json.dumps(swing_lows, indent=2)}

CANDIDATE ZONES FOUND BY ALGORITHM:

DEMAND ZONES (Support - Bullish):
{json.dumps(candidate_zones.get('demand_zones', [])[:5], indent=2, default=str)}

SUPPLY ZONES (Resistance - Bearish):
{json.dumps(candidate_zones.get('supply_zones', [])[:5], indent=2, default=str)}

VOLUME PROFILE:
- Point of Control (POC): {candidate_zones.get('poc', 'N/A')}
- Value Area High (VAH): {candidate_zones.get('vah', 'N/A')}
- Value Area Low (VAL): {candidate_zones.get('val', 'N/A')}

TASK:
Validate and enhance these zones for INTRADAY trading (zones must be usable within same day):

1. **Validate each zone** - Mark as VALID or INVALID based on:
   - Zone quality (clear rejection with volume)
   - Freshness (not heavily tested recently)
   - Distance from current price (< 300 points for intraday)
   - Confluence with volume profile or swing points
   - Price action context

2. **Rank valid zones** by strength (1-10 scale):
   - 9-10: Extremely strong (multiple confirmations)
   - 7-8: Strong (good setup)
   - 5-6: Moderate (watchlist)
   - Below 5: Weak (ignore)

3. **Assign realistic confidence** (0-100%):
   - Consider RSI overbought/oversold at zone
   - Bollinger Band squeeze/expansion
   - Recent candlestick patterns
   - Volume confirmation

4. **Remove or merge zones that**:
   - Are >300 points away (too far for intraday)
   - Have been broken through
   - Are too close together (<20 points - merge them)
   - Lack volume confirmation

5. **Provide specific reasoning** for top 3 of each type

Return JSON with TOP 3 DEMAND and TOP 3 SUPPLY zones only:

{{
  "demand_zones": [
    {{
      "zone_top": float,
      "zone_bottom": float,
      "strength": int (1-10),
      "confidence": int (0-100),
      "touches": int,
      "distance_from_price_points": float,
      "is_fresh": boolean,
      "confluence_factors": ["list of factors"],
      "reasoning": "1-2 sentence explanation",
      "entry_signal": "STRONG|MODERATE|WEAK",
      "rsi_support": boolean,
      "volume_confirmed": boolean
    }}
  ],
  "supply_zones": [
    {{
      "zone_top": float,
      "zone_bottom": float,
      "strength": int (1-10),
      "confidence": int (0-100),
      "touches": int,
      "distance_from_price_points": float,
      "is_fresh": boolean,
      "confluence_factors": ["list of factors"],
      "reasoning": "1-2 sentence explanation",
      "entry_signal": "STRONG|MODERATE|WEAK",
      "rsi_support": boolean,
      "volume_confirmed": boolean
    }}
  ],
  "market_assessment": "Overall market bias and key levels",
  "primary_bias": "BULLISH|BEARISH|NEUTRAL",
  "intraday_range_estimate": {{"high": float, "low": float}},
  "rejected_zones_count": int,
  "key_levels_to_watch": [list of critical price levels]
}}

IMPORTANT:
- Focus on INTRADAY relevance (zones within reach today)
- Prioritize fresh zones over tested ones
- Consider current RSI and BB position for entries
- Zones should be 20-30 point ranges for Nifty and 10-20 point range for BankNifty.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional technical analyst specializing in intraday Nifty/BankNifty Futures trading with expertise in supply/demand zones, volume profile analysis, and multi-indicator confluence."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent analysis
                response_format={"type": "json_object"}
            )
            
            enhanced_zones = json.loads(response.choices[0].message.content)
            
            log.info(f"✅ LLM Zone Enhancement Complete:")
            log.info(f"   Valid Demand Zones: {len(enhanced_zones.get('demand_zones', []))}")
            log.info(f"   Valid Supply Zones: {len(enhanced_zones.get('supply_zones', []))}")
            log.info(f"   Market Bias: {enhanced_zones.get('primary_bias', 'Unknown')}")
            log.info(f"   Rejected Zones: {enhanced_zones.get('rejected_zones_count', 0)}")
            
            return enhanced_zones
            
        except Exception as e:
            log.error(f"LLM zone enhancement error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            
            # Fallback to original zones if LLM fails
            return {
                "demand_zones": candidate_zones.get('demand_zones', [])[:3],
                "supply_zones": candidate_zones.get('supply_zones', [])[:3],
                "market_assessment": "LLM analysis unavailable - using rule-based zones",
                "primary_bias": "NEUTRAL",
                "rejected_zones_count": 0
            }

    def _format_recent_price_action(self, df: pd.DataFrame, num_candles: int = 20) -> str:
        """Format recent candles for LLM context."""
        try:
            recent = df.tail(num_candles)
            formatted = []
            
            for idx, (i, row) in enumerate(recent.iterrows(), 1):
                candle_type = "🟢" if row['close'] > row['open'] else "🔴"
                formatted.append(
                    f"{idx}. {candle_type} O:{row['open']:.2f} H:{row['high']:.2f} "
                    f"L:{row['low']:.2f} C:{row['close']:.2f} V:{int(row['volume'])}"
                )
            
            return "\n".join(formatted)
        except Exception as e:
            log.error(f"Error formatting price action: {e}")
            return "Price action data unavailable"
    
    def _find_swing_points(
        self,
        df: pd.DataFrame,
        column: str,
        window: int = 5,
        max_points: int = 8
    ) -> List[Dict]:
        """Find swing highs/lows for zone confluence."""
        try:
            swings = []
            
            for i in range(window, len(df) - window):
                if column == 'high':
                    if df[column].iloc[i] == df[column].iloc[i-window:i+window+1].max():
                        swings.append({
                            'price': float(df[column].iloc[i]),
                            'timestamp': str(df['timestamp'].iloc[i]) if 'timestamp' in df.columns else str(df.index[i]),
                            'volume': float(df['volume'].iloc[i]) if 'volume' in df.columns else 0
                        })
                else:  # low
                    if df[column].iloc[i] == df[column].iloc[i-window:i+window+1].min():
                        swings.append({
                            'price': float(df[column].iloc[i]),
                            'timestamp': str(df['timestamp'].iloc[i]) if 'timestamp' in df.columns else str(df.index[i]),
                            'volume': float(df['volume'].iloc[i]) if 'volume' in df.columns else 0
                        })
            
            # Return most recent swing points
            return swings[-max_points:] if swings else []
            
        except Exception as e:
            log.error(f"Error finding swing points: {e}")
            return []


    def evaluate_trade_setup(self, trade_data: Dict) -> Dict:
        """
        Evaluate if a trade setup meets the probability threshold.
        
        Args:
            trade_data: Complete trade setup information
        
        Returns:
            dict: Trade evaluation results
        """
        prompt = f"""
Evaluate this options trade setup for Nifty 50/BankNifty:

TRADE DETAILS:
{json.dumps(trade_data, indent=2, default=str)}

Consider:
1. Technical confluence (Volume Profile + Order Blocks + FVG alignment)
2. RSI positioning and divergence signals
3. Bollinger Band squeeze or expansion signals
4. Candlestick pattern confirmation at entry point
5. Chart pattern support for directional bias
6. Risk-Reward ratio (target 1:3)
7. Zone strength and validation
8. Market conditions and trends
9. Options analysis and positioning

EVALUATION CRITERIA:
- Strong confluence of 3+ indicators = Higher probability
- RSI confirming direction (oversold for buy, overbought for sell)
- Candlestick reversal pattern at zone
- Chart pattern alignment with trade direction
- Clean price action with clear stop loss level

Assess if this trade has >= 70% probability of hitting the target before stop loss.

Respond in JSON:
{{
    "trade_approved": true/false,
    "probability_estimate": float (0-100),
    "confidence_score": float (0-100),
    "confluence_count": int (number of confirming indicators),
    "reasoning": "detailed explanation covering all technical factors",
    "risk_assessment": "low|medium|high",
    "recommendations": ["list of suggestions"],
    "entry_confirmation": "strong|moderate|weak",
    "key_supporting_factors": ["list of bullish/bearish factors"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a risk management expert for options trading with expertise in multi-indicator confluence analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            evaluation = json.loads(response.choices[0].message.content)
            
            log.info(
                f"Trade Evaluation: Approved={evaluation.get('trade_approved')}, "
                f"Probability={evaluation.get('probability_estimate')}%, "
                f"Confluence={evaluation.get('confluence_count')}, "
                f"Entry Confirmation={evaluation.get('entry_confirmation')}"
            )
            
            return evaluation
            
        except Exception as e:
            log.error(f"Trade evaluation error: {str(e)}")
            return {
                "trade_approved": False,
                "probability_estimate": 0,
                "confidence_score": 0,
                "confluence_count": 0,
                "reasoning": f"Evaluation failed: {str(e)}",
                "risk_assessment": "high",
                "entry_confirmation": "weak"
            }


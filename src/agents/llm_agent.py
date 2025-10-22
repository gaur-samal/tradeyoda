"""LLM-powered analysis agent for intelligent decision making."""
from openai import OpenAI
from typing import Dict, Callable
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
You are an expert market analyst specializing in technical analysis for Nifty 50 Futures and options trading.

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
    
    def evaluate_trade_setup(self, trade_data: Dict) -> Dict:
        """
        Evaluate if a trade setup meets the probability threshold.
        
        Args:
            trade_data: Complete trade setup information
        
        Returns:
            dict: Trade evaluation results
        """
        prompt = f"""
Evaluate this options trade setup for Nifty 50:

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

Assess if this trade has >= 80% probability of hitting the target before stop loss.

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


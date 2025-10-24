"""Options analysis agent for option chain and strike selection."""
import pandas as pd
import numpy as np
from typing import Dict, List
from src.utils.logger import log


class OptionsAnalysisAgent:
    """Agent for comprehensive option chain analysis."""
    
    def __init__(self, cfg):
        self.config = cfg
    
    def analyze_option_chain(
        self,
        option_chain: pd.DataFrame,
        spot_price: float,
        zones: Dict
    ) -> Dict:
        """
        Analyze option chain for trading opportunities.
        
        Args:
            option_chain: Option chain DataFrame with columns:
                         strike, call_oi, call_volume, call_iv, call_ltp, call_oi_change,
                         put_oi, put_volume, put_iv, put_ltp, put_oi_change
            spot_price: Current spot price
            zones: Supply/demand zones
        
        Returns:
            dict: Option chain analysis
        """
        try:
            if option_chain.empty:
                log.warning("Empty option chain received")
                return {}
            
            log.info(f"Analyzing option chain with {len(option_chain)} strikes")
            log.info(f"Spot price: {spot_price}")
            
            # Analyze calls and puts
            call_analysis = self._analyze_calls(option_chain, spot_price)
            put_analysis = self._analyze_puts(option_chain, spot_price)
            
            # PCR calculation
            total_call_oi = option_chain['call_oi'].sum()
            total_put_oi = option_chain['put_oi'].sum()
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Max pain
            max_pain = self._calculate_max_pain(option_chain)
            
            # Support/resistance from OI
            support_levels = self._find_support_from_oi(option_chain, spot_price)
            resistance_levels = self._find_resistance_from_oi(option_chain, spot_price)
            
            analysis = {
                "pcr": float(pcr),
                "max_pain": float(max_pain),
                "call_analysis": call_analysis,
                "put_analysis": put_analysis,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "market_sentiment": self._determine_sentiment(pcr, call_analysis, put_analysis)
            }
            
            log.info(f"✅ Option Analysis Complete:")
            log.info(f"   PCR: {pcr:.2f}")
            log.info(f"   Max Pain: {max_pain:.2f}")
            log.info(f"   Sentiment: {analysis['market_sentiment']}")
            log.info(f"   Support levels: {support_levels}")
            log.info(f"   Resistance levels: {resistance_levels}")
            
            return analysis
            
        except Exception as e:
            log.error(f"Option chain analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}
    
    def _analyze_calls(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze call options."""
        try:
            atm_strike = self._find_atm_strike(df, spot)
            
            # Get ATM data
            atm_data = df[df['strike'] == atm_strike]
            
            # Calculate totals
            total_oi = df['call_oi'].sum()
            total_oi_change = df['call_oi_change'].sum()
            total_volume = df['call_volume'].sum()
            
            # Get ATM IV
            atm_iv = 0
            if len(atm_data) > 0:
                atm_iv = atm_data['call_iv'].iloc[0]
            
            analysis = {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_iv),
                "total_oi": float(total_oi),
                "oi_change": float(total_oi_change),
                "volume": float(total_volume)
            }
            
            log.debug(f"Call analysis: {analysis}")
            return analysis
            
        except Exception as e:
            log.error(f"Call analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {"atm_strike": spot, "atm_iv": 0, "total_oi": 0, "oi_change": 0, "volume": 0}
    
    def _analyze_puts(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze put options."""
        try:
            atm_strike = self._find_atm_strike(df, spot)
            
            # Get ATM data
            atm_data = df[df['strike'] == atm_strike]
            
            # Calculate totals
            total_oi = df['put_oi'].sum()
            total_oi_change = df['put_oi_change'].sum()
            total_volume = df['put_volume'].sum()
            
            # Get ATM IV
            atm_iv = 0
            if len(atm_data) > 0:
                atm_iv = atm_data['put_iv'].iloc[0]
            
            analysis = {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_iv),
                "total_oi": float(total_oi),
                "oi_change": float(total_oi_change),
                "volume": float(total_volume)
            }
            
            log.debug(f"Put analysis: {analysis}")
            return analysis
            
        except Exception as e:
            log.error(f"Put analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {"atm_strike": spot, "atm_iv": 0, "total_oi": 0, "oi_change": 0, "volume": 0}
    
    def _find_atm_strike(self, df: pd.DataFrame, spot: float) -> float:
        """Find ATM strike price closest to spot."""
        if df.empty or 'strike' not in df.columns:
            log.warning(f"Cannot find ATM strike: empty={df.empty}")
            return spot
        
        strikes = df['strike'].values
        idx = np.abs(strikes - spot).argmin()
        atm = float(strikes[idx])
        
        log.debug(f"ATM strike for spot {spot}: {atm}")
        return atm
    
    def _calculate_max_pain(self, df: pd.DataFrame) -> float:
        """
        Calculate max pain point - strike where option sellers lose least money.
        
        Max pain is the strike price with the least total loss for option writers.
        """
        try:
            if df.empty:
                return 0
            
            strikes = df['strike'].unique()
            pain_values = []
            
            for strike in strikes:
                # For calls: if spot > strike, call writers lose (spot - strike) * OI
                call_loss = 0
                for idx, row in df[df['strike'] < strike].iterrows():
                    call_loss += row['call_oi'] * (strike - row['strike'])
                
                # For puts: if spot < strike, put writers lose (strike - spot) * OI
                put_loss = 0
                for idx, row in df[df['strike'] > strike].iterrows():
                    put_loss += row['put_oi'] * (row['strike'] - strike)
                
                total_loss = call_loss + put_loss
                pain_values.append((strike, total_loss))
            
            if pain_values:
                # Find strike with minimum total loss
                max_pain_strike = min(pain_values, key=lambda x: x[1])[0]
                log.debug(f"Max pain calculated: {max_pain_strike}")
                return float(max_pain_strike)
            
            return 0
            
        except Exception as e:
            log.error(f"Max pain calculation error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return 0
    
    def _find_support_from_oi(self, df: pd.DataFrame, spot: float) -> List[float]:
        """
        Find support levels from high put OI.
        High put OI indicates support as buyers are betting on price not falling below that level.
        """
        try:
            if df.empty:
                return []
            
            # Look at strikes below spot
            below_spot = df[df['strike'] < spot].copy()
            
            if below_spot.empty:
                return []
            
            # Sort by put OI (descending) and get top 3
            support_strikes = below_spot.nlargest(3, 'put_oi')['strike'].tolist()
            
            log.debug(f"Support levels from put OI: {support_strikes}")
            return [float(x) for x in support_strikes]
            
        except Exception as e:
            log.error(f"Support identification error: {str(e)}")
            return []
    
    def _find_resistance_from_oi(self, df: pd.DataFrame, spot: float) -> List[float]:
        """
        Find resistance levels from high call OI.
        High call OI indicates resistance as sellers are betting on price not rising above that level.
        """
        try:
            if df.empty:
                return []
            
            # Look at strikes above spot
            above_spot = df[df['strike'] > spot].copy()
            
            if above_spot.empty:
                return []
            
            # Sort by call OI (descending) and get top 3
            resistance_strikes = above_spot.nlargest(3, 'call_oi')['strike'].tolist()
            
            log.debug(f"Resistance levels from call OI: {resistance_strikes}")
            return [float(x) for x in resistance_strikes]
            
        except Exception as e:
            log.error(f"Resistance identification error: {str(e)}")
            return []
    
    def _determine_sentiment(self, pcr: float, call_data: Dict, put_data: Dict) -> str:
        """
        Determine market sentiment from options data.
        
        PCR > 1.3: More put OI than call OI -> Bullish (expecting upside)
        PCR < 0.7: More call OI than put OI -> Bearish (expecting downside)
        PCR between 0.7-1.3: Neutral
        """
        if pcr > 1.3:
            sentiment = "Bullish"
        elif pcr < 0.7:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"
        
        log.debug(f"Market sentiment (PCR={pcr:.2f}): {sentiment}")
        return sentiment
    
    def select_best_strike(
        self,
        zones: Dict,
        option_analysis: Dict,
        trade_direction: str,
        current_price: float,
        option_chain: pd.DataFrame
    ) -> Dict:
        """
        Select optimal strike for INTRADAY options trading.
        
        Features:
        - Caps intraday moves at 150 points max
        - Uses ATM strikes for better delta
        - 5% premium stop loss (tight control)
        - 2:1 minimum R:R for intraday
        - Works for both CALL and PUT
        """
        try:
            # INTRADAY CONFIGURATION
            MAX_INTRADAY_MOVE = 200  # Cap target at 150 points
            DEFAULT_TARGET_POINTS = 80  # Default 80-point target
            STOP_LOSS_PERCENT = 5  # 5% of premium (tight SL)
            MIN_RR_INTRADAY = 2.0  # 2:1 minimum R:R
            
            log.info(f"Selecting INTRADAY {trade_direction} strike at futures: {current_price:.2f}")
            
            # Get zones based on direction
            if trade_direction == "CALL":
                entry_zones = zones.get('demand_zones', [])
                target_zones = zones.get('supply_zones', [])
            else:  # PUT
                entry_zones = zones.get('supply_zones', [])
                target_zones = zones.get('demand_zones', [])
            
            # ============ DETERMINE FUTURES ENTRY ============
            if entry_zones:
                entry_zone = entry_zones[0]
                futures_entry = (entry_zone.get('zone_top', 0) + entry_zone.get('zone_bottom', 0)) / 2
                entry_confidence = entry_zone.get('confidence', 0)
            else:
                futures_entry = current_price
                entry_confidence = 0.5
            
            # ============ DETERMINE FUTURES TARGET (CAPPED) ============
            if target_zones:
                target_zone = target_zones[0]
                zone_target = (target_zone.get('zone_top', 0) + target_zone.get('zone_bottom', 0)) / 2
                distance = abs(zone_target - futures_entry)
                
                # Cap at MAX_INTRADAY_MOVE
                if distance > MAX_INTRADAY_MOVE:
                    log.warning(f"⚠️ Zone target is {distance:.0f} points away")
                    log.warning(f"   Capping intraday target to {MAX_INTRADAY_MOVE} points")
                    
                    if trade_direction == "CALL":
                        futures_target = futures_entry + MAX_INTRADAY_MOVE
                    else:
                        futures_target = futures_entry - MAX_INTRADAY_MOVE
                    target_confidence = 0.6
                else:
                    futures_target = zone_target
                    target_confidence = target_zone.get('confidence', 0)
            else:
                # No zone: Use default 80-point target
                log.info(f"No target zone - using default {DEFAULT_TARGET_POINTS}-point target")
                if trade_direction == "CALL":
                    futures_target = futures_entry + DEFAULT_TARGET_POINTS
                else:
                    futures_target = futures_entry - DEFAULT_TARGET_POINTS
                target_confidence = 0.5
            
            futures_move = abs(futures_target - futures_entry)
            
            # ============ SELECT ATM STRIKE ============
            atm_strike = self._find_atm_strike(option_chain, futures_entry)
            
            # Use ATM strike for better delta (0.5)
            selected_strike = atm_strike
            strike_key = 'call_ltp' if trade_direction == "CALL" else 'put_ltp'
            
            # Get option premium at selected strike
            strike_data = option_chain[option_chain['strike'] == selected_strike]
            
            if strike_data.empty:
                log.warning(f"⚠️ Selected strike {selected_strike} not found in chain")
                return {}
            
            option_entry_premium = strike_data[strike_key].iloc[0]
            
            if option_entry_premium == 0:
                log.warning(f"⚠️ Option premium is 0 at strike {selected_strike}")
                return {}
            
            # ============ CALCULATE OPTION TARGET PREMIUM ============
            # ATM delta ~0.5, so premium moves ~50% of futures move
            delta_estimate = 0.5
            premium_change = futures_move * delta_estimate
            
            option_target_premium = option_entry_premium + premium_change
            
            # ============ CALCULATE OPTION STOP PREMIUM (5% LOSS) ============
            option_stop_premium = option_entry_premium * (1 - STOP_LOSS_PERCENT/100)
            
            # Calculate corresponding futures stop level
            premium_loss_at_stop = option_entry_premium - option_stop_premium
            futures_stop_distance = premium_loss_at_stop / delta_estimate
            
            if trade_direction == "CALL":
                futures_stop = futures_entry - futures_stop_distance
            else:
                futures_stop = futures_entry + futures_stop_distance
            
            # ============ RISK-REWARD CALCULATION ============
            risk = option_entry_premium - option_stop_premium
            reward = option_target_premium - option_entry_premium
            risk_reward = reward / risk if risk > 0 else 0
            
            risk_percent = (risk / option_entry_premium) * 100
            reward_percent = (reward / option_entry_premium) * 100
            
            # ============ BUILD TRADE SETUP ============
            trade_setup = {
                'direction': trade_direction,
                'selected_strike': float(selected_strike),
                # Option premiums
                'entry_price': float(option_entry_premium),
                'target_price': float(option_target_premium),
                'stop_loss': float(option_stop_premium),
                # Futures reference levels
                'futures_entry': float(futures_entry),
                'futures_target': float(futures_target),
                'futures_stop': float(futures_stop),
                'futures_move_points': float(futures_move),
                'futures_stop_points': float(futures_stop_distance),
                # Risk-reward metrics
                'risk_reward': float(risk_reward),
                'risk_amount': float(risk),
                'reward_amount': float(reward),
                'risk_percent': float(risk_percent),
                'reward_percent': float(reward_percent),
                # Metadata
                'entry_zone_confidence': float(entry_confidence),
                'target_zone_confidence': float(target_confidence),
                'option_sentiment': option_analysis.get('market_sentiment', 'Neutral'),
                'pcr': option_analysis.get('pcr', 0),
                'has_entry_zone': bool(entry_zones),
                'has_target_zone': bool(target_zones),
                'is_trending_trade': not (entry_zones and target_zones),
                'trade_type': 'INTRADAY'
            }
            
            # ============ DETAILED LOGGING ============
            log.info(f"✅ INTRADAY Strike Selection Complete:")
            log.info(f"   Direction: {trade_direction} at strike {selected_strike}")
            log.info(f"   Option Entry: ₹{option_entry_premium:.2f}")
            log.info(f"   Option Target: ₹{option_target_premium:.2f} (+{reward_percent:.1f}% gain)")
            log.info(f"   Option Stop: ₹{option_stop_premium:.2f} (-{risk_percent:.1f}% loss = 5% SL)")
            log.info(f"   Futures: {futures_entry:.0f} → {futures_target:.0f} ({futures_move:.0f} pts) | Stop: {futures_stop:.0f} ({futures_stop_distance:.0f} pts)")
            log.info(f"   Risk: ₹{risk:.2f} | Reward: ₹{reward:.2f} | R:R = {risk_reward:.2f}:1")
            log.info(f"   Sentiment: {trade_setup['option_sentiment']}, PCR: {trade_setup['pcr']:.2f}")
            log.info(f"   Trade Type: {'Trending' if trade_setup['is_trending_trade'] else 'Zone-based'}")
            
            # ============ VALIDATION ============
            if risk_reward < MIN_RR_INTRADAY:
                log.warning(f"⚠️ Risk-reward {risk_reward:.2f} below minimum {MIN_RR_INTRADAY}:1")
                return {}
            
            if risk_percent > 10:  # Safety check - should not exceed 10% with 5% SL
                log.warning(f"⚠️ Risk {risk_percent:.0f}% exceeds maximum 10%")
                return {}
            
            return trade_setup
            
        except Exception as e:
            log.error(f"Strike selection error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}


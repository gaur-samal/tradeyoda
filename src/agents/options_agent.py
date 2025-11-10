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
      Analyze option chain for trading opportunities with theta analysis.
      
      Args:
            option_chain: Option chain DataFrame with columns:
                        strike, call_oi, call_volume, call_iv, call_ltp, call_oi_change,
                        put_oi, put_volume, put_iv, put_ltp, put_oi_change,
                        call_greeks (dict with delta, theta, gamma, vega),
                        put_greeks (dict with delta, theta, gamma, vega)
            spot_price: Current spot price
            zones: Supply/demand zones
      
      Returns:
            dict: Option chain analysis with theta metrics
      """
      try:
            from src.utils.theta_calculator import theta_calculator
            
            if option_chain.empty:
                  log.warning("Empty option chain received")
                  return {}

            log.info(f"Analyzing option chain with {len(option_chain)} strikes")
            log.info(f"Spot price: {spot_price}")

            # ===== EXTRACT GREEKS AND THETA =====
            # Process calls
            if 'call_greeks' in option_chain.columns and 'call_ltp' in option_chain.columns:
                option_chain['call_theta_daily'] = option_chain['call_greeks'].apply(
                    lambda g: g.get('theta', None) if isinstance(g, dict) and g else None
                )
                option_chain['call_delta'] = option_chain['call_greeks'].apply(
                    lambda g: g.get('delta', None) if isinstance(g, dict) and g else None
                )
                option_chain['call_gamma'] = option_chain['call_greeks'].apply(
                    lambda g: g.get('gamma', None) if isinstance(g, dict) and g else None
                )
                option_chain['call_vega'] = option_chain['call_greeks'].apply(
                    lambda g: g.get('vega', None) if isinstance(g, dict) and g else None
                )
                
                # ===== FILTER: Keep only rows with valid Greeks =====
                # Valid = non-null, non-zero theta and delta
                option_chain['call_has_valid_greeks'] = (
                    option_chain['call_theta_daily'].notna() & 
                    (option_chain['call_theta_daily'] != 0) &
                    option_chain['call_delta'].notna() &
                    (option_chain['call_delta'] != 0) &
                    (option_chain['call_ltp'] > 0)
                )
                
                # Calculate theta metrics only for valid rows
                option_chain['call_theta_hourly'] = option_chain.apply(
                    lambda row: row['call_theta_daily'] / 6.5 if row.get('call_has_valid_greeks', False) else None,
                    axis=1
                )
                option_chain['call_theta_abs_hourly'] = option_chain['call_theta_hourly'].abs()
                
                # Decay percentage
                option_chain['call_decay_pct_hourly'] = option_chain.apply(
                    lambda row: (abs(row['call_theta_hourly']) / row['call_ltp'] * 100) 
                    if row.get('call_has_valid_greeks', False) and row['call_ltp'] > 0 else None,
                    axis=1
                )
                
                # Quality score
                option_chain['call_quality_score'] = option_chain.apply(
                    lambda row: theta_calculator.get_theta_quality_score(
                        row['call_theta_daily'],
                        row['call_ltp'],
                        row['call_delta']
                    ) if row.get('call_has_valid_greeks', False) else None,
                    axis=1
                )
                
                # Log how many valid calls we have
                valid_calls = option_chain['call_has_valid_greeks'].sum()
                log.info(f"✅ Found {valid_calls} CALL strikes with valid Greeks")
            
            # Process puts (same logic)
            if 'put_greeks' in option_chain.columns and 'put_ltp' in option_chain.columns:
                option_chain['put_theta_daily'] = option_chain['put_greeks'].apply(
                    lambda g: g.get('theta', None) if isinstance(g, dict) and g else None
                )
                option_chain['put_delta'] = option_chain['put_greeks'].apply(
                    lambda g: g.get('delta', None) if isinstance(g, dict) and g else None
                )
                option_chain['put_gamma'] = option_chain['put_greeks'].apply(
                    lambda g: g.get('gamma', None) if isinstance(g, dict) and g else None
                )
                option_chain['put_vega'] = option_chain['put_greeks'].apply(
                    lambda g: g.get('vega', None) if isinstance(g, dict) and g else None
                )
                
                # Filter valid puts
                option_chain['put_has_valid_greeks'] = (
                    option_chain['put_theta_daily'].notna() & 
                    (option_chain['put_theta_daily'] != 0) &
                    option_chain['put_delta'].notna() &
                    (option_chain['put_delta'] != 0) &
                    (option_chain['put_ltp'] > 0)
                )
                
                option_chain['put_theta_hourly'] = option_chain.apply(
                    lambda row: row['put_theta_daily'] / 6.5 if row.get('put_has_valid_greeks', False) else None,
                    axis=1
                )
                option_chain['put_theta_abs_hourly'] = option_chain['put_theta_hourly'].abs()
                
                option_chain['put_decay_pct_hourly'] = option_chain.apply(
                    lambda row: (abs(row['put_theta_hourly']) / row['put_ltp'] * 100) 
                    if row.get('put_has_valid_greeks', False) and row['put_ltp'] > 0 else None,
                    axis=1
                )
                
                option_chain['put_quality_score'] = option_chain.apply(
                    lambda row: theta_calculator.get_theta_quality_score(
                        row['put_theta_daily'],
                        row['put_ltp'],
                        row['put_delta']
                    ) if row.get('put_has_valid_greeks', False) else None,
                    axis=1
                )
                
                valid_puts = option_chain['put_has_valid_greeks'].sum()
                log.info(f"✅ Found {valid_puts} PUT strikes with valid Greeks")

            # Analyze calls and puts (existing methods will now have theta data)
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

            # ===== ADD THETA SUMMARY =====
            theta_summary = self._analyze_theta_distribution(option_chain, spot_price)

            analysis = {
                  "pcr": float(pcr),
                  "max_pain": float(max_pain),
                  "call_analysis": call_analysis,
                  "put_analysis": put_analysis,
                  "support_levels": support_levels,
                  "resistance_levels": resistance_levels,
                  "theta_summary": theta_summary,  # NEW
                  "market_sentiment": self._determine_sentiment(pcr, call_analysis, put_analysis)
            }

            log.info(f"✅ Option Analysis Complete:")
            log.info(f"   PCR: {pcr:.2f}")
            log.info(f"   Max Pain: {max_pain:.2f}")
            log.info(f"   Sentiment: {analysis['market_sentiment']}")
            log.info(f"   Support levels: {support_levels}")
            log.info(f"   Resistance levels: {resistance_levels}")
            
            # Log theta info
            if theta_summary:
                  log.info(f"📉 Theta Analysis:")
                  log.info(f"   Avg Call Theta/hour: ₹{theta_summary.get('avg_call_theta_hourly', 0):.2f}")
                  log.info(f"   Avg Put Theta/hour: ₹{theta_summary.get('avg_put_theta_hourly', 0):.2f}")
                  log.info(f"   Best Call Quality: {theta_summary.get('best_call_quality', 0):.1f}")
                  log.info(f"   Best Put Quality: {theta_summary.get('best_put_quality', 0):.1f}")
            
            return analysis

      except Exception as e:
            log.error(f"Option chain analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}

    def _analyze_theta_distribution(self, option_chain: pd.DataFrame, spot_price: float) -> Dict:
        """
        Analyze theta distribution across strikes.

        Args:
            option_chain: DataFrame with theta columns
            spot_price: Current spot price

        Returns:
            Dict with theta statistics
        """
        try:
            # Filter ATM and near-the-money options (within 2%)
            atm_range = spot_price * 0.02
            atm_strikes = option_chain[
                    (option_chain['strike'] >= spot_price - atm_range) &
                    (option_chain['strike'] <= spot_price + atm_range)
            ]
            
            summary = {}
            
            # Call theta stats
            if 'call_theta_abs_hourly' in option_chain.columns:
                    summary['avg_call_theta_hourly'] = atm_strikes['call_theta_abs_hourly'].mean()
                    summary['max_call_theta_hourly'] = atm_strikes['call_theta_abs_hourly'].max()
                    summary['best_call_quality'] = option_chain['call_quality_score'].max()
                    
                    # Find strike with best quality
                    best_call_idx = option_chain['call_quality_score'].idxmax()
                    if pd.notna(best_call_idx):
                        summary['best_call_strike'] = option_chain.loc[best_call_idx, 'strike']
            
            # Put theta stats
            if 'put_theta_abs_hourly' in option_chain.columns:
                    summary['avg_put_theta_hourly'] = atm_strikes['put_theta_abs_hourly'].mean()
                    summary['max_put_theta_hourly'] = atm_strikes['put_theta_abs_hourly'].max()
                    summary['best_put_quality'] = option_chain['put_quality_score'].max()
                    
                    # Find strike with best quality
                    best_put_idx = option_chain['put_quality_score'].idxmax()
                    if pd.notna(best_put_idx):
                        summary['best_put_strike'] = option_chain.loc[best_put_idx, 'strike']
            
            return summary
            
        except Exception as e:
            log.error(f"Theta distribution analysis error: {e}")
            return {}

    def _analyze_calls(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze call options - only valid strikes."""
        try:
            # Filter to valid calls only
            if 'call_has_valid_greeks' in df.columns:
                valid_calls = df[df['call_has_valid_greeks'] == True]
                if valid_calls.empty:
                    log.warning("⚠️ No valid CALL strikes with Greeks")
                    return self._empty_call_analysis(spot)
                
                atm_strike = self._find_atm_strike(valid_calls, spot)
                atm_data = valid_calls[valid_calls['strike'] == atm_strike]
            else:
                atm_strike = self._find_atm_strike(df, spot)
                atm_data = df[df['strike'] == atm_strike]

            if atm_data.empty:
                log.warning(f"⚠️ No ATM call data found for strike {atm_strike}")
                return self._empty_call_analysis(spot)

            # Calculate totals
            total_oi = df['call_oi'].sum()
            total_oi_change = df['call_oi_change'].sum()
            total_volume = df['call_volume'].sum()

            # Get ATM values (guaranteed valid if we got here)
            atm_iv = atm_data['call_iv'].iloc[0] if 'call_iv' in atm_data.columns else 0
            atm_ltp = atm_data['call_ltp'].iloc[0] if 'call_ltp' in atm_data.columns else 0
            
            # Extract Greeks (may be None if not in valid set)
            theta_daily = atm_data['call_theta_daily'].iloc[0] if 'call_theta_daily' in atm_data.columns else 0
            theta_hourly = atm_data['call_theta_hourly'].iloc[0] if 'call_theta_hourly' in atm_data.columns else 0
            theta_abs_hourly = atm_data['call_theta_abs_hourly'].iloc[0] if 'call_theta_abs_hourly' in atm_data.columns else 0
            decay_pct_hourly = atm_data['call_decay_pct_hourly'].iloc[0] if 'call_decay_pct_hourly' in atm_data.columns else 0
            
            delta = atm_data['call_delta'].iloc[0] if 'call_delta' in atm_data.columns else 0
            gamma = atm_data['call_gamma'].iloc[0] if 'call_gamma' in atm_data.columns else 0
            vega = atm_data['call_vega'].iloc[0] if 'call_vega' in atm_data.columns else 0
            quality_score = atm_data['call_quality_score'].iloc[0] if 'call_quality_score' in atm_data.columns else 50

            analysis = {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_iv) if pd.notna(atm_iv) else 0,
                "atm_ltp": float(atm_ltp) if pd.notna(atm_ltp) else 0,
                "total_oi": float(total_oi),
                "oi_change": float(total_oi_change),
                "volume": float(total_volume),
                "delta": float(delta) if pd.notna(delta) else 0,
                "gamma": float(gamma) if pd.notna(gamma) else 0,
                "vega": float(vega) if pd.notna(vega) else 0,
                "theta_daily": float(theta_daily) if pd.notna(theta_daily) else 0,
                "theta_hourly": float(theta_hourly) if pd.notna(theta_hourly) else 0,
                "theta_abs_hourly": float(theta_abs_hourly) if pd.notna(theta_abs_hourly) else 0,
                "decay_pct_hourly": float(decay_pct_hourly) if pd.notna(decay_pct_hourly) else 0,
                "quality_score": float(quality_score) if pd.notna(quality_score) else 50
            }

            log.debug(f"Call analysis: ATM {atm_strike}, Greeks valid: {theta_daily != 0}")
            return analysis

        except Exception as e:
            log.error(f"Call analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return self._empty_call_analysis(spot)


    def _analyze_puts(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze put options - only valid strikes."""
        try:
            # Filter to valid puts only
            if 'put_has_valid_greeks' in df.columns:
                valid_puts = df[df['put_has_valid_greeks'] == True]
                if valid_puts.empty:
                    log.warning("⚠️ No valid PUT strikes with Greeks")
                    return self._empty_put_analysis(spot)
                
                atm_strike = self._find_atm_strike(valid_puts, spot)
                atm_data = valid_puts[valid_puts['strike'] == atm_strike]
            else:
                atm_strike = self._find_atm_strike(df, spot)
                atm_data = df[df['strike'] == atm_strike]

            if atm_data.empty:
                log.warning(f"⚠️ No ATM put data found for strike {atm_strike}")
                return self._empty_put_analysis(spot)

            # Calculate totals
            total_oi = df['put_oi'].sum()
            total_oi_change = df['put_oi_change'].sum()
            total_volume = df['put_volume'].sum()

            # Get ATM values (guaranteed valid if we got here)
            atm_iv = atm_data['put_iv'].iloc[0] if 'put_iv' in atm_data.columns else 0
            atm_ltp = atm_data['put_ltp'].iloc[0] if 'put_ltp' in atm_data.columns else 0
            
            # Extract Greeks (may be None if not in valid set)
            theta_daily = atm_data['put_theta_daily'].iloc[0] if 'put_theta_daily' in atm_data.columns else 0
            theta_hourly = atm_data['put_theta_hourly'].iloc[0] if 'put_theta_hourly' in atm_data.columns else 0
            theta_abs_hourly = atm_data['put_theta_abs_hourly'].iloc[0] if 'put_theta_abs_hourly' in atm_data.columns else 0
            decay_pct_hourly = atm_data['put_decay_pct_hourly'].iloc[0] if 'put_decay_pct_hourly' in atm_data.columns else 0
            
            delta = atm_data['put_delta'].iloc[0] if 'put_delta' in atm_data.columns else 0
            gamma = atm_data['put_gamma'].iloc[0] if 'put_gamma' in atm_data.columns else 0
            vega = atm_data['put_vega'].iloc[0] if 'put_vega' in atm_data.columns else 0
            quality_score = atm_data['put_quality_score'].iloc[0] if 'put_quality_score' in atm_data.columns else 50

            analysis = {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_iv) if pd.notna(atm_iv) else 0,
                "atm_ltp": float(atm_ltp) if pd.notna(atm_ltp) else 0,
                "total_oi": float(total_oi),
                "oi_change": float(total_oi_change),
                "volume": float(total_volume),
                "delta": float(delta) if pd.notna(delta) else 0,
                "gamma": float(gamma) if pd.notna(gamma) else 0,
                "vega": float(vega) if pd.notna(vega) else 0,
                "theta_daily": float(theta_daily) if pd.notna(theta_daily) else 0,
                "theta_hourly": float(theta_hourly) if pd.notna(theta_hourly) else 0,
                "theta_abs_hourly": float(theta_abs_hourly) if pd.notna(theta_abs_hourly) else 0,
                "decay_pct_hourly": float(decay_pct_hourly) if pd.notna(decay_pct_hourly) else 0,
                "quality_score": float(quality_score) if pd.notna(quality_score) else 50
            }

            log.debug(f"Put analysis: ATM {atm_strike}, Greeks valid: {theta_daily != 0}")
            return analysis

        except Exception as e:
            log.error(f"Put analysis error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return self._empty_put_analysis(spot)


    def _empty_call_analysis(self, spot: float) -> Dict:
        """Return empty call analysis structure."""
        return {
            "atm_strike": spot,
            "atm_iv": 0,
            "atm_ltp": 0,
            "total_oi": 0,
            "oi_change": 0,
            "volume": 0,
            "delta": 0,
            "gamma": 0,
            "vega": 0,
            "theta_daily": 0,
            "theta_hourly": 0,
            "theta_abs_hourly": 0,
            "decay_pct_hourly": 0,
            "quality_score": 0
        }


    def _empty_put_analysis(self, spot: float) -> Dict:
        """Return empty put analysis structure."""
        return {
            "atm_strike": spot,
            "atm_iv": 0,
            "atm_ltp": 0,
            "total_oi": 0,
            "oi_change": 0,
            "volume": 0,
            "delta": 0,
            "gamma": 0,
            "vega": 0,
            "theta_daily": 0,
            "theta_hourly": 0,
            "theta_abs_hourly": 0,
            "decay_pct_hourly": 0,
            "quality_score": 0
        }


    
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
        Select optimal strike for INTRADAY options trading with zone-based + theta filtering.
        
        Features:
        - Zone-based strike selection (target-oriented)
        - Theta pre-filtering (removes high-decay strikes)
        - Quality-score ranking for best strikes
        - Caps intraday moves at 200 points max
        - 5% premium stop loss (tight control)
        - 2:1 minimum R:R for intraday
        - Works for both CALL and PUT
        """
        try:
            from src.utils.theta_calculator import theta_calculator
            
            # INTRADAY CONFIGURATION
            MAX_INTRADAY_MOVE = 150  # Cap target at 150 points
            DEFAULT_TARGET_POINTS = 80  # Default 80-point target
            STOP_LOSS_PERCENT = 2  # % of premium (tight SL)
            MIN_RR_INTRADAY = 2.0  # 2:1 minimum R:R
            
            # THETA CONFIGURATION
            EXPECTED_HOLD_HOURS = getattr(self.config, 'EXPECTED_HOLD_HOURS', 3.0)
            MAX_THETA_IMPACT = getattr(self.config, 'MAX_THETA_IMPACT_PERCENTAGE', 5.0)
            
            # STRIKE SELECTION CONFIGURATION
            TARGET_STRIKE_RANGE = 200  # Points around target to search for strikes
            
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
                log.info(f"📍 Entry from zone: {futures_entry:.2f} (confidence: {entry_confidence:.1f}%)")
            else:
                futures_entry = current_price
                entry_confidence = 0.5
                log.info(f"📍 Entry from current price: {futures_entry:.2f}")
            
            # ============ DETERMINE FUTURES TARGET (CAPPED) ============
            if target_zones:
                target_zone = target_zones[0]
                zone_target = (target_zone.get('zone_top', 0) + target_zone.get('zone_bottom', 0)) / 2
                distance = abs(zone_target - futures_entry)
                log.info(f"   Target zone found at: {zone_target:.0f}")
                log.info(f"   Distance from entry: {distance:.0f} points")
                
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
                log.info(f"   Final target: {futures_target:.0f}")
            else:
                # No zone: Use default 80-point target
                log.info(f"No target zone - using default {DEFAULT_TARGET_POINTS}-point target")
                log.info(f"   Entry point: {futures_entry:.2f}")
                log.info(f"   Trade direction: {trade_direction}")
                if trade_direction == "CALL":
                    futures_target = futures_entry + DEFAULT_TARGET_POINTS
                    log.info(f"   CALL calculation: {futures_entry:.2f} + {DEFAULT_TARGET_POINTS} = {futures_target:.2f}")
                else:
                    futures_target = futures_entry - DEFAULT_TARGET_POINTS
                    log.info(f"   PUT calculation: {futures_entry:.2f} - {DEFAULT_TARGET_POINTS} = {futures_target:.2f}")
                target_confidence = 0.5
            
            futures_move = abs(futures_target - futures_entry)
            
            log.info(f"✅ Target Summary:")
            log.info(f"   Entry: {futures_entry:.2f}")
            log.info(f"   Target: {futures_target:.2f}")
            log.info(f"   Move: {futures_move:.0f} points {'UP' if futures_target > futures_entry else 'DOWN'}") 
            # ============ FILTER VALID STRIKES WITH GREEKS ============
            valid_col = 'call_has_valid_greeks' if trade_direction == "CALL" else 'put_has_valid_greeks'
            has_greeks = False
            
            if valid_col in option_chain.columns:
                valid_strikes = option_chain[option_chain[valid_col] == True].copy()
                
                if valid_strikes.empty:
                    log.warning(f"⚠️ No {trade_direction} strikes with valid Greeks found")
                    log.warning("   Falling back to all strikes without Greek validation")
                    valid_strikes = option_chain.copy()
                    has_greeks = False
                else:
                    log.info(f"📊 Found {len(valid_strikes)} valid {trade_direction} strikes with Greeks")
                    has_greeks = True
            else:
                log.warning(f"⚠️ No Greeks validation column found - using all strikes")
                valid_strikes = option_chain.copy()
                has_greeks = False
            
            # ============ THETA PRE-FILTERING (if Greeks available) ============
            if has_greeks:
                theta_col = 'call_theta_hourly' if trade_direction == "CALL" else 'put_theta_hourly'
                strike_key = 'call_ltp' if trade_direction == "CALL" else 'put_ltp'
                
                # Calculate theta impact for all strikes
                def calc_theta_impact(row):
                    premium = row.get(strike_key, 0)
                    theta = row.get(theta_col, 0)
                    
                    if premium <= 0 or pd.isna(theta) or theta == 0:
                        return 999.0  # High value to filter out
                    
                    expected_decay = abs(theta) * EXPECTED_HOLD_HOURS
                    impact_pct = (expected_decay / premium * 100)
                    return impact_pct
                
                valid_strikes['theta_impact_pct'] = valid_strikes.apply(calc_theta_impact, axis=1)
                
                # Filter by theta threshold
                theta_approved = valid_strikes[valid_strikes['theta_impact_pct'] <= MAX_THETA_IMPACT].copy()
                
                if theta_approved.empty:
                    best_theta = valid_strikes['theta_impact_pct'].min()
                    log.warning(f"⚠️ No strikes pass theta filter ({MAX_THETA_IMPACT}%)")
                    log.warning(f"   Best available theta impact: {best_theta:.1f}%")
                    return {}
                
                strikes_filtered = len(valid_strikes) - len(theta_approved)
                log.info(f"✅ Theta filtering: {len(theta_approved)}/{len(valid_strikes)} strikes approved")
                log.info(f"   Filtered out {strikes_filtered} high-theta strikes")
                
                valid_strikes = theta_approved
            
            # ============ ZONE-BASED STRIKE SELECTION ============
            strike_key = 'call_ltp' if trade_direction == "CALL" else 'put_ltp'
            selected_strike = None
            selection_method = None
            
            # Strategy 1: Find strike near target zone (if we have target and Greeks)
            if target_zones and has_greeks:
                # Find strikes within range of target
                near_target = valid_strikes[
                    (valid_strikes['strike'] >= futures_target - TARGET_STRIKE_RANGE) &
                    (valid_strikes['strike'] <= futures_target + TARGET_STRIKE_RANGE)
                ].copy()
                
                if not near_target.empty:
                    # Sort by quality score (best first)
                    quality_col = 'call_quality_score' if trade_direction == "CALL" else 'put_quality_score'
                    
                    if quality_col in near_target.columns:
                        near_target = near_target.sort_values(quality_col, ascending=False)
                        selected_strike = near_target.iloc[0]['strike']
                        selection_method = "target_zone_quality"
                        
                        best_quality = near_target.iloc[0].get(quality_col, 0)
                        log.info(f"✅ Selected strike near target zone: {selected_strike:.0f}")
                        log.info(f"   Target: {futures_target:.0f}, Selected: {selected_strike:.0f}")
                        log.info(f"   Quality score: {best_quality:.1f}/100")
                    else:
                        # No quality column, pick closest to target
                        near_target['distance_to_target'] = (near_target['strike'] - futures_target).abs()
                        near_target = near_target.sort_values('distance_to_target')
                        selected_strike = near_target.iloc[0]['strike']
                        selection_method = "target_zone_closest"
                        
                        log.info(f"✅ Selected closest strike to target: {selected_strike:.0f}")
                else:
                    log.warning(f"⚠️ No strikes within {TARGET_STRIKE_RANGE} points of target {futures_target:.0f}")
            
            # Strategy 2: Fallback to ATM if no target zone or nothing found
            if selected_strike is None:
                selected_strike = self._find_atm_strike(valid_strikes, futures_entry)
                selection_method = "atm_fallback"
                log.info(f"✅ Using ATM strike (fallback): {selected_strike:.0f}")
            
            # ============ GET STRIKE DATA ============
            strike_data = valid_strikes[valid_strikes['strike'] == selected_strike]
            
            if strike_data.empty:
                log.warning(f"⚠️ Selected strike {selected_strike} not found after filtering")
                return {}
            
            option_entry_premium = strike_data[strike_key].iloc[0]
            
            if option_entry_premium == 0 or pd.isna(option_entry_premium):
                log.warning(f"⚠️ Invalid option premium at strike {selected_strike}")
                return {}
            
            # ============ EXTRACT GREEKS (IF AVAILABLE) ============
            theta_hourly = 0
            delta = 0.5  # Default ATM delta
            gamma = 0
            vega = 0
            quality_score = 50
            decay_pct = 0
            
            if has_greeks:
                theta_col = 'call_theta_hourly' if trade_direction == "CALL" else 'put_theta_hourly'
                delta_col = 'call_delta' if trade_direction == "CALL" else 'put_delta'
                gamma_col = 'call_gamma' if trade_direction == "CALL" else 'put_gamma'
                vega_col = 'call_vega' if trade_direction == "CALL" else 'put_vega'
                quality_col = 'call_quality_score' if trade_direction == "CALL" else 'put_quality_score'
                decay_pct_col = 'call_decay_pct_hourly' if trade_direction == "CALL" else 'put_decay_pct_hourly'
                
                theta_hourly = strike_data[theta_col].iloc[0] if theta_col in strike_data.columns and pd.notna(strike_data[theta_col].iloc[0]) else 0
                delta = strike_data[delta_col].iloc[0] if delta_col in strike_data.columns and pd.notna(strike_data[delta_col].iloc[0]) else 0.5
                gamma = strike_data[gamma_col].iloc[0] if gamma_col in strike_data.columns and pd.notna(strike_data[gamma_col].iloc[0]) else 0
                vega = strike_data[vega_col].iloc[0] if vega_col in strike_data.columns and pd.notna(strike_data[vega_col].iloc[0]) else 0
                quality_score = strike_data[quality_col].iloc[0] if quality_col in strike_data.columns and pd.notna(strike_data[quality_col].iloc[0]) else 50
                decay_pct = strike_data[decay_pct_col].iloc[0] if decay_pct_col in strike_data.columns and pd.notna(strike_data[decay_pct_col].iloc[0]) else 0
                
                if delta == 0:
                    delta = 0.5  # Fallback
                
                log.info(f"📊 Greeks at selected strike:")
                log.info(f"   Delta: {delta:.4f}")
                log.info(f"   Theta: {theta_hourly:.2f}/hour")
                log.info(f"   Quality: {quality_score:.1f}/100")
            else:
                log.warning("⚠️ Trading without Greeks - using default delta 0.5")
            
            # ============ CALCULATE OPTION TARGET PREMIUM ============
            delta_estimate = abs(delta) if delta != 0 else 0.5
            premium_change = futures_move * delta_estimate
            
            option_target_premium = option_entry_premium + premium_change
            
            # ============ ADJUST TARGET FOR THETA DECAY ============
            if has_greeks and theta_hourly != 0:
                option_target_premium = theta_calculator.adjust_target_for_theta(
                    entry_premium=option_entry_premium,
                    target_premium=option_target_premium,
                    expected_hold_hours=EXPECTED_HOLD_HOURS,
                    theta_hourly=theta_hourly
                )
            
            # ============ CALCULATE OPTION STOP PREMIUM (5% LOSS) ============
            option_stop_premium = option_entry_premium * (1 - STOP_LOSS_PERCENT/100)
            
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
            
            expected_theta_decay = abs(theta_hourly) * EXPECTED_HOLD_HOURS
            theta_impact_percent = (expected_theta_decay / option_entry_premium * 100) if option_entry_premium > 0 else 0
            
            # ============ BUILD TRADE SETUP ============
            trade_setup = {
                'direction': trade_direction,
                'strike': float(selected_strike),
                'selected_strike': float(selected_strike),
                'selection_method': selection_method,  # Track how strike was selected
                # Option premiums
                'option_type': trade_direction,
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
                # Greeks and Theta
                'delta': float(delta),
                'theta_hourly': float(theta_hourly),
                'theta_abs_hourly': float(abs(theta_hourly)),
                'gamma': float(gamma),
                'vega': float(vega),
                'expected_theta_decay': float(expected_theta_decay),
                'theta_impact_percent': float(theta_impact_percent),
                'quality_score': float(quality_score),
                'decay_percentage_hourly': float(decay_pct),
                'expected_hold_hours': float(EXPECTED_HOLD_HOURS),
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
            log.info(f"   Method: {selection_method}")
            log.info(f"   Direction: {trade_direction} at strike {selected_strike}")
            log.info(f"   Option Entry: ₹{option_entry_premium:.2f}")
            log.info(f"   Option Target: ₹{option_target_premium:.2f} (+{reward_percent:.1f}% gain)")
            log.info(f"   Option Stop: ₹{option_stop_premium:.2f} (-{risk_percent:.1f}% loss)")
            log.info(f"   Futures: {futures_entry:.0f} → {futures_target:.0f} ({futures_move:.0f} pts)")
            log.info(f"   Risk: ₹{risk:.2f} | Reward: ₹{reward:.2f} | R:R = {risk_reward:.2f}:1")
            
            if has_greeks and theta_hourly != 0:
                log.info(f"📉 Theta Analysis:")
                log.info(f"   Theta/hour: {theta_hourly:.2f} (₹{abs(theta_hourly):.2f} decay)")
                log.info(f"   Expected decay ({EXPECTED_HOLD_HOURS}h): ₹{expected_theta_decay:.2f} ({theta_impact_percent:.2f}%)")
                log.info(f"   Delta: {delta:.4f} | Quality: {quality_score:.1f}/100")
            
            log.info(f"   Sentiment: {trade_setup['option_sentiment']}, PCR: {trade_setup['pcr']:.2f}")
            log.info(f"   Trade Type: {'Trending' if trade_setup['is_trending_trade'] else 'Zone-based'}")
            
            # ============ VALIDATION ============
            if risk_reward < MIN_RR_INTRADAY:
                log.warning(f"⚠️ Risk-reward {risk_reward:.2f} below minimum {MIN_RR_INTRADAY}:1")
                return {}
            
            if risk_percent > 10:
                log.warning(f"⚠️ Risk {risk_percent:.0f}% exceeds maximum 10%")
                return {}
            
            return trade_setup
            
        except Exception as e:
            log.error(f"Strike selection error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}


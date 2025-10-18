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
            option_chain: Option chain DataFrame
            spot_price: Current spot price
            zones: Supply/demand zones
        
        Returns:
            dict: Option chain analysis
        """
        try:
            if option_chain.empty:
                log.warning("Empty option chain received")
                return {}
            
            # Analyze calls and puts
            call_analysis = self._analyze_calls(option_chain, spot_price)
            put_analysis = self._analyze_puts(option_chain, spot_price)
            
            # PCR calculation
            total_call_oi = option_chain.get('call_oi', pd.Series([0])).sum()
            total_put_oi = option_chain.get('put_oi', pd.Series([0])).sum()
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
            
            log.info(f"Option Analysis: PCR={pcr:.2f}, MaxPain={max_pain:.2f}, Sentiment={analysis['market_sentiment']}")
            
            return analysis
            
        except Exception as e:
            log.error(f"Option chain analysis error: {str(e)}")
            return {}
    
    def _analyze_calls(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze call options."""
        try:
            atm_strike = self._find_atm_strike(df, spot)
            
            atm_data = df[df['strike'] == atm_strike]
            
            return {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_data['call_iv'].iloc[0]) if len(atm_data) > 0 and 'call_iv' in atm_data else 0,
                "total_oi": float(df['call_oi'].sum()) if 'call_oi' in df else 0,
                "oi_change": float(df['call_oi_change'].sum()) if 'call_oi_change' in df else 0,
                "volume": float(df['call_volume'].sum()) if 'call_volume' in df else 0
            }
        except Exception as e:
            log.error(f"Call analysis error: {str(e)}")
            return {"atm_strike": spot}
    
    def _analyze_puts(self, df: pd.DataFrame, spot: float) -> Dict:
        """Analyze put options."""
        try:
            atm_strike = self._find_atm_strike(df, spot)
            
            atm_data = df[df['strike'] == atm_strike]
            
            return {
                "atm_strike": float(atm_strike),
                "atm_iv": float(atm_data['put_iv'].iloc[0]) if len(atm_data) > 0 and 'put_iv' in atm_data else 0,
                "total_oi": float(df['put_oi'].sum()) if 'put_oi' in df else 0,
                "oi_change": float(df['put_oi_change'].sum()) if 'put_oi_change' in df else 0,
                "volume": float(df['put_volume'].sum()) if 'put_volume' in df else 0
            }
        except Exception as e:
            log.error(f"Put analysis error: {str(e)}")
            return {"atm_strike": spot}
    
    def _find_atm_strike(self, df: pd.DataFrame, spot: float) -> float:
        """Find ATM strike price."""
        if df.empty or 'strike' not in df:
            return spot
        
        strikes = df['strike'].values
        idx = np.abs(strikes - spot).argmin()
        return float(strikes[idx])
    
    def _calculate_max_pain(self, df: pd.DataFrame) -> float:
        """Calculate max pain point."""
        try:
            if 'strike' not in df or 'call_oi' not in df or 'put_oi' not in df:
                return 0
            
            strikes = df['strike'].unique()
            pain_values = []
            
            for strike in strikes:
                call_pain = df[df['strike'] > strike]['call_oi'].sum() * \
                           (df[df['strike'] > strike]['strike'] - strike).sum()
                put_pain = df[df['strike'] < strike]['put_oi'].sum() * \
                          (strike - df[df['strike'] < strike]['strike']).sum()
                total_pain = call_pain + put_pain
                pain_values.append((strike, total_pain))
            
            if pain_values:
                return float(min(pain_values, key=lambda x: x[1])[0])
            return 0
            
        except Exception as e:
            log.error(f"Max pain calculation error: {str(e)}")
            return 0
    
    def _find_support_from_oi(self, df: pd.DataFrame, spot: float) -> List[float]:
        """Find support levels from put OI."""
        try:
            if 'strike' not in df or 'put_oi' not in df:
                return []
            
            below_spot = df[df['strike'] < spot].copy()
            if below_spot.empty:
                return []
            
            below_spot = below_spot.nlargest(3, 'put_oi')
            return [float(x) for x in below_spot['strike'].tolist()]
            
        except Exception as e:
            log.error(f"Support identification error: {str(e)}")
            return []
    
    def _find_resistance_from_oi(self, df: pd.DataFrame, spot: float) -> List[float]:
        """Find resistance levels from call OI."""
        try:
            if 'strike' not in df or 'call_oi' not in df:
                return []
            
            above_spot = df[df['strike'] > spot].copy()
            if above_spot.empty:
                return []
            
            above_spot = above_spot.nlargest(3, 'call_oi')
            return [float(x) for x in above_spot['strike'].tolist()]
            
        except Exception as e:
            log.error(f"Resistance identification error: {str(e)}")
            return []
    
    def _determine_sentiment(self, pcr: float, call_data: Dict, put_data: Dict) -> str:
        """Determine market sentiment from options data."""
        if pcr > 1.3:
            return "Bullish"
        elif pcr < 0.7:
            return "Bearish"
        else:
            return "Neutral"
    
    def select_best_strike(
        self,
        zones: Dict,
        option_analysis: Dict,
        trade_direction: str
    ) -> Dict:
        """
        Select optimal strike based on zones and analysis.
        
        Args:
            zones: Supply/demand zones
            option_analysis: Option chain analysis
            trade_direction: "CALL" or "PUT"
        
        Returns:
            dict: Trade setup with strike selection
        """
        try:
            if trade_direction == "CALL":
                target_zone = zones.get('supply_zones', [{}])[0] if zones.get('supply_zones') else {}
                entry_zone = zones.get('demand_zones', [{}])[0] if zones.get('demand_zones') else {}
            else:  # PUT
                target_zone = zones.get('demand_zones', [{}])[0] if zones.get('demand_zones') else {}
                entry_zone = zones.get('supply_zones', [{}])[0] if zones.get('supply_zones') else {}
            
            if not target_zone or not entry_zone:
                return {}
            
            # Calculate prices
            entry_price = (entry_zone.get('zone_top', 0) + entry_zone.get('zone_bottom', 0)) / 2
            target_price = (target_zone.get('zone_top', 0) + target_zone.get('zone_bottom', 0)) / 2
            
            # Calculate stop loss (2% from entry)
            if trade_direction == "CALL":
                stop_loss = entry_price * 0.98
            else:
                stop_loss = entry_price * 1.02
            
            # Risk-reward calculation
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            trade_setup = {
                'direction': trade_direction,
                'entry_price': float(entry_price),
                'target_price': float(target_price),
                'stop_loss': float(stop_loss),
                'risk_reward': float(risk_reward),
                'entry_zone_confidence': entry_zone.get('confidence', 0),
                'target_zone_confidence': target_zone.get('confidence', 0),
                'option_sentiment': option_analysis.get('market_sentiment', 'Neutral')
            }
            
            log.info(f"Strike Selection: {trade_direction}, RR={risk_reward:.2f}")
            
            return trade_setup
            
        except Exception as e:
            log.error(f"Strike selection error: {str(e)}")
            return {}


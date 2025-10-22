"""Technical analysis agent for calculating indicators and identifying zones."""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from src.config import config
from src.utils.logger import log


class TechnicalAnalysisAgent:
    """Agent for technical analysis calculations."""
    
    def __init__(self, cfg: config):
        self.config = cfg
    
    # ========== EXISTING METHODS ==========
    
    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        value_area: float = 70
    ) -> Dict:
        """Calculate Volume Profile with POC, VAH, VAL."""
        try:
            if df.empty:
                return {}
            
            price_range = df["high"].max() - df["low"].min()
            num_bins = 50
            bin_size = price_range / num_bins
            
            if bin_size == 0:
                return {}
            
            volume_at_price = {}
            
            for idx, row in df.iterrows():
                candle_range = row["high"] - row["low"]
                
                if candle_range == 0:
                    price_level = round(row["close"] / bin_size) * bin_size
                    volume_at_price[price_level] = (
                        volume_at_price.get(price_level, 0) + row["volume"]
                    )
                else:
                    levels_in_candle = max(1, int(candle_range / bin_size))
                    volume_per_level = row["volume"] / levels_in_candle
                    
                    for i in range(levels_in_candle):
                        price_level = round((row["low"] + i * bin_size) / bin_size) * bin_size
                        volume_at_price[price_level] = (
                            volume_at_price.get(price_level, 0) + volume_per_level
                        )
            
            if not volume_at_price:
                return {}
            
            sorted_levels = sorted(
                volume_at_price.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            poc = sorted_levels[0][0]
            total_volume = sum(volume_at_price.values())
            value_area_volume = total_volume * (value_area / 100)
            
            cumulative_volume = 0
            value_area_prices = []
            
            for price, volume in sorted_levels:
                cumulative_volume += volume
                value_area_prices.append(price)
                if cumulative_volume >= value_area_volume:
                    break
            
            vah = max(value_area_prices)
            val = min(value_area_prices)
            
            log.info(f"Volume Profile: POC={poc:.2f}, VAH={vah:.2f}, VAL={val:.2f}")
            
            return {
                "poc": poc,
                "vah": vah,
                "val": val,
                "volume_profile": volume_at_price,
                "high_volume_nodes": sorted_levels[:5],
                "low_volume_nodes": sorted_levels[-5:],
            }
            
        except Exception as e:
            log.error(f"Volume profile calculation error: {str(e)}")
            return {}
    
    def identify_order_blocks(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> List[Dict]:
        """Identify Order Blocks (last candle before strong move)."""
        order_blocks = []
        
        try:
            if len(df) < lookback + 1:
                return []
            
            for i in range(lookback, len(df) - 1):
                if df["close"].iloc[i] > df["open"].iloc[i]:
                    next_move = df["close"].iloc[i + 1] - df["close"].iloc[i]
                    avg_move = df["close"].iloc[i - lookback:i].diff().abs().mean()
                    
                    if avg_move > 0 and next_move > 2 * avg_move:
                        order_blocks.append({
                            "type": "bullish",
                            "timestamp": df["timestamp"].iloc[i],
                            "high": float(df["high"].iloc[i]),
                            "low": float(df["low"].iloc[i]),
                            "zone_top": float(df["high"].iloc[i]),
                            "zone_bottom": float(df["open"].iloc[i]),
                            "strength": float(next_move / avg_move)
                        })
                
                elif df["close"].iloc[i] < df["open"].iloc[i]:
                    next_move = df["close"].iloc[i] - df["close"].iloc[i + 1]
                    avg_move = df["close"].iloc[i - lookback:i].diff().abs().mean()
                    
                    if avg_move > 0 and next_move > 2 * avg_move:
                        order_blocks.append({
                            "type": "bearish",
                            "timestamp": df["timestamp"].iloc[i],
                            "high": float(df["high"].iloc[i]),
                            "low": float(df["low"].iloc[i]),
                            "zone_top": float(df["close"].iloc[i]),
                            "zone_bottom": float(df["low"].iloc[i]),
                            "strength": float(next_move / avg_move)
                        })
            
            order_blocks = sorted(
                order_blocks,
                key=lambda x: x["strength"],
                reverse=True
            )[:10]
            
            log.info(f"Identified {len(order_blocks)} order blocks")
            return order_blocks
            
        except Exception as e:
            log.error(f"Order block identification error: {str(e)}")
            return []
    
    def identify_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Identify Fair Value Gaps."""
        fvgs = []
        
        try:
            if len(df) < 3:
                return []
            
            for i in range(1, len(df) - 1):
                if df["high"].iloc[i - 1] < df["low"].iloc[i + 1]:
                    gap_size = df["low"].iloc[i + 1] - df["high"].iloc[i - 1]
                    gap_pct = (gap_size / df["close"].iloc[i]) * 100
                    
                    if gap_pct >= self.config.FVG_MIN_SIZE:
                        fvgs.append({
                            "type": "bullish",
                            "timestamp": df["timestamp"].iloc[i],
                            "gap_top": float(df["low"].iloc[i + 1]),
                            "gap_bottom": float(df["high"].iloc[i - 1]),
                            "gap_size": float(gap_size),
                            "gap_percentage": float(gap_pct),
                            "filled": False
                        })
                
                elif df["low"].iloc[i - 1] > df["high"].iloc[i + 1]:
                    gap_size = df["low"].iloc[i - 1] - df["high"].iloc[i + 1]
                    gap_pct = (gap_size / df["close"].iloc[i]) * 100
                    
                    if gap_pct >= self.config.FVG_MIN_SIZE:
                        fvgs.append({
                            "type": "bearish",
                            "timestamp": df["timestamp"].iloc[i],
                            "gap_top": float(df["low"].iloc[i - 1]),
                            "gap_bottom": float(df["high"].iloc[i + 1]),
                            "gap_size": float(gap_size),
                            "gap_percentage": float(gap_pct),
                            "filled": False
                        })
            
            log.info(f"Identified {len(fvgs)} fair value gaps")
            return fvgs
            
        except Exception as e:
            log.error(f"FVG identification error: {str(e)}")
            return []
    
    def identify_supply_demand_zones(
        self,
        df: pd.DataFrame,
        vp_data: Dict,
        order_blocks: List[Dict],
        fvgs: List[Dict]
    ) -> Dict:
        """Combine indicators to identify supply/demand zones."""
        supply_zones = []
        demand_zones = []
        
        try:
            if df.empty:
                return {"demand_zones": [], "supply_zones": []}
            
            current_price = float(df["close"].iloc[-1])
            
            for ob in order_blocks:
                if ob["type"] == "bullish" and ob["zone_top"] < current_price:
                    volume_support = any(
                        abs(ob["zone_bottom"] - hvn[0]) / current_price < 0.02
                        for hvn in vp_data.get("high_volume_nodes", [])
                    )
                    
                    fvg_support = any(
                        fvg["type"] == "bullish" and
                        abs(fvg["gap_bottom"] - ob["zone_bottom"]) / current_price < 0.02
                        for fvg in fvgs
                    )
                    
                    confidence = 60 + (20 if volume_support else 0) + (20 if fvg_support else 0)
                    
                    demand_zones.append({
                        "zone_top": ob["zone_top"],
                        "zone_bottom": ob["zone_bottom"],
                        "confidence": confidence,
                        "distance_from_price": ((current_price - ob["zone_top"]) / current_price) * 100,
                        "factors": ["order_block"] +
                                 (["high_volume"] if volume_support else []) +
                                 (["fvg"] if fvg_support else [])
                    })
            
            for ob in order_blocks:
                if ob["type"] == "bearish" and ob["zone_bottom"] > current_price:
                    volume_support = any(
                        abs(ob["zone_top"] - hvn[0]) / current_price < 0.02
                        for hvn in vp_data.get("high_volume_nodes", [])
                    )
                    
                    fvg_support = any(
                        fvg["type"] == "bearish" and
                        abs(fvg["gap_top"] - ob["zone_top"]) / current_price < 0.02
                        for fvg in fvgs
                    )
                    
                    confidence = 60 + (20 if volume_support else 0) + (20 if fvg_support else 0)
                    
                    supply_zones.append({
                        "zone_top": ob["zone_top"],
                        "zone_bottom": ob["zone_bottom"],
                        "confidence": confidence,
                        "distance_from_price": ((ob["zone_bottom"] - current_price) / current_price) * 100,
                        "factors": ["order_block"] +
                                 (["high_volume"] if volume_support else []) +
                                 (["fvg"] if fvg_support else [])
                    })
            
            demand_zones = sorted(demand_zones, key=lambda x: x["confidence"], reverse=True)
            supply_zones = sorted(supply_zones, key=lambda x: x["confidence"], reverse=True)
            
            log.info(f"Identified {len(demand_zones)} demand zones, {len(supply_zones)} supply zones")
            
            return {
                "demand_zones": demand_zones,
                "supply_zones": supply_zones,
                "current_price": current_price,
                "poc": vp_data.get("poc"),
                "vah": vp_data.get("vah"),
                "val": vp_data.get("val"),
            }
            
        except Exception as e:
            log.error(f"Zone identification error: {str(e)}")
            return {"demand_zones": [], "supply_zones": []}
    
    # ========== NEW METHODS ==========
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calculate RSI (Relative Strength Index)."""
        try:
            if period is None:
                period = self.config.RSI_PERIOD
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            log.error(f"RSI calculation error: {e}")
            return pd.Series()
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = None, std_dev: float = None) -> Dict:
        """Calculate Bollinger Bands."""
        try:
            if period is None:
                period = self.config.BB_PERIOD
            if std_dev is None:
                std_dev = self.config.BB_STD_DEV
            
            sma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            
            return {
                'upper_band': sma + (std * std_dev),
                'middle_band': sma,
                'lower_band': sma - (std * std_dev),
                'bandwidth': ((sma + (std * std_dev)) - (sma - (std * std_dev))) / sma * 100
            }
        except Exception as e:
            log.error(f"Bollinger Bands calculation error: {e}")
            return {}
    
    def identify_candlestick_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Identify important candlestick patterns."""
        if not self.config.ENABLE_CANDLESTICK_PATTERNS:
            return []
        
        patterns = []
        
        try:
            for i in range(2, len(df)):
                current = df.iloc[i]
                prev = df.iloc[i-1]
                prev2 = df.iloc[i-2]
                
                body_current = abs(current['close'] - current['open'])
                body_prev = abs(prev['close'] - prev['open'])
                candle_range = current['high'] - current['low']
                
                # Bullish Engulfing
                if (prev['close'] < prev['open'] and
                    current['close'] > current['open'] and
                    current['open'] < prev['close'] and
                    current['close'] > prev['open']):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Bullish Engulfing',
                        'signal': 'BULLISH',
                        'confidence': 75
                    })
                
                # Bearish Engulfing
                if (prev['close'] > prev['open'] and
                    current['close'] < current['open'] and
                    current['open'] > prev['close'] and
                    current['close'] < prev['open']):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Bearish Engulfing',
                        'signal': 'BEARISH',
                        'confidence': 75
                    })
                
                # Doji
                if candle_range > 0 and body_current < (candle_range * 0.1):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Doji',
                        'signal': 'NEUTRAL',
                        'confidence': 60
                    })
                
                # Hammer
                lower_shadow = min(current['open'], current['close']) - current['low']
                upper_shadow = current['high'] - max(current['open'], current['close'])
                if (lower_shadow > body_current * 2 and
                    upper_shadow < body_current * 0.5 and
                    prev['close'] < prev['open']):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Hammer',
                        'signal': 'BULLISH',
                        'confidence': 70
                    })
                
                # Shooting Star
                if (upper_shadow > body_current * 2 and
                    lower_shadow < body_current * 0.5 and
                    prev['close'] > prev['open']):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Shooting Star',
                        'signal': 'BEARISH',
                        'confidence': 70
                    })
                
                # Morning Star
                if (prev2['close'] < prev2['open'] and
                    abs(prev['close'] - prev['open']) < (prev['high'] - prev['low']) * 0.3 and
                    current['close'] > current['open'] and
                    current['close'] > (prev2['open'] + prev2['close']) / 2):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Morning Star',
                        'signal': 'BULLISH',
                        'confidence': 80
                    })
                
                # Evening Star
                if (prev2['close'] > prev2['open'] and
                    abs(prev['close'] - prev['open']) < (prev['high'] - prev['low']) * 0.3 and
                    current['close'] < current['open'] and
                    current['close'] < (prev2['open'] + prev2['close']) / 2):
                    patterns.append({
                        'timestamp': current['timestamp'],
                        'pattern': 'Evening Star',
                        'signal': 'BEARISH',
                        'confidence': 80
                    })
            
            # Filter by minimum confidence
            patterns = [p for p in patterns if p['confidence'] >= self.config.MIN_PATTERN_CONFIDENCE]
            log.info(f"Identified {len(patterns)} candlestick patterns")
            return patterns
            
        except Exception as e:
            log.error(f"Candlestick pattern identification error: {e}")
            return []
    
    def identify_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Identify chart patterns (Double Top/Bottom, Head & Shoulders, etc.)."""
        if not self.config.ENABLE_CHART_PATTERNS:
            return []
        
        patterns = []
        
        try:
            from scipy.signal import argrelextrema
            
            high_idx = argrelextrema(df['high'].values, np.greater, order=5)[0]
            low_idx = argrelextrema(df['low'].values, np.less, order=5)[0]
            
            # Double Top
            if len(high_idx) >= 2:
                for i in range(len(high_idx) - 1):
                    peak1 = df.iloc[high_idx[i]]
                    peak2 = df.iloc[high_idx[i+1]]
                    
                    if abs(peak1['high'] - peak2['high']) / peak1['high'] < 0.02:
                        patterns.append({
                            'timestamp': peak2['timestamp'],
                            'pattern': 'Double Top',
                            'signal': 'BEARISH',
                            'confidence': 70,
                            'resistance': float(peak1['high'])
                        })
            
            # Double Bottom
            if len(low_idx) >= 2:
                for i in range(len(low_idx) - 1):
                    trough1 = df.iloc[low_idx[i]]
                    trough2 = df.iloc[low_idx[i+1]]
                    
                    if abs(trough1['low'] - trough2['low']) / trough1['low'] < 0.02:
                        patterns.append({
                            'timestamp': trough2['timestamp'],
                            'pattern': 'Double Bottom',
                            'signal': 'BULLISH',
                            'confidence': 70,
                            'support': float(trough1['low'])
                        })
            
            # Head and Shoulders
            if len(high_idx) >= 3:
                for i in range(len(high_idx) - 2):
                    left_shoulder = df.iloc[high_idx[i]]['high']
                    head = df.iloc[high_idx[i+1]]['high']
                    right_shoulder = df.iloc[high_idx[i+2]]['high']
                    
                    if (head > left_shoulder and head > right_shoulder and
                        abs(left_shoulder - right_shoulder) / left_shoulder < 0.03):
                        patterns.append({
                            'timestamp': df.iloc[high_idx[i+2]]['timestamp'],
                            'pattern': 'Head and Shoulders',
                            'signal': 'BEARISH',
                            'confidence': 80,
                            'neckline': float(min(df.iloc[high_idx[i]:high_idx[i+2]]['low']))
                        })
            
            # Filter by minimum confidence
            patterns = [p for p in patterns if p['confidence'] >= self.config.MIN_PATTERN_CONFIDENCE]
            log.info(f"Identified {len(patterns)} chart patterns")
            return patterns
            
        except Exception as e:
            log.error(f"Chart pattern identification error: {e}")
            return []
    
    def calculate_comprehensive_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators together."""
        try:
            indicators = {
                'rsi': self.calculate_rsi(df),
                'bollinger_bands': self.calculate_bollinger_bands(df),
                'candlestick_patterns': self.identify_candlestick_patterns(df),
                'chart_patterns': self.identify_chart_patterns(df),
                'latest_rsi': None,
                'bb_position': None,
                'rsi_signal': None
            }
            
            # Get latest RSI value
            if not indicators['rsi'].empty:
                latest_rsi = indicators['rsi'].iloc[-1]
                indicators['latest_rsi'] = float(latest_rsi)
                
                # RSI signal
                if latest_rsi > self.config.RSI_OVERBOUGHT:
                    indicators['rsi_signal'] = 'OVERBOUGHT'
                elif latest_rsi < self.config.RSI_OVERSOLD:
                    indicators['rsi_signal'] = 'OVERSOLD'
                else:
                    indicators['rsi_signal'] = 'NEUTRAL'
            
            # Check Bollinger Band position
            if indicators['bollinger_bands']:
                current_price = df['close'].iloc[-1]
                upper = indicators['bollinger_bands']['upper_band'].iloc[-1]
                lower = indicators['bollinger_bands']['lower_band'].iloc[-1]
                
                if current_price > upper:
                    indicators['bb_position'] = 'ABOVE_UPPER'
                elif current_price < lower:
                    indicators['bb_position'] = 'BELOW_LOWER'
                else:
                    indicators['bb_position'] = 'INSIDE_BANDS'
            
            log.info(f"Comprehensive indicators calculated: RSI={indicators['latest_rsi']}, "
                    f"RSI Signal={indicators['rsi_signal']}, BB Position={indicators['bb_position']}")
            
            return indicators
            
        except Exception as e:
            log.error(f"Comprehensive indicators error: {e}")
            return {}


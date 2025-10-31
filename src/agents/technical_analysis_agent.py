"""Technical analysis agent with enhanced Order Blocks, FVG, and Volume Profile."""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from src.config import config
from src.utils.logger import log


class TechnicalAnalysisAgent:
    """Agent for technical analysis with Smart Money Concepts."""
    
    def __init__(self, cfg: config):
        self.config = cfg
    
    # ========== OPTIMIZED VOLUME PROFILE ==========
    
    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        value_area: float = 70,
        sessions: int = None
    ) -> Dict:
        """
        Enhanced Volume Profile with delta tracking and HVN/LVN identification.
        
        Improvements:
        - Weighted volume distribution
        - Buy/Sell delta per price level
        - High Volume Nodes (HVN) and Low Volume Nodes (LVN)
        - Session-based calculation
        """
        try:
            if df.empty:
                return {}
            
            # Use only recent sessions
            if sessions is None:
                sessions = self.config.VP_SESSIONS
            
            recent_df = df.tail(sessions) if len(df) > sessions else df
            
            price_min = recent_df["low"].min()
            price_max = recent_df["high"].max()
            price_range = price_max - price_min
            
            if price_range == 0:
                return {}
            
            # Adaptive bin size (10 points for Nifty)
            num_bins = max(50, int(price_range / 10))
            bin_size = price_range / num_bins
            
            volume_profile = {}
            
            # Initialize bins
            for i in range(num_bins):
                bin_low = price_min + (i * bin_size)
                bin_high = bin_low + bin_size
                bin_mid = round((bin_low + bin_high) / 2, 2)
                
                volume_profile[bin_mid] = {
                    'price_low': bin_low,
                    'price_high': bin_high,
                    'total_volume': 0,
                    'buy_volume': 0,
                    'sell_volume': 0,
                    'delta': 0,
                    'touch_count': 0
                }
            
            # Weighted volume distribution
            for idx, row in recent_df.iterrows():
                candle_range = row["high"] - row["low"]
                
                for price_level, data in volume_profile.items():
                    # Calculate overlap
                    overlap_low = max(row["low"], data['price_low'])
                    overlap_high = min(row["high"], data['price_high'])
                    
                    if overlap_low < overlap_high:
                        # Weighted distribution
                        overlap_pct = (overlap_high - overlap_low) / candle_range if candle_range > 0 else 1
                        weighted_volume = row["volume"] * overlap_pct
                        
                        data['total_volume'] += weighted_volume
                        data['touch_count'] += 1
                        
                        # Buy/Sell classification
                        if row["close"] > row["open"]:
                            data['buy_volume'] += weighted_volume
                        else:
                            data['sell_volume'] += weighted_volume
                        
                        data['delta'] = data['buy_volume'] - data['sell_volume']
            
            # Find POC (Point of Control)
            if volume_profile:
                poc_price, poc_data = max(volume_profile.items(), key=lambda x: x[1]['total_volume'])
            else:
                return {}
            
            # Calculate Value Area
            total_volume = sum(v['total_volume'] for v in volume_profile.values())
            if total_volume == 0:
                return {}
            
            target_va_volume = total_volume * (value_area / 100)
            
            sorted_levels = sorted(
                volume_profile.items(),
                key=lambda x: x[1]['total_volume'],
                reverse=True
            )
            
            va_volume = 0
            va_high = 0
            va_low = float('inf')
            va_levels = []
            
            for price, data in sorted_levels:
                va_volume += data['total_volume']
                va_high = max(va_high, data['price_high'])
                va_low = min(va_low, data['price_low'])
                va_levels.append(price)
                
                if va_volume >= target_va_volume:
                    break
            
            # Identify HVN and LVN
            avg_volume = total_volume / len(volume_profile)
            
            hvn_levels = [
                {'price': price, 'volume': data['total_volume'], 'delta': data['delta']}
                for price, data in volume_profile.items()
                if data['total_volume'] > avg_volume * 1.5
            ]
            
            lvn_levels = [
                {'price': price, 'volume': data['total_volume']}
                for price, data in volume_profile.items()
                if data['total_volume'] < avg_volume * 0.5
            ]
            
            log.info(f"Volume Profile: POC={poc_price:.2f}, VAH={va_high:.2f}, VAL={va_low:.2f}")
            log.info(f"   HVN count: {len(hvn_levels)}, LVN count: {len(lvn_levels)}")
            log.info(f"   POC Delta: {poc_data['delta']:.0f} (Buy: {poc_data['buy_volume']:.0f}, Sell: {poc_data['sell_volume']:.0f})")
            
            return {
                "poc": poc_price,
                "poc_volume": poc_data['total_volume'],
                "poc_delta": poc_data['delta'],
                "vah": va_high,
                "val": va_low,
                "value_area_levels": va_levels,
                "high_volume_nodes": hvn_levels,
                "low_volume_nodes": lvn_levels,
                "volume_profile": volume_profile,
                "total_volume": total_volume,
                "sessions_analyzed": len(recent_df)
            }
            
        except Exception as e:
            log.error(f"Volume profile calculation error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}
    
    # ========== OPTIMIZED ORDER BLOCKS ==========
    
    def identify_order_blocks(
        self,
        df: pd.DataFrame,
        lookback: int = None
    ) -> List[Dict]:
        """
        Enhanced Order Blocks with volume confirmation and zone respect validation.
        
        Improvements:
        - Volume confirmation (impulse > OB volume)
        - Zone respect tracking (bounces)
        - Strength scoring (0-100)
        - Mitigation tracking
        """
        if lookback is None:
            lookback = self.config.OB_LOOKBACK
        
        order_blocks = []
        
        try:
            if len(df) < lookback + 10:
                return []
            
            for i in range(lookback, len(df) - 2):
                current = df.iloc[i]
                next_candle = df.iloc[i + 1]
                
                # BULLISH ORDER BLOCK
                if current["close"] < current["open"]:  # Down candle
                    impulse_move = next_candle["close"] - next_candle["open"]
                    ob_size = current["high"] - current["low"]
                    
                    if ob_size > 0 and impulse_move > ob_size * 1.5:
                        # Volume confirmation
                        volume_confirmed = next_candle["volume"] > current["volume"] * 1.2
                        
                        if volume_confirmed:
                            # Check if zone was respected
                            tested = False
                            bounced = False
                            touch_count = 0
                            
                            for j in range(i + 2, min(i + 10, len(df))):
                                test_candle = df.iloc[j]
                                
                                # Price tested the zone
                                if (test_candle["low"] <= current["high"] and 
                                    test_candle["low"] >= current["low"]):
                                    tested = True
                                    touch_count += 1
                                    
                                    # Price bounced (closed above zone)
                                    if test_candle["close"] > current["high"]:
                                        bounced = True
                            
                            # Calculate strength (0-100)
                            impulse_strength = min(50, (impulse_move / ob_size) * 20)
                            volume_strength = min(30, (next_candle["volume"] / current["volume"]) * 15)
                            respect_strength = 20 if bounced else (10 if tested else 0)
                            
                            total_strength = impulse_strength + volume_strength + respect_strength
                            
                            # Only add if strength >= 50
                            if total_strength >= 50:
                                order_blocks.append({
                                    "type": "demand",
                                    "zone_top": float(current["high"]),
                                    "zone_bottom": float(current["low"]),
                                    "zone_mid": float((current["high"] + current["low"]) / 2),
                                    "timestamp": current["timestamp"],
                                    "strength": float(total_strength),
                                    "tested": tested,
                                    "respected": bounced,
                                    "touch_count": touch_count,
                                    "mitigated": False,
                                    "volume_ratio": float(next_candle["volume"] / current["volume"]),
                                    "impulse_size": float(impulse_move)
                                })
                
                # BEARISH ORDER BLOCK
                elif current["close"] > current["open"]:  # Up candle
                    impulse_move = current["open"] - next_candle["close"]
                    ob_size = current["high"] - current["low"]
                    
                    if ob_size > 0 and impulse_move > ob_size * 1.5:
                        volume_confirmed = next_candle["volume"] > current["volume"] * 1.2
                        
                        if volume_confirmed:
                            tested = False
                            bounced = False
                            touch_count = 0
                            
                            for j in range(i + 2, min(i + 10, len(df))):
                                test_candle = df.iloc[j]
                                
                                if (test_candle["high"] >= current["low"] and 
                                    test_candle["high"] <= current["high"]):
                                    tested = True
                                    touch_count += 1
                                    
                                    if test_candle["close"] < current["low"]:
                                        bounced = True
                            
                            impulse_strength = min(50, (impulse_move / ob_size) * 20)
                            volume_strength = min(30, (next_candle["volume"] / current["volume"]) * 15)
                            respect_strength = 20 if bounced else (10 if tested else 0)
                            
                            total_strength = impulse_strength + volume_strength + respect_strength
                            
                            if total_strength >= 50:
                                order_blocks.append({
                                    "type": "supply",
                                    "zone_top": float(current["high"]),
                                    "zone_bottom": float(current["low"]),
                                    "zone_mid": float((current["high"] + current["low"]) / 2),
                                    "timestamp": current["timestamp"],
                                    "strength": float(total_strength),
                                    "tested": tested,
                                    "respected": bounced,
                                    "touch_count": touch_count,
                                    "mitigated": False,
                                    "volume_ratio": float(next_candle["volume"] / current["volume"]),
                                    "impulse_size": float(impulse_move)
                                })
            
            # Sort by strength
            order_blocks = sorted(order_blocks, key=lambda x: x["strength"], reverse=True)[:10]
            
            demand_count = sum(1 for ob in order_blocks if ob["type"] == "demand")
            supply_count = sum(1 for ob in order_blocks if ob["type"] == "supply")
            
            log.info(f"Identified {len(order_blocks)} order blocks (Demand: {demand_count}, Supply: {supply_count})")
            if order_blocks:
                log.info(f"   Top OB: {order_blocks[0]['type'].upper()} at {order_blocks[0]['zone_mid']:.2f} (Strength: {order_blocks[0]['strength']:.0f})")
            
            return order_blocks
            
        except Exception as e:
            log.error(f"Order block identification error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return []
    
    # ========== OPTIMIZED FAIR VALUE GAPS ==========
    
    def identify_fair_value_gaps(
        self,
        df: pd.DataFrame,
        min_gap_pct: float = None
    ) -> List[Dict]:
        """
        Enhanced Fair Value Gaps with fill tracking and classification.
        
        Improvements:
        - Gap size classification (large/medium/small)
        - Fill percentage tracking
        - Confidence scoring
        - Only returns valid (unfilled) FVGs
        """
        if min_gap_pct is None:
            min_gap_pct = self.config.FVG_MIN_SIZE * 100  # Convert to percentage
        
        fvgs = []
        
        try:
            if len(df) < 3:
                return []
            
            for i in range(1, len(df) - 1):
                candle_1 = df.iloc[i - 1]
                candle_2 = df.iloc[i]
                candle_3 = df.iloc[i + 1]
                
                # BULLISH FVG
                bullish_gap = candle_3["low"] - candle_1["high"]
                gap_pct = (bullish_gap / candle_1["high"]) * 100
                
                if bullish_gap > 0 and gap_pct >= min_gap_pct:
                    # Classify FVG size
                    if gap_pct >= 1.0:
                        gap_class = 'large'
                        confidence = 90
                    elif gap_pct >= 0.5:
                        gap_class = 'medium'
                        confidence = 75
                    else:
                        gap_class = 'small'
                        confidence = 60
                    
                    # Track fill percentage
                    filled_pct = 0
                    fully_filled = False
                    
                    for j in range(i + 2, min(i + 20, len(df))):
                        future = df.iloc[j]
                        
                        if future["low"] <= candle_1["high"]:
                            fill_level = candle_1["high"]
                            filled_pct = ((candle_3["low"] - fill_level) / bullish_gap) * 100
                            
                            if future["low"] <= candle_3["low"]:
                                fully_filled = True
                                break
                    
                    if not fully_filled:  # Only add valid FVGs
                        fvgs.append({
                            "type": "bullish",
                            "gap_top": float(candle_3["low"]),
                            "gap_bottom": float(candle_1["high"]),
                            "gap_mid": float((candle_3["low"] + candle_1["high"]) / 2),
                            "gap_size": float(bullish_gap),
                            "gap_pct": float(gap_pct),
                            "classification": gap_class,
                            "timestamp": candle_2["timestamp"],
                            "confidence": confidence,
                            "filled_pct": float(filled_pct),
                            "fully_filled": fully_filled,
                            "valid": True
                        })
                
                # BEARISH FVG
                bearish_gap = candle_1["low"] - candle_3["high"]
                gap_pct = (bearish_gap / candle_1["low"]) * 100
                
                if bearish_gap > 0 and gap_pct >= min_gap_pct:
                    if gap_pct >= 1.0:
                        gap_class = 'large'
                        confidence = 90
                    elif gap_pct >= 0.5:
                        gap_class = 'medium'
                        confidence = 75
                    else:
                        gap_class = 'small'
                        confidence = 60
                    
                    filled_pct = 0
                    fully_filled = False
                    
                    for j in range(i + 2, min(i + 20, len(df))):
                        future = df.iloc[j]
                        
                        if future["high"] >= candle_3["high"]:
                            fill_level = candle_3["high"]
                            filled_pct = ((fill_level - candle_1["low"]) / bearish_gap) * 100
                            
                            if future["high"] >= candle_1["low"]:
                                fully_filled = True
                                break
                    
                    if not fully_filled:
                        fvgs.append({
                            "type": "bearish",
                            "gap_top": float(candle_1["low"]),
                            "gap_bottom": float(candle_3["high"]),
                            "gap_mid": float((candle_1["low"] + candle_3["high"]) / 2),
                            "gap_size": float(bearish_gap),
                            "gap_pct": float(gap_pct),
                            "classification": gap_class,
                            "timestamp": candle_2["timestamp"],
                            "confidence": confidence,
                            "filled_pct": float(filled_pct),
                            "fully_filled": fully_filled,
                            "valid": True
                        })
            
            bullish_count = sum(1 for fvg in fvgs if fvg["type"] == "bullish")
            bearish_count = sum(1 for fvg in fvgs if fvg["type"] == "bearish")
            
            log.info(f"Identified {len(fvgs)} valid FVGs (Bullish: {bullish_count}, Bearish: {bearish_count})")
            if fvgs:
                large_fvgs = [fvg for fvg in fvgs if fvg["classification"] == "large"]
                log.info(f"   Large FVGs: {len(large_fvgs)}")
            
            return fvgs
            
        except Exception as e:
            log.error(f"FVG identification error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return []
    
    # ========== NEW: CONFLUENCE SCORING ==========
    
    def calculate_zone_confluence(
        self,
        price_level: float,
        order_blocks: List[Dict],
        fvgs: List[Dict],
        vp_data: Dict,
        tolerance: float = 50
    ) -> Dict:
        """
        Calculate confluence score for a specific price level.
        
        Combines Order Blocks, FVGs, and Volume Profile data.
        Higher score = stronger zone.
        """
        confluence_score = 0
        confluences = []
        
        try:
            # Check Order Blocks
            for ob in order_blocks:
                if ob["zone_bottom"] - tolerance <= price_level <= ob["zone_top"] + tolerance:
                    confluence_score += ob["strength"]
                    confluences.append(f"OB_{ob['type']}_{ob['strength']:.0f}")
            
            # Check FVGs
            for fvg in fvgs:
                if fvg["gap_bottom"] - tolerance <= price_level <= fvg["gap_top"] + tolerance:
                    confluence_score += fvg["confidence"]
                    confluences.append(f"FVG_{fvg['type']}_{fvg['classification']}")
            
            # Check Volume Profile HVNs
            for hvn in vp_data.get("high_volume_nodes", []):
                if abs(hvn["price"] - price_level) <= tolerance:
                    volume_score = min(50, (hvn["volume"] / vp_data["total_volume"]) * 1000)
                    confluence_score += volume_score
                    confluences.append(f"VP_HVN_{volume_score:.0f}")
            
            # Check POC
            if abs(vp_data.get("poc", 0) - price_level) <= tolerance:
                confluence_score += 50
                confluences.append("VP_POC")
            
            # Check VAH/VAL
            if abs(vp_data.get("vah", 0) - price_level) <= tolerance:
                confluence_score += 30
                confluences.append("VP_VAH")
            if abs(vp_data.get("val", 0) - price_level) <= tolerance:
                confluence_score += 30
                confluences.append("VP_VAL")
            
            return {
                "price_level": float(price_level),
                "confluence_score": min(100, float(confluence_score)),
                "confluence_count": len(confluences),
                "confluences": confluences,
                "rating": "STRONG" if confluence_score >= 150 else ("MODERATE" if confluence_score >= 100 else "WEAK")
            }
            
        except Exception as e:
            log.error(f"Confluence calculation error: {e}")
            return {
                "price_level": float(price_level),
                "confluence_score": 0,
                "confluence_count": 0,
                "confluences": [],
                "rating": "WEAK"
            }
    
    # ========== UPDATED: ZONE IDENTIFICATION ==========
    
    def identify_supply_demand_zones(
        self,
        df: pd.DataFrame,
        vp_data: Dict,
        order_blocks: List[Dict],
        fvgs: List[Dict]
    ) -> Dict:
        """
        Enhanced zone identification with confluence scoring.
        
        Improvements:
        - Uses confluence scoring for each zone
        - Better filtering based on confluence
        - More accurate confidence ratings
        """
        supply_zones = []
        demand_zones = []
        
        try:
            if df.empty:
                return {"demand_zones": [], "supply_zones": []}
            
            current_price = float(df["close"].iloc[-1])
            
            # Process demand zones (bullish)
            for ob in order_blocks:
                if ob["type"] == "demand" and ob["zone_top"] < current_price:
                    # Calculate confluence at this zone
                    confluence = self.calculate_zone_confluence(
                        ob["zone_mid"],
                        order_blocks,
                        fvgs,
                        vp_data,
                        tolerance=50
                    )
                    
                    demand_zones.append({
                        "zone_top": ob["zone_top"],
                        "zone_bottom": ob["zone_bottom"],
                        "zone_mid": ob["zone_mid"],
                        "confidence": confluence["confluence_score"],
                        "distance_from_price": ((current_price - ob["zone_top"]) / current_price) * 100,
                        "confluence_count": confluence["confluence_count"],
                        "factors": confluence["confluences"],
                        "rating": confluence["rating"],
                        "ob_strength": ob["strength"],
                        "tested": ob["tested"],
                        "respected": ob["respected"]
                    })
            
            # Process supply zones (bearish)
            for ob in order_blocks:
                if ob["type"] == "supply" and ob["zone_bottom"] > current_price:
                    confluence = self.calculate_zone_confluence(
                        ob["zone_mid"],
                        order_blocks,
                        fvgs,
                        vp_data,
                        tolerance=50
                    )
                    
                    supply_zones.append({
                        "zone_top": ob["zone_top"],
                        "zone_bottom": ob["zone_bottom"],
                        "zone_mid": ob["zone_mid"],
                        "confidence": confluence["confluence_score"],
                        "distance_from_price": ((ob["zone_bottom"] - current_price) / current_price) * 100,
                        "confluence_count": confluence["confluence_count"],
                        "factors": confluence["confluences"],
                        "rating": confluence["rating"],
                        "ob_strength": ob["strength"],
                        "tested": ob["tested"],
                        "respected": ob["respected"]
                    })
            
            # Sort by confluence score
            demand_zones = sorted(demand_zones, key=lambda x: x["confidence"], reverse=True)
            supply_zones = sorted(supply_zones, key=lambda x: x["confidence"], reverse=True)
            
            log.info(f"Zone Summary:")
            log.info(f"   Demand zones: {len(demand_zones)}")
            log.info(f"   Supply zones: {len(supply_zones)}")
            
            if demand_zones:
                top_demand = demand_zones[0]
                log.info(f"   Top Demand: {top_demand['zone_mid']:.2f} "
                        f"(Confidence: {top_demand['confidence']:.0f}, "
                        f"Confluence: {top_demand['confluence_count']}, "
                        f"Rating: {top_demand['rating']})")
            
            if supply_zones:
                top_supply = supply_zones[0]
                log.info(f"   Top Supply: {top_supply['zone_mid']:.2f} "
                        f"(Confidence: {top_supply['confidence']:.0f}, "
                        f"Confluence: {top_supply['confluence_count']}, "
                        f"Rating: {top_supply['rating']})")
            
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
            import traceback
            log.error(traceback.format_exc())
            return {"demand_zones": [], "supply_zones": []}
    
    # ========== KEEP EXISTING METHODS ==========
    
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


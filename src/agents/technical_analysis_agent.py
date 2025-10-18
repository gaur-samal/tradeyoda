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
    
    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        value_area: float = 70
    ) -> Dict:
        """
        Calculate Volume Profile with POC, VAH, VAL.
        
        Args:
            df: OHLCV DataFrame
            value_area: Value area percentage (default 70%)
        
        Returns:
            dict: Volume profile data
        """
        try:
            if df.empty:
                return {}
            
            # Create price bins
            price_range = df["high"].max() - df["low"].min()
            num_bins = 50
            bin_size = price_range / num_bins
            
            if bin_size == 0:
                return {}
            
            # Calculate volume at each price level
            volume_at_price = {}
            
            for idx, row in df.iterrows():
                candle_range = row["high"] - row["low"]
                
                if candle_range == 0:
                    price_level = round(row["close"] / bin_size) * bin_size
                    volume_at_price[price_level] = (
                        volume_at_price.get(price_level, 0) + row["volume"]
                    )
                else:
                    # Distribute volume across candle range
                    levels_in_candle = max(1, int(candle_range / bin_size))
                    volume_per_level = row["volume"] / levels_in_candle
                    
                    for i in range(levels_in_candle):
                        price_level = round((row["low"] + i * bin_size) / bin_size) * bin_size
                        volume_at_price[price_level] = (
                            volume_at_price.get(price_level, 0) + volume_per_level
                        )
            
            if not volume_at_price:
                return {}
            
            # Sort by volume
            sorted_levels = sorted(
                volume_at_price.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Point of Control (highest volume)
            poc = sorted_levels[0][0]
            
            # Calculate Value Area
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
        """
        Identify Order Blocks (last candle before strong move).
        
        Args:
            df: OHLCV DataFrame
            lookback: Lookback period
        
        Returns:
            list: Order blocks
        """
        order_blocks = []
        
        try:
            if len(df) < lookback + 1:
                return []
            
            for i in range(lookback, len(df) - 1):
                # Bullish Order Block
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
                
                # Bearish Order Block
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
            
            # Sort by strength and return top 10
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
        """
        Identify Fair Value Gaps.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            list: Fair value gaps
        """
        fvgs = []
        
        try:
            if len(df) < 3:
                return []
            
            for i in range(1, len(df) - 1):
                # Bullish FVG
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
                
                # Bearish FVG
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
        """
        Combine indicators to identify supply/demand zones.
        
        Args:
            df: OHLCV DataFrame
            vp_data: Volume profile data
            order_blocks: List of order blocks
            fvgs: List of fair value gaps
        
        Returns:
            dict: Supply and demand zones
        """
        supply_zones = []
        demand_zones = []
        
        try:
            if df.empty:
                return {"demand_zones": [], "supply_zones": []}
            
            current_price = float(df["close"].iloc[-1])
            
            # Demand zones from bullish order blocks
            for ob in order_blocks:
                if ob["type"] == "bullish" and ob["zone_top"] < current_price:
                    # Check volume confluence
                    volume_support = any(
                        abs(ob["zone_bottom"] - hvn[0]) / current_price < 0.02
                        for hvn in vp_data.get("high_volume_nodes", [])
                    )
                    
                    # Check FVG confluence
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
            
            # Supply zones from bearish order blocks
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
            
            # Sort by confidence
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


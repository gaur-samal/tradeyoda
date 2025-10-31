"""Main trading orchestrator coordinating all agents."""
import asyncio
from datetime import datetime, timedelta, date
import pandas as pd
from typing import Dict, Optional
from dhanhq import MarketFeed

def ensure_str_date(val):
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    return str(val)

from src.config import config
from src.agents import (
    DataCollectionAgent,
    TechnicalAnalysisAgent,
    LLMAnalysisAgent,
    OptionsAnalysisAgent,
    ExecutionAgent
)
from src.utils.logger import log
from src.utils.helpers import (
    get_nearest_expiry,
    validate_market_hours,
    create_trade_record
)

class TradingOrchestrator:
    """Main orchestrator with real-time feeds and trade management."""

    def __init__(self, cfg: config):
        self.config = cfg
        self.dhan_context = cfg.get_dhan_context()

        self.data_agent = DataCollectionAgent(self.dhan_context)
        self.tech_agent = TechnicalAnalysisAgent(cfg)
        self.llm_agent = LLMAnalysisAgent(cfg.OPENAI_API_KEY)
        self.options_agent = OptionsAnalysisAgent(cfg)
        self.execution_agent = ExecutionAgent(self.dhan_context)

        self.active_trades = []
        self.analysis_cache = {}
        self.is_running = False
        self.monitoring_task = None
        
        # ===== TRADE MANAGEMENT =====
        self.last_trade_times = {}  # Track last trade time per zone
        self.daily_trade_count = 0
        self.daily_trade_date = datetime.now().date()
        
        log.info("🤖 Trading Orchestrator initialized")
        log.info(f"   Max trades per day: {cfg.MAX_TRADES_PER_DAY}")
        log.info(f"   Zone cooldown: {cfg.ZONE_COOLDOWN_MINUTES} minutes")
        log.info(f"   Max concurrent positions: {cfg.MAX_CONCURRENT_POSITIONS}")

    def start(self):
        """Start the trading system."""
        try:
            self.config.validate()
            self.is_running = True
            log.info("✅ Trading system started")
        except Exception as e:
            log.error(f"❌ Failed to start system: {e}")
            raise

    def _handle_order_update(self, order_data: dict):
        try:
            data = order_data.get("Data", {})
            order_id = data.get("OrderNo") or data.get("orderId")
            order_status = data.get("Status") or data.get("orderStatus")
            log.info(f"📢 Order Update: {order_id} ➜ {order_status}")

            for trade in self.active_trades:
                if trade.get("order_ids", {}).get("order_id") == order_id:
                    trade["current_status"] = order_status
                    trade["last_update"] = datetime.now()
                    if order_status == "TRADED":
                        self._calculate_trade_pnl(trade, data)

        except Exception as e:
            log.error(f"Order update handler error: {e}")

    def _calculate_trade_pnl(self, trade: dict, order_data: dict):
        try:
            trade["pnl"] = 0.0
            trade["status"] = "CLOSED"
            log.info(f"Trade closed → P&L = {trade['pnl']}")
        except Exception as e:
            log.error(f"P&L calculation error: {e}")

    # ===== TRADE DEDUPLICATION METHODS =====
    
    def _check_duplicate_trade(
        self,
        strike: float,
        option_type: str,
        zone_mid: float,
        tolerance: float = None
    ) -> bool:
        """
        Check if there's already an active trade for this strike/zone.
        
        Args:
            strike: Option strike price
            option_type: CALL or PUT
            zone_mid: Zone midpoint
            tolerance: Percentage tolerance for zone matching (uses config default if None)
        
        Returns:
            True if duplicate found, False otherwise
        """
        tolerance = tolerance or self.config.DUPLICATE_ZONE_TOLERANCE
        
        for trade in self.active_trades:
            # Skip closed/cancelled trades
            if trade.get("status") not in ["ACTIVE", "PENDING", "PAPER"]:
                continue
            
            # Check if same strike and direction
            trade_strike = trade.get("strike", 0)
            trade_type = trade.get("option_type")
            
            if (abs(trade_strike - strike) < 1 and trade_type == option_type):
                log.warning(f"⚠️ Duplicate trade detected: {strike} {option_type} already active")
                log.warning(f"   Existing trade: {trade.get('trade_id')}")
                return True
            
            # Check if same zone (within tolerance)
            trade_entry = trade.get("futures_entry", 0)
            if trade_entry > 0 and zone_mid > 0:
                zone_distance = abs(trade_entry - zone_mid) / zone_mid * 100
                if zone_distance <= tolerance:
                    log.warning(f"⚠️ Similar zone trade active:")
                    log.warning(f"   Existing zone: {trade_entry:.2f}")
                    log.warning(f"   New zone: {zone_mid:.2f}")
                    log.warning(f"   Distance: {zone_distance:.2f}% (tolerance: {tolerance}%)")
                    return True
        
        return False

    def _check_zone_cooldown(self, zone_mid: float, cooldown_minutes: int = None) -> bool:
        """
        Check if enough time has passed since last trade in this zone.
        
        Args:
            zone_mid: Zone midpoint
            cooldown_minutes: Cooldown period (uses config default if None)
        
        Returns:
            True if zone is in cooldown, False if can trade
        """
        cooldown = cooldown_minutes or self.config.ZONE_COOLDOWN_MINUTES
        zone_key = f"{zone_mid:.2f}"
        
        last_trade_time = self.last_trade_times.get(zone_key)
        
        if last_trade_time:
            elapsed = (datetime.now() - last_trade_time).seconds / 60
            if elapsed < cooldown:
                remaining = cooldown - elapsed
                log.warning(f"⚠️ Zone cooldown active:")
                log.warning(f"   Zone: {zone_key}")
                log.warning(f"   Time remaining: {remaining:.1f} minutes")
                return True
        
        return False

    def _record_zone_trade(self, zone_mid: float):
        """Record that a trade was taken in this zone."""
        zone_key = f"{zone_mid:.2f}"
        self.last_trade_times[zone_key] = datetime.now()
        log.info(f"📝 Zone trade recorded: {zone_key}")
        log.debug(f"   Active zone cooldowns: {len(self.last_trade_times)}")

    def _check_daily_trade_limit(self) -> bool:
        """
        Check if daily trade limit reached.
        
        Returns:
            True if limit reached, False if can trade
        """
        # Reset counter if new day
        current_date = datetime.now().date()
        if current_date != self.daily_trade_date:
            self.daily_trade_count = 0
            self.daily_trade_date = current_date
            log.info(f"📅 Daily trade counter reset for {current_date}")
        
        # Check limit
        if self.daily_trade_count >= self.config.MAX_TRADES_PER_DAY:
            log.warning(f"⚠️ Daily trade limit reached: {self.daily_trade_count}/{self.config.MAX_TRADES_PER_DAY}")
            return True
        
        return False

    def _increment_daily_trades(self):
        """Increment daily trade counter."""
        self.daily_trade_count += 1
        log.info(f"📊 Daily trades: {self.daily_trade_count}/{self.config.MAX_TRADES_PER_DAY}")

    def _check_max_positions(self) -> bool:
        """Check if maximum concurrent positions reached."""
        active_count = sum(
            1 for trade in self.active_trades 
            if trade.get("status") in ["ACTIVE", "PENDING"]
        )
        
        if active_count >= self.config.MAX_CONCURRENT_POSITIONS:
            log.warning(f"⚠️ Max concurrent positions reached: {active_count}/{self.config.MAX_CONCURRENT_POSITIONS}")
            return True
        
        return False

    # ===== EXISTING METHODS =====

    async def run_zone_identification_cycle(self) -> Optional[Dict]:
        """Enhanced zone identification with LLM validation + rule-based metadata."""
        instrument = self.config.get_active_instrument()
        log.info(f"🔍 Zone identification for {instrument['name']} ({instrument['symbol']})...")
        log.info(f"   Expiry Type: {instrument['expiry_type']}, Day: {instrument['expiry_day']}")
        log.info(f"   Lot Size: {instrument['lot_size']}")
        
        try:
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            if self.config.USE_BACKTEST_MODE:
                log.info("🧪 Backtest mode active - loading historical data")
                from_date = ensure_str_date(self.config.BACKTEST_FROM)
                to_date = ensure_str_date(self.config.BACKTEST_TO)
                df_15min = self.data_agent.fetch_historical_data(
                    security_id=self.config.NIFTY_FUTURES_SECURITY_ID,
                    exchange_segment=self.config.NIFTY_FUTURES_EXCHANGE,
                    instrument_type=self.config.ANALYSIS_INSTRUMENT_TYPE,
                    timeframe=str(self.config.ZONE_TIMEFRAME),
                    from_date=from_date,
                    to_date=to_date,
                )
            else:
                if not validate_market_hours():
                    log.info("⏰ Outside market hours")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
                log.info("Fetching FUTURES Data")
                df_15min = self.data_agent.fetch_historical_data(
                    security_id=self.config.NIFTY_FUTURES_SECURITY_ID,
                    exchange_segment=self.config.NIFTY_FUTURES_EXCHANGE,
                    instrument_type=self.config.ANALYSIS_INSTRUMENT_TYPE,
                    timeframe=str(self.config.ZONE_TIMEFRAME),
                    from_date=start_date.strftime("%Y-%m-%d"),
                    to_date=end_date.strftime("%Y-%m-%d"),
                )
            
            if df_15min.empty:
                log.warning("⚠️ No 15-min data available")
                return None

            # Fetch live quote
            quotes = self.data_agent.fetch_market_quotes(
                securities=[self.config.NIFTY_FUTURES_SECURITY_ID],
                exchange_segment=self.config.NIFTY_FUTURES_EXCHANGE
            )
            live_quote = quotes.get(str(self.config.NIFTY_FUTURES_SECURITY_ID), {})
            current_price = live_quote.get("LTP", df_15min["close"].iloc[-1])

            # Calculate comprehensive indicators
            tech_indicators = self.tech_agent.calculate_comprehensive_indicators(df_15min)
            
            # STEP 1: Rule-based zone identification (FULL METADATA)
            log.info("📊 Running rule-based zone identification...")
            vp_data = self.tech_agent.calculate_volume_profile(df_15min, self.config.VP_VALUE_AREA)
            order_blocks = self.tech_agent.identify_order_blocks(df_15min, self.config.OB_LOOKBACK)
            fvgs = self.tech_agent.identify_fair_value_gaps(df_15min)
            rule_based_zones = self.tech_agent.identify_supply_demand_zones(df_15min, vp_data, order_blocks, fvgs)
            
            # Log technical analysis
            log.info(f"📊 Technical Analysis Summary:")
            log.info(f"   Order Blocks: {len(order_blocks)} identified")
            log.info(f"   Fair Value Gaps: {len(fvgs)} valid FVGs")
            log.info(f"   Volume Profile:")
            log.info(f"      POC: {vp_data.get('poc', 0):.2f} (Delta: {vp_data.get('poc_delta', 0):.0f})")
            log.info(f"      VAH: {vp_data.get('vah', 0):.2f}")
            log.info(f"      VAL: {vp_data.get('val', 0):.2f}")
            log.info(f"      HVN Count: {len(vp_data.get('high_volume_nodes', []))}")

            # Log top zones
            demand_zones = rule_based_zones.get('demand_zones', [])
            supply_zones = rule_based_zones.get('supply_zones', [])

            if demand_zones:
                top_demand = demand_zones[0]
                log.info(f"🟢 Top Demand Zone: {top_demand['zone_mid']:.2f}")
                log.info(f"      Confluence Score: {top_demand['confidence']:.0f}")
                log.info(f"      Rating: {top_demand.get('rating', 'N/A')}")
                log.info(f"      Factors: {', '.join(top_demand.get('factors', []))}")
                log.info(f"      Confluence Count: {top_demand.get('confluence_count', 0)}")

            if supply_zones:
                top_supply = supply_zones[0]
                log.info(f"🔴 Top Supply Zone: {top_supply['zone_mid']:.2f}")
                log.info(f"      Confluence Score: {top_supply['confidence']:.0f}")
                log.info(f"      Rating: {top_supply.get('rating', 'N/A')}")
                log.info(f"      Factors: {', '.join(top_supply.get('factors', []))}")
                log.info(f"      Confluence Count: {top_supply.get('confluence_count', 0)}")

            # Market context
            market_context = {
                "trend": self._determine_trend(df_15min),
                "volatility": float(df_15min["close"].pct_change().std()),
                "current_price": current_price,
                "rsi": tech_indicators.get('latest_rsi'),
                "rsi_signal": tech_indicators.get('rsi_signal'),
                "bb_position": tech_indicators.get('bb_position'),
                "recent_candlestick_patterns": tech_indicators.get('candlestick_patterns', [])[-5:],
                "recent_chart_patterns": tech_indicators.get('chart_patterns', [])[-3:],
            }

            # STEP 2: LLM Enhancement (VALIDATION + RANKING)
            log.info("🤖 Running LLM zone validation and enhancement...")
            llm_enhanced_zones = self.llm_agent.validate_and_enhance_zones(
                rule_based_zones,
                df_15min,
                tech_indicators,
                market_context
            )
            
            # STEP 3: MERGE - LLM validation + Rule-based metadata
            log.info("🔗 Merging LLM validation with rule-based metadata...")
            final_zones = self._merge_llm_and_rule_zones(
                rule_based_zones=rule_based_zones,
                llm_zones=llm_enhanced_zones,
                current_price=current_price
            )
            
            # STEP 4: Existing LLM analysis
            llm_analysis = self.llm_agent.analyze_zones(final_zones, market_context)
            
            # Cache results
            self.analysis_cache = {
                "zones": final_zones,
                "llm_analysis": llm_analysis,
                "llm_enhanced_zones": llm_enhanced_zones,
                "rule_based_zones": rule_based_zones,
                "vp_data": vp_data,
                "market_context": market_context,
                "technical_indicators": tech_indicators,
                "timestamp": datetime.now(),
                "current_price": current_price,
            }

            log.info(f"✅ Zone Identification Complete (LLM + Rule-Based):")
            log.info(f"   Final Demand Zones: {len(final_zones['demand_zones'])} (LLM-validated)")
            log.info(f"   Final Supply Zones: {len(final_zones['supply_zones'])} (LLM-validated)")
            log.info(f"   Market Bias: {llm_enhanced_zones.get('primary_bias', 'Unknown')}")
            log.info(f"   RSI: {tech_indicators.get('latest_rsi', 'N/A')} ({tech_indicators.get('rsi_signal', 'N/A')})")
            log.info(f"   BB Position: {tech_indicators.get('bb_position', 'N/A')}")
            
            return self.analysis_cache

        except Exception as e:
            log.error(f"❌ Zone identification error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None

    def _merge_llm_and_rule_zones(
        self,
        rule_based_zones: Dict,
        llm_zones: Dict,
        current_price: float
    ) -> Dict:
        """Merge LLM-validated zones with rule-based metadata."""
        try:
            llm_demand_zones = llm_zones.get('demand_zones', [])
            llm_supply_zones = llm_zones.get('supply_zones', [])
            
            llm_demand_lookup = {self._get_zone_id(z): z for z in llm_demand_zones}
            llm_supply_lookup = {self._get_zone_id(z): z for z in llm_supply_zones}
            
            merged_demand = []
            for rule_zone in rule_based_zones.get('demand_zones', []):
                zone_id = self._get_zone_id(rule_zone)
                
                if zone_id in llm_demand_lookup:
                    llm_zone = llm_demand_lookup[zone_id]
                    
                    merged_zone = {
                        **rule_zone,
                        'llm_validated': True,
                        'llm_confidence': llm_zone.get('llm_confidence', 0),
                        'llm_reasoning': llm_zone.get('llm_reasoning', ''),
                        'llm_priority': llm_zone.get('priority', 0),
                    }
                    
                    merged_demand.append(merged_zone)
                    log.debug(f"✅ Merged demand zone at {rule_zone.get('zone_mid', 0):.2f}")
            
            merged_supply = []
            for rule_zone in rule_based_zones.get('supply_zones', []):
                zone_id = self._get_zone_id(rule_zone)
                
                if zone_id in llm_supply_lookup:
                    llm_zone = llm_supply_lookup[zone_id]
                    
                    merged_zone = {
                        **rule_zone,
                        'llm_validated': True,
                        'llm_confidence': llm_zone.get('llm_confidence', 0),
                        'llm_reasoning': llm_zone.get('llm_reasoning', ''),
                        'llm_priority': llm_zone.get('priority', 0),
                    }
                    
                    merged_supply.append(merged_zone)
                    log.debug(f"✅ Merged supply zone at {rule_zone.get('zone_mid', 0):.2f}")
            
            merged_demand = sorted(
                merged_demand,
                key=lambda z: z.get('confidence', 0) + z.get('llm_confidence', 0),
                reverse=True
            )
            
            merged_supply = sorted(
                merged_supply,
                key=lambda z: z.get('confidence', 0) + z.get('llm_confidence', 0),
                reverse=True
            )
            
            log.info(f"🔗 Merge complete:")
            log.info(f"   Demand: {len(rule_based_zones.get('demand_zones', []))} → {len(merged_demand)} LLM-validated")
            log.info(f"   Supply: {len(rule_based_zones.get('supply_zones', []))} → {len(merged_supply)} LLM-validated")
            
            return {
                'demand_zones': merged_demand,
                'supply_zones': merged_supply,
                'current_price': current_price,
                'poc': rule_based_zones.get('poc'),
                'vah': rule_based_zones.get('vah'),
                'val': rule_based_zones.get('val'),
            }
            
        except Exception as e:
            log.error(f"Zone merge error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return rule_based_zones

    def _get_zone_id(self, zone: Dict) -> str:
        """Generate unique identifier for a zone using zone_mid."""
        zone_mid = zone.get('zone_mid', 0)
        if not zone_mid:
            zone_top = zone.get('zone_top', 0)
            zone_bottom = zone.get('zone_bottom', 0)
            zone_mid = (zone_top + zone_bottom) / 2
        return f"{zone_mid:.2f}"

    async def run_trade_identification_cycle(self) -> Optional[Dict]:
        """3-minute cycle for trade identification with deduplication."""
        log.info("🎯 Trade identification cycle starting...")
        
        if self.config.NO_TRADES_ON_EXPIRY and self.config.is_expiry_day():
            instrument_name = self.config.get_active_instrument()["name"]
            log.warning(f"⚠️ No trades on expiry day for {instrument_name}")
            return None
        
        try:
            if not validate_market_hours():
                log.info("⏰ Outside market hours")

            if not self.analysis_cache or \
               (datetime.now() - self.analysis_cache.get("timestamp", datetime.now())).seconds > 900:
                log.warning("⚠️ Zone analysis too old → refreshing")
                await self.run_zone_identification_cycle()

            # ===== CHECK DAILY LIMIT =====
            if self._check_daily_trade_limit():
                log.info("⚠️ Trade skipped: Daily limit reached")
                return None

            # ===== CHECK MAX POSITIONS =====
            if self._check_max_positions():
                log.info("⚠️ Trade skipped: Maximum positions reached")
                return None

            quotes = self.data_agent.fetch_market_quotes(
                securities=[self.config.NIFTY_FUTURES_SECURITY_ID],
                exchange_segment=self.config.NIFTY_FUTURES_EXCHANGE
            )
            live_quote = quotes.get(str(self.config.NIFTY_FUTURES_SECURITY_ID), {})
            current_price = live_quote.get("LTP")

            zones = self.analysis_cache.get("zones", {})
            trade_opportunity = self._check_zone_proximity(current_price, zones)
            
            if not trade_opportunity:
                log.info("ℹ️ No trade opportunity — price away from zones")
                return None

            # ===== CHECK ZONE COOLDOWN =====
            zone = trade_opportunity.get("zone", {})
            zone_mid = zone.get("zone_mid", 0)
            
            if self._check_zone_cooldown(zone_mid):
                log.info(f"⚠️ Trade skipped: Zone {zone_mid:.2f} in cooldown")
                return None

            expiry = get_nearest_expiry(self.config.get_active_instrument())
            option_chain = self.data_agent.fetch_option_chain(
                self.config.NIFTY_INDEX_SECURITY_ID,
                self.config.NIFTY_INDEX_EXCHANGE,
                expiry
            )
            
            option_analysis = self.options_agent.analyze_option_chain(
                option_chain, current_price, zones
            )
            
            trade_setup = self.options_agent.select_best_strike(
                zones, option_analysis, trade_opportunity["direction"], current_price, option_chain
            )
            
            if not trade_setup:
                log.info("ℹ️ No valid trade setup")
                return None
            
            # Add expiry and symbol
            trade_setup["expiry"] = expiry
            trade_setup["symbol"] = self.config.get_active_instrument()["symbol"]
            
            # ===== CHECK FOR DUPLICATE STRIKE =====
            if self._check_duplicate_trade(
                strike=trade_setup.get("strike"),
                option_type=trade_setup.get("option_type"),
                zone_mid=zone_mid
            ):
                log.info("⚠️ Trade skipped: Duplicate position")
                return None
            
            trade_opportunity_data = {
                **trade_setup,
                "zones": zones,
                "option_analysis": option_analysis,
                "technical_indicators": self.analysis_cache.get("technical_indicators", {}),
                "market_context": self.analysis_cache.get("market_context", {}),
                "zone_confluence": {
                    "score": trade_opportunity.get("confluence_score", 0),
                    "count": trade_opportunity.get("confluence_count", 0),
                    "rating": trade_opportunity.get("rating", "WEAK"),
                    "factors": trade_opportunity.get("zone", {}).get("factors", [])
                }
            }
            
            llm_eval = self.llm_agent.evaluate_trade_setup(trade_opportunity_data)
            llm_eval["confluence_count"] = trade_opportunity.get("confluence_count", 0)
            llm_eval["zone_confluence_score"] = trade_opportunity.get("confluence_score", 0)
            
            if llm_eval.get("trade_approved") and \
               llm_eval.get("probability_estimate", 0) >= self.config.MIN_PROBABILITY_THRESHOLD:
                log.info(f"✅ Trade approved:")
                log.info(f"   Probability: {llm_eval['probability_estimate']}%")
                log.info(f"   Zone Confluence: {trade_opportunity.get('confluence_score', 0):.0f}")
                log.info(f"   Confluence Factors: {trade_opportunity.get('confluence_count', 0)}")
                
                result = await self._execute_trade(trade_setup, llm_eval)
                
                # ===== RECORD TRADE IF SUCCESSFUL =====
                if result.get("success"):
                    self._record_zone_trade(zone_mid)
                    self._increment_daily_trades()
                
                return {
                    "trade_setup": trade_setup,
                    "llm_evaluation": llm_eval,
                    "zone_confluence": trade_opportunity.get("confluence_score", 0),
                    "execution_result": result,
                    "timestamp": datetime.now()
                }

            log.info(f"❌ Trade rejected: {llm_eval.get('probability_estimate', 0)}%")
            return None
            
        except Exception as e:
            log.error(f"❌ Trade identification error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None
    
    def get_zone_quality_summary(self) -> Dict:
        """Get summary of current zone quality."""
        try:
            if not self.analysis_cache or "zones" not in self.analysis_cache:
                return {"status": "no_data"}

            zones = self.analysis_cache["zones"]
            strong_demand = [z for z in zones.get("demand_zones", []) if z.get("rating") == "STRONG"]
            strong_supply = [z for z in zones.get("supply_zones", []) if z.get("rating") == "STRONG"]
            moderate_demand = [z for z in zones.get("demand_zones", []) if z.get("rating") == "MODERATE"]
            moderate_supply = [z for z in zones.get("supply_zones", []) if z.get("rating") == "MODERATE"]

            return {
                "status": "active",
                "total_demand_zones": len(zones.get("demand_zones", [])),
                "total_supply_zones": len(zones.get("supply_zones", [])),
                "strong_demand_zones": len(strong_demand),
                "strong_supply_zones": len(strong_supply),
                "moderate_demand_zones": len(moderate_demand),
                "moderate_supply_zones": len(moderate_supply),
                "top_demand": strong_demand[0] if strong_demand else None,
                "top_supply": strong_supply[0] if strong_supply else None,
                "poc": zones.get("poc"),
                "vah": zones.get("vah"),
                "val": zones.get("val"),
                "current_price": zones.get("current_price"),
                "last_updated": self.analysis_cache.get("timestamp")
            }
        except Exception as e:
            log.error(f"Zone quality summary error: {e}")
            return {"status": "error", "error": str(e)}

    def _check_zone_proximity(
        self, 
        current_price: float, 
        zones: Dict,
        min_confluence: int = 80,
        proximity_threshold: float = 1.0
    ) -> Optional[Dict]:
        """Check if price is within proximity of any zone."""
        try:
            if not current_price or current_price <= 0:
                log.warning(f"⚠️ Invalid current price: {current_price}")
                return None
            
            if not zones or (not zones.get("demand_zones") and not zones.get("supply_zones")):
                log.warning(f"⚠️ No zones available")
                return None
            
            # Check demand zones
            for zone in zones.get("demand_zones", []):
                if zone.get("confidence", 0) < min_confluence:
                    continue
                
                rating = zone.get("rating", "UNKNOWN")
                zone_top = zone.get("zone_top", 0)
                zone_bottom = zone.get("zone_bottom", 0)
                
                if not zone_top or not zone_bottom:
                    continue
                
                distance = abs(current_price - zone_top)
                distance_pct = (distance / current_price) * 100
                
                if distance_pct <= proximity_threshold:
                    log.info(f"✅ Price NEAR DEMAND zone: {zone_top:.2f}")
                    log.info(f"   Confluence: {zone.get('confidence', 0):.0f} ({rating})")
                    log.info(f"   Distance: {distance_pct:.2f}%")
                    
                    return {
                        "direction": "CALL",
                        "zone": zone,
                        "confluence_score": zone.get("confidence", 0),
                        "confluence_count": zone.get("confluence_count", 0),
                        "rating": rating
                    }
            
            # Check supply zones
            for zone in zones.get("supply_zones", []):
                if zone.get("confidence", 0) < min_confluence:
                    continue
                
                rating = zone.get("rating", "UNKNOWN")
                zone_top = zone.get("zone_top", 0)
                zone_bottom = zone.get("zone_bottom", 0)
                
                if not zone_top or not zone_bottom:
                    continue
                
                distance = abs(current_price - zone_bottom)
                distance_pct = (distance / current_price) * 100
                
                if distance_pct <= proximity_threshold:
                    log.info(f"✅ Price NEAR SUPPLY zone: {zone_bottom:.2f}")
                    log.info(f"   Confluence: {zone.get('confidence', 0):.0f} ({rating})")
                    log.info(f"   Distance: {distance_pct:.2f}%")
                    
                    return {
                        "direction": "PUT",
                        "zone": zone,
                        "confluence_score": zone.get("confidence", 0),
                        "confluence_count": zone.get("confluence_count", 0),
                        "rating": rating
                    }
            
            log.info(f"ℹ️ No trade opportunity - current price: {current_price:.2f}")
            
            demand_zones = zones.get("demand_zones", [])
            supply_zones = zones.get("supply_zones", [])
            
            if demand_zones:
                closest_demand = min(demand_zones, key=lambda z: abs(current_price - z.get("zone_top", 0)))
                zone_top = closest_demand.get("zone_top")
                if zone_top:
                    distance_pct = abs(current_price - zone_top) / current_price * 100
                    log.info(f"   Closest DEMAND: {zone_top:.2f} ({distance_pct:.2f}% away, "
                            f"Conf: {closest_demand.get('confidence', 0):.0f}, Rating: {closest_demand.get('rating', 'N/A')})")
            
            if supply_zones:
                closest_supply = min(supply_zones, key=lambda z: abs(current_price - z.get("zone_bottom", 0)))
                zone_bottom = closest_supply.get("zone_bottom")
                if zone_bottom:
                    distance_pct = abs(current_price - zone_bottom) / current_price * 100
                    log.info(f"   Closest SUPPLY: {zone_bottom:.2f} ({distance_pct:.2f}% away, "
                            f"Conf: {closest_supply.get('confidence', 0):.0f}, Rating: {closest_supply.get('rating', 'N/A')})")
            
            return None
            
        except Exception as e:
            log.error(f"Zone proximity check error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None

    def _determine_trend(self, df: pd.DataFrame) -> str:
        try:
            ema20 = df["close"].ewm(span=20).mean()
            ema50 = df["close"].ewm(span=50).mean()
            if ema20.iloc[-1] > ema50.iloc[-1]:
                return "Bullish"
            elif ema20.iloc[-1] < ema50.iloc[-1]:
                return "Bearish"
            return "Neutral"
        except Exception:
            return "Neutral"

    async def _execute_trade(self, setup: Dict, evaluation: Dict) -> Dict:
        """Execute trade with fresh option price and security ID lookup."""
        try:
            from src.utils.security_master import security_master
            
            if setup.get("needs_live_price"):
                log.info(f"🔍 Fetching live option chain for strike {setup['strike']}...")
                expiry = setup.get("expiry") or get_nearest_expiry(self.config.get_active_instrument())
                option_chain = self.data_agent.fetch_option_chain(
                    self.config.INSTRUMENT_INDEX_SECURITY_ID,
                    self.config.INSTRUMENT_INDEX_EXCHANGE,
                    expiry
                )
                
                if not option_chain or option_chain.get("status") != "success":
                    log.error("❌ Failed to fetch fresh option chain")
                    return {"success": False, "error": "Could not fetch live option prices"}
                
                strike = setup["selected_strike"]
                option_type = "CE" if setup["option_type"] == "CALL" else "PE"
                
                strike_data = None
                for chain_strike in option_chain.get("data", []):
                    if chain_strike.get("strike_price") == strike:
                        if option_type == "CE":
                            strike_data = chain_strike.get("call_options", {})
                        else:
                            strike_data = chain_strike.get("put_options", {})
                        break
                
                if not strike_data:
                    log.error(f"❌ Strike {strike} not found")
                    return {"success": False, "error": "Strike not found"}
                
                live_premium = strike_data.get("LTP") or strike_data.get("ltp")
                
                if not live_premium or live_premium == 0:
                    log.warning(f"⚠️ No live price, using estimate")
                    live_premium = setup["entry_premium"]
                else:
                    log.info(f"📊 Live premium: ₹{live_premium}")
                
                setup["entry_premium"] = live_premium
                setup["stop_loss_premium"] = live_premium * 0.95
                risk_per_lot = live_premium - setup["stop_loss_premium"]
                reward_per_lot = risk_per_lot * self.config.RISK_REWARD_RATIO
                setup["target_premium"] = live_premium + reward_per_lot
            
            expiry = setup.get("expiry") or get_nearest_expiry(self.config.get_active_instrument())
            instrument = self.config.get_active_instrument()
            symbol = instrument["symbol"]
            
            security_id = security_master.get_option_security_id(
                symbol=symbol,
                strike=setup["selected_strike"],
                option_type=setup["option_type"],
                expiry=expiry
            )
            
            if not security_id:
                log.error(f"❌ Could not find security ID")
                return {"success": False, "error": "Option security ID not found"}
            
            log.info(f"✅ Found option security ID: {security_id}")
            
            setup["security_id"] = security_id
            setup["exchange_segment"] = "NSE_FNO"
            
            record = create_trade_record(setup, evaluation)
            
            if self.config.USE_SANDBOX:
                log.info("📝 Paper trade recorded")
                record["status"] = "PAPER"
                record["security_id"] = security_id
                self.active_trades.append(record)
                return {"success": True, "mode": "paper", "security_id": security_id}
            
            log.info(f"📤 Placing LIVE order")
            
            order_params = {
                "security_id": str(security_id),
                "exchange_segment": "NSE_FNO",
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "product_type": "INTRA",
                "quantity": self.config.ORDER_QUANTITY * instrument["lot_size"],
                "entry_price": setup["entry_premium"],
                "stop_loss": setup["stop_loss_premium"],
                "target_price": setup["target_premium"],
                "use_super_order": self.config.USE_SUPER_ORDER,
                "correlation_id": f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            result = self.execution_agent.place_bracket_or_super_order(order_params)
            
            if result["success"]:
                record["order_ids"] = result
                record["status"] = "ACTIVE"
                record["security_id"] = security_id
                self.active_trades.append(record)
                log.info(f"✅ Order placed: {result.get('order_id')}")
            else:
                log.error(f"❌ Order failed: {result}")
            
            return result
            
        except Exception as e:
            log.error(f"❌ Trade execution error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    def get_active_trades(self) -> list:
        return self.active_trades

    async def run_continuous_monitoring(self):
        """Run continuous monitoring with configurable intervals."""
        log.info("🔄 Starting continuous monitoring...")
        log.info(f"   Zone Analysis: Every {self.config.ZONE_REFRESH_INTERVAL} minutes")
        log.info(f"   Trade Checks: Every {self.config.TRADE_TIMEFRAME} minutes")
        
        last_zone_analysis = datetime.now() - timedelta(minutes=self.config.ZONE_REFRESH_INTERVAL)
        last_trade_check = datetime.now() - timedelta(minutes=self.config.TRADE_TIMEFRAME)
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                zone_elapsed = (current_time - last_zone_analysis).seconds
                trade_elapsed = (current_time - last_trade_check).seconds
                
                zone_interval_seconds = self.config.ZONE_REFRESH_INTERVAL * 60
                if zone_elapsed >= zone_interval_seconds:
                    log.info(f"🔍 Running scheduled zone analysis...")
                    await self.run_zone_identification_cycle()
                    last_zone_analysis = current_time
                
                trade_interval_seconds = self.config.TRADE_TIMEFRAME * 60
                if trade_elapsed >= trade_interval_seconds:
                    log.info(f"🎯 Running scheduled trade identification...")
                    await self.run_trade_identification_cycle()
                    last_trade_check = current_time
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                log.info("⚠️ Continuous monitoring cancelled")
                break
            except Exception as e:
                log.error(f"❌ Error in continuous monitoring: {e}")
                import traceback
                log.error(traceback.format_exc())
                await asyncio.sleep(60)
        
        log.info("✅ Continuous monitoring stopped")

    def shutdown(self):
        log.info("🛑 Shutting down trading system...")
        self.is_running = False
        if hasattr(self, "execution_agent"):
            self.execution_agent.stop_order_updates()
        log.info("✅ System shutdown complete")


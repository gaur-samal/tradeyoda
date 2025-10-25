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
    """Main orchestrator with real-time feeds."""

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
        log.info("🤖 Trading Orchestrator initialized")

    def start(self):
        """Start the trading system."""
        try:
            self.config.validate()
            #self._setup_realtime_feeds()
            self.is_running = True
            log.info("✅ Trading system started")
        except Exception as e:
            log.error(f"❌ Failed to start system: {e}")
            raise

    def _setup_realtime_feeds(self):
        """Initialize live market and order feeds - NOW USING NIFTY FUTURES."""
        
        # Subscribe to Nifty FUTURES for live data
        # v2 format: (exchange_segment, security_id_as_string, subscription_type)
        nifty_instruments = [
            (self.config.NIFTY_FUTURES_EXCHANGE, 
             self.config.NIFTY_FUTURES_SECURITY_ID, 
             MarketFeed.Full)
        ] 
        success = self.data_agent.start_live_feed(nifty_instruments)
        
        if success:
            log.info("✅ Market feed initialized - waiting for data...")
            # Give it time to connect
            import time
            time.sleep(5)
            
            # Check if data is flowing
            if self.data_agent.latest_data:
                log.info(f"✅ Market data flowing for: {list(self.data_agent.latest_data.keys())}")
                # Show sample data
                for sec_id, data in self.data_agent.latest_data.items():
                    log.info(f"📊 Sample data [{sec_id}]: {data}")
            else:
                log.warning("⚠️ No market data received yet")
                log.warning("⚠️ Possible reasons:")
                log.warning("   1. Market is closed (data only flows 9:15 AM - 3:30 PM)")
                log.warning("   2. No Data API subscription")
                log.warning("   3. Invalid credentials")
        else:
            log.error("❌ Failed to start market feed")

        # Start order updates
        self.execution_agent.start_order_updates(
            on_update_callback=self._handle_order_update
        )
        log.info("✅ Real‑time feeds setup complete")


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
            trade["pnl"] = 0.0  # placeholder
            trade["status"] = "CLOSED"
            log.info(f"Trade closed → P&L = {trade['pnl']}")
        except Exception as e:
            log.error(f"P&L calculation error: {e}")

    async def run_zone_identification_cycle(self) -> Optional[Dict]:
        """Enhanced 15-minute zone identification with LLM validation."""
        log.info("🔍 Zone identification cycle starting (LLM-Enhanced)...")
        
        try:
            # [Keep your existing data fetching code exactly as is]
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
                    #return None
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
            
            # STEP 1: Rule-based zone identification (existing logic)
            log.info("📊 Running rule-based zone identification...")
            vp_data = self.tech_agent.calculate_volume_profile(
                df_15min, self.config.VP_VALUE_AREA
            )
            order_blocks = self.tech_agent.identify_order_blocks(
                df_15min, self.config.OB_LOOKBACK
            )
            fvgs = self.tech_agent.identify_fair_value_gaps(df_15min)
            rule_based_zones = self.tech_agent.identify_supply_demand_zones(
                df_15min, vp_data, order_blocks, fvgs
            )

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

            # STEP 2: LLM Enhancement (NEW - validates and ranks zones)
            log.info("🤖 Running LLM zone validation and enhancement...")
            llm_enhanced_zones = self.llm_agent.validate_and_enhance_zones(
                rule_based_zones,
                df_15min,
                tech_indicators,
                market_context
            )
            
            # STEP 3: Use LLM-enhanced zones (but keep rule-based as fallback)
            final_zones = {
                "demand_zones": llm_enhanced_zones.get('demand_zones', rule_based_zones.get('demand_zones', [])[:3]),
                "supply_zones": llm_enhanced_zones.get('supply_zones', rule_based_zones.get('supply_zones', [])[:3]),
                "poc": rule_based_zones.get('poc'),
                "vah": rule_based_zones.get('vah'),
                "val": rule_based_zones.get('val'),
                "current_price": current_price
            }
            
            # STEP 4: Existing LLM analysis (keep for trade evaluation)
            llm_analysis = self.llm_agent.analyze_zones(final_zones, market_context)
            
            # Cache results
            self.analysis_cache = {
                "zones": final_zones,
                "llm_analysis": llm_analysis,
                "llm_enhanced_zones": llm_enhanced_zones,  # NEW
                "vp_data": vp_data,
                "market_context": market_context,
                "technical_indicators": tech_indicators,
                "timestamp": datetime.now(),
                "current_price": current_price,
            }

            log.info(f"✅ Zone Identification Complete (LLM-Enhanced):")
            log.info(f"   Demand Zones: {len(final_zones['demand_zones'])}")
            log.info(f"   Supply Zones: {len(final_zones['supply_zones'])}")
            log.info(f"   Market Bias: {llm_enhanced_zones.get('primary_bias', 'Unknown')}")
            log.info(f"   RSI: {tech_indicators.get('latest_rsi', 'N/A')} ({tech_indicators.get('rsi_signal', 'N/A')})")
            log.info(f"   BB Position: {tech_indicators.get('bb_position', 'N/A')}")
            
            return self.analysis_cache

        except Exception as e:
            log.error(f"❌ Zone identification error: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None


    async def run_trade_identification_cycle(self) -> Optional[Dict]:
        """3‑minute cycle for trade identification."""
        log.info("🎯 Trade identification cycle starting …")
        
        if self.config.NO_TRADES_ON_EXPIRY:
            today = datetime.now().date()
            if today.weekday() == 1:  # Tuesday
                log.info("🚫 Expiry day (Tuesday) – no trades executed today")
                return None

        try:
            if not validate_market_hours():
                log.info("⏰ Outside market hours")
                #return None

            if not self.analysis_cache or \
               (datetime.now() - self.analysis_cache.get("timestamp", datetime.now())).seconds > 900:
                log.warning("⚠️ Zone analysis too old → refreshing")
                await self.run_zone_identification_cycle()

            # Fetch live quote from FUTURES
            quotes = self.data_agent.fetch_market_quotes(
                securities=[self.config.NIFTY_FUTURES_SECURITY_ID],
                exchange_segment=self.config.NIFTY_FUTURES_EXCHANGE
            )
            print(quotes)
            live_quote = quotes.get(str(self.config.NIFTY_FUTURES_SECURITY_ID), {})
            current_price = live_quote.get("LTP")
            # Get live price from MarketFeed (real-time cached data)
            #futures_id = str(self.config.NIFTY_FUTURES_SECURITY_ID)
            #live_data = self.data_agent.latest_data.get(futures_id, {})
            #if not live_data:
            #    log.warning("⚠️ No live MarketFeed data available - waiting for data")
            #    return None
        
            #current_price = live_data.get('LTP')
            #if not current_price:
            #    log.warning("⚠️ No live price")
            #    return None

            zones = self.analysis_cache.get("zones", {})
            trade_opportunity = self._check_zone_proximity(current_price, zones)
            if not trade_opportunity:
                log.info("ℹ️ No trade opportunity — price away from zones")
                return None

            # Fetch option chain using INDEX as underlying (correct for options)
            expiry = get_nearest_expiry()
            #print(f"expiry : {expiry}")
            option_chain = self.data_agent.fetch_option_chain(
                self.config.NIFTY_INDEX_SECURITY_ID,  # Use index for options
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

            # Enhanced trade evaluation with all indicators
            llm_eval = self.llm_agent.evaluate_trade_setup({
                **trade_setup,
                "zones": zones,
                "option_analysis": option_analysis,
                "technical_indicators": self.analysis_cache.get("technical_indicators", {}),
                "market_context": self.analysis_cache.get("market_context", {})
            })

            if llm_eval.get("trade_approved") and \
               llm_eval.get("probability_estimate", 0) >= self.config.MIN_PROBABILITY_THRESHOLD:
                log.info(f"✅ Trade approved at {llm_eval['probability_estimate']}% "
                        f"(Confluence: {llm_eval.get('confluence_count', 0)})")
                result = await self._execute_trade(trade_setup, llm_eval)
                return {
                    "trade_setup": trade_setup,
                    "llm_evaluation": llm_eval,
                    "execution_result": result,
                    "timestamp": datetime.now()
                }

            log.info(f"Trade rejected ({llm_eval.get('probability_estimate', 0)}% - "
                    f"Confluence: {llm_eval.get('confluence_count', 0)})")
            return None

        except Exception as e:
            log.error(f"❌ Trade identification error: {e}")
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

    def _check_zone_proximity(self, current_price: float, zones: Dict) -> Optional[Dict]:
        for zone in zones.get("demand_zones", []):
            if zone["confidence"] >= 80:
                if abs(current_price - zone["zone_top"]) / current_price <= 0.005:
                    return {"direction": "CALL", "zone": zone}
        for zone in zones.get("supply_zones", []):
            if zone["confidence"] >= 80:
                if abs(current_price - zone["zone_bottom"]) / current_price <= 0.005:
                    return {"direction": "PUT", "zone": zone}
        return None

    async def _execute_trade(self, setup: Dict, evaluation: Dict) -> Dict:
        """Execute trade with configurable quantity and order type."""
        try:
            record = create_trade_record(setup, evaluation)
            if self.config.USE_SANDBOX:
                log.info("📝 Paper trade recorded (sandbox mode)")
                record["status"] = "PAPER"
                self.active_trades.append(record)
                return {"success": True, "mode": "paper"}

            order_params = {
                "security_id": setup.get("security_id", "13"),
                "exchange_segment": setup.get("exchange_segment", "NSE_FNO"),
                "transaction_type": setup.get("transaction_type", "BUY"),
                "order_type": setup.get("order_type", "LIMIT"),
                "product_type": setup.get("product_type", "INTRADAY"),
                "quantity": getattr(self.config, "ORDER_QUANTITY", 1),
                "entry_price": setup["entry_price"],
                "stop_loss": setup["stop_loss"],
                "target_price": setup["target_price"],
                "trailing_jump": setup.get("trailing_jump", 0),
                "use_super_order": getattr(self.config, "USE_SUPER_ORDER", True),
                "correlation_id": f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }

            log.info(f"📤 Executing trade: {order_params['transaction_type']} "
                    f"{order_params['quantity']} @ {order_params['entry_price']}")
            
            result = self.execution_agent.place_bracket_or_super_order(order_params)
            
            if result["success"]:
                record["order_ids"] = result
                record["status"] = "ACTIVE"
                record["order_type"] = "SUPER_ORDER" if order_params["use_super_order"] else "BRACKET_ORDER"
                self.active_trades.append(record)
                log.info(f"✅ Trade executed successfully: Order ID {result.get('order_id')}")
            else:
                log.error(f"❌ Trade execution failed: {result}")
            
            return result
            
        except Exception as e:
            log.error(f"❌ Trade execution error: {e}")
            return {"success": False, "error": str(e)}

    def get_active_trades(self) -> list:
        return self.active_trades
    async def run_continuous_monitoring(self):
        """
        Run continuous monitoring with configurable intervals.
        
        Uses config parameters:
        - ZONE_REFRESH_INTERVAL: How often to recalculate zones (minutes)
        - TRADE_TIMEFRAME: How often to check for trades (minutes)
        """
        log.info("🔄 Starting continuous monitoring...")
        log.info(f"   Zone Analysis: Every {self.config.ZONE_REFRESH_INTERVAL} minutes (using {self.config.ZONE_TIMEFRAME}-min candles)")
        log.info(f"   Trade Checks: Every {self.config.TRADE_TIMEFRAME} minutes")
        
        # Initialize with past times to trigger immediate execution
        last_zone_analysis = datetime.now() - timedelta(minutes=self.config.ZONE_REFRESH_INTERVAL)
        last_trade_check = datetime.now() - timedelta(minutes=self.config.TRADE_TIMEFRAME)
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Calculate time since last runs
                zone_elapsed = (current_time - last_zone_analysis).seconds
                trade_elapsed = (current_time - last_trade_check).seconds
                
                # Run zone analysis based on ZONE_REFRESH_INTERVAL
                zone_interval_seconds = self.config.ZONE_REFRESH_INTERVAL * 60
                if zone_elapsed >= zone_interval_seconds:
                    log.info(f"🔍 Running scheduled zone analysis ({int(zone_elapsed/60)} min elapsed)...")
                    await self.run_zone_identification_cycle()
                    last_zone_analysis = current_time
                
                # Run trade identification based on TRADE_TIMEFRAME
                trade_interval_seconds = self.config.TRADE_TIMEFRAME * 60
                if trade_elapsed >= trade_interval_seconds:
                    log.info(f"🎯 Running scheduled trade identification ({int(trade_elapsed/60)} min elapsed)...")
                    await self.run_trade_identification_cycle()
                    last_trade_check = current_time
                
                # Sleep for 30 seconds before next iteration (efficient checking)
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                log.info("⚠️ Continuous monitoring cancelled")
                break
            except Exception as e:
                log.error(f"❌ Error in continuous monitoring: {e}")
                import traceback
                log.error(traceback.format_exc())
                await asyncio.sleep(60)  # Wait longer on error
        
        log.info("✅ Continuous monitoring stopped")

    def shutdown(self):
        log.info("🛑 Shutting down trading system …")
        self.is_running = False
        #if hasattr(self, "data_agent"):
        #    self.data_agent.stop_live_feed()
        if hasattr(self, "execution_agent"):
            self.execution_agent.stop_order_updates()
        log.info("✅ System shutdown complete")


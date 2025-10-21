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

        log.info("🤖 Trading Orchestrator initialized")

    def start(self):
        """Start the trading system."""
        try:
            self.config.validate()
            self._setup_realtime_feeds()
            self.is_running = True
            log.info("✅ Trading system started")
        except Exception as e:
            log.error(f"❌ Failed to start system: {e}")
            raise

    def _setup_realtime_feeds(self):
        """Initialize live market and order feeds."""
        nifty_instruments = [
            ("IDX_I", self.config.NIFTY_SECURITY_ID, MarketFeed.Full)
        ]
        self.data_agent.start_live_feed(nifty_instruments)

        self.execution_agent.start_order_updates(
            on_update_callback=self._handle_order_update
        )
        log.info("✅ Real‑time feeds initialized")

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
        """15‑minute cycle for zone identification."""
        log.info("🔍 Zone identification cycle starting …")
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            if self.config.USE_BACKTEST_MODE:
                log.info("🧪 Backtest mode active ‑ loading historical data")
                from_date = ensure_str_date(self.config.BACKTEST_FROM)
                to_date = ensure_str_date(self.config.BACKTEST_TO)
                df_15min = self.data_agent.fetch_historical_data(
                    security_id=self.config.NIFTY_SECURITY_ID,
                    exchange_segment=self.config.NIFTY_EXCHANGE,
                    instrument_type="INDEX",
                    timeframe=str(self.config.ZONE_TIMEFRAME),
                    from_date=from_date,
                    to_date=to_date,
                )
            else:
                if not validate_market_hours():
                    log.info("⏰ Outside market hours")
                    return None
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                df_15min = self.data_agent.fetch_historical_data(
                    security_id=self.config.NIFTY_SECURITY_ID,
                    exchange_segment=self.config.NIFTY_EXCHANGE,
                    instrument_type="INDEX",
                    timeframe=str(self.config.ZONE_TIMEFRAME),
                    from_date=start_date.strftime("%Y-%m-%d"),
                    to_date=end_date.strftime("%Y-%m-%d"),
                )
            
            if df_15min.empty:
                log.warning("⚠️ No 15‑min data available")
                return None

            # Fetch live quote using SDK's quote_data method
            quotes = self.data_agent.fetch_market_quotes(
                securities=[self.config.NIFTY_SECURITY_ID],
                exchange_segment=self.config.NIFTY_EXCHANGE
            )
            live_quote = quotes.get(str(self.config.NIFTY_SECURITY_ID), {})
            current_price = live_quote.get("LTP", df_15min["close"].iloc[-1])

            vp_data = self.tech_agent.calculate_volume_profile(
                df_15min, self.config.VP_VALUE_AREA
            )
            order_blocks = self.tech_agent.identify_order_blocks(
                df_15min, self.config.OB_LOOKBACK
            )
            fvgs = self.tech_agent.identify_fair_value_gaps(df_15min)
            zones = self.tech_agent.identify_supply_demand_zones(
                df_15min, vp_data, order_blocks, fvgs
            )

            market_context = {
                "trend": self._determine_trend(df_15min),
                "volatility": float(df_15min["close"].pct_change().std()),
                "current_price": current_price,
            }

            llm_analysis = self.llm_agent.analyze_zones(zones, market_context)
            self.analysis_cache = {
                "zones": zones,
                "llm_analysis": llm_analysis,
                "vp_data": vp_data,
                "market_context": market_context,
                "timestamp": datetime.now(),
                "current_price": current_price,
            }

            log.info(
                f"✅ Zones: {len(zones['demand_zones'])} demand / {len(zones['supply_zones'])} supply"
            )
            return self.analysis_cache

        except Exception as e:
            log.error(f"❌ Zone identification error: {e}")
            return None

    async def run_trade_identification_cycle(self) -> Optional[Dict]:
        """3‑minute cycle for trade identification."""
        log.info("🎯 Trade identification cycle starting …")
        
        if self.config.NO_TRADES_ON_EXPIRY:
            today = datetime.now().date()
            if today.weekday() == 1:
                log.info("🚫 Expiry day (Tuesday) – no trades executed today")
                return None

        try:
            if not validate_market_hours():
                log.info("⏰ Outside market hours")
                return None

            if not self.analysis_cache or \
               (datetime.now() - self.analysis_cache.get("timestamp", datetime.now())).seconds > 900:
                log.warning("⚠️ Zone analysis too old → refreshing")
                await self.run_zone_identification_cycle()

            # Fetch live quote using SDK's quote_data method
            quotes = self.data_agent.fetch_market_quotes(
                securities=[self.config.NIFTY_SECURITY_ID],
                exchange_segment=self.config.NIFTY_EXCHANGE
            )
            print(quotes)
            live_quote = quotes.get(str(self.config.NIFTY_SECURITY_ID), {})
            current_price = live_quote.get("LTP")
            
            if not current_price:
                log.warning("⚠️ No live price")
                return None

            zones = self.analysis_cache.get("zones", {})
            trade_opportunity = self._check_zone_proximity(current_price, zones)
            if not trade_opportunity:
                log.info("ℹ️ No trade opportunity — price away from zones")
                return None

            expiry = get_nearest_expiry()
            option_chain = self.data_agent.fetch_option_chain(
                self.config.NIFTY_SECURITY_ID,
                self.config.NIFTY_EXCHANGE,
                expiry
            )
            option_analysis = self.options_agent.analyze_option_chain(
                option_chain, current_price, zones
            )
            trade_setup = self.options_agent.select_best_strike(
                zones, option_analysis, trade_opportunity["direction"]
            )
            if not trade_setup:
                log.info("ℹ️ No valid trade setup")
                return None

            llm_eval = self.llm_agent.evaluate_trade_setup({
                **trade_setup,
                "zones": zones,
                "option_analysis": option_analysis
            })

            if llm_eval.get("trade_approved") and \
               llm_eval.get("probability_estimate", 0) >= self.config.MIN_PROBABILITY_THRESHOLD:
                log.info(f"✅ Trade approved at {llm_eval['probability_estimate']} %")
                result = await self._execute_trade(trade_setup, llm_eval)
                return {
                    "trade_setup": trade_setup,
                    "llm_evaluation": llm_eval,
                    "execution_result": result,
                    "timestamp": datetime.now()
                }

            log.info(f"Trade rejected ({llm_eval.get('probability_estimate', 0)}%)")
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

            # Build order parameters from config and setup
            order_params = {
                "security_id": setup.get("security_id", "13"),
                "exchange_segment": setup.get("exchange_segment", "NSE_FNO"),
                "transaction_type": setup.get("transaction_type", "BUY"),
                "order_type": setup.get("order_type", "LIMIT"),
                "product_type": setup.get("product_type", "INTRADAY"),
                "quantity": getattr(self.config, "ORDER_QUANTITY", 50),  # From config or default 50
                "entry_price": setup["entry_price"],
                "stop_loss": setup["stop_loss"],
                "target_price": setup["target_price"],
                "trailing_jump": setup.get("trailing_jump", 0),
                "use_super_order": getattr(self.config, "USE_SUPER_ORDER", True),  # From config or default True
                "correlation_id": f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }

            log.info(f"📤 Executing trade: {order_params['transaction_type']} "
                    f"{order_params['quantity']} @ {order_params['entry_price']}")
            
            # Call the unified order placement function
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

    def shutdown(self):
        log.info("🛑 Shutting down trading system …")
        self.is_running = False
        if hasattr(self, "data_agent"):
            self.data_agent.stop_live_feed()
        if hasattr(self, "execution_agent"):
            self.execution_agent.stop_order_updates()
        log.info("✅ System shutdown complete")


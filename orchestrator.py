"""Main trading orchestrator coordinating all agents."""
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Optional
from dhanhq import MarketFeed

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
        
        # Initialize agents
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
            # Validate configuration
            self.config.validate()
            
            # Setup real-time feeds
            self._setup_realtime_feeds()
            
            self.is_running = True
            log.info("✅ Trading system started")
            
        except Exception as e:
            log.error(f"❌ Failed to start system: {str(e)}")
            raise
    
    def _setup_realtime_feeds(self):
        """Initialize real-time market and order feeds."""
        # Setup Nifty 50 live feed
        nifty_instruments = [
            (MarketFeed.NSE, self.config.NIFTY_SECURITY_ID, MarketFeed.Full)
        ]
        
        self.data_agent.start_live_feed(nifty_instruments)
        
        # Setup order updates
        self.execution_agent.start_order_updates(
            on_update_callback=self._handle_order_update
        )
        
        log.info("✅ Real-time feeds initialized")
    
    def _handle_order_update(self, order_data: dict):
        """Handle real-time order updates."""
        try:
            data = order_data.get("Data", {})
            order_id = data.get("orderId")
            order_status = data.get("orderStatus")
            
            log.info(f"📢 Order Update: {order_id} -> {order_status}")
            
            # Update active trades
            for trade in self.active_trades:
                if trade.get('order_ids', {}).get('main_order_id') == order_id:
                    trade['current_status'] = order_status
                    trade['last_update'] = datetime.now()
                    
                    if order_status == "TRADED":
                        self._calculate_trade_pnl(trade, data)
                    
        except Exception as e:
            log.error(f"Order update handler error: {str(e)}")
    
    def _calculate_trade_pnl(self, trade: dict, order_data: dict):
        """Calculate P&L for completed trade."""
        try:
            # Implement P&L calculation logic
            trade['pnl'] = 0.0  # Placeholder
            trade['status'] = 'CLOSED'
            log.info(f"Trade closed: P&L={trade['pnl']}")
            
        except Exception as e:
            log.error(f"P&L calculation error: {str(e)}")
    
    async def run_zone_identification_cycle(self) -> Optional[Dict]:
        """15-min cycle for zone identification."""
        log.info("🔍 Zone identification cycle starting...")
        
        try:
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            df_15min = self.data_agent.fetch_historical_data(
                security_id=self.config.NIFTY_SECURITY_ID,
                exchange_segment=self.config.NIFTY_EXCHANGE,
                instrument_type='INDEX',
                timeframe=str(self.config.ZONE_TIMEFRAME),
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            if df_15min.empty:
                log.warning("⚠️ No 15-min data available")
                return None
            
            # Get live quote
            live_quote = self.data_agent.get_live_quote(self.config.NIFTY_SECURITY_ID)
            current_price = live_quote.get('LTP', df_15min['close'].iloc[-1])
            
            # Technical analysis
            vp_data = self.tech_agent.calculate_volume_profile(
                df_15min,
                self.config.VP_VALUE_AREA
            )
            
            order_blocks = self.tech_agent.identify_order_blocks(
                df_15min,
                self.config.OB_LOOKBACK
            )
            
            fvgs = self.tech_agent.identify_fair_value_gaps(df_15min)
            
            zones = self.tech_agent.identify_supply_demand_zones(
                df_15min, vp_data, order_blocks, fvgs
            )
            
            # Market context
            market_context = {
                'trend': self._determine_trend(df_15min),
                'volatility': float(df_15min['close'].pct_change().std()),
                'current_price': current_price
            }
            
            # LLM analysis
            llm_analysis = self.llm_agent.analyze_zones(zones, market_context)
            
            # Cache results
            self.analysis_cache = {
                'zones': zones,
                'llm_analysis': llm_analysis,
                'vp_data': vp_data,
                'market_context': market_context,
                'timestamp': datetime.now(),
                'current_price': current_price
            }
            
            log.info(
                f"✅ Zones identified: {len(zones['demand_zones'])} demand, "
                f"{len(zones['supply_zones'])} supply"
            )
            
            return self.analysis_cache
            
        except Exception as e:
            log.error(f"❌ Zone identification error: {str(e)}")
            return None
    
    async def run_trade_identification_cycle(self) -> Optional[Dict]:
        """3-min cycle for trade identification."""
        log.info("🎯 Trade identification cycle starting...")
        
        try:
            # Check market hours
            if not validate_market_hours():
                log.info("⏰ Outside market hours")
                return None
            
            # Check zone analysis age
            if not self.analysis_cache or \
               (datetime.now() - self.analysis_cache.get('timestamp', datetime.now())).seconds > 900:
                log.warning("⚠️ Zone analysis too old, running new cycle...")
                await self.run_zone_identification_cycle()
            
            # Get live data
            live_quote = self.data_agent.get_live_quote(self.config.NIFTY_SECURITY_ID)
            current_price = live_quote.get('LTP')
            
            if not current_price:
                log.warning("⚠️ No live price available")
                return None
            
            zones = self.analysis_cache.get('zones', {})
            
            # Check zone proximity
            trade_opportunity = self._check_zone_proximity(current_price, zones)
            
            if not trade_opportunity:
                log.info("ℹ️ No trade opportunity - price not near zones")
                return None
            
            # Get option chain
            expiry = get_nearest_expiry()
            option_chain = self.data_agent.fetch_option_chain(
                under_security_id=int(self.config.NIFTY_SECURITY_ID),
                under_exchange_segment=self.config.NIFTY_EXCHANGE,
                expiry=expiry
            )
            
            # Options analysis
            option_analysis = self.options_agent.analyze_option_chain(
                option_chain, current_price, zones
            )
            
            # Strike selection
            trade_setup = self.options_agent.select_best_strike(
                zones, option_analysis, trade_opportunity['direction']
            )
            
            if not trade_setup:
                log.info("ℹ️ No valid trade setup")
                return None
            
            # LLM evaluation
            llm_evaluation = self.llm_agent.evaluate_trade_setup({
                **trade_setup,
                'zones': zones,
                'option_analysis': option_analysis
            })
            
            # Check approval
            if llm_evaluation.get('trade_approved') and \
               llm_evaluation.get('probability_estimate', 0) >= self.config.MIN_PROBABILITY_THRESHOLD:
                
                log.info(
                    f"✅ Trade approved! Probability: {llm_evaluation['probability_estimate']}%"
                )
                
                # Execute trade
                execution_result = await self._execute_trade(trade_setup, llm_evaluation)
                
                return {
                    'trade_setup': trade_setup,
                    'llm_evaluation': llm_evaluation,
                    'execution_result': execution_result,
                    'timestamp': datetime.now()
                }
            
            log.info(
                f"❌ Trade rejected. Probability: {llm_evaluation.get('probability_estimate', 0)}%"
            )
            return None
            
        except Exception as e:
            log.error(f"❌ Trade identification error: {str(e)}")
            return None
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine market trend."""
        try:
            ema_20 = df['close'].ewm(span=20).mean()
            ema_50 = df['close'].ewm(span=50).mean()
            
            if ema_20.iloc[-1] > ema_50.iloc[-1]:
                return "Bullish"
            elif ema_20.iloc[-1] < ema_50.iloc[-1]:
                return "Bearish"
            return "Neutral"
        except:
            return "Neutral"
    
    def _check_zone_proximity(self, current_price: float, zones: Dict) -> Optional[Dict]:
        """Check if price is near a tradeable zone."""
        # Check demand zones (for long)
        for zone in zones.get('demand_zones', []):
            if zone['confidence'] >= 80:
                distance = abs(current_price - zone['zone_top']) / current_price
                if distance <= 0.005:  # Within 0.5%
                    return {
                        'direction': 'CALL',
                        'zone': zone,
                        'distance': distance
                    }
        
        # Check supply zones (for short)
        for zone in zones.get('supply_zones', []):
            if zone['confidence'] >= 80:
                distance = abs(current_price - zone['zone_bottom']) / current_price
                if distance <= 0.005:
                    return {
                        'direction': 'PUT',
                        'zone': zone,
                        'distance': distance
                    }
        
        return None
    
    async def _execute_trade(self, trade_setup: Dict, evaluation: Dict) -> Dict:
        """Execute approved trade."""
        try:
            # Create trade record
            trade_record = create_trade_record(trade_setup, evaluation)
            
            # For paper trading - just log
            if self.config.USE_SANDBOX:
                log.info("📝 Paper trade recorded (sandbox mode)")
                trade_record['status'] = 'PAPER'
                self.active_trades.append(trade_record)
                return {'success': True, 'mode': 'paper'}
            
            # Real execution
            order_params = {
                'security_id': trade_setup.get('security_id', '13'),
                'quantity': 50,  # Adjust based on margin
                'entry_price': trade_setup['entry_price'],
                'stop_loss': trade_setup['stop_loss'],
                'target_price': trade_setup['target_price']
            }
            
            result = self.execution_agent.place_bracket_order(order_params)
            
            if result['success']:
                trade_record['order_ids'] = result
                trade_record['status'] = 'ACTIVE'
                self.active_trades.append(trade_record)
            
            return result
            
        except Exception as e:
            log.error(f"❌ Trade execution error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_active_trades(self) -> list:
        """Return active trades."""
        return self.active_trades
    
    def shutdown(self):
        """Cleanup and shutdown."""
        log.info("🛑 Shutting down trading system...")
        self.is_running = False
        self.data_agent.stop_live_feed()
        self.execution_agent.stop_order_updates()
        log.info("✅ System shutdown complete")


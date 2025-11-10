"""Data collection agent aligned with Dhan API v2.2."""
import pandas as pd
from datetime import datetime, timedelta
from dhanhq import dhanhq, MarketFeed
import threading
import asyncio
import requests
import queue
import time
from typing import Dict, Optional
from src.utils.logger import log


class DataCollectionAgent:
    """Agent responsible for fetching and streaming Dhan market data."""
    
    def __init__(self, dhan_context):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.market_feed = None
        self.live_data_queue = queue.Queue()
        self.latest_data = {}
        self.is_running = False
        self.subscribed_instruments = []
        
        # ===== ADD CACHING =====
        self._cache = {}
        self._cache_ttl = {
            'positions': 10,      # Cache positions for 10 seconds
            'orders': 5,          # Cache orders for 5 seconds
            'quotes': 3,          # Cache quotes for 3 seconds
            'funds': 30,          # Cache funds for 30 seconds
            'holdings': 60,       # Cache holdings for 60 seconds
        }
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            ttl = self._cache_ttl.get(key.split('_')[0], 5)
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < ttl:
                log.debug(f"📦 Cache HIT for {key} (age: {age:.1f}s)")
                return data
            else:
                log.debug(f"⏰ Cache EXPIRED for {key} (age: {age:.1f}s)")
        
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Set cache data with timestamp."""
        self._cache[key] = (data, datetime.now())
    
    def start_live_feed(self, instruments):
        """Start real-time market feed (WebSocket) v2.2."""
        try:
            if self.is_running:
                log.warning("Market feed already running")
                return True
            
            self.market_feed = MarketFeed(
                self.dhan_context,
                instruments,
                version="v2"
            )
            
            feed_thread = threading.Thread(
                target=self._market_feed_loop,
                name="MarketFeedWorker",
                daemon=True
            )
            feed_thread.start()

            self.is_running = True
            log.info(f"✅ Market feed started successfully")
            return True

        except Exception as e:
            log.error(f"❌ Feed start error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return False

    def _market_feed_loop(self):
        """Background thread for market feed with its own event loop."""
        log.info("🔌 Market feed thread started")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def feed_worker():
            """Async worker that handles the feed."""
            while self.is_running:
                try:
                    await self.market_feed.connect()
                    response = await self.market_feed.get_data()
                    
                    if response:
                        self._process_market_data(response)
                        
                except Exception as e:
                    if self.is_running:
                        log.error(f"❌ Feed error: {e}")
                        await asyncio.sleep(2)
                    else:
                        break
        
        try:
            loop.run_until_complete(feed_worker())
        except Exception as e:
            log.error(f"❌ Market feed thread error: {e}")
            import traceback
            log.error(traceback.format_exc())
        finally:
            loop.close()
            log.info("✅ Market feed thread stopped")

    def _process_market_data(self, data):
        """Process incoming market data."""
        try:
            if not data or not isinstance(data, dict):
                return

            security_id = str(data.get("security_id", ""))

            if security_id:
                data["received_at"] = datetime.now()
                self.latest_data[security_id] = data
                self.live_data_queue.put(data)

                if not hasattr(self, '_log_count'):
                    self._log_count = {}

                count = self._log_count.get(security_id, 0)
                if count < 5:
                    log.info(f"📊 Market data [{security_id}]: Type={data.get('type')}, LTP={data.get('LTP', 'N/A')}")
                    self._log_count[security_id] = count + 1

        except Exception as e:
            log.error(f"Error processing market data: {e}")

    def stop_live_feed(self):
        """Stop market feed."""
        try:
            self.is_running = False
            if hasattr(self, 'market_feed') and self.market_feed:
                self.market_feed.close_connection()
            log.info("✅ Market feed stopped")
        except Exception as e:
            log.error(f"Error stopping market feed: {e}") 
    
    def _on_message(self, instance, message):
        """Handle incoming WebSocket tick messages."""
        if not message or not isinstance(message, dict):
            return
        security_id = str(message.get("security_id", ""))
        if security_id:
            message["received_at"] = datetime.now()
            self.latest_data[security_id] = message
            self.live_data_queue.put(message)
        
    def fetch_historical_data(
        self,
        security_id,
        exchange_segment,
        instrument_type,
        timeframe="15",
        from_date=None,
        to_date=None,
        oi=False
    ):
        """Fetch historical intraday minute data using new v2.2 API."""
        try:
            params = {
                "security_id": security_id,
                "exchange_segment": exchange_segment,
                "instrument_type": instrument_type,
                "from_date": from_date,
                "to_date": to_date,
            }
            result = self.dhan.intraday_minute_data(**params)
            
            if not result or result.get("status") != "success":
                return pd.DataFrame()
            
            df = pd.DataFrame(result["data"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df = df.sort_values("timestamp")
            return df
        
        except Exception as e:
            log.error(f"❌ Historical fetch error: {str(e)}")
            return pd.DataFrame()
    
    def fetch_option_chain(self, security_id, exchange_segment, expiry_date, max_retries=3):
        """Fetch option chain with proper data transformation including Greeks."""
        for attempt in range(max_retries):
            try:
                time.sleep(3)
                
                log.info(f"Fetching option chain (attempt {attempt + 1}/{max_retries})")
                log.info(f"  Security: {security_id}, Exchange: {exchange_segment}, Expiry: {expiry_date}")
                
                chain = self.dhan.option_chain(
                    under_security_id=int(security_id),
                    under_exchange_segment=exchange_segment,
                    expiry=str(expiry_date)
                )
                
                if chain and chain.get("status") == "success":
                    outer_data = chain.get("data", {})
                    inner_data = outer_data.get("data", {})
                    option_chain_data = inner_data.get("oc", {})
                    spot_price = inner_data.get("last_price", 0)
                    
                    if not option_chain_data:
                        log.warning("Empty option chain in response")
                        return pd.DataFrame()
                    
                    rows = []
                    for strike_str, strike_data in option_chain_data.items():
                        strike = float(strike_str)
                        
                        ce_data = strike_data.get("ce", {})
                        pe_data = strike_data.get("pe", {})
                        
                        call_greeks = ce_data.get('greeks', {})
                        put_greeks = pe_data.get('greeks', {})
                        
                        row = {
                            'strike': strike,
                            'call_oi': ce_data.get('oi', 0),
                            'call_volume': ce_data.get('volume', 0),
                            'call_iv': ce_data.get('implied_volatility', 0),
                            'call_ltp': ce_data.get('last_price', 0),
                            'call_oi_change': ce_data.get('oi', 0) - ce_data.get('previous_oi', 0),
                            'call_greeks': call_greeks,
                            'put_oi': pe_data.get('oi', 0),
                            'put_volume': pe_data.get('volume', 0),
                            'put_iv': pe_data.get('implied_volatility', 0),
                            'put_ltp': pe_data.get('last_price', 0),
                            'put_oi_change': pe_data.get('oi', 0) - pe_data.get('previous_oi', 0),
                            'put_greeks': put_greeks,
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    df = df.sort_values('strike')
                    
                    has_call_greeks = df['call_greeks'].apply(lambda x: isinstance(x, dict) and len(x) > 0).sum()
                    has_put_greeks = df['put_greeks'].apply(lambda x: isinstance(x, dict) and len(x) > 0).sum()
                    
                    log.info(f"✅ Processed {len(df)} strikes from option chain")
                    log.info(f"   Spot price: {spot_price}")
                    log.info(f"   Strike range: {df['strike'].min()} to {df['strike'].max()}")
                    log.info(f"   Strikes with call Greeks: {has_call_greeks}/{len(df)}")
                    log.info(f"   Strikes with put Greeks: {has_put_greeks}/{len(df)}")
                    
                    if has_call_greeks > 0:
                        sample_strike = df[df['call_greeks'].apply(lambda x: isinstance(x, dict) and len(x) > 0)].iloc[0]
                        log.info(f"   Sample call Greeks at strike {sample_strike['strike']}: {sample_strike['call_greeks']}")
                    
                    return df
                else:
                    remarks = chain.get("remarks", {})
                    log.error(f"API returned failure: {remarks}")
                    return pd.DataFrame()
                    
            except Exception as e:
                log.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    import traceback
                    log.error(traceback.format_exc())
                    return pd.DataFrame()
        
        return pd.DataFrame()

    def fetch_market_quotes(self, securities, exchange_segment="NSE_FNO"):
        """Fetch market quote data with caching."""
        try:
            # Create cache key
            cache_key = f"quotes_{exchange_segment}_{'_'.join(map(str, securities))}"
            
            # Check cache first
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            # Fetch from API
            securities = [int(sec) if isinstance(sec, str) else sec for sec in securities]
            
            log.debug(f"Fetching quotes for {exchange_segment}: {securities}")
            
            response = self.dhan.ticker_data(
                securities={exchange_segment: securities}
            )
            
            if not response or response.get("status") != "success":
                log.error(f"API returned error: {response}")
                # Return cached data even if expired
                if cache_key in self._cache:
                    log.warning("⚠️ Using expired cache due to API error")
                    return self._cache[cache_key][0]
                return {}
            
            outer_data = response.get("data", {})
            inner_data = outer_data.get("data", {})
            exchange_data = inner_data.get(exchange_segment, {})
            
            quotes = {}
            for sec_id_str, quote_data in exchange_data.items():
                quotes[sec_id_str] = {
                    "LTP": quote_data.get("last_price"),
                    "security_id": sec_id_str,
                    "exchange_segment": exchange_segment
                }
            
            # Cache the result
            self._set_cache(cache_key, quotes)
            
            log.debug(f"Processed quotes: {quotes}")
            return quotes
            
        except Exception as e:
            log.error(f"Market quote error: {str(e)}")
            # Try to return cached data
            if 'cache_key' in locals() and cache_key in self._cache:
                log.warning("⚠️ Using cached data due to exception")
                return self._cache[cache_key][0]
            return {}

    def get_positions(self) -> Dict:
        """Get all positions from Dhan with caching."""
        try:
            cache_key = "positions_all"
            
            # Check cache
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            # Fetch from API
            positions = self.dhan.get_positions()
            
            if positions.get("status") == "success":
                log.info(f"✅ Fetched {len(positions.get('data', []))} positions from Dhan")
                self._set_cache(cache_key, positions)
            else:
                log.warning(f"⚠️ Failed to fetch positions: {positions.get('remarks')}")
                # Return cached even if expired
                if cache_key in self._cache:
                    return self._cache[cache_key][0]
            
            return positions
            
        except Exception as e:
            log.error(f"Error fetching positions: {e}")
            # Return cached data if available
            cache_key = "positions_all"
            if cache_key in self._cache:
                log.warning("⚠️ Using cached positions due to error")
                return self._cache[cache_key][0]
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    def get_orders(self) -> Dict:
        """Get all orders from Dhan with caching."""
        try:
            cache_key = "orders_all"
            
            # Check cache
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            # Fetch from API
            orders = self.dhan.get_order_list()
            
            if orders.get("status") == "success":
                log.info(f"✅ Fetched {len(orders.get('data', []))} orders from Dhan")
                self._set_cache(cache_key, orders)
            else:
                log.warning(f"⚠️ Failed to fetch orders: {orders.get('remarks')}")
                if cache_key in self._cache:
                    return self._cache[cache_key][0]
            
            return orders
            
        except Exception as e:
            log.error(f"Error fetching orders: {e}")
            cache_key = "orders_all"
            if cache_key in self._cache:
                log.warning("⚠️ Using cached orders due to error")
                return self._cache[cache_key][0]
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    def get_trade_book(self, order_id: str) -> Dict:
        """Get trade book for specific order."""
        try:
            trades = self.dhan.get_trade_book(order_id)
            
            if trades.get("status") == "success":
                log.info(f"✅ Fetched trade book for order {order_id}")
            
            return trades
            
        except Exception as e:
            log.error(f"Error fetching trade book: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    def get_fund_limits(self) -> Dict:
        """Get fund limits with caching."""
        try:
            cache_key = "funds_limits"
            
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            funds = self.dhan.get_fund_limits()
            
            if funds.get("status") == "success":
                log.info(f"✅ Fetched fund limits from Dhan")
                self._set_cache(cache_key, funds)
            else:
                if cache_key in self._cache:
                    return self._cache[cache_key][0]
            
            return funds
            
        except Exception as e:
            log.error(f"Error fetching fund limits: {e}")
            cache_key = "funds_limits"
            if cache_key in self._cache:
                return self._cache[cache_key][0]
            return {
                "status": "error",
                "error": str(e),
                "data": {}
            }

    def get_holdings(self) -> Dict:
        """Get holdings from Dhan with caching."""
        try:
            cache_key = "holdings_all"
            
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
            
            holdings = self.dhan.get_holdings()
            
            if holdings.get("status") == "success":
                log.info(f"✅ Fetched {len(holdings.get('data', []))} holdings from Dhan")
                self._set_cache(cache_key, holdings)
            else:
                if cache_key in self._cache:
                    return self._cache[cache_key][0]
            
            return holdings
            
        except Exception as e:
            log.error(f"Error fetching holdings: {e}")
            cache_key = "holdings_all"
            if cache_key in self._cache:
                return self._cache[cache_key][0]
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    def get_trade_history(self, from_date: str, to_date: str, page_number: int = 0) -> Dict:
        """Get trade history for date range."""
        try:
            history = self.dhan.get_trade_history(from_date, to_date, page_number)
            
            if history.get("status") == "success":
                log.info(f"✅ Fetched trade history from {from_date} to {to_date}")
            
            return history
            
        except Exception as e:
            log.error(f"Error fetching trade history: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }


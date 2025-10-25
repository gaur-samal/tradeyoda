"""Data collection agent aligned with Dhan API v2.2."""
import pandas as pd
from datetime import datetime, timedelta
from dhanhq import dhanhq, MarketFeed
import threading
import asyncio
import requests
import queue
import time
from src.utils.logger import log


class DataCollectionAgent:
    """Agent responsible for fetching and streaming Dhan market data."""
    
    def __init__(self, dhan_context):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        #self.client_id = client_id
        #self.access_token = access_token
        #self.dhan = dhanhq(client_id, access_token)
        self.market_feed = None
        self.live_data_queue = queue.Queue()
        self.latest_data = {}
        self.is_running = False
        self.subscribed_instruments = []
    
    def start_live_feed(self, instruments):
        """
        Start real-time market feed (WebSocket) v2.2.
        
        Args:
            instruments: List of tuples [(exchange, security_id, marketfeed.Full)]
        """
        try:
            if self.is_running:
                log.warning("Market feed already running")
                return True
            
            # Initialize updated MarketFeed
            self.market_feed = MarketFeed(
                self.dhan_context,
                #self.client_id,
                #self.access_token,
                instruments,
                version="v2"
            )
            # Start background thread with the correct pattern
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
        
        # Create a NEW event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def feed_worker():
            """Async worker that handles the feed."""
            while self.is_running:
                try:
                    # Connect
                    await self.market_feed.connect()
                    
                    # Get data
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
            # Run in this thread's event loop
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

            # Extract security_id from response
            security_id = str(data.get("security_id", ""))

            if security_id:
                # Add timestamp
                data["received_at"] = datetime.now()

                # Store in latest_data cache
                self.latest_data[security_id] = data

                # Put in queue for processing
                self.live_data_queue.put(data)

                # Log first few updates
                if not hasattr(self, '_log_count'):
                    self._log_count = {}

                count = self._log_count.get(security_id, 0)
                if count < 5:  # Log first 5 messages
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
        """
        Fetch historical intraday minute data using new v2.2 API.
        
        Added support:
        - `oi` parameter for open interest
        - from_date / to_date accepts ISO-format timestamps
        """
        try:
            params = {
                "security_id": security_id,
                "exchange_segment": exchange_segment,
                "instrument_type": instrument_type,
                "from_date": from_date,
                "to_date": to_date,
            }
            result = self.dhan.intraday_minute_data(**params)
            #log.info(f"intraday_minute_data : {result}")
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
        """
        Fetch option chain with proper data transformation.
        """
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
                    # Extract nested data structure
                    # Structure: {'data': {'data': {'last_price': X, 'oc': {strike: {ce/pe data}}}}}
                    outer_data = chain.get("data", {})
                    inner_data = outer_data.get("data", {})
                    option_chain_data = inner_data.get("oc", {})
                    spot_price = inner_data.get("last_price", 0)
                    
                    if not option_chain_data:
                        log.warning("Empty option chain in response")
                        return pd.DataFrame()
                    
                    # Transform nested dict to flat DataFrame
                    rows = []
                    for strike_str, strike_data in option_chain_data.items():
                        strike = float(strike_str)
                        
                        ce_data = strike_data.get("ce", {})
                        pe_data = strike_data.get("pe", {})
                        
                        row = {
                            'strike': strike,
                            # Call data
                            'call_oi': ce_data.get('oi', 0),
                            'call_volume': ce_data.get('volume', 0),
                            'call_iv': ce_data.get('implied_volatility', 0),
                            'call_ltp': ce_data.get('last_price', 0),
                            'call_oi_change': ce_data.get('oi', 0) - ce_data.get('previous_oi', 0),
                            # Put data
                            'put_oi': pe_data.get('oi', 0),
                            'put_volume': pe_data.get('volume', 0),
                            'put_iv': pe_data.get('implied_volatility', 0),
                            'put_ltp': pe_data.get('last_price', 0),
                            'put_oi_change': pe_data.get('oi', 0) - pe_data.get('previous_oi', 0),
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    df = df.sort_values('strike')
                    
                    log.info(f"✅ Processed {len(df)} strikes from option chain")
                    log.info(f"   Spot price: {spot_price}")
                    log.info(f"   Strike range: {df['strike'].min()} to {df['strike'].max()}")
                    
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
        """
        Fetch market quote data using SDK's ticker_data method.
        
        Args:
            securities: List of security IDs (can be strings or ints)
            exchange_segment: Exchange segment (default: NSE_FNO for Nifty Futures)
        
        Returns:
            Dict with security_id as key and quote data as value
        """
        try:
            # Convert securities to integers if they're strings
            securities = [int(sec) if isinstance(sec, str) else sec for sec in securities]
            
            log.info(f"Fetching quotes for {exchange_segment}: {securities}")
            
            # Call Dhan API
            response = self.dhan.ticker_data(
                securities={exchange_segment: securities}
            )
            
            #log.info(f"Raw response: {response}")
            
            if not response or response.get("status") != "success":
                log.error(f"API returned error: {response}")
                return {}
            
            # Extract nested data structure
            # Response format: {'status': 'success', 'data': {'data': {'NSE_FNO': {'52168': {...}}}}}
            outer_data = response.get("data", {})
            inner_data = outer_data.get("data", {})
            exchange_data = inner_data.get(exchange_segment, {})
            
            # Convert to our format: {security_id: {LTP: value, ...}}
            quotes = {}
            for sec_id_str, quote_data in exchange_data.items():
                quotes[sec_id_str] = {
                    "LTP": quote_data.get("last_price"),
                    "security_id": sec_id_str,
                    "exchange_segment": exchange_segment
                }
            
            log.info(f"Processed quotes: {quotes}")
            return quotes
            
        except Exception as e:
            log.error(f"Market quote error: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return {}


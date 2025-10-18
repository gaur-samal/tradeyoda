"""Data collection agent aligned with Dhan API v2.2."""
import pandas as pd
from datetime import datetime, timedelta
from dhanhq import dhanhq, MarketFeed
import threading
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
            
            # Set event handlers
            self.market_feed.on_connect = lambda _: log.info("Market feed connected")
            self.market_feed.on_message = self._on_message
            
            # Start background thread
            t = threading.Thread(
                target=self.market_feed.run_forever, name="MarketFeedWorker", daemon=True
            )
            t.start()
            
            self.is_running = True
            log.info(f"✅ Subscribed {len(instruments)} instruments")
            return True
        except Exception as e:
            log.error(f"❌ Feed start error: {str(e)}")
            return False
   
    def stop_live_feed(self):
        """
        Stop the live market feed and disconnect WebSocket gracefully.
        """
        try:
            if not self.is_running:
                log.warning("⚠️ Market feed not running")
                return True

            if self.market_feed:
                # Disconnect the WebSocket connection
                self.market_feed.disconnect()
                log.info("✅ MarketFeed WebSocket disconnected")

            # Update state
            self.is_running = False
            self.market_feed = None

            log.info("✅ Market feed stopped successfully")
            return True

        except Exception as e:
            log.error(f"❌ Error stopping market feed: {str(e)}")
            # Force state update even if disconnect fails
            self.is_running = False
            self.market_feed = None
            return False
   
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
            
            if not result or result.get("status") != "success":
                return pd.DataFrame()
            
            df = pd.DataFrame(result["data"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df = df.sort_values("timestamp")
            return df
        
        except Exception as e:
            log.error(f"❌ Historical fetch error: {str(e)}")
            return pd.DataFrame()
    
    def fetch_option_chain(self, security_id, exchange_segment, expiry_date):
        """
        Fetch option chain (aligned with get_option_chain in v2.2).
        Throttled by 3 secs to comply with API limits.
        """
        try:
            time.sleep(3)
            chain = self.dhan.get_option_chain(
                underlying_security_id=security_id,
                underlying_exchange_segment=exchange_segment,
                expiry_date=expiry_date
            )
            if chain and chain.get("status") == "success":
                return pd.DataFrame(chain["data"])
            return pd.DataFrame()
        except Exception as e:
            log.error(f"❌ Option chain fetch error: {str(e)}")
            return pd.DataFrame()
    
    def fetch_market_quotes(self, securities):
        """Fetch market quote data per v2.2 (supports up to 1000 instruments)."""
        try:
            data = self.dhan.get_market_quote(securities)
            return data
        except Exception as e:
            log.error(f"Market quote error: {str(e)}")
            return {}


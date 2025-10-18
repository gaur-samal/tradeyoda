"""Data collection agent with real-time market feed."""
import pandas as pd
import numpy as np
from dhanhq import DhanContext, dhanhq, MarketFeed
from datetime import datetime, timedelta
import threading
import queue
from typing import List, Dict, Optional, Tuple
from src.utils.logger import log


class DataCollectionAgent:
    """Agent responsible for fetching market data with WebSocket support."""
    
    def __init__(self, dhan_context: DhanContext):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.market_feed: Optional[MarketFeed] = None
        self.live_data_queue = queue.Queue()
        self.feed_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.latest_data: Dict[str, dict] = {}
        self.subscribed_instruments: List = []
    
    def start_live_feed(self, instruments: List[Tuple]) -> bool:
        """
        Start real-time market feed via WebSocket.
        
        Args:
            instruments: List of tuples (exchange, security_id, mode)
                        e.g., [(MarketFeed.NSE, "13", MarketFeed.Full)]
        
        Returns:
            bool: Success status
        """
        try:
            if self.is_running:
                log.warning("Market feed already running")
                return True
            
            self.market_feed = MarketFeed(
                self.dhan_context,
                instruments,
                version="v2"
            )
            
            self.subscribed_instruments = instruments
            self.is_running = True
            
            # Start feed worker thread
            self.feed_thread = threading.Thread(
                target=self._feed_worker,
                daemon=True,
                name="MarketFeedWorker"
            )
            self.feed_thread.start()
            
            log.info(f"✅ Live market feed started for {len(instruments)} instruments")
            return True
            
        except Exception as e:
            log.error(f"❌ Error starting market feed: {str(e)}")
            return False
    
    def _feed_worker(self):
        """Worker thread for processing market feed."""
        try:
            self.market_feed.run_forever()
            
            while self.is_running:
                response = self.market_feed.get_data()
                if response:
                    security_id = response.get("security_id")
                    if security_id:
                        self.latest_data[security_id] = {
                            **response,
                            "received_at": datetime.now()
                        }
                        self.live_data_queue.put(response)
                        
        except Exception as e:
            log.error(f"Market feed error: {str(e)}")
            self.is_running = False
    
    def get_live_quote(self, security_id: str) -> Dict:
        """
        Get latest live data for a security.
        
        Args:
            security_id: Security ID to fetch
        
        Returns:
            dict: Latest market data
        """
        data = self.latest_data.get(security_id, {})
        
        if not data:
            log.warning(f"No live data available for security {security_id}")
        
        return data
    
    def subscribe_instruments(self, instruments: List[Tuple]) -> bool:
        """Subscribe to additional instruments."""
        if not self.market_feed:
            log.error("Market feed not initialized")
            return False
        
        try:
            self.market_feed.subscribe_symbols(instruments)
            self.subscribed_instruments.extend(instruments)
            log.info(f"✅ Subscribed to {len(instruments)} new instruments")
            return True
        except Exception as e:
            log.error(f"Subscription error: {str(e)}")
            return False
    
    def unsubscribe_instruments(self, instruments: List[Tuple]) -> bool:
        """Unsubscribe from instruments."""
        if not self.market_feed:
            return False
        
        try:
            self.market_feed.unsubscribe_symbols(instruments)
            self.subscribed_instruments = [
                i for i in self.subscribed_instruments if i not in instruments
            ]
            log.info(f"✅ Unsubscribed from {len(instruments)} instruments")
            return True
        except Exception as e:
            log.error(f"Unsubscription error: {str(e)}")
            return False
    
    def stop_live_feed(self):
        """Stop market feed."""
        self.is_running = False
        if self.market_feed:
            try:
                self.market_feed.disconnect()
                log.info("✅ Market feed disconnected")
            except Exception as e:
                log.error(f"Error disconnecting feed: {str(e)}")
    
    def fetch_historical_data(
        self,
        security_id: str,
        exchange_segment: str,
        instrument_type: str,
        timeframe: str = "15",
        from_date: str = None,
        to_date: str = None
    ) -> pd.DataFrame:
        """
        Fetch historical intraday data.
        
        Args:
            security_id: Security ID
            exchange_segment: Exchange segment
            instrument_type: Type of instrument
            timeframe: Timeframe in minutes
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame: Historical OHLCV data
        """
        try:
            # Use intraday_minute_data for recent data
            data = self.dhan.intraday_minute_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type
            )
            
            if data and data.get("status") == "success":
                df = pd.DataFrame(data["data"])
                if not df.empty:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                    df = df.sort_values("timestamp")
                    
                    # Resample to desired timeframe if needed
                    if timeframe != "1":
                        df = self._resample_data(df, timeframe)
                    
                    log.info(f"✅ Fetched {len(df)} candles for {security_id}")
                    return df
            
            log.warning(f"⚠️ No data received for {security_id}")
            return pd.DataFrame()
            
        except Exception as e:
            log.error(f"❌ Error fetching historical data: {str(e)}")
            return pd.DataFrame()
    
    def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data to different timeframe."""
        try:
            df = df.set_index("timestamp")
            
            ohlc_dict = {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }
            
            resampled = df.resample(f"{timeframe}T").agg(ohlc_dict).dropna()
            resampled = resampled.reset_index()
            
            return resampled
            
        except Exception as e:
            log.error(f"Resampling error: {str(e)}")
            return df
    
    def fetch_option_chain(
        self,
        under_security_id: int,
        under_exchange_segment: str,
        expiry: str
    ) -> pd.DataFrame:
        """
        Fetch option chain data.
        
        Args:
            under_security_id: Underlying security ID
            under_exchange_segment: Exchange segment
            expiry: Expiry date (YYYY-MM-DD)
        
        Returns:
            DataFrame: Option chain data
        """
        try:
            option_chain = self.dhan.option_chain(
                under_security_id=under_security_id,
                under_exchange_segment=under_exchange_segment,
                expiry=expiry
            )
            
            if option_chain and option_chain.get("status") == "success":
                df = pd.DataFrame(option_chain["data"])
                log.info(f"✅ Fetched option chain with {len(df)} strikes")
                return df
            
            log.warning("⚠️ No option chain data received")
            return pd.DataFrame()
            
        except Exception as e:
            log.error(f"❌ Error fetching option chain: {str(e)}")
            return pd.DataFrame()
    
    def fetch_market_quotes(self, securities: Dict[str, List[int]]) -> Dict:
        """
        Fetch market quotes for multiple securities.
        
        Args:
            securities: Dict of exchange: [security_ids]
                       e.g., {"NSE_EQ": [1333, 11915], "NSE_FNO": [52175]}
        
        Returns:
            dict: Quote data
        """
        try:
            quotes = self.dhan.quote_data(securities=securities)
            
            if quotes and quotes.get("status") == "success":
                log.info(f"✅ Fetched quotes for {len(securities)} securities")
                return quotes
            
            return {}
            
        except Exception as e:
            log.error(f"❌ Error fetching quotes: {str(e)}")
            return {}


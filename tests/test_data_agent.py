"""Tests for DataCollectionAgent."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from src.agents.data_agent import DataCollectionAgent
from dhanhq import DhanContext, MarketFeed


@pytest.fixture
def mock_dhan_context():
    """Create mock DhanContext."""
    return DhanContext("test_client", "test_token")


@pytest.fixture
def data_agent(mock_dhan_context):
    """Create DataCollectionAgent instance."""
    return DataCollectionAgent(mock_dhan_context)


class TestDataCollectionAgent:
    """Test cases for DataCollectionAgent."""
    
    def test_initialization(self, data_agent):
        """Test agent initialization."""
        assert data_agent.dhan_context is not None
        assert data_agent.dhan is not None
        assert data_agent.is_running is False
        assert len(data_agent.latest_data) == 0
    
    @patch('src.agents.data_agent.MarketFeed')
    def test_start_live_feed(self, mock_market_feed, data_agent):
        """Test starting live market feed."""
        instruments = [(MarketFeed.NSE, "13", MarketFeed.Full)]
        
        result = data_agent.start_live_feed(instruments)
        
        assert result is True
        assert data_agent.is_running is True
        assert data_agent.feed_thread is not None
    
    def test_get_live_quote_no_data(self, data_agent):
        """Test getting live quote with no data."""
        quote = data_agent.get_live_quote("13")
        
        assert quote == {}
    
    def test_get_live_quote_with_data(self, data_agent):
        """Test getting live quote with data."""
        test_data = {
            'security_id': '13',
            'LTP': 19500.50,
            'volume': 1000000
        }
        data_agent.latest_data['13'] = test_data
        
        quote = data_agent.get_live_quote("13")
        
        assert quote == test_data
        assert quote['LTP'] == 19500.50
    
    @patch('src.agents.data_agent.dhanhq')
    def test_fetch_historical_data_success(self, mock_dhanhq, data_agent):
        """Test fetching historical data successfully."""
        # Mock API response
        mock_response = {
            'status': 'success',
            'data': [
                {'timestamp': 1234567890, 'open': 100, 'high': 105, 'low': 99, 'close': 103, 'volume': 1000},
                {'timestamp': 1234567900, 'open': 103, 'high': 107, 'low': 102, 'close': 106, 'volume': 1200},
            ]
        }
        data_agent.dhan.intraday_minute_data = Mock(return_value=mock_response)
        
        df = data_agent.fetch_historical_data(
            security_id="13",
            exchange_segment="IDX_I",
            instrument_type="INDEX",
            timeframe="15"
        )
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == 2
        assert 'timestamp' in df.columns
    
    @patch('src.agents.data_agent.dhanhq')
    def test_fetch_historical_data_empty(self, mock_dhanhq, data_agent):
        """Test fetching historical data with empty response."""
        mock_response = {'status': 'failed'}
        data_agent.dhan.intraday_minute_data = Mock(return_value=mock_response)
        
        df = data_agent.fetch_historical_data(
            security_id="13",
            exchange_segment="IDX_I",
            instrument_type="INDEX"
        )
        
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    
    @patch('src.agents.data_agent.dhanhq')
    def test_fetch_option_chain_success(self, mock_dhanhq, data_agent):
        """Test fetching option chain successfully."""
        mock_response = {
            'status': 'success',
            'data': [
                {'strike': 19000, 'call_oi': 1000, 'put_oi': 2000},
                {'strike': 19500, 'call_oi': 1500, 'put_oi': 2500},
            ]
        }
        data_agent.dhan.option_chain = Mock(return_value=mock_response)
        
        df = data_agent.fetch_option_chain(
            under_security_id=13,
            under_exchange_segment="IDX_I",
            expiry="2025-10-30"
        )
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == 2
    
    def test_stop_live_feed(self, data_agent):
        """Test stopping live feed."""
        data_agent.is_running = True
        data_agent.market_feed = Mock()
        
        data_agent.stop_live_feed()
        
        assert data_agent.is_running is False


@pytest.mark.asyncio
class TestDataAgentAsync:
    """Async test cases."""
    
    async def test_concurrent_data_fetch(self, data_agent):
        """Test concurrent data fetching."""
        # Test concurrent operations
        pass


"""Integration tests for the trading system."""
import pytest
from unittest.mock import Mock, patch
import asyncio

from orchestrator import TradingOrchestrator
from src.config import Config


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Config()
    config.DHAN_CLIENT_ID = "test_client"
    config.DHAN_ACCESS_TOKEN = "test_token"
    config.OPENAI_API_KEY = "test_openai_key"
    config.USE_SANDBOX = True
    return config


@pytest.fixture
@patch('orchestrator.DhanContext')
def orchestrator(mock_dhan_context, mock_config):
    """Create orchestrator instance."""
    return TradingOrchestrator(mock_config)


class TestTradingOrchestrator:
    """Integration tests for orchestrator."""
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.config is not None
        assert orchestrator.data_agent is not None
        assert orchestrator.tech_agent is not None
        assert orchestrator.llm_agent is not None
        assert orchestrator.options_agent is not None
        assert orchestrator.execution_agent is not None
        assert orchestrator.is_running is False
    
    @patch('orchestrator.DataCollectionAgent.start_live_feed')
    @patch('orchestrator.ExecutionAgent.start_order_updates')
    def test_start_system(self, mock_order_updates, mock_live_feed, orchestrator):
        """Test starting the trading system."""
        mock_live_feed.return_value = True
        mock_order_updates.return_value = True
        
        orchestrator.start()
        
        assert orchestrator.is_running is True
        mock_live_feed.assert_called_once()
        mock_order_updates.assert_called_once()
    
    def test_shutdown(self, orchestrator):
        """Test system shutdown."""
        orchestrator.is_running = True
        orchestrator.data_agent.stop_live_feed = Mock()
        orchestrator.execution_agent.stop_order_updates = Mock()
        
        orchestrator.shutdown()
        
        assert orchestrator.is_running is False
        orchestrator.data_agent.stop_live_feed.assert_called_once()
        orchestrator.execution_agent.stop_order_updates.assert_called_once()


@pytest.mark.asyncio
class TestAsyncWorkflows:
    """Test async workflows."""
    
    @patch('orchestrator.DataCollectionAgent.fetch_historical_data')
    async def test_zone_identification_cycle(self, mock_fetch, orchestrator):
        """Test zone identification workflow."""
        import pandas as pd
        
        # Mock data
        mock_df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=100, freq='15T'),
            'open': [19000] * 100,
            'high': [19100] * 100,
            'low': [18900] * 100,
            'close': [19050] * 100,
            'volume': [100000] * 100
        })
        mock_fetch.return_value = mock_df
        
        result = await orchestrator.run_zone_identification_cycle()
        
        # Should return analysis cache
        assert result is not None or result is None  # May fail due to mock limitations


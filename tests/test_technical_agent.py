"""Tests for TechnicalAnalysisAgent."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.agents.technical_analysis_agent import TechnicalAnalysisAgent
from src.config import Config


@pytest.fixture
def config():
    """Create test configuration."""
    return Config()


@pytest.fixture
def tech_agent(config):
    """Create TechnicalAnalysisAgent instance."""
    return TechnicalAnalysisAgent(config)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data."""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='15T')
    
    data = {
        'timestamp': dates,
        'open': np.random.uniform(19000, 19500, 100),
        'high': np.random.uniform(19100, 19600, 100),
        'low': np.random.uniform(18900, 19400, 100),
        'close': np.random.uniform(19000, 19500, 100),
        'volume': np.random.randint(100000, 1000000, 100)
    }
    
    df = pd.DataFrame(data)
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df


class TestTechnicalAnalysisAgent:
    """Test cases for TechnicalAnalysisAgent."""
    
    def test_initialization(self, tech_agent):
        """Test agent initialization."""
        assert tech_agent.config is not None
    
    def test_calculate_volume_profile_success(self, tech_agent, sample_ohlcv_data):
        """Test volume profile calculation."""
        vp_data = tech_agent.calculate_volume_profile(sample_ohlcv_data)
        
        assert vp_data is not None
        assert 'poc' in vp_data
        assert 'vah' in vp_data
        assert 'val' in vp_data
        assert 'volume_profile' in vp_data
        assert vp_data['vah'] >= vp_data['val']
    
    def test_calculate_volume_profile_empty_df(self, tech_agent):
        """Test volume profile with empty DataFrame."""
        empty_df = pd.DataFrame()
        vp_data = tech_agent.calculate_volume_profile(empty_df)
        
        assert vp_data == {}
    
    def test_identify_order_blocks(self, tech_agent, sample_ohlcv_data):
        """Test order block identification."""
        order_blocks = tech_agent.identify_order_blocks(sample_ohlcv_data, lookback=20)
        
        assert isinstance(order_blocks, list)
        # Should find some order blocks in random data
        if order_blocks:
            assert 'type' in order_blocks[0]
            assert order_blocks[0]['type'] in ['bullish', 'bearish']
            assert 'zone_top' in order_blocks[0]
            assert 'zone_bottom' in order_blocks[0]
    
    def test_identify_order_blocks_insufficient_data(self, tech_agent):
        """Test order blocks with insufficient data."""
        small_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=10, freq='15T'),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
        
        order_blocks = tech_agent.identify_order_blocks(small_df, lookback=20)
        
        assert order_blocks == []
    
    def test_identify_fair_value_gaps(self, tech_agent, sample_ohlcv_data):
        """Test FVG identification."""
        fvgs = tech_agent.identify_fair_value_gaps(sample_ohlcv_data)
        
        assert isinstance(fvgs, list)
        if fvgs:
            assert 'type' in fvgs[0]
            assert fvgs[0]['type'] in ['bullish', 'bearish']
            assert 'gap_top' in fvgs[0]
            assert 'gap_bottom' in fvgs[0]
            assert fvgs[0]['gap_top'] >= fvgs[0]['gap_bottom']
    
    def test_identify_supply_demand_zones(self, tech_agent, sample_ohlcv_data):
        """Test supply/demand zone identification."""
        vp_data = tech_agent.calculate_volume_profile(sample_ohlcv_data)
        order_blocks = tech_agent.identify_order_blocks(sample_ohlcv_data)
        fvgs = tech_agent.identify_fair_value_gaps(sample_ohlcv_data)
        
        zones = tech_agent.identify_supply_demand_zones(
            sample_ohlcv_data, vp_data, order_blocks, fvgs
        )
        
        assert 'demand_zones' in zones
        assert 'supply_zones' in zones
        assert 'current_price' in zones
        assert isinstance(zones['demand_zones'], list)
        assert isinstance(zones['supply_zones'], list)
    
    def test_zone_confidence_calculation(self, tech_agent, sample_ohlcv_data):
        """Test that zone confidence is calculated correctly."""
        vp_data = tech_agent.calculate_volume_profile(sample_ohlcv_data)
        order_blocks = tech_agent.identify_order_blocks(sample_ohlcv_data)
        fvgs = tech_agent.identify_fair_value_gaps(sample_ohlcv_data)
        
        zones = tech_agent.identify_supply_demand_zones(
            sample_ohlcv_data, vp_data, order_blocks, fvgs
        )
        
        for zone in zones['demand_zones']:
            assert 0 <= zone['confidence'] <= 100
            assert len(zone['factors']) >= 1


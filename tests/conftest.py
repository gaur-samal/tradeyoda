"""Pytest configuration and shared fixtures."""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory."""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before each test."""
    from src.config import Config
    
    # Store original values
    original_values = {
        'DHAN_CLIENT_ID': Config.DHAN_CLIENT_ID,
        'DHAN_ACCESS_TOKEN': Config.DHAN_ACCESS_TOKEN,
        'OPENAI_API_KEY': Config.OPENAI_API_KEY,
    }
    
    yield
    
    # Restore original values
    Config.DHAN_CLIENT_ID = original_values['DHAN_CLIENT_ID']
    Config.DHAN_ACCESS_TOKEN = original_values['DHAN_ACCESS_TOKEN']
    Config.OPENAI_API_KEY = original_values['OPENAI_API_KEY']


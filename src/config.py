"""Configuration management for the trading system."""
import os
from dhanhq import DhanContext
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class Config:
    """Main configuration class."""
    
    # API Configuration
    DHAN_CLIENT_ID: str = os.getenv("DHAN_CLIENT_ID", "")
    DHAN_ACCESS_TOKEN: str = os.getenv("DHAN_ACCESS_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Environment
    USE_SANDBOX: bool = os.getenv("USE_SANDBOX", "true").lower() == "true"
    
    USE_BACKTEST_MODE: bool = False   # default live
    BACKTEST_FROM: str = "2025-10-01"
    BACKTEST_TO: str = "2025-10-17"
    
    # Trading Parameters
    RISK_REWARD_RATIO: float = float(os.getenv("RISK_REWARD_RATIO", "3.0"))
    MAX_RISK_PERCENTAGE: float = float(os.getenv("MAX_RISK_PERCENTAGE", "2.0"))
    MIN_PROBABILITY_THRESHOLD: float = float(os.getenv("MIN_PROBABILITY_THRESHOLD", "80.0"))
    
    # Order Execution Settings
    ORDER_QUANTITY = 50  # Number of lots/units per trade
    USE_SUPER_ORDER = True  # True = Super Order, False = Bracket Order

    # Timeframes
    ZONE_TIMEFRAME: int = int(os.getenv("ZONE_TIMEFRAME", "15"))
    TRADE_TIMEFRAME: int = int(os.getenv("TRADE_TIMEFRAME", "3"))
    
    # Nifty Configuration
    NIFTY_SECURITY_ID: str = os.getenv("NIFTY_SECURITY_ID", "13")
    NIFTY_EXCHANGE: str = os.getenv("NIFTY_EXCHANGE", "IDX_I")
    NIFTY_SYMBOL: str = "NIFTY 50"
    
    # Technical Indicators
    VP_SESSIONS: int = int(os.getenv("VP_SESSIONS", "24"))
    VP_VALUE_AREA: float = float(os.getenv("VP_VALUE_AREA", "70"))
    OB_LOOKBACK: int = int(os.getenv("OB_LOOKBACK", "20"))
    FVG_MIN_SIZE: float = float(os.getenv("FVG_MIN_SIZE", "0.001"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = LOGS_DIR / os.getenv("LOG_FILE", "trading_agent.log")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/trades.db")
    
    # Streamlit
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    @classmethod
    def get_dhan_context(cls):
        """Return a reusable DhanContext object."""
        return DhanContext(cls.DHAN_CLIENT_ID, cls.DHAN_ACCESS_TOKEN)
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        required_fields = [
            ("DHAN_CLIENT_ID", cls.DHAN_CLIENT_ID),
            ("DHAN_ACCESS_TOKEN", cls.DHAN_ACCESS_TOKEN),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
        ]
        
        missing = [name for name, value in required_fields if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


# Global config instance
config = Config()


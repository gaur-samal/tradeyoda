"""Configuration management for the trading system."""
import os
from dhanhq import DhanContext
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Lazy import desktop_config to avoid circular imports
# Import happens inside _initialize_paths() function
_desktop_config = None

def _get_desktop_config():
    """Lazy load desktop config to avoid circular imports."""
    global _desktop_config
    if _desktop_config is None:
        # Import directly without triggering src.utils.__init__.py
        import importlib.util
        import os

        # Get the path to desktop_config.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        desktop_config_path = os.path.join(current_dir, 'utils', 'desktop_config.py')

        # Load module directly
        spec = importlib.util.spec_from_file_location("desktop_config_module", desktop_config_path)
        desktop_config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(desktop_config_module)

        _desktop_config = desktop_config_module.desktop_config
    return _desktop_config

def _initialize_paths():
    """Initialize base paths based on desktop mode."""
    desktop_config = _get_desktop_config()

    if desktop_config.is_desktop_mode:
        return (
            desktop_config.app_data_dir,
            desktop_config.data_dir,
            desktop_config.logs_dir
        )
    else:
        # Web/dev mode - use current directory
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "data"
        logs_dir = base_dir / "logs"
        # Ensure directories exist
        data_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        return base_dir, data_dir, logs_dir

# Initialize paths
BASE_DIR, DATA_DIR, LOGS_DIR = _initialize_paths()

# Base paths
#BASE_DIR = Path(__file__).parent.parent
#DATA_DIR = BASE_DIR / "data"
#LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
#DATA_DIR.mkdir(exist_ok=True)
#LOGS_DIR.mkdir(exist_ok=True)


class Config:
    """Main configuration class."""
    
    # API Configuration
    DHAN_CLIENT_ID: str = os.getenv("DHAN_CLIENT_ID", "")
    DHAN_ACCESS_TOKEN: str = os.getenv("DHAN_ACCESS_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    # Flag to track if credentials were loaded from store
    _credentials_loaded_from_store: bool = False 
    # ==================== LICENSING CONFIGURATION ====================
    # Licensing server URL
    LICENSING_SERVER_URL: str = os.getenv("LICENSING_SERVER_URL", "http://localhost:8100")
    
    # License validation
    LICENSE_KEY: str = ""
    LICENSE_TIER: str = "TRIAL"  # TRIAL, BASIC, ADVANCED, PRO
    LICENSE_VALID: bool = False
    LICENSE_FEATURES: dict = {}
    
    # Feature flags (controlled by license tier)
    FEATURE_MANUAL_TRADING: bool = True  # Default for development
    FEATURE_AUTO_TRADING: bool = True    # Default for development
    # Environment
    USE_SANDBOX: bool = os.getenv("USE_SANDBOX", "true").lower() == "true"
    
    USE_BACKTEST_MODE: bool = False
    BACKTEST_FROM: str = "2025-10-01"
    BACKTEST_TO: str = "2025-10-17"
    
    # Trading Parameters
    RISK_REWARD_RATIO: float = float(os.getenv("RISK_REWARD_RATIO", "3.0"))
    MAX_RISK_PERCENTAGE: float = float(os.getenv("MAX_RISK_PERCENTAGE", "2.0"))
    MIN_PROBABILITY_THRESHOLD: float = float(os.getenv("MIN_PROBABILITY_THRESHOLD", "80.0"))
    
    # Order Execution Settings
    ORDER_QUANTITY = 1
    USE_SUPER_ORDER = True
    NO_TRADES_ON_EXPIRY = True

    # Timeframes
    ZONE_TIMEFRAME: int = int(os.getenv("ZONE_TIMEFRAME", "15"))
    TRADE_TIMEFRAME: int = int(os.getenv("TRADE_TIMEFRAME", "5"))
    ZONE_REFRESH_INTERVAL: int = int(os.getenv("ZONE_REFRESH_INTERVAL", "15"))
    
    # ===== TRADE MANAGEMENT PARAMETERS =====
    # Maximum trades per day
    MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "5"))

    # Cooldown period before trading same zone again (minutes)
    ZONE_COOLDOWN_MINUTES = int(os.getenv("ZONE_COOLDOWN_MINUTES", "15"))

    # Tolerance for duplicate zone detection (percentage)
    DUPLICATE_ZONE_TOLERANCE = float(os.getenv("DUPLICATE_ZONE_TOLERANCE", "0.1"))

    # Maximum concurrent positions
    MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "3"))

    # ==================== INSTRUMENT SELECTION ====================
    # User can select: NIFTY or BANKNIFTY
    SELECTED_INSTRUMENT: str = os.getenv("SELECTED_INSTRUMENT", "NIFTY")
    
    # Nifty Configuration
    NIFTY_CONFIG = {
        "symbol": "NIFTY",
        "name": "Nifty 50",
        "index_security_id": 13,
        "futures_security_id": int(os.getenv("NIFTY_FUTURES_SECURITY_ID", "37054")),
        "exchange": "NSE_FNO",
        "index_exchange": "IDX_I",
        "expiry_day": "TUESDAY",  # Nifty weekly expiry
        "expiry_type": "WEEKLY",
        "lot_size": 75,
    }
    
    # BankNifty Configuration
    BANKNIFTY_CONFIG = {
        "symbol": "BANKNIFTY",
        "name": "Bank Nifty",
        "index_security_id": 25,
        "futures_security_id": int(os.getenv("BANKNIFTY_FUTURES_SECURITY_ID", "52175")),
        "exchange": "NSE_FNO",
        "index_exchange": "IDX_I",
        "expiry_day": "LAST_TUESDAY",  # BankNifty monthly expiry (last Tuesday)
        "expiry_type": "MONTHLY",
        "lot_size": 35,
    }
    
    # ==================== THETA DECAY SETTINGS ====================
    # Maximum theta impact allowed (%)
    MAX_THETA_IMPACT_PERCENTAGE: float = float(os.getenv("MAX_THETA_IMPACT_PERCENTAGE", "5.0"))

    # Expected holding time for intraday trades (hours)
    EXPECTED_HOLD_HOURS: float = float(os.getenv("EXPECTED_HOLD_HOURS", "3.0"))
    
    # Get active instrument config
    @classmethod
    def get_active_instrument(cls):
        """Get configuration for currently selected instrument."""
        if cls.SELECTED_INSTRUMENT == "BANKNIFTY":
            return cls.BANKNIFTY_CONFIG
        else:
            return cls.NIFTY_CONFIG
    
    # ==================== EXPIRY DAY CHECK ====================
    @classmethod
    def is_expiry_day(cls) -> bool:
        """
        Check if today is expiry day for the selected instrument.
        
        Returns:
            bool: True if today is expiry day
        """
        from datetime import datetime
        import calendar
        from src.utils.logger import log
        
        today = datetime.now()
        weekday = today.weekday()  # Monday=0, Tuesday=1, ..., Sunday=6
        
        instrument = cls.get_active_instrument()
        expiry_type = instrument.get("expiry_type", "WEEKLY")
        
        if expiry_type == "WEEKLY":
            # Nifty: Weekly expiry on Tuesday
            # Tuesday = 1
            is_expiry = (weekday == 1)
            log.info(f"📅 Weekly expiry check ({instrument['name']}): Today is {'Tuesday (EXPIRY)' if is_expiry else 'not Tuesday'}")
            return is_expiry
            
        elif expiry_type == "MONTHLY":
            # BankNifty: Monthly expiry on last Tuesday
            # Tuesday = 1
            if weekday != 1:  # Not Tuesday
                return False
            
            # Check if this is the last Tuesday of the month
            last_day = calendar.monthrange(today.year, today.month)[1]
            
            # Calculate days until next Tuesday
            days_until_next_tuesday = (1 - weekday) % 7
            if days_until_next_tuesday == 0:
                days_until_next_tuesday = 7
            
            next_tuesday = today.day + days_until_next_tuesday
            
            is_last_tuesday = next_tuesday > last_day
            
            log.info(f"📅 Monthly expiry check ({instrument['name']}): Today is Tuesday, last Tuesday of month: {is_last_tuesday}")
            return is_last_tuesday
        
        return False
    
    # ==================== DYNAMIC INSTRUMENT PROPERTIES ====================
    @property
    def INSTRUMENT_SYMBOL(self):
        return self.get_active_instrument()["symbol"]
    
    @property
    def INSTRUMENT_NAME(self):
        return self.get_active_instrument()["name"]
    
    @property
    def INSTRUMENT_INDEX_SECURITY_ID(self):
        return self.get_active_instrument()["index_security_id"]
    
    @property
    def INSTRUMENT_FUTURES_SECURITY_ID(self):
        return self.get_active_instrument()["futures_security_id"]
    
    @property
    def INSTRUMENT_EXCHANGE(self):
        return self.get_active_instrument()["exchange"]
    
    @property
    def INSTRUMENT_INDEX_EXCHANGE(self):
        return self.get_active_instrument()["index_exchange"]
    
    @property
    def INSTRUMENT_EXPIRY_DAY(self):
        return self.get_active_instrument()["expiry_day"]
    
    @property
    def INSTRUMENT_EXPIRY_TYPE(self):
        return self.get_active_instrument()["expiry_type"]
    
    @property
    def INSTRUMENT_LOT_SIZE(self):
        return self.get_active_instrument()["lot_size"]
    
    # ==================== LEGACY COMPATIBILITY (Keep for now) ====================
    # These will use the selected instrument dynamically
    @property
    def NIFTY_FUTURES_SECURITY_ID(self):
        return str(self.INSTRUMENT_FUTURES_SECURITY_ID)
    
    @property
    def NIFTY_FUTURES_EXCHANGE(self):
        return self.INSTRUMENT_EXCHANGE
    
    @property
    def NIFTY_INDEX_SECURITY_ID(self):
        return self.INSTRUMENT_INDEX_SECURITY_ID
    
    @property
    def NIFTY_INDEX_EXCHANGE(self):
        return self.INSTRUMENT_INDEX_EXCHANGE
    
    @property
    def ANALYSIS_INSTRUMENT_TYPE(self):
        return "FUTIDX"  # Same for both Nifty and BankNifty
    
    @property
    def NIFTY_SYMBOL(self):
        return self.INSTRUMENT_NAME
    
    # Technical Indicators
    VP_SESSIONS: int = int(os.getenv("VP_SESSIONS", "24"))
    VP_VALUE_AREA: float = float(os.getenv("VP_VALUE_AREA", "70"))
    OB_LOOKBACK: int = int(os.getenv("OB_LOOKBACK", "20"))
    FVG_MIN_SIZE: float = float(os.getenv("FVG_MIN_SIZE", "0.001"))
    
    RSI_PERIOD: int = int(os.getenv("RSI_PERIOD", "14"))
    RSI_OVERBOUGHT: float = float(os.getenv("RSI_OVERBOUGHT", "70"))
    RSI_OVERSOLD: float = float(os.getenv("RSI_OVERSOLD", "30"))
    
    BB_PERIOD: int = int(os.getenv("BB_PERIOD", "20"))
    BB_STD_DEV: float = float(os.getenv("BB_STD_DEV", "2"))
    
    # Pattern Detection
    ENABLE_CANDLESTICK_PATTERNS: bool = True
    ENABLE_CHART_PATTERNS: bool = True
    MIN_PATTERN_CONFIDENCE: float = 70.0
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = LOGS_DIR / os.getenv("LOG_FILE", "trading_agent.log")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/trades.db")
    
    # Streamlit
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # ==================== DHAN CREDENTIALS ====================
    # Load from persistent store first, fallback to .env
    @classmethod
    def load_dhan_credentials(cls):
        if cls._credentials_loaded_from_store:
            return
        try:
            from src.utils.credentials_store import credentials_store
            from src.utils.logger import log
            
            stored_creds = credentials_store.get_dhan_credentials()
            
            if stored_creds:
                log.info("🔑 Using Dhan credentials from persistent storage")
                cls.DHAN_CLIENT_ID = stored_creds['client_id']
                cls.DHAN_ACCESS_TOKEN = stored_creds['access_token']
                cls._credentials_loaded_from_store = True
            else:
                log.info("🔑 Using Dhan credentials from .env")
        except Exception as e:
            # This is okay - just use .env values
            print(f"⚠️ Could not load stored credentials, using .env: {e}")

    @classmethod
    def get_dhan_context(cls):
        """Return a reusable DhanContext object."""
        return DhanContext(cls.DHAN_CLIENT_ID, cls.DHAN_ACCESS_TOKEN)
    
    @classmethod
    def validate_license(cls, use_cache: bool = True) -> bool:
        """
        Validate license and fetch OpenAI key from licensing server.
        Returns True if license is valid, False otherwise.
        """
        try:
            from src.utils.licensing_client import licensing_client
            from src.utils.logger import log
            
            # Validate license
            #result = licensing_client.validate_license()
            result = licensing_client.validate_license(use_cache=use_cache) 
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                log.error(f"❌ License validation failed: {error}")
                cls.LICENSE_VALID = False
                return False
            
            # Extract license data
            data = result.get("data", {})
            
            cls.LICENSE_KEY = licensing_client.load_license_key() or ""
            cls.LICENSE_TIER = data.get("tier", "TRIAL")
            cls.LICENSE_VALID = data.get("valid", False)
            cls.LICENSE_FEATURES = data.get("features", {})
            
            # Set OpenAI configuration from license
            cls.OPENAI_API_KEY = data.get("openai_key", cls.OPENAI_API_KEY)
            cls.OPENAI_MODEL = data.get("openai_model", cls.OPENAI_MODEL)
            
            # Set feature flags based on tier
            cls.FEATURE_MANUAL_TRADING = cls.LICENSE_FEATURES.get("manual_trading", False)
            cls.FEATURE_AUTO_TRADING = cls.LICENSE_FEATURES.get("auto_trading", False)
            
            # Log license status
            from_cache = result.get("from_cache", False)
            cache_msg = " (from cache)" if from_cache else ""
            
            log.info(f"✅ License validated{cache_msg}")
            log.info(f"   Tier: {cls.LICENSE_TIER}")
            log.info(f"   Manual Trading: {'✅' if cls.FEATURE_MANUAL_TRADING else '❌'}")
            log.info(f"   Auto Trading: {'✅' if cls.FEATURE_AUTO_TRADING else '❌'}")
            log.info(f"   OpenAI Model: {cls.OPENAI_MODEL}")
            
            # Check for scrip master updates
            update_check = licensing_client.check_scrip_master_update()
            if update_check.get("has_update"):
                log.info(f"📦 Scrip master update available: {update_check.get('version')}")
            
            return True
            
        except Exception as e:
            log.error(f"❌ License validation error: {e}")
            import traceback
            log.error(traceback.format_exc())
            cls.LICENSE_VALID = False
            return False
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        required_fields = [
            ("DHAN_CLIENT_ID", cls.DHAN_CLIENT_ID),
            ("DHAN_ACCESS_TOKEN", cls.DHAN_ACCESS_TOKEN),
        ]
        
        # OpenAI key will be fetched from licensing server, so don't require it here
        # unless licensing is disabled (development mode)
        if not cls.LICENSE_VALID and not cls.OPENAI_API_KEY:
            required_fields.append(("OPENAI_API_KEY", cls.OPENAI_API_KEY))
        
        missing = [name for name, value in required_fields if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
# ==================== INITIALIZE CREDENTIALS ====================
# Call this AFTER the class is fully defined
Config.load_dhan_credentials()

# Global config instance
config = Config()


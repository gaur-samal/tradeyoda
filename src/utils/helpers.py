"""Helper utilities."""
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from calendar import monthrange


def get_nearest_expiry(instrument_config: Dict = None, base_date: datetime = None) -> str:
    """
    Get nearest expiry for given instrument.
    
    Args:
        instrument_config: Instrument configuration dict with expiry_day and expiry_type
        base_date: Base date to calculate from (default: current date)
    
    Returns:
        Expiry date in YYYY-MM-DD format
    """
    if base_date is None:
        base_date = datetime.now()
    
    # Default to Nifty if no config provided
    if instrument_config is None:
        from src.config import config
        instrument_config = config.get_active_instrument()
    
    expiry_type = instrument_config.get("expiry_type", "WEEKLY")
    expiry_day = instrument_config.get("expiry_day", "TUESDAY")
    
    if expiry_type == "WEEKLY":
        # Weekly expiry (Nifty - Tuesday)
        return _get_weekly_expiry(base_date, expiry_day)
    elif expiry_type == "MONTHLY":
        # Monthly expiry (BankNifty - Last Tuesday)
        return _get_monthly_expiry(base_date, expiry_day)
    else:
        raise ValueError(f"Unknown expiry type: {expiry_type}")


def _get_weekly_expiry(base_date: datetime, day_name: str = "TUESDAY") -> str:
    """Get nearest weekly expiry (e.g., Nifty Tuesday)."""
    
    # Map day names to weekday numbers
    day_map = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4
    }
    
    target_weekday = day_map.get(day_name, 1)  # Default to Tuesday
    
    days_ahead = target_weekday - base_date.weekday()
    
    # If today is the target day and before 3:30 PM, use today
    # Otherwise, get next week
    if days_ahead == 0:
        if base_date.hour < 15 or (base_date.hour == 15 and base_date.minute < 30):
            return base_date.strftime("%Y-%m-%d")
        else:
            days_ahead = 7
    elif days_ahead < 0:
        days_ahead += 7
    
    next_expiry = base_date + timedelta(days=days_ahead)
    return next_expiry.strftime("%Y-%m-%d")


def _get_monthly_expiry(base_date: datetime, day_name: str = "LAST_TUESDAY") -> str:
    """
    Get last Tuesday of the current or next month (BankNifty monthly expiry).
    
    Args:
        base_date: Base date
        day_name: Should be "LAST_TUESDAY" for BankNifty
    
    Returns:
        Expiry date in YYYY-MM-DD format
    """
    # Map day names to weekday numbers
    day_map = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4
    }
    
    # For monthly, we always want Tuesday (1)
    target_weekday = 1  # Tuesday
    
    # Get last day of current month
    year = base_date.year
    month = base_date.month
    last_day_of_month = monthrange(year, month)[1]
    last_date = datetime(year, month, last_day_of_month)
    
    # Find last Tuesday of current month
    last_tuesday = last_date
    while last_tuesday.weekday() != target_weekday:
        last_tuesday -= timedelta(days=1)
    
    # Check if last Tuesday has passed or is today after 3:30 PM
    is_after_expiry = (
        base_date.date() > last_tuesday.date() or
        (base_date.date() == last_tuesday.date() and 
         (base_date.hour > 15 or (base_date.hour == 15 and base_date.minute >= 30)))
    )
    
    if is_after_expiry:
        # Get last Tuesday of next month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        last_day_next = monthrange(next_year, next_month)[1]
        last_date_next = datetime(next_year, next_month, last_day_next)
        
        last_tuesday = last_date_next
        while last_tuesday.weekday() != target_weekday:
            last_tuesday -= timedelta(days=1)
    
    return last_tuesday.strftime("%Y-%m-%d")


def calculate_position_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss: float
) -> int:
    """Calculate position size based on risk management."""
    risk_amount = capital * (risk_per_trade / 100)
    risk_per_unit = abs(entry_price - stop_loss)
    
    if risk_per_unit == 0:
        return 0
    
    position_size = int(risk_amount / risk_per_unit)
    return position_size


def format_price(price: float) -> str:
    """Format price for display."""
    return f"₹{price:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage for display."""
    return f"{value:+.2f}%"


def validate_market_hours() -> bool:
    """Check if current time is within market hours."""
    now = datetime.now()
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # Skip weekends
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    return market_open <= now <= market_close

def create_trade_record(setup: Dict, evaluation: Dict) -> Dict:
    """Create a standardized trade record with all relevant information."""
    from datetime import datetime
    risk_reward_ratio = setup.get("risk_reward_ratio") or setup.get("risk_reward")    
    return {
        "timestamp": datetime.now().isoformat(),
        "trade_id": f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        
        # Option details
        "symbol": setup.get("symbol", "NIFTY"),
        "strike": setup.get("selected_strike") or setup.get("strike"),
        "option_type": setup.get("option_type"),
        "expiry": setup.get("expiry"),
        "security_id": setup.get("security_id"),
        
        # Trade details - handle both field names
        "direction": setup.get("direction") or setup.get("option_type"),
        "entry_price": setup.get("entry_premium") or setup.get("entry_price"),
        "target_price": setup.get("target_premium") or setup.get("target_price"),
        "stop_loss": setup.get("stop_loss_premium") or setup.get("stop_loss"),
        "quantity": setup.get("quantity", 0),
        
        # Risk metrics
        "risk_reward_ratio": float(risk_reward_ratio) if risk_reward_ratio else 0.0,
        "risk_per_lot": setup.get("risk_amount"),
        "reward_per_lot": setup.get("reward_amount"),

        # LLM evaluation
        "probability": evaluation.get("probability_estimate", 0),
        "llm_reasoning": evaluation.get("reasoning", ""),
        "entry_confirmation": evaluation.get("entry_confirmation", ""),
        
        # Confluence
        "confluence": evaluation.get("confluence_count", 0),
        "confluence_score": evaluation.get("zone_confluence_score", 0),
        
        # Greeks
        "delta": setup.get("delta"),
        "theta": setup.get("theta"),
        "gamma": setup.get("gamma"),
        "vega": setup.get("vega"),
        
        # Status
        "status": "PENDING",
        "pnl": 0.0,
        "exit_price": None,
        "exit_time": None,
        "order_ids": {},
    }




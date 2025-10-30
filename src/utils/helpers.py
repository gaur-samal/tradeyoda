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


def create_trade_record(trade_setup: Dict, llm_evaluation: Dict) -> Dict:
    """Create a standardized trade record."""
    return {
        "timestamp": datetime.now(),
        "direction": trade_setup.get("direction"),
        "entry_price": trade_setup.get("entry_price"),
        "target_price": trade_setup.get("target_price"),
        "stop_loss": trade_setup.get("stop_loss"),
        "risk_reward": trade_setup.get("risk_reward"),
        "probability": llm_evaluation.get("probability_estimate"),
        "confidence": llm_evaluation.get("confidence_score"),
        "reasoning": llm_evaluation.get("reasoning"),
        "status": "PENDING",
        "pnl": 0.0,
    }


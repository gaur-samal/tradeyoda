"""Helper utilities."""
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd


def get_nearest_expiry(base_date: datetime = None) -> str:
        """
        Get nearest Tuesday expiry for Nifty options.
        
        Note: Nifty weekly options now expire on Tuesdays (changed from Thursday).
        
        Args:
            base_date: Base date to calculate from (default: current date)
        
        Returns:
            Expiry date in YYYY-MM-DD format
        """
        if base_date is None:
            base_date = datetime.now()

        # Tuesday = 1 (Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4)
        days_ahead = 1 - base_date.weekday()
        
        # If today is Tuesday and it's before 3:30 PM, use today
        # Otherwise, get next Tuesday
        if days_ahead == 0:
            # It's Tuesday today
            if base_date.hour < 15 or (base_date.hour == 15 and base_date.minute < 30):
                # Before expiry time, use today
                return base_date.strftime("%Y-%m-%d")
            else:
                # After expiry time, get next Tuesday
                days_ahead = 7
        elif days_ahead < 0:
            # If we're past Tuesday this week, get next Tuesday
            days_ahead += 7

        next_tuesday = base_date + timedelta(days=days_ahead)
        return next_tuesday.strftime("%Y-%m-%d")

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


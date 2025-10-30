"""Theta decay utilities using real Greeks from option chain."""
from datetime import datetime
from typing import Dict, Tuple
from src.utils.logger import log

class ThetaCalculator:
    """Manage theta decay analysis for options."""
    
    @staticmethod
    def calculate_days_to_expiry(expiry_date: str) -> float:
        """
        Calculate days to expiry (including fractional days).
        
        Args:
            expiry_date: Expiry in YYYY-MM-DD format
        
        Returns:
            Days to expiry as float
        """
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            expiry = expiry.replace(hour=15, minute=30)  # Market closes at 3:30 PM
            
            now = datetime.now()
            delta = expiry - now
            days = delta.total_seconds() / 86400
            
            return max(0, days)
            
        except Exception as e:
            log.error(f"Error calculating days to expiry: {e}")
            return 0
    
    @staticmethod
    def get_theta_metrics(
        theta_daily: float,
        premium: float
    ) -> Dict[str, float]:
        """
        Calculate theta metrics from daily theta.
        
        Args:
            theta_daily: Daily theta from Greeks (negative value)
            premium: Current option premium
        
        Returns:
            Dict with hourly theta and decay percentages
        """
        try:
            # Theta is typically negative (premium decay)
            # Convert to absolute for calculations
            theta_abs = abs(theta_daily)
            
            # Hourly theta (6.5 trading hours per day)
            theta_hourly = theta_abs / 6.5
            
            # Percentage decay
            decay_pct_daily = (theta_abs / premium * 100) if premium > 0 else 0
            decay_pct_hourly = decay_pct_daily / 6.5
            
            return {
                "theta_daily": -theta_abs,  # Keep negative
                "theta_hourly": -theta_hourly,  # Keep negative
                "theta_abs_daily": theta_abs,
                "theta_abs_hourly": theta_hourly,
                "decay_percentage_daily": decay_pct_daily,
                "decay_percentage_hourly": decay_pct_hourly
            }
            
        except Exception as e:
            log.error(f"Error calculating theta metrics: {e}")
            return {
                "theta_daily": 0,
                "theta_hourly": 0,
                "theta_abs_daily": 0,
                "theta_abs_hourly": 0,
                "decay_percentage_daily": 0,
                "decay_percentage_hourly": 0
            }
    
    @staticmethod
    def adjust_target_for_theta(
        entry_premium: float,
        target_premium: float,
        expected_hold_hours: float,
        theta_hourly: float
    ) -> float:
        """
        Adjust target price to account for theta decay.
        
        Args:
            entry_premium: Entry price
            target_premium: Initial target
            expected_hold_hours: Expected holding period (hours)
            theta_hourly: Hourly theta decay (negative value)
        
        Returns:
            Adjusted target premium
        """
        try:
            # Calculate expected decay during hold period
            expected_decay = abs(theta_hourly) * expected_hold_hours
            
            # Add decay to target to compensate
            adjusted_target = target_premium + expected_decay
            
            log.info(f"📉 Theta adjustment:")
            log.info(f"   Original target: ₹{target_premium:.2f}")
            log.info(f"   Expected decay ({expected_hold_hours}h): ₹{expected_decay:.2f}")
            log.info(f"   Adjusted target: ₹{adjusted_target:.2f}")
            
            return adjusted_target
            
        except Exception as e:
            log.error(f"Error adjusting target for theta: {e}")
            return target_premium
    
    @staticmethod
    def should_avoid_due_to_theta(
        premium: float,
        theta_hourly: float,
        expected_hold_hours: float,
        max_theta_impact: float = 5.0
    ) -> Tuple[bool, str]:
        """
        Check if option should be avoided due to excessive theta.
        
        Args:
            premium: Current premium
            theta_hourly: Hourly theta (negative value)
            expected_hold_hours: Expected hold time
            max_theta_impact: Maximum acceptable theta impact (%)
        
        Returns:
            (should_avoid, reason)
        """
        try:
            # Calculate total decay impact
            total_decay = abs(theta_hourly) * expected_hold_hours
            theta_impact_pct = (total_decay / premium * 100) if premium > 0 else 0
            
            if theta_impact_pct > max_theta_impact:
                reason = f"Theta impact too high: {theta_impact_pct:.1f}% (max: {max_theta_impact}%)"
                return (True, reason)
            
            return (False, "")
            
        except Exception as e:
            log.error(f"Error checking theta impact: {e}")
            return (False, "")
    
    @staticmethod
    def get_theta_quality_score(
        theta_daily: float,
        premium: float,
        delta: float
    ) -> float:
        """
        Calculate a quality score based on theta vs delta.
        Better for options with good delta/theta ratio.
        
        Args:
            theta_daily: Daily theta
            premium: Current premium
            delta: Option delta
        
        Returns:
            Quality score (0-100, higher is better)
        """
        try:
            theta_abs = abs(theta_daily)
            delta_abs = abs(delta)
            
            # Avoid division by zero
            if theta_abs == 0 or premium == 0:
                return 50  # Neutral score
            
            # Theta as percentage of premium
            theta_pct = (theta_abs / premium) * 100
            
            # Good: High delta, low theta percentage
            # Bad: Low delta, high theta percentage
            
            # Delta score (higher is better)
            delta_score = min(delta_abs * 100, 50)  # Max 50 points
            
            # Theta score (lower theta % is better)
            theta_score = max(0, 50 - (theta_pct * 5))  # Max 50 points
            
            total_score = delta_score + theta_score
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            log.error(f"Error calculating theta quality score: {e}")
            return 50


# Global instance
theta_calculator = ThetaCalculator()


"""
Feature gating middleware for TradeYoda backend.
Blocks access to endpoints based on license tier.
"""
from fastapi import HTTPException, Request
from src.config import config

def check_manual_trading_feature():
    """Check if manual trading is allowed for current license tier."""
    if not config.FEATURE_MANUAL_TRADING:
        raise HTTPException(
            status_code=403,
            detail=f"Manual trading not available in {config.LICENSE_TIER} tier. Please upgrade to ADVANCED or PRO."
        )

def check_auto_trading_feature():
    """Check if auto trading is allowed for current license tier."""
    if not config.FEATURE_AUTO_TRADING:
        raise HTTPException(
            status_code=403,
            detail=f"Auto trading not available in {config.LICENSE_TIER} tier. Please upgrade to PRO."
        )

async def license_gate_middleware(request: Request, call_next):
    """
    Middleware to check license requirements for protected endpoints.
    """
    path = request.url.path
    
    # Endpoints that require manual trading
    manual_trading_endpoints = [
        "/api/run-trade-identification",
        "/api/execute-manual-trade",  # If you have this
        # Add other manual trading endpoints here
    ]
    
    # Endpoints that require auto trading
    auto_trading_endpoints = [
        "/api/start-continuous",
        # Add other auto trading endpoints here
    ]
    
    # Check manual trading endpoints
    if any(path.startswith(endpoint) for endpoint in manual_trading_endpoints):
        if not config.FEATURE_MANUAL_TRADING:
            return {
                "success": False,
                "error": f"Manual trading not available in {config.LICENSE_TIER} tier",
                "tier": config.LICENSE_TIER,
                "upgrade_required": True
            }
    
    # Check auto trading endpoints
    if any(path.startswith(endpoint) for endpoint in auto_trading_endpoints):
        if not config.FEATURE_AUTO_TRADING:
            return {
                "success": False,
                "error": f"Auto trading not available in {config.LICENSE_TIER} tier",
                "tier": config.LICENSE_TIER,
                "upgrade_required": True
            }
    
    # Proceed with request
    response = await call_next(request)
    return response

"""
Trade Yoda - FastAPI Backend
Production-ready API server for AI trading system
"""
from fastapi import FastAPI, HTTPException, WebSocket, Request, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import TradingOrchestrator
from src.config import config
from src.config import Config
from src.utils.logger import log
from src.utils.credentials_store import credentials_store
from middleware import check_auto_trading_feature,check_manual_trading_feature
# ===== LOAD STORED CREDENTIALS (after logger is initialized) =====
config.load_dhan_credentials()

# ===== VALIDATE LICENSE (Fetch OpenAI key from licensing server) =====
try:
    config.validate_license()
except Exception as e:
    log.warning(f"⚠️ License validation failed: {e}")
    log.warning("⚠️ Running in development mode without licensing")

# Global orchestrator instance
orchestrator: Optional[TradingOrchestrator] = None
active_websockets: List[WebSocket] = []

# Rate limiting cache
_api_call_cache = {}
_min_api_interval = 2.0  # Minimum 2 seconds between calls


uvicorn_logger = logging.getLogger("uvicorn.access")

async def rate_limit_check(api_name: str, min_interval: float = 2.0):
    """Check and enforce rate limiting."""
    last_call = _api_call_cache.get(api_name)

    if last_call:
        elapsed = (datetime.now() - last_call).total_seconds()
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            await asyncio.sleep(wait_time)

    _api_call_cache[api_name] = datetime.now()



# ==================== UTILITY FUNCTIONS ====================

def clean_json_data(obj):
    """
    Recursively clean data for JSON serialization.
    Handles NaN, inf, datetime, numpy types, and pandas objects.
    """
    if isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    elif isinstance(obj, datetime):
        return obj.isoformat()
    
    elif isinstance(obj, pd.Series):
        return [clean_json_data(x) for x in obj.tolist()]
    
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    
    elif isinstance(obj, dict):
        return {k: clean_json_data(v) for k, v in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        return [clean_json_data(item) for item in obj]
    
    return obj

# ==================== LIFECYCLE MANAGEMENT ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    global orchestrator
    log.info("🚀 Starting Trade Yoda API Server...")
    
    # Startup
    try:
        orchestrator = TradingOrchestrator(config)
        log.info("✅ Orchestrator initialized")
    except Exception as e:
        log.error(f"❌ Failed to initialize orchestrator: {e}")
        raise
    
    yield
    
    # Shutdown
    log.info("🛑 Shutting down Trade Yoda API Server...")
    if orchestrator and orchestrator.is_running:
        orchestrator.shutdown()
    log.info("✅ Shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Trade Yoda API",
    description="AI-Powered Trading System for Nifty 50 Futures & Options",
    version="1.0.0",
    lifespan=lifespan
)

# ===== SUPPRESS FREQUENT ENDPOINT LOGS (BETTER METHOD) =====
class QuietEndpointFilter(logging.Filter):
    """Suppress logs for frequently polled endpoints."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Return False to suppress the log."""
        message = record.getMessage()

        # List of paths to suppress
        quiet_paths = [
            "/api/market/live-price",
            "/api/status",
            "/api/trades/active",
            "/api/pnl/total",
            "/api/monitoring-status",
            "/health"
        ]

        # Suppress if message contains any quiet path
        for path in quiet_paths:
            if path in message:
                return False  # Don't log

        return True  # Log normally

# Apply filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(QuietEndpointFilter())

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_running": orchestrator.is_running if orchestrator else False
    }

# ==================== SYSTEM ENDPOINTS ====================

@app.get("/api/status")
async def get_status():
    """Get system status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    is_expiry = config.is_expiry_day()
    instrument = config.get_active_instrument()
    return {
        "running": orchestrator.is_running,
        "active_trades": len([t for t in orchestrator.active_trades if t.get('status') == 'ACTIVE']),
        "total_trades": len(orchestrator.active_trades),
        "analysis_available": orchestrator.analysis_cache is not None,
        "instrument": instrument["name"],
        "is_expiry_day": is_expiry,
        "no_trades_on_expiry": config.NO_TRADES_ON_EXPIRY,
        "trading_blocked": is_expiry and config.NO_TRADES_ON_EXPIRY,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/monitoring-status")
async def get_monitoring_status():
    """Get continuous monitoring status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    continuous_active = orchestrator.monitoring_task and not orchestrator.monitoring_task.done()
    
    return {
        "running": orchestrator.is_running,
        "continuous_mode": continuous_active,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/start")
async def start_trading():
    """Start the trading system."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        if orchestrator.is_running:
            return {"success": False, "message": "Already running"}
        
        orchestrator.start()
        log.info("✅ Trading system started via API")
        
        # Notify all connected WebSocket clients
        await broadcast_message({
            "type": "system_status",
            "data": {"running": True, "message": "Trade Yoda activated!"}
        })
        
        return {"success": True, "message": "Trade Yoda activated!"}
    except Exception as e:
        log.error(f"Failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_trading():
    """Stop the trading system."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        orchestrator.shutdown()
        log.info("⚠️ Trading system stopped via API")
        
        # Notify all connected WebSocket clients
        await broadcast_message({
            "type": "system_status",
            "data": {"running": False, "message": "Trade Yoda deactivated"}
        })
        
        return {"success": True, "message": "Trade Yoda deactivated"}
    except Exception as e:
        log.error(f"Failed to stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#==============FUTURES STATUS CHECK===================
@app.get("/api/futures/status")
async def get_futures_status():
    """Get current futures contract status."""
    try:
        from src.utils.security_master import security_master

        # Get both Nifty and BankNifty futures
        nifty_futures = security_master.get_current_futures_contract("NIFTY")
        banknifty_futures = security_master.get_current_futures_contract("BANKNIFTY")

        return {
            "nifty": {
                "contract_name": nifty_futures['contract_name'] if nifty_futures else None,
                "security_id": nifty_futures['security_id'] if nifty_futures else None,
                "expiry_date": nifty_futures['expiry_date'].isoformat() if nifty_futures else None,
                "days_to_expiry": (nifty_futures['expiry_date'] - datetime.now()).days if nifty_futures else None
            },
            "banknifty": {
                "contract_name": banknifty_futures['contract_name'] if banknifty_futures else None,
                "security_id": banknifty_futures['security_id'] if banknifty_futures else None,
                "expiry_date": banknifty_futures['expiry_date'].isoformat() if banknifty_futures else None,
                "days_to_expiry": (banknifty_futures['expiry_date'] - datetime.now()).days if banknifty_futures else None
            }
        }
    except Exception as e:
        log.error(f"Error getting futures status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


#==============CONTINOUS MONITORING===================
@app.post("/api/start-continuous")
async def start_continuous_monitoring():
    """Start continuous automated trading."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    # ===== FEATURE GATE: Auto Trading =====
    check_auto_trading_feature() 
    try:
        if not orchestrator.is_running:
            orchestrator.start()
        
        # Start continuous monitoring in background
        if not orchestrator.monitoring_task or orchestrator.monitoring_task.done():
            orchestrator.monitoring_task = asyncio.create_task(
                orchestrator.run_continuous_monitoring()
            )
            log.info("✅ Continuous monitoring started")
            
            # Notify WebSocket clients
            await broadcast_message({
                "type": "continuous_monitoring",
                "data": {"active": True, "message": "Continuous monitoring activated"}
            })
            
            return {
                "success": True,
                "message": "Continuous monitoring activated. System will auto-trade based on zones."
            }
        else:
            return {
                "success": False,
                "message": "Continuous monitoring already running"
            }
            
    except Exception as e:
        log.error(f"Failed to start continuous monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop-continuous")
async def stop_continuous_monitoring():
    """Stop continuous automated trading."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        orchestrator.is_running = False
        
        if orchestrator.monitoring_task:
            orchestrator.monitoring_task.cancel()
            log.info("⚠️ Continuous monitoring stopped")
        
        # Notify WebSocket clients
        await broadcast_message({
            "type": "continuous_monitoring",
            "data": {"active": False, "message": "Continuous monitoring stopped"}
        })
        
        return {
            "success": True,
            "message": "Continuous monitoring stopped"
        }
        
    except Exception as e:
        log.error(f"Failed to stop continuous monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANALYSIS ENDPOINTS ====================
@app.post("/api/run-zone-analysis")
async def run_zone_analysis():
    """Run zone analysis."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        log.info(f"🔍 Running zone analysis")
        result = await orchestrator.run_zone_identification_cycle()
        
        if result:
            result = clean_json_data(result)
            
            await broadcast_message({
                "type": "zone_analysis_complete",
                "data": result
            })
            return {"success": True, "data": result}
        else:
            # Better message when no result
            return {
                "success": False, 
                "message": "Zone analysis could not be completed. Check if market is open (9:15 AM - 3:30 PM IST, Mon-Fri)"
            }
    except Exception as e:
        log.error(f"Zone analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run-trade-identification")
async def run_trade_identification():
    """Run 3-minute trade identification cycle."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    # ===== FEATURE GATE: Manual Trading =====
    check_manual_trading_feature() 
    try:
        log.info("🎯 Running trade identification via API...")
        result = await orchestrator.run_trade_identification_cycle()
        
        if result:
            # Clean result before broadcasting and returning
            result = clean_json_data(result)
            
            # Notify WebSocket clients
            await broadcast_message({
                "type": "trade_identified",
                "data": result
            })
            return {"success": True, "data": result}
        else:
            return {"success": False, "message": "No trade opportunities found"}
    except Exception as e:
        log.error(f"Trade identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis")
async def get_analysis():
    """Get latest analysis cache."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if not orchestrator.analysis_cache:
        raise HTTPException(
            status_code=404, 
            detail="No analysis available. Please run zone analysis first."
        )
    
    # Clean and return cache
    cache = clean_json_data(orchestrator.analysis_cache.copy())
    return cache

# ==================== TRADING ENDPOINTS ====================

@app.get("/api/trades")
async def get_trades():
    """Get all trades."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    trades = orchestrator.get_active_trades()
    
    # Clean and return trades
    trades = clean_json_data(trades)
    return {"trades": trades, "count": len(trades)}


@app.get("/api/trades/active")
async def get_active_trades():
    """Get active trades from Dhan (live) or memory (paper)."""
    try:
        if not orchestrator:
            return {"trades": [], "mode": "none"}

        trades = orchestrator.get_active_trades()
        mode = "paper" if orchestrator.config.USE_SANDBOX else "live"

        return {
            "trades": trades,
            "mode": mode,
            "count": len(trades)
        }
    except Exception as e:
        log.error(f"Get active trades error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pnl/total")
async def get_total_pnl():
    """Get total P&L from Dhan."""
    try:
        if not orchestrator:
            return {"total_pnl": 0}

        pnl_data = orchestrator.get_total_pnl()
        return pnl_data
    except Exception as e:
        log.error(f"Get P&L error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get all positions from Dhan."""
    try:
        if not orchestrator:
            return {"positions": []}
        
        if orchestrator.config.USE_SANDBOX:
            return {
                "positions": [],
                "message": "Paper trading mode - no real positions"
            }
        
        positions = orchestrator.data_agent.get_positions()
        return positions
    except Exception as e:
        log.error(f"Get positions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders")
async def get_orders():
    """Get all orders from Dhan."""
    try:
        if not orchestrator:
            return {"orders": []}
        
        if orchestrator.config.USE_SANDBOX:
            return {
                "orders": [],
                "message": "Paper trading mode - no real orders"
            }
        
        orders = orchestrator.data_agent.get_orders()
        return orders
    except Exception as e:
        log.error(f"Get orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/statistics")
async def get_trade_statistics():
    """Get trading statistics."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    trades = orchestrator.get_active_trades()
    
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0
        }
    
    winning = [t for t in trades if t.get('pnl', 0) > 0]
    losing = [t for t in trades if t.get('pnl', 0) < 0]
    
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    avg_win = sum(t['pnl'] for t in winning) / len(winning) if winning else 0
    avg_loss = sum(t['pnl'] for t in losing) / len(losing) if losing else 0
    
    total_wins_pnl = sum(t['pnl'] for t in winning)
    total_loss_pnl = abs(sum(t['pnl'] for t in losing))
    profit_factor = total_wins_pnl / total_loss_pnl if total_loss_pnl > 0 else 0
    
    return {
        "total_trades": len(trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": (len(winning) / len(trades) * 100) if trades else 0,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor
    }

# ==================== MARKET DATA ENDPOINTS ====================

@app.get("/api/market/live-price")
async def get_live_price():
    """Get live price for active instrument with market status."""
    try:
        # ===== RATE LIMIT: 2 seconds minimum =====
        await rate_limit_check("market_quotes", min_interval=2.0)
        if not orchestrator:
            return {
                "success": False,
                "message": "System not initialized"
            }

        # Get active instrument config
        instrument = config.get_active_instrument()

        # ===== CHECK MARKET HOURS =====
        from src.utils.helpers import validate_market_hours
        is_market_open = validate_market_hours()

        # Fetch live quote
        quotes = orchestrator.data_agent.fetch_market_quotes(
            securities=[config.NIFTY_FUTURES_SECURITY_ID],
            exchange_segment=config.NIFTY_FUTURES_EXCHANGE
        )

        live_quote = quotes.get(str(config.NIFTY_FUTURES_SECURITY_ID), {})
        price = live_quote.get("LTP")

        if not price:
            # Return cached price if available
            if orchestrator.analysis_cache and "current_price" in orchestrator.analysis_cache:
                cached_price = orchestrator.analysis_cache["current_price"]
                cached_time = orchestrator.analysis_cache.get("timestamp", datetime.now())

                return {
                    "success": True,
                    "price": float(cached_price),
                    "instrument": instrument["name"],
                    "symbol": instrument["symbol"],
                    "lot_size": instrument["lot_size"],
                    "timestamp": cached_time.isoformat() if isinstance(cached_time, datetime) else cached_time,
                    "cached": True,
                    "market_open": is_market_open,
                    "market_status": "OPEN" if is_market_open else "CLOSED",
                    "message": "Market closed - showing last cached price"
                }

            return {
                "success": False,
                "message": "No price data available (market closed or system not running)",
                "market_open": is_market_open,
                "market_status": "CLOSED"
            }

        return {
            "success": True,
            "price": float(price),
            "instrument": instrument["name"],
            "symbol": instrument["symbol"],
            "lot_size": instrument["lot_size"],
            "timestamp": datetime.now().isoformat(),
            "cached": False,
            "market_open": is_market_open,
            "market_status": "OPEN" if is_market_open else "CLOSED"
        }

    except Exception as e:
        log.error(f"Live price API error: {e}")
        import traceback
        log.error(traceback.format_exc())

        return {
            "success": False,
            "message": f"Error fetching live price: {str(e)}",
            "market_open": False,
            "market_status": "ERROR"
        }


@app.get("/api/market/active-instrument")
async def get_active_instrument():
    """Get active instrument details."""
    try:
        instrument = config.get_active_instrument()
        
        return {
            "success": True,
            "name": instrument["name"],
            "symbol": instrument["symbol"],
            "lot_size": instrument["lot_size"],
            "expiry_type": instrument["expiry_type"],
            "expiry_day": instrument["expiry_day"],
            "security_id": config.NIFTY_FUTURES_SECURITY_ID,
            "exchange": config.NIFTY_FUTURES_EXCHANGE
        }
        
    except Exception as e:
        log.error(f"Active instrument API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ==================== CONFIGURATION ENDPOINTS ====================

@app.get("/api/config")
async def get_config():
    """Get current configuration (safe fields only)."""
    dhan_client_id = config.DHAN_CLIENT_ID
    dhan_access_token = config.DHAN_ACCESS_TOKEN
    # Get active instrument config
    instrument = config.get_active_instrument()
    return {
        # ===== Include selected_instrument =====
        "selected_instrument": config.SELECTED_INSTRUMENT,
        
        # Include full instrument details for display
        "instrument_config": {
            "symbol": instrument["symbol"],
            "name": instrument["name"],
            "expiry_type": instrument["expiry_type"],
            "expiry_day": instrument["expiry_day"],
            "lot_size": instrument["lot_size"]
        },
        # Trading params
        "use_sandbox": config.USE_SANDBOX,
        "risk_reward_ratio": config.RISK_REWARD_RATIO,
        "max_risk_percentage": config.MAX_RISK_PERCENTAGE,
        "min_probability_threshold": config.MIN_PROBABILITY_THRESHOLD,
        "zone_timeframe": config.ZONE_TIMEFRAME,
        "trade_timeframe": config.TRADE_TIMEFRAME,
        
        # Dhan credentials (masked for display, but preserve for editing)
        "dhan_client_id": dhan_client_id if dhan_client_id else "",
        "dhan_access_token": "",  # Never send token back for security
        "dhan_configured": bool(dhan_client_id and dhan_access_token),

        # RSI settings
        "rsi_period": getattr(config, 'RSI_PERIOD', 14),
        "rsi_overbought": getattr(config, 'RSI_OVERBOUGHT', 70),
        "rsi_oversold": getattr(config, 'RSI_OVERSOLD', 30),
        
        # Bollinger Bands settings
        "bb_period": getattr(config, 'BB_PERIOD', 20),
        "bb_std_dev": getattr(config, 'BB_STD_DEV', 2.0),
        
        # Pattern detection
        "enable_candlestick_patterns": getattr(config, 'ENABLE_CANDLESTICK_PATTERNS', True),
        "enable_chart_patterns": getattr(config, 'ENABLE_CHART_PATTERNS', True),
        
        # Experimental Features
        "use_backtest_mode": getattr(config, 'USE_BACKTEST_MODE', False),
        "backtest_from": str(getattr(config, 'BACKTEST_FROM', '')) if hasattr(config, 'BACKTEST_FROM') else None,
        "backtest_to": str(getattr(config, 'BACKTEST_TO', '')) if hasattr(config, 'BACKTEST_TO') else None,
        "no_trades_on_expiry": getattr(config, 'NO_TRADES_ON_EXPIRY', True),
        "order_quantity": getattr(config, 'ORDER_QUANTITY', 50),
        "use_super_order": getattr(config, 'USE_SUPER_ORDER', True),
    }

@app.post("/api/config/update")
async def update_config(updates: dict):
    """Update configuration dynamically (runtime only, not saved to .env)."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        updated_fields = []
        # ===== Instrument Selection =====
        if "selected_instrument" in updates:
            instrument = updates["selected_instrument"]
            if instrument in ["NIFTY", "BANKNIFTY"]:
                Config.SELECTED_INSTRUMENT = instrument 
                config.SELECTED_INSTRUMENT = instrument
                updated_fields.append("selected_instrument")
                log.info(f"✅ Switched to {instrument}")
            else:
                raise HTTPException(status_code=400, detail="Invalid instrument") 
        # Update trading parameters
        if "risk_reward_ratio" in updates:
            config.RISK_REWARD_RATIO = float(updates["risk_reward_ratio"])
            updated_fields.append("risk_reward_ratio")
        
        if "max_risk_percentage" in updates:
            config.MAX_RISK_PERCENTAGE = float(updates["max_risk_percentage"])
            updated_fields.append("max_risk_percentage")
        
        if "min_probability_threshold" in updates:
            config.MIN_PROBABILITY_THRESHOLD = float(updates["min_probability_threshold"])
            updated_fields.append("min_probability_threshold")
        
        # Update experimental features
        if "use_backtest_mode" in updates:
            config.USE_BACKTEST_MODE = bool(updates["use_backtest_mode"])
            updated_fields.append("use_backtest_mode")
        
        if "backtest_from" in updates:
            config.BACKTEST_FROM = updates["backtest_from"]
            updated_fields.append("backtest_from")
        
        if "backtest_to" in updates:
            config.BACKTEST_TO = updates["backtest_to"]
            updated_fields.append("backtest_to")
        
        if "no_trades_on_expiry" in updates:
            config.NO_TRADES_ON_EXPIRY = bool(updates["no_trades_on_expiry"])
            updated_fields.append("no_trades_on_expiry")
        
        if "order_quantity" in updates:
            config.ORDER_QUANTITY = int(updates["order_quantity"])
            updated_fields.append("order_quantity")
        
        if "use_super_order" in updates:
            config.USE_SUPER_ORDER = bool(updates["use_super_order"])
            updated_fields.append("use_super_order")
        
        if "use_sandbox" in updates:
            config.USE_SANDBOX = bool(updates["use_sandbox"])
            updated_fields.append("use_sandbox")
        
        # Update RSI settings
        if "rsi_period" in updates:
            config.RSI_PERIOD = int(updates["rsi_period"])
            updated_fields.append("rsi_period")
        
        if "rsi_overbought" in updates:
            config.RSI_OVERBOUGHT = float(updates["rsi_overbought"])
            updated_fields.append("rsi_overbought")
        
        if "rsi_oversold" in updates:
            config.RSI_OVERSOLD = float(updates["rsi_oversold"])
            updated_fields.append("rsi_oversold")
        
        # Update Bollinger Bands settings
        if "bb_period" in updates:
            config.BB_PERIOD = int(updates["bb_period"])
            updated_fields.append("bb_period")
        
        if "bb_std_dev" in updates:
            config.BB_STD_DEV = float(updates["bb_std_dev"])
            updated_fields.append("bb_std_dev")
        
        # Update pattern detection
        if "enable_candlestick_patterns" in updates:
            config.ENABLE_CANDLESTICK_PATTERNS = bool(updates["enable_candlestick_patterns"])
            updated_fields.append("enable_candlestick_patterns")
        
        if "enable_chart_patterns" in updates:
            config.ENABLE_CHART_PATTERNS = bool(updates["enable_chart_patterns"])
            updated_fields.append("enable_chart_patterns")
        
        log.info(f"✅ Configuration updated: {', '.join(updated_fields)}")
        
        # Notify WebSocket clients
        await broadcast_message({
            "type": "config_updated",
            "data": {
                "updated_fields": updated_fields,
                "message": "Configuration updated successfully"
            }
        })
        
        return {
            "success": True,
            "updated_fields": updated_fields,
            "message": "Configuration updated successfully. Changes are active immediately."
        }
        
    except Exception as e:
        log.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INSTRUMENT SELECTION  ======================
@app.post("/api/config/switch-instrument")
async def switch_instrument(instrument_data: dict):
    """Switch trading instrument (requires system restart)."""
    try:
        instrument = instrument_data.get("instrument", "NIFTY")

        if instrument not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid instrument")

        config.SELECTED_INSTRUMENT = instrument

        log.info(f"🔄 Switched to {instrument}")

        return {
            "success": True,
            "instrument": instrument,
            "config": config.get_active_instrument(),
            "message": f"Switched to {instrument}. Please restart the system."
        }

    except Exception as e:
        log.error(f"Failed to switch instrument: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/instruments")
async def get_available_instruments():
    """Get list of available instruments."""
    return {
        "instruments": [
            {
                "id": "NIFTY",
                "name": "Nifty 50",
                "expiry": "Weekly (Tuesday)",
                "lot_size": 25
            },
            {
                "id": "BANKNIFTY",
                "name": "Bank Nifty",
                "expiry": "Monthly (Last Tuesday)",
                "lot_size": 15
            }
        ],
        "active": config.SELECTED_INSTRUMENT
    }


# ==================== DHAN CREDENTIALS (FIXED) ====================

@app.get("/api/dhan/credentials")
async def get_dhan_credentials():
    """Get Dhan credentials status (masked)."""
    return {
        "client_id": config.DHAN_CLIENT_ID[:4] + "****" if config.DHAN_CLIENT_ID else None,
        "access_token": "****" + config.DHAN_ACCESS_TOKEN[-4:] if config.DHAN_ACCESS_TOKEN else None,
        "configured": bool(config.DHAN_CLIENT_ID and config.DHAN_ACCESS_TOKEN),
        "connected": bool(orchestrator and orchestrator.data_agent and orchestrator.data_agent.dhan)
    }

@app.post("/api/dhan/credentials")
async def update_dhan_credentials(credentials: dict):
    """Update Dhan credentials and reinitialize connections."""
    try:
        client_id = credentials.get("client_id", "").strip()
        access_token = credentials.get("access_token", "").strip()

        if not client_id or not access_token:
            raise HTTPException(
                status_code=400,
                detail="Both Client ID and Access Token are required"
            )

        # Update config
        config.DHAN_CLIENT_ID = client_id
        config.DHAN_ACCESS_TOKEN = access_token
        # ===== SAVE TO PERSISTENT STORE =====
        credentials_store.save_dhan_credentials(client_id, access_token)
        log.info("🔐 Updating Dhan credentials...")
        
        log.info("✅ Credentials saved to persistent storage")

        # CRITICAL: Reinitialize orchestrator's Dhan connections
        if orchestrator:
            from dhanhq import dhanhq, DhanContext

            # Create new context
            new_context = DhanContext(client_id, access_token)

            # Update orchestrator
            orchestrator.dhan_context = new_context

            # Reinitialize data agent
            if orchestrator.data_agent:
                orchestrator.data_agent.dhan_context = new_context
                orchestrator.data_agent.dhan = dhanhq(new_context)
                log.info("✅ Data agent updated with new credentials")

            # Reinitialize execution agent
            if orchestrator.execution_agent:
                orchestrator.execution_agent.dhan_context = new_context
                orchestrator.execution_agent.dhan = dhanhq(new_context)
                log.info("✅ Execution agent updated with new credentials")

            log.info("✅ Dhan credentials updated successfully across all agents")

        
        # Notify WebSocket clients
        await broadcast_message({
            "type": "dhan_credentials_updated",
            "data": {
                "success": True,
                "message": "Dhan credentials updated successfully"
            }
        })

        return {
            "success": True,
            "message": "Dhan credentials updated successfully. All connections reinitialized.",
            "configured": True
        }

    except Exception as e:
        log.error(f"Failed to update Dhan credentials: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dhan/credential-source")
async def get_credential_source():
    """Check where Dhan credentials are loaded from."""
    from src.utils.credentials_store import credentials_store

    stored_creds = credentials_store.get_dhan_credentials()

    return {
        "has_stored_credentials": stored_creds is not None,
        "current_client_id": config.DHAN_CLIENT_ID[:4] + "****" if config.DHAN_CLIENT_ID else "Not set",
        "source": "persistent_storage" if stored_creds else "env_file"
    }


@app.post("/api/dhan/test")
async def test_dhan_connection():
    """Test Dhan API connection with current credentials."""
    try:
        if not config.DHAN_CLIENT_ID or not config.DHAN_ACCESS_TOKEN:
            return {
                "success": False,
                "message": "Dhan credentials not configured. Please enter Client ID and Access Token."
            }

        # Use v2.1.0 API with DhanContext
        from dhanhq import dhanhq, DhanContext

        log.info("🔍 Testing Dhan connection...")

        # Create context and client
        context = DhanContext(config.DHAN_CLIENT_ID, config.DHAN_ACCESS_TOKEN)
        dhan = dhanhq(context)

        # Test with Nifty index quote
        result = dhan.ticker_data(securities={"IDX_I": [13]})

        log.info(f"Test result: {result}")

        if result and result.get("status") == "success":
            log.info("✅ Dhan connection test successful")
            return {
                "success": True,
                "message": "✅ Connection successful! Dhan API is working perfectly.",
                "details": "Successfully fetched market data."
            }
        else:
            error_msg = result.get("remarks", {}).get("error_message", "Unknown error")
            log.error(f"❌ Dhan connection test failed: {error_msg}")
            return {
                "success": False,
                "message": f"❌ Connection failed: {error_msg}",
                "details": "Please check your Client ID and Access Token."
            }

    except Exception as e:
        error_str = str(e)
        log.error(f"❌ Dhan connection test exception: {error_str}")

        # Better error messages
        if "401" in error_str or "Unauthorized" in error_str:
            message = "❌ Authentication failed. Your Access Token may have expired (tokens expire every 24 hours)."
        elif "403" in error_str or "Forbidden" in error_str:
            message = "❌ Access denied. Please check your Client ID."
        elif "Network" in error_str or "timeout" in error_str:
            message = "❌ Network error. Please check your internet connection."
        else:
            message = f"❌ Connection failed: {error_str}"

        return {
            "success": False,
            "message": message,
            "details": str(e)
        }

# ==================== LOGGING ENDPOINT  ====================
from src.utils.logger import logger

@app.post("/api/admin/log-level")
async def set_log_level(request: dict):
    """
    Dynamically change log level without restart.

    Body: {"level": "DEBUG" | "INFO" | "WARNING" | "ERROR"}
    """
    try:
        level = request.get("level", "INFO").upper()

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid level. Choose from: {valid_levels}")

        # Remove existing handlers
        logger.remove()

        # Add new handler with specified level
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )

        # File handler (always DEBUG)
        logger.add(
            "logs/tradeyoda_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

        log.info(f"✅ Log level changed to: {level}")

        return {
            "success": True,
            "level": level,
            "message": f"Log level changed to {level}"
        }

    except Exception as e:
        log.error(f"Failed to change log level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/log-level")
async def get_log_level():
    """Get current log level."""
    # Get the first handler's level
    try:
        import logging
        current_level = logging.getLevelName(logger._core.min_level)

        return {
            "success": True,
            "level": current_level,
            "available_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== WEBSOCKET ENDPOINT ====================

async def broadcast_message(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    disconnected = []
    for websocket in active_websockets:
        try:
            await websocket.send_json(message)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        if ws in active_websockets:
            active_websockets.remove(ws)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_websockets.append(websocket)
    log.info(f"📡 WebSocket client connected. Total clients: {len(active_websockets)}")
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connected to Trade Yoda",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for messages from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                
                # Handle client messages
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send live data update every 5 seconds
                if orchestrator and orchestrator.data_agent:
                    futures_id = str(config.NIFTY_FUTURES_SECURITY_ID)
                    live_data = orchestrator.data_agent.latest_data.get(futures_id, {})
                    
                    if live_data:
                        await websocket.send_json({
                            "type": "live_price_update",
                            "data": {
                                "ltp": live_data.get('LTP'),
                                "high": live_data.get('high'),
                                "low": live_data.get('low'),
                                "volume": live_data.get('volume'),
                                "timestamp": datetime.now().isoformat()
                            }
                        })
                
    except WebSocketDisconnect:
        log.info("📡 WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        log.info(f"📡 WebSocket clients remaining: {len(active_websockets)}")

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    log.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

# ==================== LICENSE MANAGEMENT ====================

@app.get("/api/license/status")
async def get_license_status():
    """Get current license status."""
    try:
        from src.utils.licensing_client import licensing_client

        tier_info = licensing_client.get_tier_info()

        return {
            "success": True,
            "licensed": config.LICENSE_VALID,
            "tier": config.LICENSE_TIER,
            "features": config.LICENSE_FEATURES,
            "openai_model": config.OPENAI_MODEL,
            "manual_trading_enabled": config.FEATURE_MANUAL_TRADING,
            "auto_trading_enabled": config.FEATURE_AUTO_TRADING,
            "expires_at": tier_info.get("expires_at")
        }
    except Exception as e:
        log.error(f"Error getting license status: {e}")
        return {
            "success": False,
            "licensed": False,
            "tier": "NONE",
            "error": str(e)
        }

@app.post("/api/license/activate")
async def activate_license(request: dict):
    """Activate a license key."""
    try:
        from src.utils.licensing_client import licensing_client

        license_key = request.get("license_key", "").strip()

        if not license_key:
            raise HTTPException(status_code=400, detail="License key is required")

        # Activate license
        result = licensing_client.activate_license(license_key)

        if result.get("success"):
            # Reload license configuration
            config.validate_license()

            return {
                "success": True,
                "message": "License activated successfully",
                "tier": config.LICENSE_TIER,
                "features": config.LICENSE_FEATURES
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Activation failed")
            }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"License activation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/license/validate")
async def revalidate_license():
    """Force revalidation of license (bypasses cache)."""
    try:
        from src.utils.licensing_client import licensing_client
        # CRITICAL: Clear cache before revalidation
        log.info(f"🗑️ Clearing cache for fresh validation")
        licensing_client.clear_cache()

        # Force validation without cache
        result = licensing_client.validate_license(use_cache=False)

        if result.get("success"):
            # Reload configuration
            log.info(f"✅ License activated, fetching fresh validation(NO CACHE)")
            config.validate_license(use_cache=False)

            return {
                "success": True,
                "message": "License revalidated successfully",
                "tier": config.LICENSE_TIER,
                "features": config.LICENSE_FEATURES
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Validation failed")
            }

    except Exception as e:
        log.error(f"License validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STARTUP MESSAGE ====================

if __name__ == "__main__":
    import uvicorn
    
    log.info("="*60)
    log.info("🧙‍♂️ Trade Yoda API Server")
    log.info("Powered by NeuralVectors Technologies LLP")
    log.info("="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


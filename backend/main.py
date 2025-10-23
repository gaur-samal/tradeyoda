"""
Trade Yoda - FastAPI Backend
Production-ready API server for AI trading system
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import sys
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
from src.utils.logger import log

# Global orchestrator instance
orchestrator: Optional[TradingOrchestrator] = None
active_websockets: List[WebSocket] = []

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
    
    return {
        "running": orchestrator.is_running,
        "active_trades": len([t for t in orchestrator.active_trades if t.get('status') == 'ACTIVE']),
        "total_trades": len(orchestrator.active_trades),
        "analysis_available": orchestrator.analysis_cache is not None,
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
#==============CONTINOUS MONITORING===================
@app.post("/api/start-continuous")
async def start_continuous_monitoring():
    """Start continuous automated trading."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
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
    """Get only active trades."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    all_trades = orchestrator.get_active_trades()
    active_trades = [t for t in all_trades if t.get('status') == 'ACTIVE']
    
    # Clean and return
    active_trades = clean_json_data(active_trades)
    return {"trades": active_trades, "count": len(active_trades)}

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
    """Get live Nifty Futures price."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    futures_id = str(config.NIFTY_FUTURES_SECURITY_ID)
    live_data = orchestrator.data_agent.latest_data.get(futures_id, {})
    
    if not live_data:
        raise HTTPException(status_code=404, detail="No live data available")
    
    return {
        "security_id": futures_id,
        "ltp": live_data.get('LTP'),
        "high": live_data.get('high'),
        "low": live_data.get('low'),
        "volume": live_data.get('volume'),
        "timestamp": datetime.now().isoformat()
    }

# ==================== CONFIGURATION ENDPOINTS ====================

@app.get("/api/config")
async def get_config():
    """Get current configuration (safe fields only)."""
    return {
        "use_sandbox": config.USE_SANDBOX,
        "risk_reward_ratio": config.RISK_REWARD_RATIO,
        "max_risk_percentage": config.MAX_RISK_PERCENTAGE,
        "min_probability_threshold": config.MIN_PROBABILITY_THRESHOLD,
        "zone_timeframe": config.ZONE_TIMEFRAME,
        "trade_timeframe": config.TRADE_TIMEFRAME,
        
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

# ==================== DHAN CREDENTIALS ====================

@app.get("/api/dhan/credentials")
async def get_dhan_credentials():
    """Get Dhan credentials status (masked)."""
    return {
        "client_id": config.DHAN_CLIENT_ID[:4] + "****" if config.DHAN_CLIENT_ID else None,
        "access_token": "****" + config.DHAN_ACCESS_TOKEN[-4:] if config.DHAN_ACCESS_TOKEN else None,
        "configured": bool(config.DHAN_CLIENT_ID and config.DHAN_ACCESS_TOKEN)
    }

@app.post("/api/dhan/credentials")
async def update_dhan_credentials(credentials: dict):
    """Update Dhan credentials."""
    try:
        client_id = credentials.get("client_id", "").strip()
        access_token = credentials.get("access_token", "").strip()

        if not client_id or not access_token:
            raise HTTPException(status_code=400, detail="Both Client ID and Access Token are required")

        # Update config
        config.DHAN_CLIENT_ID = client_id
        config.DHAN_ACCESS_TOKEN = access_token

        # Update orchestrator's dhan_context
        if orchestrator:
            orchestrator.dhan_context = config.get_dhan_context()
            orchestrator.data_agent.dhan_context = config.get_dhan_context()
            orchestrator.execution_agent.dhan_context = config.get_dhan_context()

            # Reinitialize dhan instances
            from dhanhq import dhanhq
            orchestrator.data_agent.dhan = dhanhq(orchestrator.dhan_context)
            orchestrator.execution_agent.dhan = dhanhq(orchestrator.dhan_context)

            log.info("✅ Dhan credentials updated successfully")

        return {
            "success": True,
            "message": "Dhan credentials updated successfully",
            "configured": True
        }

    except Exception as e:
        log.error(f"Failed to update Dhan credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dhan/test")
async def test_dhan_connection():
    """Test Dhan API connection."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        # Try to fetch a simple quote
        from dhanhq import dhanhq
        dhan = dhanhq(config.DHAN_CLIENT_ID, config.DHAN_ACCESS_TOKEN)

        # Test with Nifty index
        result = dhan.ticker_data(securities={"IDX_I": [13]})

        if result and result.get("status") == "success":
            return {
                "success": True,
                "message": "Connection successful! Dhan API is working."
            }
        else:
            return {
                "success": False,
                "message": "Connection failed. Please check your credentials."
            }

    except Exception as e:
        log.error(f"Dhan connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
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


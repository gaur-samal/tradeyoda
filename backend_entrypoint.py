#!/usr/bin/env python3
"""
Backend Entrypoint for TradeYoda Desktop App
Handles initialization and starts FastAPI server
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_desktop_environment():
    """Set up desktop environment before starting backend."""
    from src.utils.desktop_config import desktop_config
    
    print("=" * 60)
    print("🚀 TradeYoda Desktop - Backend Initialization")
    print("=" * 60)
    
    # Check if first run
    if desktop_config.is_first_run():
        print("\n🎉 First Run Detected!")
        print(f"📁 App Data Directory: {desktop_config.app_data_dir}")
        
        # Copy default files
        desktop_config.copy_default_files()
        
        print("✅ Desktop environment initialized")
    else:
        print(f"\n📁 App Data Directory: {desktop_config.app_data_dir}")
    
    print(f"📊 Data Directory: {desktop_config.data_dir}")
    print(f"📝 Logs Directory: {desktop_config.logs_dir}")
    print(f"💾 Cache Directory: {desktop_config.cache_dir}")
    print("\n" + "=" * 60 + "\n")


def start_backend():
    """Start the FastAPI backend server."""
    import uvicorn
    from backend.main import app
    
    # Set up desktop environment
    setup_desktop_environment()
    
    # Get port from environment or use default
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    print(f"🚀 Starting backend server on http://127.0.0.1:{port}")
    print("=" * 60)
    
    # Start server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False  # Reduce log spam in desktop mode
    )


if __name__ == "__main__":
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n\n⚠️ Backend shutdown by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Backend failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


"""
Desktop application configuration and path management.
Handles OS-specific app data directories and first-run detection.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import platform


class DesktopConfig:
    """Manage desktop application paths and configuration."""
    
    def __init__(self):
        """Initialize desktop configuration."""
        self.is_desktop_mode = self._detect_desktop_mode()
        self.app_name = "TradeYoda"
        
        # Set up paths based on mode
        if self.is_desktop_mode:
            self.app_data_dir = self._get_app_data_dir()
        else:
            # Web/dev mode - use current directory
            self.app_data_dir = Path(__file__).parent.parent.parent
        
        # Create subdirectories
        self.data_dir = self.app_data_dir / "data"
        self.logs_dir = self.app_data_dir / "logs"
        self.cache_dir = self.app_data_dir / "cache"
        self.config_dir = self.app_data_dir
        
        # Config files
        self.config_file = self.config_dir / "config.json"
        self.license_key_file = self.cache_dir / ".license_key"
        self.license_cache_file = self.cache_dir / ".license_cache"
        
        # Data files
        self.scrip_master_file = self.data_dir / "api-scrip-master.csv"
        self.credentials_file = self.data_dir / "credentials.json"
        
        # Ensure all directories exist
        self._create_directories()
    
    def _detect_desktop_mode(self) -> bool:
        """
        Detect if running as desktop app (packaged with PyInstaller).
        
        Returns:
            True if running as packaged desktop app, False otherwise
        """
        # Check if frozen (packaged by PyInstaller)
        if getattr(sys, 'frozen', False):
            return True
        
        # Check environment variable (can be set manually for testing)
        if os.getenv("TRADEYODA_DESKTOP_MODE", "").lower() == "true":
            return True
        
        return False
    
    def _get_app_data_dir(self) -> Path:
        """
        Get OS-specific application data directory.
        
        Returns:
            Path to app data directory
        
        Paths:
            - Windows: C:\\Users\\{username}\\AppData\\Roaming\\TradeYoda
            - macOS: ~/Library/Application Support/TradeYoda
            - Linux: ~/.tradeyoda
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows: AppData\Roaming
            base = os.getenv("APPDATA")
            if base:
                return Path(base) / self.app_name
            else:
                return Path.home() / "AppData" / "Roaming" / self.app_name
        
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/Application Support
            return Path.home() / "Library" / "Application Support" / self.app_name
        
        else:  # Linux and others
            # Linux: ~/.tradeyoda (hidden directory)
            return Path.home() / f".{self.app_name.lower()}"
    
    def _create_directories(self):
        """Create all required directories."""
        directories = [
            self.app_data_dir,
            self.data_dir,
            self.logs_dir,
            self.cache_dir,
            self.config_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def is_first_run(self) -> bool:
        """
        Check if this is the first run of the application.
        
        Returns:
            True if first run, False otherwise
        """
        # Check if license key file exists
        if self.license_key_file.exists():
            return False
        
        # Check if config file exists
        if self.config_file.exists():
            return False
        
        return True
    
    def get_config_value(self, key: str, default=None):
        """
        Get configuration value from config.json.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        try:
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get(key, default)
        except Exception as e:
            print(f"Error reading config: {e}")
        
        return default
    
    def set_config_value(self, key: str, value):
        """
        Set configuration value in config.json.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        try:
            import json
            
            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
            
            # Update value
            config_data[key] = value
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_log_file_path(self) -> Path:
        """
        Get log file path.
        
        Returns:
            Path to log file
        """
        from datetime import datetime
        log_filename = f"tradeyoda_{datetime.now().strftime('%Y-%m-%d')}.log"
        return self.logs_dir / log_filename
    
    def get_resource_path(self, relative_path: str) -> Path:
        """
        Get absolute path to resource (works for dev and frozen/packaged app).
        
        Args:
            relative_path: Relative path to resource
        
        Returns:
            Absolute path to resource
        """
        if getattr(sys, 'frozen', False):
            # Running as packaged app
            base_path = Path(sys._MEIPASS)
        else:
            # Running in development
            base_path = Path(__file__).parent.parent.parent
        
        return base_path / relative_path
    
    def copy_default_files(self):
        """
        Copy default files from bundle to app data directory on first run.
        Should be called during first run setup.
        """
        # Check if scrip master exists in app data
        if not self.scrip_master_file.exists():
            # Try to copy from bundled resources
            bundled_scrip = self.get_resource_path("api-scrip-master.csv")
            if bundled_scrip.exists():
                import shutil
                shutil.copy2(bundled_scrip, self.scrip_master_file)
                print(f"✅ Copied scrip master to {self.scrip_master_file}")
        
        # Create empty credentials file if not exists
        if not self.credentials_file.exists():
            import json
            with open(self.credentials_file, 'w') as f:
                json.dump({}, f)
            print(f"✅ Created credentials file at {self.credentials_file}")


# Global instance
desktop_config = DesktopConfig()


# Helper functions for backward compatibility
def get_data_dir() -> Path:
    """Get data directory path."""
    return desktop_config.data_dir


def get_logs_dir() -> Path:
    """Get logs directory path."""
    return desktop_config.logs_dir


def get_cache_dir() -> Path:
    """Get cache directory path."""
    return desktop_config.cache_dir


def is_desktop_mode() -> bool:
    """Check if running in desktop mode."""
    return desktop_config.is_desktop_mode


def is_first_run() -> bool:
    """Check if this is first run."""
    return desktop_config.is_first_run()


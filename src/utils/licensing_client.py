"""
Licensing Client for TradeYoda Desktop App
Communicates with licensing server for validation and key management
"""
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import os

# Import desktop config for paths
from src.utils.desktop_config import desktop_config

class LicensingClient:
    """Client to interact with TradeYoda licensing server."""
    
    def __init__(self, server_url: str = None, cache_dir: Path = None):
        """
        Initialize licensing client.
        
        Args:
            server_url: URL of licensing server (defaults to env var)
            cache_dir: Directory for license cache (defaults to desktop cache dir)
        """
        self.server_url = server_url or os.getenv(
            "LICENSING_SERVER_URL",
            "http://localhost:8100"  # Default for development
        )
        # Cache directory - lazy load desktop config to avoid circular imports
        if cache_dir is None:
            try:
                # Import directly without triggering package __init__
                import importlib.util
                desktop_config_path = Path(__file__).parent / 'desktop_config.py'

                spec = importlib.util.spec_from_file_location("desktop_config_module", str(desktop_config_path))
                desktop_config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(desktop_config_module)

                cache_dir = desktop_config_module.desktop_config.cache_dir
            except Exception:
                # Fallback if desktop_config not available
                cache_dir = Path.home() / ".tradeyoda"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True) 
        self.cache_file = self.cache_dir / ".license_cache"
        self.license_key_file = self.cache_dir / ".license_key"
        
        # Timeouts
        self.validation_timeout = 10  # seconds
        self.grace_period_hours = 24
        
    def save_license_key(self, license_key: str):
        """Save license key to file."""
        try:
            with open(self.license_key_file, 'w') as f:
                f.write(license_key)
            return True
        except Exception as e:
            print(f"Error saving license key: {e}")
            return False
    
    def load_license_key(self) -> Optional[str]:
        """Load license key from file."""
        try:
            if self.license_key_file.exists():
                with open(self.license_key_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error loading license key: {e}")
        return None
    
    def save_cache(self, validation_data: Dict):
        """Save validation response to cache."""
        try:
            cache_data = {
                "validation": validation_data,
                "cached_at": datetime.utcnow().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_cache(self) -> Optional[Dict]:
        """Load validation from cache if still valid."""
        try:
            if not self.cache_file.exists():
                return None
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid (within grace period)
            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            age_hours = (datetime.utcnow() - cached_at).total_seconds() / 3600
            
            if age_hours < self.grace_period_hours:
                return cache_data["validation"]
            else:
                print(f"Cache expired (age: {age_hours:.1f} hours)")
                return None
                
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None
    
    def clear_cache(self):
        """Clear license cache."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    def activate_license(self, license_key: str, device_id: str = None) -> Dict:
        """
        Activate a license (first-time activation).
        
        Args:
            license_key: License key from user
            device_id: Optional device identifier
            
        Returns:
            Dict with activation result
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/licenses/activate",
                json={
                    "license_key": license_key,
                    "device_id": device_id
                },
                timeout=self.validation_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Save license key and cache
                self.save_license_key(license_key)
                return {
                    "success": True,
                    "data": result
                }
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("detail", "Activation failed"),
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Licensing server timeout. Please check your connection.",
                "offline": True
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Cannot reach licensing server. Please check your internet connection.",
                "offline": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Activation error: {str(e)}",
                "offline": False
            }
    
    def validate_license(
        self,
        license_key: str = None,
        device_id: str = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Validate license and get OpenAI key + features.
        
        Args:
            license_key: License key (loads from file if not provided)
            device_id: Optional device identifier
            use_cache: Whether to use cached validation if available
            
        Returns:
            Dict with validation result, OpenAI key, and features
        """
        # Try to load license key if not provided
        if not license_key:
            license_key = self.load_license_key()
        
        if not license_key:
            return {
                "success": False,
                "error": "No license key found. Please activate a license.",
                "valid": False
            }
        
        # Try cache first if enabled
        if use_cache:
            cached = self.load_cache()
            if cached:
                print("✅ Using cached license validation")
                return {
                    "success": True,
                    "data": cached,
                    "from_cache": True
                }
        
        # Validate with server
        try:
            response = requests.post(
                f"{self.server_url}/api/licenses/validate",
                json={
                    "license_key": license_key,
                    "device_id": device_id
                },
                timeout=self.validation_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Save to cache
                self.save_cache(result)
                return {
                    "success": True,
                    "data": result,
                    "from_cache": False
                }
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("detail", "Validation failed"),
                    "status_code": response.status_code,
                    "valid": False
                }
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # Server unreachable - try cache as fallback
            cached = self.load_cache()
            if cached:
                print("⚠️ Licensing server offline, using cached validation")
                return {
                    "success": True,
                    "data": cached,
                    "from_cache": True,
                    "server_offline": True
                }
            else:
                return {
                    "success": False,
                    "error": "Cannot reach licensing server and no cached validation available.",
                    "offline": True,
                    "valid": False
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "valid": False
            }
    
    def check_scrip_master_update(self) -> Dict:
        """Check if there's a new scrip master version available."""
        try:
            response = requests.get(
                f"{self.server_url}/api/scrip-master/version",
                timeout=self.validation_timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": "Failed to check scrip master version"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "offline": True
            }
    
    def download_scrip_master(self, version: str, save_path: str) -> bool:
        """
        Download scrip master CSV.
        
        Args:
            version: Version to download
            save_path: Where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.server_url}/api/scrip-master/download/{version}",
                timeout=30,  # Longer timeout for file download
                stream=True
            )
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"Failed to download: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def get_tier_info(self) -> Dict:
        """Get current tier information from cached validation."""
        cached = self.load_cache()
        if cached and cached.get("valid"):
            return {
                "tier": cached.get("tier"),
                "features": cached.get("features", {}),
                "openai_model": cached.get("openai_model"),
                "expires_at": cached.get("expires_at")
            }
        return {}


# Global instance
licensing_client = LicensingClient()


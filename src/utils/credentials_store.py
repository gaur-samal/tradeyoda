"""Persistent credentials storage."""
import json
from pathlib import Path
from typing import Optional, Dict
from src.utils.logger import log

class CredentialsStore:
    """Store and retrieve persistent credentials."""
    
    def __init__(self, store_path: str = None):
        """Initialize credentials store."""
        if store_path is None:
            # Store in data directory
            from src.config import DATA_DIR
            store_path = DATA_DIR / "credentials.json"
        
        self.store_path = Path(store_path)
        self._ensure_store_exists()
    
    def _ensure_store_exists(self):
        """Create store file if it doesn't exist."""
        if not self.store_path.exists():
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            self._save({})
            log.info(f"📁 Created credentials store at {self.store_path}")
    
    def _save(self, data: Dict):
        """Save credentials to file."""
        try:
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save credentials: {e}")
    
    def _load(self) -> Dict:
        """Load credentials from file."""
        try:
            if self.store_path.exists():
                with open(self.store_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log.error(f"Failed to load credentials: {e}")
            return {}
    
    def save_dhan_credentials(self, client_id: str, access_token: str):
        """
        Save Dhan credentials persistently.
        
        Args:
            client_id: Dhan client ID
            access_token: Dhan access token
        """
        from src.utils.logger import log
        try:
            data = self._load()
            data['dhan_client_id'] = client_id
            data['dhan_access_token'] = access_token
            self._save(data)
            log.info("✅ Dhan credentials saved to persistent storage")
            return True
        except Exception as e:
            log.error(f"Failed to save Dhan credentials: {e}")
            return False
    
    def get_dhan_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get Dhan credentials from persistent storage.
        
        Returns:
            Dict with client_id and access_token, or None
        """
        from src.utils.logger import log
        try:
            data = self._load()
            
            client_id = data.get('dhan_client_id')
            access_token = data.get('dhan_access_token')
            
            if client_id and access_token:
                log.info("✅ Loaded Dhan credentials from persistent storage")
                return {
                    'client_id': client_id,
                    'access_token': access_token
                }
            
            log.warning("⚠️ No stored Dhan credentials found")
            return None
            
        except Exception as e:
            log.error(f"Failed to load Dhan credentials: {e}")
            return None
    
    def clear_dhan_credentials(self):
        """Clear stored Dhan credentials."""
        from src.utils.logger import log
        try:
            data = self._load()
            data.pop('dhan_client_id', None)
            data.pop('dhan_access_token', None)
            self._save(data)
            log.info("✅ Dhan credentials cleared from storage")
            return True
        except Exception as e:
            log.error(f"Failed to clear credentials: {e}")
            return False


# Global instance
credentials_store = CredentialsStore()


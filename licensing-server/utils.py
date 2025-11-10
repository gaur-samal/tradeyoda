"""Utility functions for licensing server."""
import uuid
import hashlib
from datetime import datetime, timedelta

def generate_license_key() -> str:
    """Generate a license key in format: TYODA-XXXX-XXXX-XXXX-XXXX."""
    # Generate UUID and convert to uppercase hex
    key_uuid = uuid.uuid4().hex.upper()
    
    # Format as TYODA-XXXX-XXXX-XXXX-XXXX
    parts = [
        "TYODA",
        key_uuid[0:4],
        key_uuid[4:8],
        key_uuid[8:12],
        key_uuid[12:16]
    ]
    
    return "-".join(parts)

def validate_license_key_format(license_key: str) -> bool:
    """Validate license key format."""
    if not license_key:
        return False
    
    parts = license_key.split("-")
    
    # Should have 5 parts
    if len(parts) != 5:
        return False
    
    # First part should be TYODA
    if parts[0] != "TYODA":
        return False
    
    # Other parts should be 4 characters each (alphanumeric)
    for part in parts[1:]:
        if len(part) != 4 or not part.isalnum():
            return False
    
    return True

def calculate_expiry_date(tier: str, from_date: datetime = None) -> datetime:
    """Calculate expiry date based on tier."""
    if from_date is None:
        from_date = datetime.utcnow()
    
    if tier == "TRIAL":
        # 14 days trial
        return from_date + timedelta(days=14)
    else:
        # Paid licenses don't expire (return far future date)
        return from_date + timedelta(days=365 * 10)  # 10 years

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def get_tier_features(tier: str) -> dict:
    """Get feature flags for a tier."""
    features = {
        "TRIAL": {
            "zone_analysis": True,
            "manual_trading": True,
            "auto_trading": False,
            "openai_model": "gpt-4o-mini",
            "support_level": "none",
            "expires": True,
        },
        "BASIC": {
            "zone_analysis": True,
            "manual_trading": False,
            "auto_trading": False,
            "openai_model": "gpt-4o-mini",
            "support_level": "email",
            "expires": False,
        },
        "ADVANCED": {
            "zone_analysis": True,
            "manual_trading": True,
            "auto_trading": False,
            "openai_model": "gpt-4o",
            "support_level": "priority_email",
            "expires": False,
        },
        "PRO": {
            "zone_analysis": True,
            "manual_trading": True,
            "auto_trading": True,
            "openai_model": "gpt-4.1",
            "support_level": "premium_oncall",
            "expires": False,
        },
    }
    
    return features.get(tier, {})

#!/usr/bin/env python3
"""
Initial setup script for licensing server.
Run this once to create initial OpenAI keys and sample licenses.
"""
import sys
from database import init_database, get_db_session
from models import License, OpenAIKey
from encryption import encryptor
from utils import generate_license_key, calculate_expiry_date
from datetime import datetime

def setup_openai_keys(db):
    """Setup OpenAI keys for all tiers."""
    print("\n" + "=" * 60)
    print("Setting up OpenAI Keys")
    print("=" * 60)
    
    # Note: You need to replace these with your actual OpenAI keys
    keys_config = [
        {"tier": "TRIAL", "model": "gpt-4o-mini", "key": "YOUR_GPT4O_MINI_KEY_HERE"},
        {"tier": "BASIC", "model": "gpt-4o-mini", "key": "YOUR_GPT4O_MINI_KEY_HERE"},
        {"tier": "ADVANCED", "model": "gpt-4o", "key": "YOUR_GPT4O_KEY_HERE"},
        {"tier": "PRO", "model": "gpt-5", "key": "YOUR_GPT5_KEY_HERE"},
    ]
    
    for config in keys_config:
        # Check if already exists
        existing = db.query(OpenAIKey).filter(OpenAIKey.tier == config["tier"]).first()
        
        if existing:
            print(f"⚠️  {config['tier']:10} - Already exists (skipping)")
            continue
        
        # Encrypt and store
        encrypted_key = encryptor.encrypt(config["key"])
        
        openai_key = OpenAIKey(
            tier=config["tier"],
            encrypted_key=encrypted_key,
            model=config["model"],
            is_active=True
        )
        
        db.add(openai_key)
        print(f"✅ {config['tier']:10} - Added (model: {config['model']})")
    
    db.commit()
    print("\n✅ OpenAI keys setup complete")
    print("⚠️  Remember to update the keys with your actual OpenAI API keys!")

def create_sample_licenses(db):
    """Create sample licenses for testing."""
    print("\n" + "=" * 60)
    print("Creating Sample Licenses")
    print("=" * 60)
    
    sample_licenses = [
        {"tier": "TRIAL", "email": "trial@example.com", "name": "Trial User"},
        {"tier": "BASIC", "email": "basic@example.com", "name": "Basic User"},
        {"tier": "ADVANCED", "email": "advanced@example.com", "name": "Advanced User"},
        {"tier": "PRO", "email": "pro@example.com", "name": "Pro User"},
    ]
    
    created_keys = []
    
    for sample in sample_licenses:
        license_key = generate_license_key()
        expires_at = calculate_expiry_date(sample["tier"])
        
        license = License(
            license_key=license_key,
            tier=sample["tier"],
            user_email=sample["email"],
            user_name=sample["name"],
            status="ACTIVE",
            expires_at=expires_at if sample["tier"] == "TRIAL" else None,
            notes="Sample license for testing"
        )
        
        db.add(license)
        created_keys.append({
            "tier": sample["tier"],
            "key": license_key,
            "email": sample["email"]
        })
        
        print(f"✅ {sample['tier']:10} - {license_key}")
    
    db.commit()
    
    print("\n" + "=" * 60)
    print("Sample License Keys Created")
    print("=" * 60)
    for item in created_keys:
        print(f"{item['tier']:10} - {item['key']} ({item['email']})")
    print("\n⚠️  Save these keys for testing!")

def main():
    """Main setup function."""
    print("\n🚀 TradeYoda Licensing Server - Initial Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n📦 Initializing database...")
    init_database()
    
    # Get database session
    db = get_db_session()
    
    try:
        # Setup OpenAI keys
        setup_openai_keys(db)
        
        # Create sample licenses
        response = input("\nCreate sample licenses for testing? (y/n): ")
        if response.lower() == 'y':
            create_sample_licenses(db)
        
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update OpenAI keys with your actual API keys:")
        print("   Use the admin API endpoint: POST /api/admin/openai-keys")
        print("\n2. Start the licensing server:")
        print("   python server.py")
        print("\n3. Test the server:")
        print("   curl http://localhost:8100/health")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

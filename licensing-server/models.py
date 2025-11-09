"""Database models for licensing system."""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class License(Base):
    """License model."""
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(50), unique=True, index=True, nullable=False)
    
    # User information
    user_email = Column(String(255), index=True)
    user_name = Column(String(255))
    
    # License tier
    tier = Column(String(20), nullable=False)  # TRIAL, BASIC, ADVANCED, PRO
    
    # Status
    status = Column(String(20), default="ACTIVE")  # ACTIVE, EXPIRED, REVOKED, SUSPENDED
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # For TRIAL licenses
    last_validated = Column(DateTime, nullable=True)
    
    # Usage tracking
    validation_count = Column(Integer, default=0)
    last_ip = Column(String(50), nullable=True)
    device_id = Column(String(255), nullable=True)  # Optional device fingerprint
    
    # Notes
    notes = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "license_key": self.license_key,
            "user_email": self.user_email,
            "user_name": self.user_name,
            "tier": self.tier,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_validated": self.last_validated.isoformat() if self.last_validated else None,
            "validation_count": self.validation_count,
        }

class OpenAIKey(Base):
    """OpenAI API keys for different tiers (encrypted)."""
    __tablename__ = "openai_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(String(20), unique=True, index=True, nullable=False)
    encrypted_key = Column(Text, nullable=False)
    model = Column(String(50), nullable=False)  # gpt-4o-mini, gpt-4o, gpt-5
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "tier": self.tier,
            "model": self.model,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ScripMaster(Base):
    """Scrip master version tracking."""
    __tablename__ = "scrip_master"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, index=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_latest = Column(Boolean, default=False)
    checksum = Column(String(64), nullable=True)  # SHA256
    notes = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "version": self.version,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "is_latest": self.is_latest,
            "checksum": self.checksum,
        }

class ValidationLog(Base):
    """Log of license validations."""
    __tablename__ = "validation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20))  # SUCCESS, EXPIRED, REVOKED, INVALID
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "license_key": self.license_key,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "status": self.status,
            "error_message": self.error_message,
        }

"""
TradeYoda Licensing Server
FastAPI server for license validation and OpenAI key distribution
"""
from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil
from typing import Optional
from pydantic import BaseModel, EmailStr

from database import get_db, init_database, get_db_session
from models import License, OpenAIKey, ScripMaster, ValidationLog
from encryption import encryptor
from utils import (
    generate_license_key,
    validate_license_key_format,
    calculate_expiry_date,
    calculate_file_checksum,
    get_tier_features
)

# Initialize FastAPI
app = FastAPI(
    title="TradeYoda Licensing Server",
    description="License validation and OpenAI key distribution",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory for scrip master files
UPLOADS_DIR = Path("./uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Admin panel static files
ADMIN_PANEL_DIR = Path("./admin-panel/build")
if ADMIN_PANEL_DIR.exists():
    app.mount("/admin", StaticFiles(directory=str(ADMIN_PANEL_DIR), html=True), name="admin")

# ==================== PYDANTIC MODELS ====================

class LicenseCreateRequest(BaseModel):
    """Request to create a new license."""
    tier: str  # TRIAL, BASIC, ADVANCED, PRO
    user_email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    notes: Optional[str] = None

class LicenseActivateRequest(BaseModel):
    """Request to activate a license."""
    license_key: str
    device_id: Optional[str] = None

class LicenseValidateRequest(BaseModel):
    """Request to validate a license."""
    license_key: str
    device_id: Optional[str] = None

class OpenAIKeyRequest(BaseModel):
    """Request to add/update OpenAI key."""
    tier: str
    api_key: str
    model: str

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()
    print("🚀 TradeYoda Licensing Server started")
    print("=" * 60)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TradeYoda Licensing Server",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== LICENSE ENDPOINTS ====================

@app.post("/api/licenses/create")
async def create_license(
    request: LicenseCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new license.
    Admin endpoint - should be protected in production.
    """
    try:
        # Validate tier
        valid_tiers = ["TRIAL", "BASIC", "ADVANCED", "PRO"]
        if request.tier not in valid_tiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
            )
        
        # Generate license key
        license_key = generate_license_key()
        
        # Calculate expiry date
        expires_at = calculate_expiry_date(request.tier)
        
        # Create license
        license = License(
            license_key=license_key,
            tier=request.tier,
            user_email=request.user_email,
            user_name=request.user_name,
            status="ACTIVE",
            expires_at=expires_at if request.tier == "TRIAL" else None,
            notes=request.notes
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        return {
            "success": True,
            "license_key": license_key,
            "tier": request.tier,
            "expires_at": expires_at.isoformat() if request.tier == "TRIAL" else None,
            "message": "License created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/licenses/activate")
async def activate_license(
    request: LicenseActivateRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Activate a license (first-time activation).
    Records device ID and IP address.
    """
    try:
        # Validate format
        if not validate_license_key_format(request.license_key):
            raise HTTPException(status_code=400, detail="Invalid license key format")
        
        # Find license
        license = db.query(License).filter(
            License.license_key == request.license_key
        ).first()
        
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        
        if license.status == "REVOKED":
            raise HTTPException(status_code=403, detail="License has been revoked")
        
        if license.status == "EXPIRED":
            raise HTTPException(status_code=403, detail="License has expired")
        
        # Check if trial expired
        if license.tier == "TRIAL" and license.expires_at:
            if datetime.utcnow() > license.expires_at:
                license.status = "EXPIRED"
                db.commit()
                raise HTTPException(status_code=403, detail="Trial period has ended")
        
        # Activate license
        license.activated_at = datetime.utcnow()
        license.device_id = request.device_id
        license.last_ip = req.client.host
        
        db.commit()
        db.refresh(license)
        
        # Get features
        features = get_tier_features(license.tier)
        
        return {
            "success": True,
            "tier": license.tier,
            "features": features,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "message": "License activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/licenses/validate")
async def validate_license(
    request: LicenseValidateRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Validate a license and return OpenAI key + features.
    Called by TradeYoda desktop app on startup and periodically.
    """
    try:
        # Validate format
        if not validate_license_key_format(request.license_key):
            # Log failed validation
            log = ValidationLog(
                license_key=request.license_key,
                ip_address=req.client.host,
                status="INVALID",
                error_message="Invalid license key format"
            )
            db.add(log)
            db.commit()
            
            raise HTTPException(status_code=400, detail="Invalid license key format")
        
        # Find license
        license = db.query(License).filter(
            License.license_key == request.license_key
        ).first()
        
        if not license:
            # Log failed validation
            log = ValidationLog(
                license_key=request.license_key,
                ip_address=req.client.host,
                status="INVALID",
                error_message="License not found"
            )
            db.add(log)
            db.commit()
            
            raise HTTPException(status_code=404, detail="License not found")
        
        # Check status
        if license.status == "REVOKED":
            log = ValidationLog(
                license_key=request.license_key,
                ip_address=req.client.host,
                status="REVOKED",
                error_message="License has been revoked"
            )
            db.add(log)
            db.commit()
            
            raise HTTPException(status_code=403, detail="License has been revoked")
        
        # Check if trial expired
        if license.tier == "TRIAL" and license.expires_at:
            if datetime.utcnow() > license.expires_at:
                license.status = "EXPIRED"
                db.commit()
                
                log = ValidationLog(
                    license_key=request.license_key,
                    ip_address=req.client.host,
                    status="EXPIRED",
                    error_message="Trial period has ended"
                )
                db.add(log)
                db.commit()
                
                raise HTTPException(status_code=403, detail="Trial period has ended")
        
        # Get OpenAI key for this tier
        openai_key_record = db.query(OpenAIKey).filter(
            OpenAIKey.tier == license.tier,
            OpenAIKey.is_active == True
        ).first()
        
        if not openai_key_record:
            raise HTTPException(
                status_code=500,
                detail=f"No OpenAI key configured for tier: {license.tier}"
            )
        
        # Decrypt OpenAI key
        openai_key = encryptor.decrypt(openai_key_record.encrypted_key)
        
        # Update license metadata
        license.last_validated = datetime.utcnow()
        license.validation_count += 1
        license.last_ip = req.client.host
        
        # Log successful validation
        log = ValidationLog(
            license_key=request.license_key,
            ip_address=req.client.host,
            status="SUCCESS"
        )
        db.add(log)
        db.commit()
        db.refresh(license)
        
        # Get features
        features = get_tier_features(license.tier)
        
        return {
            "success": True,
            "valid": True,
            "tier": license.tier,
            "openai_key": openai_key,
            "openai_model": openai_key_record.model,
            "features": features,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "user_email": license.user_email,
            "user_name": license.user_name,
            "validation_count": license.validation_count,
            "cache_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== OPENAI KEY MANAGEMENT ====================

@app.post("/api/admin/openai-keys")
async def add_openai_key(
    request: OpenAIKeyRequest,
    db: Session = Depends(get_db)
):
    """
    Add or update OpenAI key for a tier.
    Admin endpoint - should be protected in production.
    """
    try:
        # Validate tier
        valid_tiers = ["TRIAL", "BASIC", "ADVANCED", "PRO"]
        if request.tier not in valid_tiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
            )
        
        # Encrypt the key
        encrypted_key = encryptor.encrypt(request.api_key)
        
        # Check if key already exists for this tier
        existing_key = db.query(OpenAIKey).filter(
            OpenAIKey.tier == request.tier
        ).first()
        
        if existing_key:
            # Update existing
            existing_key.encrypted_key = encrypted_key
            existing_key.model = request.model
            existing_key.updated_at = datetime.utcnow()
            message = f"OpenAI key updated for tier: {request.tier}"
        else:
            # Create new
            new_key = OpenAIKey(
                tier=request.tier,
                encrypted_key=encrypted_key,
                model=request.model
            )
            db.add(new_key)
            message = f"OpenAI key added for tier: {request.tier}"
        
        db.commit()
        
        return {
            "success": True,
            "tier": request.tier,
            "model": request.model,
            "message": message
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/openai-keys")
async def list_openai_keys(db: Session = Depends(get_db)):
    """
    List all configured OpenAI keys (without showing actual keys).
    Admin endpoint.
    """
    try:
        keys = db.query(OpenAIKey).all()
        
        return {
            "success": True,
            "keys": [key.to_dict() for key in keys]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SCRIP MASTER MANAGEMENT ====================

@app.post("/api/admin/scrip-master/upload")
async def upload_scrip_master(
    version: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a new scrip master CSV file.
    Admin endpoint.
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Create filename with version
        file_name = f"api-scrip-master-{version}.csv"
        file_path = UPLOADS_DIR / file_name
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate checksum
        checksum = calculate_file_checksum(str(file_path))
        file_size = file_path.stat().st_size
        
        # Mark all existing as not latest
        db.query(ScripMaster).update({"is_latest": False})
        
        # Add to database
        scrip_master = ScripMaster(
            version=version,
            file_name=file_name,
            file_size=file_size,
            checksum=checksum,
            is_latest=True
        )
        
        db.add(scrip_master)
        db.commit()
        db.refresh(scrip_master)
        
        return {
            "success": True,
            "version": version,
            "file_name": file_name,
            "file_size": file_size,
            "checksum": checksum,
            "message": "Scrip master uploaded successfully"
        }
        
    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()  # Delete file on error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrip-master/version")
async def get_scrip_master_version(db: Session = Depends(get_db)):
    """
    Get latest scrip master version info.
    Called by desktop app to check for updates.
    """
    try:
        latest = db.query(ScripMaster).filter(
            ScripMaster.is_latest == True
        ).first()
        
        if not latest:
            return {
                "success": True,
                "has_update": False,
                "message": "No scrip master available"
            }
        
        return {
            "success": True,
            "has_update": True,
            "version": latest.version,
            "file_size": latest.file_size,
            "checksum": latest.checksum,
            "upload_date": latest.upload_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrip-master/download/{version}")
async def download_scrip_master(version: str, db: Session = Depends(get_db)):
    """
    Download a specific version of scrip master.
    Called by desktop app to update.
    """
    try:
        scrip_master = db.query(ScripMaster).filter(
            ScripMaster.version == version
        ).first()
        
        if not scrip_master:
            raise HTTPException(status_code=404, detail="Version not found")
        
        file_path = UPLOADS_DIR / scrip_master.file_name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename="api-scrip-master.csv",
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN ENDPOINTS ====================

@app.get("/api/admin/licenses")
async def list_licenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all licenses.
    Admin endpoint.
    """
    try:
        licenses = db.query(License).offset(skip).limit(limit).all()
        total = db.query(License).count()
        
        return {
            "success": True,
            "total": total,
            "licenses": [lic.to_dict() for lic in licenses]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/licenses/{license_key}")
async def get_license_details(
    license_key: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a license.
    Admin endpoint.
    """
    try:
        license = db.query(License).filter(
            License.license_key == license_key
        ).first()
        
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        
        # Get validation logs
        logs = db.query(ValidationLog).filter(
            ValidationLog.license_key == license_key
        ).order_by(ValidationLog.timestamp.desc()).limit(10).all()
        
        return {
            "success": True,
            "license": license.to_dict(),
            "recent_validations": [log.to_dict() for log in logs]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/licenses/{license_key}/revoke")
async def revoke_license(
    license_key: str,
    db: Session = Depends(get_db)
):
    """
    Revoke a license.
    Admin endpoint.
    """
    try:
        license = db.query(License).filter(
            License.license_key == license_key
        ).first()
        
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        
        license.status = "REVOKED"
        db.commit()
        
        return {
            "success": True,
            "message": f"License {license_key} has been revoked"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATISTICS ====================

@app.get("/api/admin/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get licensing statistics.
    Admin endpoint.
    """
    try:
        total_licenses = db.query(License).count()
        active_licenses = db.query(License).filter(License.status == "ACTIVE").count()
        expired_licenses = db.query(License).filter(License.status == "EXPIRED").count()
        revoked_licenses = db.query(License).filter(License.status == "REVOKED").count()
        
        # Count by tier
        trial_count = db.query(License).filter(License.tier == "TRIAL").count()
        basic_count = db.query(License).filter(License.tier == "BASIC").count()
        advanced_count = db.query(License).filter(License.tier == "ADVANCED").count()
        pro_count = db.query(License).filter(License.tier == "PRO").count()
        
        # Recent validations
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        validations_today = db.query(ValidationLog).filter(
            ValidationLog.timestamp >= today
        ).count()
        
        return {
            "success": True,
            "total_licenses": total_licenses,
            "active_licenses": active_licenses,
            "expired_licenses": expired_licenses,
            "revoked_licenses": revoked_licenses,
            "by_tier": {
                "trial": trial_count,
                "basic": basic_count,
                "advanced": advanced_count,
                "pro": pro_count
            },
            "validations_today": validations_today,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🧙‍♂️ TradeYoda Licensing Server")
    print("=" * 60)
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8100"))
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

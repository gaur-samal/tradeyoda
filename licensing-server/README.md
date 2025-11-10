# TradeYoda Licensing Server

Complete licensing system with admin panel for managing licenses, OpenAI keys, and scrip master updates.

---

## Table of Contents
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation & Setup](#installation--setup)
- [Building & Deployment](#building--deployment)
- [API Documentation](#api-documentation)
- [Database Management](#database-management)
- [Admin Panel](#admin-panel)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

---

## Architecture

### System Flow

```
┌─────────────────┐
│  TradeYoda App  │ (Desktop/Web)
│  (Client)       │
└────────┬────────┘
         │
         │ HTTP/HTTPS
         ├─ Validate License
         ├─ Fetch OpenAI Key
         ├─ Check Scrip Master Updates
         │
         ▼
┌─────────────────────────────────┐
│   Licensing Server (FastAPI)    │
│   Port: 8100                    │
├─────────────────────────────────┤
│  API Endpoints:                 │
│  - POST /api/licenses/validate  │
│  - GET  /api/openai-keys/{tier} │
│  - GET  /api/scrip-master/*     │
│  - POST /api/admin/*            │
└────────┬───────────────────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  SQLite DB      │      │  Admin Panel    │
│  licensing.db   │      │  (React SPA)    │
│                 │      │  /admin         │
│  Tables:        │      └─────────────────┘
│  - licenses     │
│  - openai_keys  │
│  - scrip_master │
│  - validation_  │
│    logs         │
└─────────────────┘
```

### Component Breakdown

**1. FastAPI Backend (`server.py`)**
- License validation and activation
- OpenAI key management
- Scrip master version control
- Admin API endpoints
- Serves React admin panel as SPA

**2. SQLite Database (`licensing.db`)**
- Persistent storage for all data
- Encrypted OpenAI keys (Fernet)
- License validation logs

**3. React Admin Panel (`admin-panel/`)**
- License management UI
- OpenAI key configuration
- Scrip master upload
- Dashboard statistics

**4. Utility Modules**
- `models.py` - SQLAlchemy ORM models
- `database.py` - Database setup
- `encryption.py` - Key encryption
- `utils.py` - Helper functions (expiry, features)

---

## Features

### License Management
- ✅ Create licenses with tiers: TRIAL, BASIC, ADVANCED, PRO
- ✅ Configurable expiry (14 days, 3 months, 6 months, 1 year, Never)
- ✅ License activation and validation
- ✅ Revoke licenses
- ✅ Bulk operations (create, delete)
- ✅ Validation logging

### OpenAI Key Management
- ✅ Store encrypted keys per tier
- ✅ Automatic key distribution based on license tier
- ✅ Support multiple models: gpt-4o-mini, gpt-4o, gpt-4.1

### Scrip Master Management
- ✅ Version-controlled CSV updates
- ✅ Upload new versions via admin panel
- ✅ Download API for desktop apps
- ✅ Version checking

### Security
- ✅ Encrypted API key storage (Fernet)
- ✅ Device ID tracking
- ✅ Validation logging
- ✅ Rate limiting ready

---

## Technology Stack

**Backend:**
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Cryptography (Fernet encryption)
- Uvicorn (ASGI server)

**Frontend (Admin Panel):**
- React 18
- Ant Design 5.x
- Axios
- Day.js

**Database:**
- SQLite 3

**Deployment:**
- Systemd service
- Nginx (reverse proxy, optional)

---

## Installation & Setup

### Prerequisites

```bash
# Python 3.8+
python3 --version

# Node.js 16+ (for admin panel)
node --version
npm --version
```

### Initial Setup

#### 1. Clone Repository

```bash
cd /home/ubuntu/apps
git clone <repository-url>
cd licensing-server
```

#### 2. Install Python Dependencies

```bash
# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Generate Encryption Key

```bash
python3 << 'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
with open('.encryption_key', 'wb') as f:
    f.write(key)
print(f"✅ Encryption key generated: .encryption_key")
EOF

# Secure the key file
chmod 600 .encryption_key
```

#### 4. Initialize Database

```bash
python3 setup_initial_data.py
```

This creates:
- Database tables
- 4 default OpenAI key entries (placeholder keys)

#### 5. Configure Environment

Create `.env` file:
```bash
cat > .env << 'EOF'
# Server
HOST=0.0.0.0
PORT=8100

# Database
DATABASE_URL=sqlite:///./licensing.db

# Security
ENCRYPTION_KEY_FILE=.encryption_key

# Admin Panel
ADMIN_PANEL_PATH=./admin-panel/build
EOF
```

---

## Building & Deployment

### Option 1: Build Admin Panel on EC2 (Recommended for t3.small)

#### Install Node.js on EC2

```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install Node.js 18
nvm install 18
nvm use 18

# Verify
node --version
npm --version
```

#### Build Admin Panel

```bash
cd /home/ubuntu/apps/licensing-server/admin-panel

# Install dependencies
npm install

# Build production bundle
npm run build

# Output: admin-panel/build/
```

#### Verify Build

```bash
ls -la build/
# Should see: index.html, static/, assets/
```

### Option 2: Build Locally and Copy to EC2

#### On Your Local Machine

```bash
cd licensing-server/admin-panel

# Install dependencies
npm install

# Build
npm run build
```

#### Copy Build to EC2 via SCP

```bash
# From local machine
cd licensing-server/admin-panel

# Using SCP
scp -r build/* ubuntu@YOUR_EC2_IP:/home/ubuntu/apps/licensing-server/admin-panel/build/

# Or using RSYNC (faster, recommended)
rsync -avz --delete build/ ubuntu@YOUR_EC2_IP:/home/ubuntu/apps/licensing-server/admin-panel/build/
```

#### Copy Build to EC2 via SFTP

```bash
# Connect via SFTP
sftp ubuntu@YOUR_EC2_IP

# On SFTP prompt
cd /home/ubuntu/apps/licensing-server/admin-panel
put -r build/*
exit
```

---

### Running the Server

#### Option 1: Direct Execution (Testing)

```bash
cd /home/ubuntu/apps/licensing-server
python3 server.py
```

Server starts on: `http://0.0.0.0:8100`
- API: `http://YOUR_IP:8100/api/`
- Admin Panel: `http://YOUR_IP:8100/admin`
- Docs: `http://YOUR_IP:8100/docs`

#### Option 2: Systemd Service (Production)

Create service file:
```bash
sudo nano /etc/systemd/system/tradeyoda-licensing.service
```

Paste this:
```ini
[Unit]
Description=TradeYoda Licensing Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/apps/licensing-server
Environment="PATH=/home/ubuntu/apps/licensing-server/venv/bin"
ExecStart=/home/ubuntu/apps/licensing-server/venv/bin/python3 server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable tradeyoda-licensing

# Start service
sudo systemctl start tradeyoda-licensing

# Check status
sudo systemctl status tradeyoda-licensing

# View logs
sudo journalctl -u tradeyoda-licensing -f
```

#### Option 3: Supervisor (Alternative)

Create supervisor config:
```bash
sudo nano /etc/supervisor/conf.d/licensing-server.conf
```

Paste:
```ini
[program:licensing-server]
command=/home/ubuntu/apps/licensing-server/venv/bin/python3 server.py
directory=/home/ubuntu/apps/licensing-server
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/licensing-server.err.log
stdout_logfile=/var/log/supervisor/licensing-server.out.log
```

Start:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start licensing-server
sudo supervisorctl status licensing-server
```

---

## API Documentation

### Base URL
```
http://YOUR_EC2_IP:8100
```

### Authentication
Currently no authentication. Consider adding API keys for production.

---

### License Management APIs

#### 1. Validate License
**Endpoint:** `POST /api/licenses/validate`

**Request:**
```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "device_id": "optional-device-id"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "tier": "PRO",
  "expires_at": "2026-11-10T10:00:00",
  "features": {
    "zone_analysis": true,
    "manual_trading": true,
    "auto_trading": true,
    "openai_model": "gpt-4.1",
    "support_level": "premium_oncall"
  },
  "openai_key": "sk-proj-...",
  "openai_model": "gpt-4.1"
}
```

**Response (Invalid):**
```json
{
  "valid": false,
  "error": "License not found"
}
```

**Testing:**
```bash
curl -X POST http://YOUR_IP:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"TEST-KEY","device_id":"test-device"}'
```

---

#### 2. Activate License
**Endpoint:** `POST /api/licenses/activate`

**Request:**
```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "device_id": "optional-device-id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "License activated successfully",
  "license": {
    "license_key": "XXXX-XXXX-XXXX-XXXX",
    "tier": "PRO",
    "valid": true,
    "expires_at": "2026-11-10T10:00:00"
  }
}
```

---

### OpenAI Key APIs

#### 3. Get OpenAI Key by Tier
**Endpoint:** `GET /api/openai-keys/{tier}`

**Example:**
```bash
curl http://YOUR_IP:8100/api/openai-keys/PRO
```

**Response:**
```json
{
  "tier": "PRO",
  "model": "gpt-4.1",
  "key": "sk-proj-..."
}
```

---

#### 4. Get Feature Flags
**Endpoint:** `GET /api/features/{tier}`

**Response:**
```json
{
  "zone_analysis": true,
  "manual_trading": true,
  "auto_trading": true,
  "openai_model": "gpt-4.1",
  "support_level": "premium_oncall"
}
```

---

### Admin APIs (License Management)

#### 5. Create License
**Endpoint:** `POST /api/admin/licenses`

**Request:**
```json
{
  "tier": "PRO",
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "notes": "VIP customer",
  "never_expires": false
}
```

**Response:**
```json
{
  "license_key": "PRO-A1B2C3D4-E5F6-7890",
  "tier": "PRO",
  "created_at": "2025-11-10T10:00:00",
  "expires_at": "2026-11-10T10:00:00"
}
```

---

#### 6. Get All Licenses
**Endpoint:** `GET /api/admin/licenses`

**Response:**
```json
{
  "licenses": [
    {
      "license_key": "PRO-...",
      "tier": "PRO",
      "user_email": "user@example.com",
      "status": "active",
      "created_at": "...",
      "expires_at": "..."
    }
  ],
  "total": 1
}
```

---

#### 7. Revoke License
**Endpoint:** `POST /api/admin/licenses/{license_key}/revoke`

**Response:**
```json
{
  "success": true,
  "message": "License revoked successfully"
}
```

---

#### 8. Delete License
**Endpoint:** `DELETE /api/admin/licenses/{license_key}`

**Response:**
```json
{
  "success": true,
  "message": "License deleted successfully"
}
```

---

#### 9. Bulk Delete Licenses
**Endpoint:** `POST /api/admin/licenses/bulk-delete`

**Request:**
```json
{
  "license_keys": ["KEY1", "KEY2", "KEY3"]
}
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 3
}
```

---

### Scrip Master APIs

#### 10. Get Scrip Master Version
**Endpoint:** `GET /api/scrip-master/version`

**Response:**
```json
{
  "version": "2025-11-10",
  "uploaded_at": "2025-11-10T10:00:00"
}
```

---

#### 11. Download Scrip Master
**Endpoint:** `GET /api/scrip-master/download/{version}`

**Example:**
```bash
curl -O http://YOUR_IP:8100/api/scrip-master/download/2025-11-10
```

Returns CSV file.

---

#### 12. Upload Scrip Master
**Endpoint:** `POST /api/admin/scrip-master/upload`

**Request:** Multipart form-data with CSV file

**Using curl:**
```bash
curl -X POST http://YOUR_IP:8100/api/admin/scrip-master/upload \
  -F "file=@api-scrip-master.csv"
```

---

### Statistics APIs

#### 13. Get Dashboard Stats
**Endpoint:** `GET /api/admin/stats`

**Response:**
```json
{
  "total_licenses": 150,
  "active_licenses": 120,
  "expired_licenses": 30,
  "by_tier": {
    "TRIAL": 20,
    "BASIC": 50,
    "ADVANCED": 40,
    "PRO": 40
  }
}
```

---

## Database Management

### Database Location
```
/home/ubuntu/apps/licensing-server/licensing.db
```

### Database Schema

```sql
-- Licenses Table
CREATE TABLE licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL,
    user_email VARCHAR(255),
    user_name VARCHAR(255),
    device_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    last_validated DATETIME,
    notes TEXT
);

-- OpenAI Keys Table
CREATE TABLE openai_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier VARCHAR(50) UNIQUE NOT NULL,
    model VARCHAR(50) NOT NULL,
    key TEXT NOT NULL,  -- Encrypted
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scrip Master Table
CREATE TABLE scrip_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(50) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Validation Logs Table
CREATE TABLE validation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    success BOOLEAN
);
```

---

### Common Database Commands

#### Connect to Database

```bash
cd /home/ubuntu/apps/licensing-server

# Using Python
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

# Your queries here...

conn.close()
EOF
```

#### View All Licenses

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT license_key, tier, user_email, status, expires_at 
    FROM licenses 
    ORDER BY created_at DESC
""")

print(f"{'License Key':<30} {'Tier':<10} {'Email':<25} {'Status':<10} {'Expires'}")
print("-" * 95)

for row in cursor.fetchall():
    license_key, tier, email, status, expires = row
    email = email or 'N/A'
    expires = expires or 'Never'
    print(f"{license_key:<30} {tier:<10} {email:<25} {status:<10} {expires}")

conn.close()
EOF
```

---

#### View OpenAI Keys

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

cursor.execute("SELECT tier, model, key FROM openai_keys ORDER BY tier")

print(f"{'Tier':<10} {'Model':<15} {'Key Preview'}")
print("-" * 60)

for tier, model, key in cursor.fetchall():
    # Show first 20 chars of encrypted key
    key_preview = key[:20] + "..." if len(key) > 20 else key
    print(f"{tier:<10} {model:<15} {key_preview}")

conn.close()
EOF
```

---

#### Count Licenses by Tier

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT tier, COUNT(*) as count 
    FROM licenses 
    WHERE status = 'active'
    GROUP BY tier
""")

print(f"{'Tier':<10} {'Count'}")
print("-" * 20)

for tier, count in cursor.fetchall():
    print(f"{tier:<10} {count}")

cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'active'")
total = cursor.fetchone()[0]
print(f"{'Total':<10} {total}")

conn.close()
EOF
```

---

#### Update OpenAI Key

```bash
python3 << 'EOF'
import sqlite3
from encryption import encrypt_key

# Your new key
new_key = "sk-proj-YOUR-NEW-KEY-HERE"
tier = "PRO"

# Encrypt the key
encrypted_key = encrypt_key(new_key)

# Update database
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

cursor.execute("""
    UPDATE openai_keys 
    SET key = ?, updated_at = CURRENT_TIMESTAMP 
    WHERE tier = ?
""", (encrypted_key, tier))

conn.commit()
print(f"✅ Updated {tier} tier key")
print(f"   Rows affected: {cursor.rowcount}")

conn.close()
EOF
```

---

#### Delete Expired Licenses

```bash
python3 << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

# Delete expired licenses
cursor.execute("""
    DELETE FROM licenses 
    WHERE expires_at < ? 
    AND status = 'active'
""", (datetime.utcnow().isoformat(),))

deleted = cursor.rowcount
conn.commit()

print(f"✅ Deleted {deleted} expired licenses")

conn.close()
EOF
```

---

#### View Validation Logs

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT license_key, device_id, validated_at, success 
    FROM validation_logs 
    ORDER BY validated_at DESC 
    LIMIT 10
""")

print(f"{'License Key':<30} {'Device ID':<20} {'Validated At':<20} {'Success'}")
print("-" * 90)

for row in cursor.fetchall():
    license_key, device_id, validated_at, success = row
    device_id = device_id or 'N/A'
    success_icon = '✅' if success else '❌'
    print(f"{license_key:<30} {device_id:<20} {validated_at:<20} {success_icon}")

conn.close()
EOF
```

---

#### Backup Database

```bash
# Create backup
cp licensing.db licensing.db.backup-$(date +%Y%m%d-%H%M%S)

# List backups
ls -lh licensing.db.backup-*

# Restore from backup
# cp licensing.db.backup-YYYYMMDD-HHMMSS licensing.db
```

---

## Admin Panel

### Access
```
http://YOUR_EC2_IP:8100/admin
```

### Features

**Dashboard:**
- Total licenses count
- Active vs expired breakdown
- Licenses by tier
- Recent validations

**Licenses Page:**
- View all licenses in table
- Create new license
- View license details
- Revoke license
- Delete license (single/bulk)
- Filter and search

**OpenAI Keys Page:**
- View keys by tier
- Add/Update keys
- Model configuration
- Tier reference table

**Scrip Master Page:**
- Current version display
- Upload new CSV
- Version history

---

### Building Admin Panel

See "Building & Deployment" section above.

### Updating Admin Panel

```bash
# After code changes
cd admin-panel
npm run build

# Restart server
sudo systemctl restart tradeyoda-licensing
```

---

## Troubleshooting

### Server Won't Start

**Check 1: Port already in use**
```bash
lsof -i :8100
# If something is running, kill it
sudo kill -9 <PID>
```

**Check 2: Missing dependencies**
```bash
pip install -r requirements.txt
```

**Check 3: Database file permissions**
```bash
ls -la licensing.db
chmod 644 licensing.db
```

**Check 4: Encryption key missing**
```bash
ls -la .encryption_key
# Regenerate if missing (see setup section)
```

---

### Admin Panel Not Loading

**Check 1: Build exists**
```bash
ls -la admin-panel/build/
# Should see index.html and static/
```

**Check 2: Server serving correct path**
```bash
grep "ADMIN_PANEL_PATH" .env
# Should be: ./admin-panel/build
```

**Check 3: Clear browser cache**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or open in Incognito mode

---

### License Validation Fails

**Check 1: License exists in database**
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()
cursor.execute("SELECT license_key, status FROM licenses WHERE license_key = ?", ("YOUR-KEY-HERE",))
print(cursor.fetchone())
conn.close()
EOF
```

**Check 2: License not expired**
```bash
python3 << 'EOF'
import sqlite3
from datetime import datetime
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()
cursor.execute("SELECT expires_at FROM licenses WHERE license_key = ?", ("YOUR-KEY-HERE",))
expires = cursor.fetchone()[0]
print(f"Expires: {expires}")
print(f"Now: {datetime.utcnow().isoformat()}")
print(f"Valid: {expires > datetime.utcnow().isoformat() if expires else 'Never expires'}")
conn.close()
EOF
```

**Check 3: Server logs**
```bash
sudo journalctl -u tradeyoda-licensing -f
# Watch for validation requests
```

---

### OpenAI Key Not Decrypting

**Check 1: Encryption key exists**
```bash
ls -la .encryption_key
```

**Check 2: Test encryption/decryption**
```bash
python3 << 'EOF'
from encryption import encrypt_key, decrypt_key

test_key = "sk-test-key"
encrypted = encrypt_key(test_key)
decrypted = decrypt_key(encrypted)

print(f"Original: {test_key}")
print(f"Encrypted: {encrypted[:50]}...")
print(f"Decrypted: {decrypted}")
print(f"Match: {test_key == decrypted}")
EOF
```

---

### Database Locked Error

**Cause:** Multiple processes accessing database simultaneously

**Solution:**
```bash
# Check for multiple server instances
ps aux | grep "server.py"

# Kill extra instances
pkill -f "python3 server.py"

# Restart properly
sudo systemctl restart tradeyoda-licensing
```

---

### Can't Connect from Desktop App

**Check 1: Server is running**
```bash
curl http://localhost:8100/api/health
```

**Check 2: Firewall/Security Group**
```bash
# Check EC2 security group allows port 8100
# AWS Console → EC2 → Security Groups → Inbound Rules
# Should have: Custom TCP, Port 8100, Source: 0.0.0.0/0
```

**Check 3: Test from external machine**
```bash
# From your local machine (not EC2)
curl http://YOUR_EC2_PUBLIC_IP:8100/api/health
```

---

### High Memory Usage

**Check 1: Monitor resources**
```bash
htop
# or
top
```

**Check 2: Restart service**
```bash
sudo systemctl restart tradeyoda-licensing
```

**Check 3: Optimize database**
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
conn.execute('VACUUM')
conn.close()
print("✅ Database optimized")
EOF
```

---

## Security Considerations

### Production Checklist

- [ ] **Use HTTPS** (Let's Encrypt with Nginx)
- [ ] **Add API authentication** (API keys, JWT)
- [ ] **Rate limiting** (prevent brute force)
- [ ] **Input validation** (sanitize all inputs)
- [ ] **Database backups** (automated daily)
- [ ] **Encryption key backup** (store securely, separate from server)
- [ ] **CORS configuration** (restrict origins)
- [ ] **Firewall rules** (only allow necessary ports)
- [ ] **Regular updates** (FastAPI, dependencies)
- [ ] **Monitor logs** (setup alerts)

### Recommended Setup

```nginx
# /etc/nginx/sites-available/licensing
server {
    listen 80;
    server_name licensing.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name licensing.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/licensing.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/licensing.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Quick Reference

### Service Commands
```bash
# Start
sudo systemctl start tradeyoda-licensing

# Stop
sudo systemctl stop tradeyoda-licensing

# Restart
sudo systemctl restart tradeyoda-licensing

# Status
sudo systemctl status tradeyoda-licensing

# Logs
sudo journalctl -u tradeyoda-licensing -f
```

### Database Backup
```bash
cp licensing.db licensing.db.backup-$(date +%Y%m%d)
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8100/api/health

# Create license
curl -X POST http://localhost:8100/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{"tier":"PRO","user_email":"test@example.com"}'

# Validate license
curl -X POST http://localhost:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"YOUR-KEY","device_id":"test"}'
```

---

## Support & Contributing

For issues or questions, please contact the development team.

**Version:** 1.0.0  
**Last Updated:** November 2025

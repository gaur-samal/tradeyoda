# Licensing System Configuration & Validation

## 🚨 CRITICAL ISSUE IDENTIFIED

### Problem: Hardcoded `localhost:8100` Won't Work for Desktop Apps

**Current situation:**
```python
# src/config.py
LICENSING_SERVER_URL = "http://localhost:8100"
```

**Why this is wrong:**
- ✅ Works on EC2 (web deployment) - server and app on same machine
- ❌ Fails on user's desktop - `localhost` points to user's machine, not your server!

---

## License Storage Locations

### 1. Licensing Server (Centralized)

**Location:** `/app/licensing-server/licensing.db` (SQLite database)

**Tables:**
- `licenses` - All issued licenses (0 currently)
- `openai_keys` - OpenAI keys per tier (4 keys currently)
- `scrip_master` - Scrip master CSV versions
- `validation_logs` - License validation history

**View data:**
```bash
# SSH to EC2
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/app/licensing-server/licensing.db')

# View all OpenAI keys
print("OpenAI Keys by Tier:")
cursor = conn.cursor()
cursor.execute("SELECT tier, model, key FROM openai_keys")
for row in cursor.fetchall():
    tier, model, key = row
    print(f"  {tier}: {model} - {key[:20]}...")

# View all licenses
print("\nLicenses:")
cursor.execute("SELECT license_key, tier, user_email, expires_at FROM licenses")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
EOF
```

### 2. Desktop App Cache (User's Machine)

**Desktop Mode:**
```
Windows: C:\Users\{username}\AppData\Roaming\TradeYoda\cache\
Mac: ~/Library/Application Support/TradeYoda/cache/
Linux: ~/.tradeyoda/cache/
```

**Files:**
- `.license_key` - User's license key
- `.license_cache` - Cached validation response (24-hour TTL)

**Web Mode (EC2):**
```
/app/tradeyoda/cache/
├── .license_key
└── .license_cache
```

---

## OpenAI Key Change Propagation

### When You Update OpenAI Key in Database

```sql
-- Update PRO tier key
UPDATE openai_keys 
SET key = 'sk-proj-new-key-here' 
WHERE tier = 'PRO';
```

### Propagation Timeline

| Event | Desktop App Behavior |
|-------|---------------------|
| **Immediately** | Server has new key ✅ |
| **User's app (cached)** | Still uses OLD key ❌ (cached for 24 hours) |
| **After 24 hours** | Cache expires, fetches NEW key ✅ |
| **Manual revalidation** | Gets NEW key immediately ✅ |
| **App restart (cache expired)** | Gets NEW key ✅ |

### Force Immediate Update

**Option 1: User manually revalidates** (best UX)
```javascript
// In desktop app settings
await fetch('http://localhost:8000/api/license/validate', {
  method: 'POST'
});
```

**Option 2: Clear cache** (requires app restart)
```bash
# User's machine
rm ~/.tradeyoda/cache/.license_cache
# Restart app
```

**Option 3: Reduce cache TTL** (not recommended - more server load)
```python
# src/utils/licensing_client.py
CACHE_GRACE_PERIOD_HOURS = 1  # Instead of 24
```

---

## How to Validate OpenAI Key Changes

### Test 1: Check Database
```bash
# SSH to EC2
cd /app/licensing-server
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('licensing.db')
cursor = conn.cursor()
cursor.execute("SELECT tier, model, key FROM openai_keys WHERE tier='PRO'")
tier, model, key = cursor.fetchone()
print(f"PRO tier: {model}")
print(f"Key starts with: {key[:20]}...")
conn.close()
EOF
```

### Test 2: Call API Directly
```bash
curl -X POST http://YOUR_EC2_IP:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"YOUR_TEST_LICENSE","device_id":"test"}'
```

Expected response includes:
```json
{
  "openai_key": "sk-proj-...",
  "openai_model": "gpt-4.1",
  "tier": "PRO"
}
```

### Test 3: From Desktop App (After Revalidation)
```bash
# Check cached data
cat ~/.tradeyoda/cache/.license_cache | jq '.validation.openai_key'
```

---

## 🔧 FIX: Configure Licensing Server URL

### Solution 1: Use Environment Variable (Recommended)

**Step 1: Create .env file**
```bash
# On EC2: /app/tradeyoda/backend/.env
echo "LICENSING_SERVER_URL=http://YOUR_EC2_PUBLIC_IP:8100" >> /app/tradeyoda/backend/.env
```

**Step 2: Verify it's loaded**
```bash
# Restart backend
sudo supervisorctl restart backend

# Check logs
tail -f /var/log/supervisor/backend.err.log | grep "LICENSING_SERVER_URL"
```

**For Desktop Apps:**
Desktop apps will need to be built with the correct URL or fetch it dynamically.

---

### Solution 2: Use Domain Name (Best for Production)

**Step 1: Set up domain**
```bash
# Point domain to EC2
licensing.tradeyoda.com → YOUR_EC2_IP
```

**Step 2: Configure Nginx reverse proxy**
```nginx
# /etc/nginx/sites-available/licensing
server {
    listen 80;
    server_name licensing.tradeyoda.com;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: Update .env**
```bash
LICENSING_SERVER_URL=https://licensing.tradeyoda.com
```

**Step 4: Enable HTTPS (Let's Encrypt)**
```bash
sudo certbot --nginx -d licensing.tradeyoda.com
```

---

### Solution 3: Configuration Service (Advanced)

Create a config endpoint that desktop apps query:

**Server side:**
```python
# licensing-server/server.py
@app.get("/api/config")
async def get_config():
    return {
        "licensing_url": "https://licensing.tradeyoda.com",
        "version": "1.0.0"
    }
```

**Desktop app:**
```javascript
// Fetch config on startup
const config = await fetch('https://config.tradeyoda.com/desktop-config.json');
const licensingUrl = config.licensing_url;
```

---

## Current Configuration Status

### Web Deployment (EC2)
```
TradeYoda Backend (EC2) ──┐
                          ├─> localhost:8100 ✅ WORKS
Licensing Server (EC2) ───┘
```

### Desktop Deployment (BROKEN)
```
TradeYoda Desktop (User's PC) ──┐
                                ├─> localhost:8100 ❌ FAILS!
Licensing Server (EC2)          │   (Points to user's PC, not EC2)
                                └─> Should be: http://EC2_IP:8100
```

---

## Recommended Setup

### For Testing (Quick Fix)

**1. Update backend/.env on EC2:**
```bash
cd /app/tradeyoda/backend
cat > .env << EOF
LICENSING_SERVER_URL=http://$(curl -s ifconfig.me):8100
EOF
```

**2. Restart backend:**
```bash
sudo supervisorctl restart backend
```

**3. Verify:**
```bash
curl http://localhost:8001/api/license/status
# Should contact EC2_IP:8100
```

---

### For Production (Proper Setup)

**1. Get domain name:**
```
licensing.yourdomain.com
```

**2. Set up HTTPS:**
```bash
sudo certbot --nginx -d licensing.yourdomain.com
```

**3. Update all configs:**
```bash
# Backend .env
LICENSING_SERVER_URL=https://licensing.yourdomain.com

# Desktop app config
LICENSING_SERVER_URL=https://licensing.yourdomain.com
```

**4. Security:**
- Enable CORS for specific origins
- Add rate limiting
- API key authentication (optional)

---

## Validation Checklist

After configuring licensing server URL:

**Server Side:**
- [ ] Licensing server running on port 8100
- [ ] OpenAI keys configured in database
- [ ] Licenses can be created via admin panel
- [ ] API endpoints respond correctly

**Desktop App:**
- [ ] LICENSING_SERVER_URL points to EC2 (not localhost)
- [ ] Can validate license from user's machine
- [ ] Fetches correct OpenAI key
- [ ] Cache works correctly

**Testing:**
```bash
# From user's machine (not EC2)
curl -X POST http://YOUR_EC2_IP:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"test-key","device_id":"test-device"}'

# Should NOT return connection refused
```

---

## Quick Fix Script

```bash
#!/bin/bash
# File: fix-licensing-url.sh

# Get EC2 public IP
EC2_IP=$(curl -s ifconfig.me)

echo "🔧 Fixing Licensing Server URL..."
echo "EC2 Public IP: $EC2_IP"

# Update backend .env
cd /app/tradeyoda/backend
echo "LICENSING_SERVER_URL=http://$EC2_IP:8100" >> .env

# Restart backend
sudo supervisorctl restart backend

echo "✅ Done!"
echo ""
echo "Updated to: http://$EC2_IP:8100"
echo ""
echo "⚠️  Note: For production, use a domain name with HTTPS"
```

---

## Summary

**Where licenses stored:**
- Server: `/app/licensing-server/licensing.db`
- Desktop cache: `~/.tradeyoda/cache/` (24h TTL)

**OpenAI key changes:**
- Server: Immediate ✅
- Desktop app: 24 hours delay ❌ (unless revalidated)

**CRITICAL FIX needed:**
```bash
# Change from:
LICENSING_SERVER_URL=http://localhost:8100  ❌

# Change to:
LICENSING_SERVER_URL=http://YOUR_EC2_IP:8100  ✅
# Or better:
LICENSING_SERVER_URL=https://licensing.yourdomain.com  ✅✅
```

**Validation:**
```bash
# Test from external machine
curl http://YOUR_EC2_IP:8100/api/licenses/validate -d '{...}'
```

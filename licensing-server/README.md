# TradeYoda Licensing Server

License validation and OpenAI key distribution server for TradeYoda desktop application.

## Features

- ✅ License key generation and validation
- ✅ Tier-based feature management (TRIAL, BASIC, ADVANCED, PRO)
- ✅ Encrypted OpenAI key storage and distribution
- ✅ Scrip master file version management and distribution
- ✅ Offline grace period support (24 hours)
- ✅ Comprehensive admin API
- ✅ Validation logging and statistics

## Installation

### 1. Install Dependencies

```bash
cd /home/ubuntu/licensing-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Important:** Change `SECRET_KEY` and `ENCRYPTION_KEY` in production!

### 3. Initial Setup

Run the setup script to initialize database and create sample data:

```bash
python setup_initial_data.py
```

This will:
- Create database schema
- Setup OpenAI key placeholders for all tiers
- Optionally create sample licenses for testing

### 4. Add Your OpenAI Keys

Update with your actual OpenAI API keys:

```bash
curl -X POST http://localhost:8100/api/admin/openai-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "TRIAL",
    "api_key": "sk-your-actual-key-here",
    "model": "gpt-4o-mini"
  }'
```

Repeat for all tiers: TRIAL, BASIC, ADVANCED, PRO

## Running the Server

### Development Mode

```bash
python server.py
```

Server will start on `http://0.0.0.0:8100`

### Production Mode (Systemd)

Create systemd service:

```bash
sudo nano /etc/systemd/system/tradeyoda-licensing.service
```

Add:

```ini
[Unit]
Description=TradeYoda Licensing Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/licensing-server
Environment="PATH=/home/ubuntu/licensing-server/venv/bin"
ExecStart=/home/ubuntu/licensing-server/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tradeyoda-licensing
sudo systemctl start tradeyoda-licensing
sudo systemctl status tradeyoda-licensing
```

## API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/licenses/activate` | POST | Activate a license |
| `/api/licenses/validate` | POST | Validate license + get OpenAI key |
| `/api/scrip-master/version` | GET | Check for scrip master updates |
| `/api/scrip-master/download/{version}` | GET | Download scrip master CSV |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/licenses/create` | POST | Create new license |
| `/api/admin/licenses` | GET | List all licenses |
| `/api/admin/licenses/{key}` | GET | Get license details |
| `/api/admin/licenses/{key}/revoke` | POST | Revoke a license |
| `/api/admin/openai-keys` | POST | Add/update OpenAI key |
| `/api/admin/openai-keys` | GET | List configured keys |
| `/api/admin/scrip-master/upload` | POST | Upload scrip master CSV |
| `/api/admin/stats` | GET | Get licensing statistics |

## Usage Examples

### Create a New License

```bash
curl -X POST http://localhost:8100/api/licenses/create \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "PRO",
    "user_email": "customer@example.com",
    "user_name": "John Doe",
    "notes": "Annual subscription"
  }'
```

Response:
```json
{
  "success": true,
  "license_key": "TYODA-A1B2-C3D4-E5F6-G7H8",
  "tier": "PRO",
  "expires_at": null,
  "message": "License created successfully"
}
```

### Validate a License (Desktop App)

```bash
curl -X POST http://localhost:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "TYODA-A1B2-C3D4-E5F6-G7H8",
    "device_id": "unique-device-id"
  }'
```

Response:
```json
{
  "success": true,
  "valid": true,
  "tier": "PRO",
  "openai_key": "sk-...",
  "openai_model": "gpt-5",
  "features": {
    "zone_analysis": true,
    "manual_trading": true,
    "auto_trading": true,
    "openai_model": "gpt-5",
    "support_level": "premium_oncall"
  },
  "expires_at": null,
  "cache_until": "2024-11-08T10:00:00"
}
```

### Upload Scrip Master

```bash
curl -X POST "http://localhost:8100/api/admin/scrip-master/upload?version=2024-11" \
  -F "file=@/path/to/api-scrip-master.csv"
```

## Tier Features

| Feature | TRIAL (14 days) | BASIC | ADVANCED | PRO |
|---------|----------------|-------|----------|-----|
| Zone Analysis | ✅ | ✅ | ✅ | ✅ |
| Manual Trading | ✅ | ❌ | ✅ | ✅ |
| Auto Trading | ❌ | ❌ | ❌ | ✅ |
| OpenAI Model | gpt-4o-mini | gpt-4o-mini | gpt-4o | gpt-5 |
| Support | ❌ | Email | Priority | Premium/on-call |

## Security Considerations

### Production Deployment

1. **Change default secrets** in `.env`:
   - Generate new `SECRET_KEY`
   - Generate new `ENCRYPTION_KEY`

2. **Protect admin endpoints**:
   - Add authentication middleware
   - Use API keys or JWT tokens
   - Restrict by IP address

3. **Use HTTPS**:
   - Configure SSL certificate
   - Set up reverse proxy (nginx)

4. **Backup database**:
   ```bash
   cp licensing.db licensing.db.backup
   ```

## Monitoring

### Check Server Status

```bash
sudo systemctl status tradeyoda-licensing
```

### View Logs

```bash
sudo journalctl -u tradeyoda-licensing -f
```

### Get Statistics

```bash
curl http://localhost:8100/api/admin/stats
```

## Troubleshooting

### Database Issues

Reset database:
```bash
rm licensing.db
python setup_initial_data.py
```

### Port Already in Use

Change port in `.env`:
```bash
PORT=8101
```

### Encryption Errors

Ensure `ENCRYPTION_KEY` is set in `.env` and hasn't changed.

## License Management Workflow

1. **Customer purchases license** → Create license via `/api/licenses/create`
2. **Send license key to customer** → Via email
3. **Customer enters key in TradeYoda** → Desktop app calls `/api/licenses/activate`
4. **App validates periodically** → Desktop app calls `/api/licenses/validate` every 4 hours
5. **Offline grace period** → App caches validation for 24 hours
6. **Revoke if needed** → Admin calls `/api/admin/licenses/{key}/revoke`

## Support

For issues, contact: gaur.samal@gmail.com

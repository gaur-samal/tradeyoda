# TradeYoda Licensing Server - Complete Setup Guide

This guide will help you set up the TradeYoda licensing server on your EC2 instance with the React admin panel.

## 📋 Prerequisites

- Ubuntu EC2 instance (running)
- Python 3.8+
- Node.js 18+ and Yarn
- Git

## 🚀 Installation Steps

### Step 1: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/gaur-samal/tradeyoda-licensing-server.git licensing-server
cd licensing-server
```

### Step 2: Setup Python Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
```

**Important:** Edit `.env` and change:
- `SECRET_KEY` - Generate a random string
- `ENCRYPTION_KEY` - Generate a random string
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` - Set your admin credentials

### Step 3: Initialize Database

```bash
python setup_initial_data.py
```

When prompted to create sample licenses, type `n` (you'll create real ones later).

### Step 4: Add Your OpenAI Keys

Start the server temporarily:
```bash
python server.py
```

In another terminal, add keys for each tier:

```bash
# TRIAL tier (gpt-4o-mini)
curl -X POST http://localhost:8100/api/admin/openai-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "TRIAL",
    "api_key": "sk-your-gpt4o-mini-key-here",
    "model": "gpt-4o-mini"
  }'

# BASIC tier (gpt-4o-mini)
curl -X POST http://localhost:8100/api/admin/openai-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "BASIC",
    "api_key": "sk-your-gpt4o-mini-key-here",
    "model": "gpt-4o-mini"
  }'

# ADVANCED tier (gpt-4o)
curl -X POST http://localhost:8100/api/admin/openai-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "ADVANCED",
    "api_key": "sk-your-gpt4o-key-here",
    "model": "gpt-4o"
  }'

# PRO tier (gpt-5)
curl -X POST http://localhost:8100/api/admin/openai-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "PRO",
    "api_key": "sk-your-gpt5-key-here",
    "model": "gpt-5"
  }'
```

Stop the server (Ctrl+C).

### Step 5: Build Admin Panel

```bash
cd admin-panel

# Install dependencies
yarn install

# Update API URL for production
echo "REACT_APP_API_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8100" > .env

# Build
yarn build

cd ..
```

### Step 6: Setup Systemd Service

Create service file:
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
Environment="PATH=/home/ubuntu/licensing-server/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/licensing-server/venv/bin/python server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

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

### Step 7: Configure Firewall

```bash
# Allow port 8100 (if using UFW)
sudo ufw allow 8100/tcp

# Or configure AWS Security Group to allow port 8100
```

### Step 8: Upload Scrip Master

1. Download latest from Dhan:
```bash
wget https://images.dhan.co/api-data/api-scrip-master.csv -O /tmp/api-scrip-master.csv
```

2. Upload via admin panel or API:
```bash
curl -X POST "http://localhost:8100/api/admin/scrip-master/upload?version=$(date +%Y-%m)" \
  -F "file=@/tmp/api-scrip-master.csv"
```

## 🌐 Access Admin Panel

Open in browser:
```
http://YOUR_EC2_PUBLIC_IP:8100/admin
```

## ✅ Testing

### Test Health
```bash
curl http://localhost:8100/health
```

### Create Test License
```bash
curl -X POST http://localhost:8100/api/licenses/create \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "PRO",
    "user_email": "test@example.com",
    "user_name": "Test User",
    "notes": "Test license"
  }'
```

Save the returned license key!

### Test Validation
```bash
curl -X POST http://localhost:8100/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "TYODA-XXXX-XXXX-XXXX-XXXX"
  }'
```

You should receive the OpenAI key and features in the response.

## 📊 Monitoring

### View Logs
```bash
sudo journalctl -u tradeyoda-licensing -f
```

### Check Service Status
```bash
sudo systemctl status tradeyoda-licensing
```

### View Statistics
```bash
curl http://localhost:8100/api/admin/stats
```

## 🔄 Updating

```bash
cd /home/ubuntu/licensing-server
git pull
source venv/bin/activate
pip install -r requirements.txt

# Rebuild admin panel if needed
cd admin-panel
yarn install
yarn build
cd ..

# Restart service
sudo systemctl restart tradeyoda-licensing
```

## 🔐 Security Checklist

- [ ] Changed `SECRET_KEY` in `.env`
- [ ] Changed `ENCRYPTION_KEY` in `.env`
- [ ] Set strong `ADMIN_PASSWORD`
- [ ] Configured firewall/security group
- [ ] Added HTTPS (optional but recommended)
- [ ] Backup `licensing.db` regularly
- [ ] Restrict admin panel access (IP whitelist)

## 🆘 Troubleshooting

### Service won't start
```bash
sudo journalctl -u tradeyoda-licensing -n 50
```

### Port already in use
```bash
sudo lsof -i :8100
# Kill the process or change port in .env
```

### Admin panel not loading
```bash
# Check if build exists
ls -la admin-panel/build/

# Rebuild if needed
cd admin-panel
yarn build
```

### Database errors
```bash
# Reset database (WARNING: deletes all data)
rm licensing.db
python setup_initial_data.py
```

## 📞 Support

For issues, contact: gaur.samal@gmail.com

## 🎉 Success!

Your licensing server is now running!

- **API**: http://YOUR_EC2_IP:8100
- **Admin Panel**: http://YOUR_EC2_IP:8100/admin
- **Health Check**: http://YOUR_EC2_IP:8100/health

Next: Configure TradeYoda desktop app to use this licensing server!

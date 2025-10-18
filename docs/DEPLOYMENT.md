# Deployment Guide

## Local Deployment

### Standard Installation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py

## Docker Deployment

### Using Docker Compose (Recommended)

Start
docker-compose up -d

View logs
docker-compose logs -f trading-agent

Stop
docker-compose down

### Manual Docker
Build
docker build -t nifty-ai-trader .

Run
docker run -d
-p 8501:8501
-v $(pwd)/logs:/app/logs
-v $(pwd)/data:/app/data
--env-file .env
--name nifty-trader
nifty-ai-trader


## Cloud Deployment

### AWS EC2
1. Launch EC2 instance (t2.medium or higher)
2. Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

3. Clone and deploy
git clone https://github.com/yourusername/nifty-ai-trader.git
cd nifty-ai-trader
docker-compose up -d

Final Instructions to Push to GitHub
# 1. Initialize git repository
git init

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "Initial commit: AI Trading Agent v1.0.0"

# 4. Create GitHub repository (on github.com)
# Then add remote:
git remote add origin https://github.com/YOUR_USERNAME/nifty-ai-trader.git

# 5. Push to GitHub
git branch -M main
git push -u origin main


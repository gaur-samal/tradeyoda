# 🧙‍♂️ Trade Yoda

**AI-Powered Algorithmic Trading System for Nifty 50 Options**

Trade Yoda is an intelligent trading system that combines advanced technical analysis, supply/demand zones, and LLM-powered decision-making to trade Nifty 50 index options on the Indian stock market.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

### 🎯 **Advanced Technical Analysis**
- **Volume Profile** - POC, VAH, VAL calculation for institutional levels
- **Order Blocks** - Identifies smart money entry/exit zones
- **Fair Value Gaps** - Detects price inefficiencies for mean reversion
- **Multi-Indicator Analysis** - RSI, Bollinger Bands, Candlestick & Chart Patterns

### 🤖 **AI-Enhanced Trading**
- **LLM Zone Validation** - GPT-4 validates and ranks supply/demand zones
- **Intelligent Trade Evaluation** - Multi-factor confluence scoring
- **Risk Management** - Dynamic stop-loss and target calculations
- **Adaptive Strategy** - Zones refresh every 15 minutes during market hours

### 📊 **Options Trading**
- Automated strike selection based on technical zones
- OI (Open Interest) and IV (Implied Volatility) analysis
- Intraday-optimized risk:reward ratios (2:1 minimum)
- Support for both CALL and PUT options

### 🖥️ **Modern Web Interface**
- Real-time dashboard with live price updates
- Trade monitoring and performance analytics
- Configurable parameters via GUI
- Secure Dhan API credential management

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│ Frontend (React) │
│ Real-time Dashboard & Controls │
└────────────────────┬────────────────────────────────┘
│ REST API + WebSocket
┌────────────────────▼────────────────────────────────┐
│ Backend (FastAPI + Python) │
│ │
│ ┌──────────────────────────────────────────────┐ │
│ │ Orchestrator (Main Engine) │ │
│ └──────────────────────────────────────────────┘ │
│ │ │ │ │
│ ┌────────▼───┐ ┌──────▼──────┐ ┌───▼─────┐ │
│ │ Data │ │ Technical │ │ LLM │ │
│ │ Agent │ │ Analysis │ │ Agent │ │
│ └────────────┘ └─────────────┘ └─────────┘ │
│ │ │ │ │
│ ┌────────▼───┐ ┌──────▼──────┐ ┌───▼─────┐ │
│ │ Options │ │ Execution │ │ Database│ │
│ │ Agent │ │ Agent │ │ │ │
│ └────────────┘ └─────────────┘ └─────────┘ │
└──────────────────────────────────────────────────────┘
│
┌──────▼──────┐
│ Dhan HQ API │
│ (Broker API) │
└─────────────┘


---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Dhan Trading Account** ([Sign up here](https://dhan.co))
- **OpenAI API Key** (for LLM features)

### Installation

#### 1. Clone the Repository

https://github.com/gaur-samal/tradeyoda.git
cd tradeyoda


#### 2. Backend Setup

Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Configure environment variables
cp .env.example .env
nano .env # Edit with your credentials


#### 3. Frontend Setup

cd frontend
npm install
npm run build
cd ..


#### 4. Configure Systemd Services (Production)

Backend service
sudo cp deployment/tradeyoda.service /etc/systemd/system/
sudo systemctl enable tradeyoda
sudo systemctl start tradeyoda

Nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/tradeyoda
sudo ln -s /etc/nginx/sites-available/tradeyoda /etc/nginx/sites-enabled/
sudo systemctl restart nginx


---

## ⚙️ Configuration

### Environment Variables (`.env`)


Dhan API Credentials
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token

OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

Trading Parameters
USE_SANDBOX=true
RISK_REWARD_RATIO=2.0
MAX_RISK_PERCENTAGE=1.5
MIN_PROBABILITY_THRESHOLD=72.0

Timeframes (in minutes)
ZONE_TIMEFRAME=15
TRADE_TIMEFRAME=5
ZONE_REFRESH_INTERVAL=15

Technical Indicators
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
BB_PERIOD=20
BB_STD_DEV=2.0

Nifty Configuration
NIFTY_FUTURES_SECURITY_ID=52168 # Update monthly
NIFTY_INDEX_SECURITY_ID=13


### GUI Configuration

Access settings at `http://your-server/settings` to configure:
- Dhan API credentials (updated daily)
- Risk parameters
- Technical indicator periods
- Experimental features

---

## 📖 Usage

### Development Mode

Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Start frontend (separate terminal)
cd frontend
npm run dev



### Production Mode

Start services
sudo systemctl start tradeyoda
sudo systemctl start nginx

View logs
sudo journalctl -u tradeyoda -f


### Trading Workflow

1. **Start System** - Click "Start System" in the dashboard
2. **Zone Analysis** - System identifies supply/demand zones (runs every 15 min)
3. **Trade Identification** - Checks for trade opportunities (every 5 min)
4. **Automatic Execution** - Places orders when LLM approves setup
5. **Position Management** - Monitors and exits based on targets/stops

---

## 🎯 Strategy Overview

### Zone Identification
1. Calculate **Volume Profile** (POC, VAH, VAL)
2. Identify **Order Blocks** (institutional levels)
3. Find **Fair Value Gaps** (price inefficiencies)
4. Combine indicators for **confluence zones**
5. **LLM validates** and ranks zones by quality

### Trade Entry
- **Demand Zone** (support) → Buy CALL options
- **Supply Zone** (resistance) → Buy PUT options
- Entry when price within 50 points of zone
- Minimum 2:1 risk:reward ratio
- LLM evaluates probability (>72% threshold)

### Risk Management
- Stop Loss: 5% of premium
- Target: Nearest opposite zone (max 150 points)
- Max risk per trade: 1.5% of capital
- No trades on weekly expiry day

---

## 📊 Performance Metrics

Track performance in the **Dashboard**:
- Total Trades
- Win Rate
- Average Profit/Loss
- Risk:Reward Ratio
- Drawdown

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance async API framework
- **Python 3.10+** - Core logic and algorithms
- **Pandas/NumPy** - Data processing and analysis
- **OpenAI API** - LLM-powered decision making
- **DhanHQ SDK** - Broker integration
- **SQLite** - Trade database

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Recharts** - Data visualization

---

## ⚠️ Risk Disclaimer

**IMPORTANT:** This is an algorithmic trading system that involves real financial risk.

- ❌ **Not Financial Advice** - Use at your own risk
- ⚠️ **Test Thoroughly** - Use sandbox mode before live trading
- 💰 **Start Small** - Begin with minimal capital
- 📉 **Can Lose Money** - Past performance ≠ future results
- 🔒 **Secure Your Credentials** - Never commit API keys to git

**Recommended:** Thoroughly backtest and paper trade for at least 1 month before live deployment.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [DhanHQ API](https://api.dhan.co/)
- Powered by [OpenAI GPT-4](https://openai.com/)
- Technical analysis inspired by institutional trading strategies

---

## 📧 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/gaur-samal/tradeyoda/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gaur-samal/tradeyoda/discussions)
- **Email:** gaur.samal@gmail.com

---

## 🗺️ Roadmap

- [ ] Multi-timeframe analysis
- [ ] Advanced Greeks calculation
- [ ] Backtesting engine
- [ ] Strategy optimization
- [ ] Mobile app
- [ ] Multi-broker support
- [ ] Cloud deployment templates

---

**Made with ❤️ by [Gaur Samal]**

*Trade responsibly. May the Force (and the zones) be with you!* 🧙‍♂️


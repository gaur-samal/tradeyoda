# 🤖 Nifty AI Trader

AI-powered automated trading system for Nifty 50 options using multi-agent architecture with GPT-4 intelligence.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ✨ Features

- **🤖 AI-Powered Analysis**: GPT-4 for intelligent market analysis and trade decisions
- **📊 Advanced Technical Analysis**: 
  - Volume Profile (Fixed Range & Session)
  - Order Blocks Detection
  - Fair Value Gap Analysis
  - Supply/Demand Zone Identification
- **⚡ Real-Time Data**: WebSocket feeds for live market data and order updates
- **🎯 Automated Execution**: Bracket orders with stop-loss and target
- **📈 Risk Management**: 1:3 RR with 2% max risk, 80% probability threshold
- **🧪 Paper Trading**: Sandbox mode for risk-free testing
- **💻 Professional UI**: Real-time dashboard with Streamlit

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│ Streamlit UI │
└───────────────────┬─────────────────────────────────┘
│
┌───────────────────▼─────────────────────────────────┐
│ Trading Orchestrator │
└──┬─────┬──────┬─────────┬───────────┬──────────────┘
│ │ │ │ │
┌──▼─┐ ┌─▼──┐ ┌─▼──┐ ┌──▼───┐ ┌───▼────┐
│Data│ │Tech│ │LLM │ │Option│ │Execute │
│ │ │ │ │ │ │ │ │ │
└──┬─┘ └─┬──┘ └─┬──┘ └──┬───┘ └───┬────┘
│ │ │ │ │
┌──▼─────▼──────▼────────▼───────────▼──────┐
│ Dhan API & OpenAI API │
└────────────────────────────────────────────┘

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Dhan Trading Account ([Register](https://dhan.co))
- OpenAI API Key ([Get Key](https://platform.openai.com))

### Installation

1. **Clone the repository:**

git clone https://github.com/yourusername/nifty-ai-trader.git
cd nifty-ai-trader


2. **Create virtual environment:**
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate


3. **Install dependencies:**
pip install -r requirements.txt


4. **Configure environment:**
cp .env.example .env

5. **Run the application:**
streamlit run app/streamlit_app.py

### Docker Deployment

Build and run with Docker Compose
docker-compose up -d

View logs
docker-compose logs -f

Stop
docker-compose down

## ⚙️ Configuration

Edit `.env` file:

Dhan API
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token

OpenAI API
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4-turbo-preview

Trading Settings
USE_SANDBOX=true
RISK_REWARD_RATIO=3.0
MAX_RISK_PERCENTAGE=2.0
MIN_PROBABILITY_THRESHOLD=80.0

## 📖 Usage

### Getting API Credentials

1. **Dhan API:**
   - Login to [DhanHQ Portal](https://dhanhq.co)
   - Navigate to API section
   - Generate Client ID and Access Token
   - For sandbox: Use sandbox credentials

2. **OpenAI API:**
   - Visit [OpenAI Platform](https://platform.openai.com)
   - Create account and generate API key
   - GPT-4 access required

### Running the System

1. **Start the application:**
streamlit run app/streamlit_app.py

2. **Configure in UI:**
- Enter API credentials in sidebar
- Enable Sandbox mode for testing
- Set risk parameters

3. **Start Trading:**
- Click "Start" button
- System will run analysis cycles automatically
- Monitor trades in real-time

### Analysis Cycles

- **15-min Cycle**: Zone identification using Volume Profile, Order Blocks, FVG
- **3-min Cycle**: Trade identification and execution
- **Real-time**: Order updates and position monitoring

## 🧪 Testing

Run tests
pytest

With coverage
pytest --cov=src --cov-report=html

Run specific test
pytest tests/test_data_agent.py

## 📊 Features Breakdown

### Technical Analysis
- **Volume Profile**: Identifies POC, VAH, VAL for price levels with high trading activity
- **Order Blocks**: Detects institutional buying/selling zones
- **Fair Value Gaps**: Identifies price imbalances for potential reversals
- **Supply/Demand Zones**: Combines all indicators for high-probability zones

### AI Decision Making
- **Zone Validation**: GPT-4 analyzes technical confluence
- **Trade Evaluation**: Assesses probability and risk
- **Dynamic Adaptation**: Learns from market conditions

### Risk Management
- **Position Sizing**: Automated based on capital and risk
- **Stop Loss**: 2% maximum risk per trade
- **Take Profit**: 1:3 minimum risk-reward ratio
- **Probability Filter**: Only trades with 80%+ success probability

## 🔒 Security

- ✅ API credentials stored in `.env` (not committed)
- ✅ Sandbox mode for testing
- ✅ Input validation on all API calls
- ✅ Error handling and logging
- ✅ Rate limiting compliance

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational purposes only. 

- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Always test in sandbox mode first
- Never trade with money you cannot afford to lose
- The developers are not responsible for any financial losses

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📧 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/nifty-ai-trader/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/nifty-ai-trader/discussions)

## 🙏 Acknowledgments

- [DhanHQ](https://dhanhq.co) for trading API
- [OpenAI](https://openai.com) for GPT-4
- [Streamlit](https://streamlit.io) for UI framework

---

Made with ❤️ for the trading community


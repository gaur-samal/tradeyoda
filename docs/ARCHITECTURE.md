# System Architecture

## Overview

The AI Trading Agent uses a multi-agent architecture where specialized agents handle different aspects of the trading workflow.

┌─────────────────────────────────────────────────────────────┐
│ Streamlit UI │
│ (Multi-page app with real-time dashboard) │
└────────────────────┬────────────────────────────────────────┘
│
┌────────────────────▼────────────────────────────────────────┐
│ Trading Orchestrator │
│ - Coordinates all agents │
│ - Manages analysis cycles (15-min, 3-min) │
│ - Handles trade lifecycle │
└─┬────┬─────┬─────────┬──────────┬────────────────────────┬─┘
│ │ │ │ │ │
┌─▼─┐┌─▼──┐┌─▼───┐┌────▼────┐┌───▼──────┐ ┌────▼──────┐
│Data││Tech││ LLM ││ Options ││Execution │ │ Database │
│ ││ ││ ││ ││ │ │ │
└─┬──┘└─┬──┘└─┬───┘└────┬────┘└───┬──────┘ └───────────┘
│ │ │ │ │
┌─▼─────▼─────▼─────────▼─────────▼───────────────────────────┐
│ External Services │
│ - Dhan API (Market Data, Trading) │
│ - OpenAI API (GPT-4 Analysis) │
└──────────────────────────────────────────────────────────────┘


## Components

### 1. Data Collection Agent

**Responsibilities:**
- Real-time market data via WebSocket
- Historical data fetching
- Option chain retrieval
- Data caching and management

**Technologies:**
- Dhan MarketFeed (WebSocket)
- REST API for historical data
- Threading for concurrent operations

**Key Methods:**
- `start_live_feed()`: Initialize WebSocket connection
- `fetch_historical_data()`: Get OHLCV data
- `fetch_option_chain()`: Get options data

### 2. Technical Analysis Agent

**Responsibilities:**
- Volume Profile calculation
- Order Block identification
- Fair Value Gap detection
- Supply/Demand zone analysis

**Techniques:**
- Volume distribution analysis
- Price action patterns
- Multi-indicator confluence

**Key Methods:**
- `calculate_volume_profile()`: POC, VAH, VAL
- `identify_order_blocks()`: Smart money zones
- `identify_fair_value_gaps()`: Price imbalances
- `identify_supply_demand_zones()`: Combined analysis

### 3. LLM Analysis Agent

**Responsibilities:**
- Intelligent market analysis
- Trade setup evaluation
- Risk assessment
- Decision making with 80% threshold

**Model:**
- GPT-4 Turbo
- Temperature: 0.1 (consistent results)
- JSON response format

**Key Methods:**
- `analyze_zones()`: Validate technical zones
- `evaluate_trade_setup()`: Assess trade probability

### 4. Options Analysis Agent

**Responsibilities:**
- Option chain analysis
- PCR calculation
- Max pain identification
- Strike selection
- Greeks analysis (if available)

**Key Methods:**
- `analyze_option_chain()`: Comprehensive analysis
- `select_best_strike()`: Optimal strike based on zones

### 5. Execution Agent

**Responsibilities:**
- Order placement and management
- Real-time order updates via WebSocket
- Position monitoring
- Risk management

**Features:**
- Bracket orders (SL + Target)
- Order modification
- Real-time status updates

**Key Methods:**
- `place_order()`: Execute single order
- `place_bracket_order()`: SL + Target orders
- `modify_order()`: Update pending orders
- `cancel_order()`: Cancel orders

## Data Flow

### Analysis Cycle (15 minutes)

Fetch Historical Data (15-min candles, last 30 days)

Calculate Volume Profile

Identify Order Blocks

Identify Fair Value Gaps

Combine into Supply/Demand Zones

LLM validates and analyzes zones

Cache results for trade identification

### Trade Cycle (3 minutes)

Check cached zone analysis (< 15 min old)

Get live price feed

Check if price near high-confidence zone

If yes:
a. Fetch option chain
b. Analyze options (PCR, max pain, etc.)
c. Select optimal strike
d. Create trade setup

LLM evaluates trade setup

If probability >= 80%:
a. Calculate position size
b. Place bracket order
c. Monitor execution


## Real-Time Updates

### Market Feed (WebSocket)

MarketFeed → Queue → latest_data cache → UI update


- Continuous price updates
- Volume tracking
- Bid/Ask spreads

### Order Updates (WebSocket)

OrderUpdate → Callback → Trade status update → UI notification


- Order placement confirmation
- Fill notifications
- P&L updates

## State Management

### Session State (Streamlit)

st.session_state = {
'orchestrator': TradingOrchestrator,
'running': bool,
'trades': List[Dict],
'last_analysis': Dict,
'config_updated': bool
}

### Analysis Cache

analysis_cache = {
'zones': Dict,
'llm_analysis': Dict,
'vp_data': Dict,
'market_context': Dict,
'timestamp': datetime,
'current_price': float
}

### Active Trades

trade_record = {
'timestamp': datetime,
'direction': str,
'entry_price': float,
'target_price': float,
'stop_loss': float,
'risk_reward': float,
'probability': float,
'confidence': float,
'status': str,
'pnl': float,
'order_ids': Dict
}


## Error Handling

### Retry Strategy

max_retries = 3
backoff = exponential (1s, 2s, 4s)



### Circuit Breaker

- API failures: 5 consecutive → pause 60s
- Data errors: Log and continue
- Critical errors: Stop system

### Logging

levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
outputs = [console, file]
rotation = '100 MB'
retention = '30 days'

## Security

### API Keys

- Stored in `.env` file
- Never committed to git
- Loaded via `python-dotenv`

### Data Protection

- No sensitive data in logs
- Secure WebSocket connections
- Input validation on all APIs

## Scalability

### Current Limitations

- Single instrument (Nifty 50)
- Single strategy
- No parallel trade execution

### Future Enhancements

- Multi-instrument support
- Strategy plugins
- Distributed architecture
- Database persistence

## Performance

### Expected Latency

- Market data: < 100ms
- Historical fetch: 1-2s
- LLM analysis: 2-5s
- Order placement: < 500ms

### Resource Usage

- RAM: ~500MB
- CPU: 10-20% (idle), 50-70% (analysis)
- Network: 1-5 Mbps

## Monitoring

### Metrics

- System uptime
- Analysis cycle time
- Trade execution time
- API response times
- Error rates

### Alerts

- System failures
- API errors
- Trade execution issues
- Risk limit breaches


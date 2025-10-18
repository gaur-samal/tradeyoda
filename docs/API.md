# API Documentation

## Dhan API Integration

### Market Feed WebSocket

from dhanhq import MarketFeed

Subscribe to instruments
instruments = [
(MarketFeed.NSE, "13", MarketFeed.Full)
]

market_feed = MarketFeed(dhan_context, instruments, version="v2")

#### Packet Types
- **Ticker**: Basic price info (LTP, volume)
- **Quote**: Detailed quotes (OHLC, bid/ask)
- **Full**: Complete data (Greeks, OI, etc.)

### Order Update WebSocket

from dhanhq import OrderUpdate

order_update = OrderUpdate(dhan_context)
order_update.on_update = callback_function


### Historical Data

Intraday minute data
data = dhan.intraday_minute_data(
security_id="13",
exchange_segment="IDX_I",
instrument_type="INDEX"
)


### Option Chain

option_chain = dhan.option_chain(
under_security_id=13,
under_exchange_segment="IDX_I",
expiry="2025-10-30"
)

### Order Placement

Place order
order = dhan.place_order(
security_id="52175",
exchange_segment=dhan.NSE_FNO,
transaction_type=dhan.BUY,
quantity=50,
order_type=dhan.LIMIT,
product_type=dhan.INTRADAY,
price=100.50
)


### Bracket Orders

Bracket order with SL and target
order = dhan.place_order(
security_id="52175",
exchange_segment=dhan.NSE_FNO,
transaction_type=dhan.BUY,
quantity=50,
order_type=dhan.LIMIT,
product_type=dhan.BO,
price=100.50,
bo_profit_value=3.0,
bo_stop_loss_Value=1.0
)

## OpenAI API Integration

### Chat Completions

from openai import OpenAI

client = OpenAI(api_key="your-key")

response = client.chat.completions.create(
model="gpt-4-turbo-preview",
messages=[
{"role": "system", "content": "You are a trading analyst."},
{"role": "user", "content": "Analyze this market data..."}
],
temperature=0.1,
response_format={"type": "json_object"}
)

### Best Practices

1. **Temperature**: Use 0.1-0.2 for consistent analysis
2. **JSON Mode**: Always use for structured responses
3. **System Prompts**: Be specific about role and output format
4. **Rate Limits**: Monitor usage and implement retries

## Internal API

### DataCollectionAgent

Start live feed
agent.start_live_feed(instruments)

Get live quote
quote = agent.get_live_quote(security_id)

Fetch historical data
df = agent.fetch_historical_data(
security_id="13",
exchange_segment="IDX_I",
instrument_type="INDEX",
timeframe="15"
)

### TechnicalAnalysisAgent

Calculate volume profile
vp_data = agent.calculate_volume_profile(df, value_area=70)

Identify order blocks
order_blocks = agent.identify_order_blocks(df, lookback=20)

Identify FVGs
fvgs = agent.identify_fair_value_gaps(df)

Get supply/demand zones
zones = agent.identify_supply_demand_zones(df, vp_data, order_blocks, fvgs)


### LLMAnalysisAgent

Analyze zones
analysis = agent.analyze_zones(technical_data, market_context)

Evaluate trade
evaluation = agent.evaluate_trade_setup(trade_data)


### OptionsAnalysisAgent

Analyze option chain
analysis = agent.analyze_option_chain(option_chain, spot_price, zones)

Select best strike
trade_setup = agent.select_best_strike(zones, option_analysis, "CALL")

### ExecutionAgent

Place order
result = agent.place_order(order_params)

Place bracket order
result = agent.place_bracket_order(trade_setup)

Modify order
result = agent.modify_order(order_id, price=new_price)

Cancel order
result = agent.cancel_order(order_id)


## Error Codes

### Dhan API Errors

- `400`: Bad Request
- `401`: Unauthorized
- `429`: Rate Limit Exceeded
- `500`: Server Error

### Internal Errors

- `CONFIG_ERROR`: Configuration missing or invalid
- `DATA_ERROR`: Data fetch or processing failed
- `ANALYSIS_ERROR`: Technical analysis failed
- `EXECUTION_ERROR`: Order execution failed



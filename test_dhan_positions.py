"""
Test script to fetch and display Dhan API responses.
Run this to see the actual structure of positions, orders, etc.
"""
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq

# Load environment variables
load_dotenv()

def pretty_print(title: str, data: dict):
    """Pretty print JSON data."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)
    print(json.dumps(data, indent=2, default=str))
    print("="*80 + "\n")

def save_to_file(filename: str, data: dict):
    """Save response to JSON file."""
    os.makedirs("test_responses", exist_ok=True)
    with open(f"test_responses/{filename}", "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ Saved to test_responses/{filename}")

def main():
    """Test Dhan API responses."""
    
    print("🔍 Testing Dhan API Responses...")
    print(f"⏰ Test Time: {datetime.now()}\n")
    
    # Get credentials from .env
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    
    if not client_id or not access_token:
        print("❌ Error: DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN not found in .env file")
        print("Please ensure these are set in your .env file:")
        print("   DHAN_CLIENT_ID=your_client_id")
        print("   DHAN_ACCESS_TOKEN=your_access_token")
        return
    
    print(f"✅ Client ID: {client_id}")
    print(f"✅ Access Token: {'*' * len(access_token[:10])}... (hidden)")
    
    # Initialize Dhan client
    dhan_context = DhanContext(client_id, access_token)
    dhan = dhanhq(dhan_context)
    
    print(f"✅ Dhan client initialized\n")
    
    # Test 1: Get Positions
    print("📊 Test 1: Fetching Positions...")
    try:
        positions = dhan.get_positions()
        pretty_print("GET POSITIONS RESPONSE", positions)
        save_to_file("positions.json", positions)
        
        # Show sample position structure
        if positions.get("status") == "success":
            data = positions.get("data", [])
            print(f"ℹ️ Found {len(data)} position(s)")
            
            if data:
                print("\n📋 Sample Position Fields:")
                sample = data[0]
                for key in sorted(sample.keys()):
                    value = sample.get(key)
                    print(f"   {key:25s}: {type(value).__name__:10s} = {value}")
        else:
            print(f"⚠️ Status: {positions.get('status')}")
            print(f"   Message: {positions.get('remarks', {}).get('error_message', 'No error message')}")
        
    except Exception as e:
        print(f"❌ Error fetching positions: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Get Order List
    print("\n📋 Test 2: Fetching Order List...")
    try:
        orders = dhan.get_order_list()
        pretty_print("GET ORDER LIST RESPONSE", orders)
        save_to_file("orders.json", orders)
        
        # Show sample order structure
        if orders.get("status") == "success":
            data = orders.get("data", [])
            print(f"ℹ️ Found {len(data)} order(s)")
            
            if data:
                print("\n📋 Sample Order Fields:")
                sample = data[0]
                for key in sorted(sample.keys()):
                    value = sample.get(key)
                    print(f"   {key:25s}: {type(value).__name__:10s} = {value}")
        else:
            print(f"⚠️ Status: {orders.get('status')}")
        
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Get Trade Book (last order if available)
    print("\n📖 Test 3: Fetching Trade Book...")
    try:
        orders = dhan.get_order_list()
        if orders.get("status") == "success" and orders.get("data"):
            last_order = orders["data"][0]
            last_order_id = last_order.get("orderId")
            if last_order_id:
                print(f"   Using order ID: {last_order_id}")
                trades = dhan.get_trade_book(last_order_id)
                pretty_print("GET TRADE BOOK RESPONSE", trades)
                save_to_file("trades.json", trades)
                
                if trades.get("status") == "success" and trades.get("data"):
                    print(f"ℹ️ Found {len(trades['data'])} trade(s)")
            else:
                print("ℹ️ No order ID available")
        else:
            print("ℹ️ No orders found to fetch trade book")
    except Exception as e:
        print(f"❌ Error fetching trade book: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Get Fund Limits
    print("\n💰 Test 4: Fetching Fund Limits...")
    try:
        funds = dhan.get_fund_limits()
        pretty_print("GET FUND LIMITS RESPONSE", funds)
        save_to_file("funds.json", funds)
        
        # Show available fields
        if funds.get("status") == "success" and funds.get("data"):
            print("\n📋 Fund Limit Fields:")
            data = funds["data"]
            for key in sorted(data.keys()):
                value = data.get(key)
                print(f"   {key:30s}: {type(value).__name__:10s} = {value}")
    except Exception as e:
        print(f"❌ Error fetching fund limits: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Get Holdings
    print("\n📦 Test 5: Fetching Holdings...")
    try:
        holdings = dhan.get_holdings()
        pretty_print("GET HOLDINGS RESPONSE", holdings)
        save_to_file("holdings.json", holdings)
        
        if holdings.get("status") == "success":
            data = holdings.get("data", [])
            print(f"ℹ️ Found {len(data)} holding(s)")
    except Exception as e:
        print(f"❌ Error fetching holdings: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Get Trade History (last 7 days)
    print("\n📊 Test 6: Fetching Trade History...")
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"   Date range: {from_date} to {to_date}")
        history = dhan.get_trade_history(from_date, to_date, page_number=0)
        pretty_print("GET TRADE HISTORY RESPONSE", history)
        save_to_file("trade_history.json", history)
        
        if history.get("status") == "success":
            data = history.get("data", [])
            print(f"ℹ️ Found {len(data)} trade(s) in history")
    except Exception as e:
        print(f"❌ Error fetching trade history: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("✅ Testing Complete!")
    print("="*80)
    print("\n📁 All responses saved to test_responses/ directory")
    print("\nFiles created:")
    print("   ✓ test_responses/positions.json")
    print("   ✓ test_responses/orders.json")
    print("   ✓ test_responses/trades.json")
    print("   ✓ test_responses/funds.json")
    print("   ✓ test_responses/holdings.json")
    print("   ✓ test_responses/trade_history.json")
    print("\n💡 Share these JSON files to get accurate implementation code!")

if __name__ == "__main__":
    main()


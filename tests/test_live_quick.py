"""
Quick test of live trading initialization to verify it's working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from live_trader import LiveTrader

print("="*60)
print("QUICK LIVE TRADING TEST")
print("="*60)

try:
    # Initialize trader
    print("\n[1/3] Initializing live trader...")
    trader = LiveTrader(
        initial_capital=10000,
        check_interval=5,  # 5 seconds for quick test
        use_testnet=True
    )
    print("   [OK] Initialization complete!")

    # Test fetching current price
    print("\n[2/3] Fetching current market data...")
    current_price = trader.executor.get_current_price()
    print(f"   [OK] Current BTC Price: ${current_price:,.2f}")

    # Test portfolio state
    print("\n[3/3] Getting portfolio state...")
    portfolio = trader.executor.get_portfolio_value(current_price)
    print(f"   [OK] Portfolio Value: ${portfolio['total_value_usd']:,.2f}")
    print(f"       - BTC: {portfolio['btc_balance']:.6f}")
    print(f"       - USDT: ${portfolio['usdt_balance']:,.2f}")

    # Test one trading cycle (should work now with preloaded data!)
    print(f"\n[4/4] Testing trading cycle with {len(trader.price_history)} data points...")
    trader.trading_cycle()

    print("\n" + "="*60)
    print("[SUCCESS] Live trading is READY!")
    print("="*60)
    print(f"\nWith {len(trader.price_history)} historical prices pre-loaded:")
    print("  ✅ Indicators can be calculated immediately")
    print("  ✅ Trading decisions can be made from first cycle")
    print("  ✅ No waiting period needed!")
    print("\nTo start live trading:")
    print("  python main.py --mode live")
    print("  python live_trader.py --interval 60 --duration 8  # 8 hours, 1-min intervals")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

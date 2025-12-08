#!/usr/bin/env python3
"""
Quick script to sell some BTC for USDT on Binance Testnet
(Gives you more cash to test DCA/Swing strategies)
"""

from src.execution.binance_executor import BinanceExecutor

def main():
    print("="*60)
    print("CONVERT BTC -> USDT (Testnet)")
    print("="*60)

    executor = BinanceExecutor(use_testnet=True)

    # Check current balances
    print("\n[1/4] Current Balances:")
    btc_balance = executor.get_balance('BTC')
    usdt_balance = executor.get_balance('USDT')
    current_price = executor.get_current_price()

    print(f"   BTC: {btc_balance['total']:.6f} (${btc_balance['total'] * current_price:,.2f})")
    print(f"   USDT: ${usdt_balance['total']:,.2f}")
    print(f"   Current BTC Price: ${current_price:,.2f}")

    # Calculate how much BTC to sell
    print("\n[2/4] Calculating...")
    target_usdt = 1000  # Get $1,000 USDT for testing
    btc_to_sell = target_usdt / current_price

    # Round to 5 decimal places (Binance BTC precision)
    btc_to_sell = round(btc_to_sell, 5)

    if btc_to_sell > btc_balance['free']:
        print(f"   [WARNING] Not enough BTC to get ${target_usdt}")
        print(f"   Max available: ${btc_balance['free'] * current_price:,.2f}")
        btc_to_sell = round(btc_balance['free'] * 0.5, 5)  # Sell 50% instead
        target_usdt = btc_to_sell * current_price

    # Ensure minimum order size (0.00001 BTC)
    if btc_to_sell < 0.00001:
        print(f"   [ERROR] Amount too small (min: 0.00001 BTC)")
        return

    print(f"   Will sell: {btc_to_sell:.5f} BTC")
    print(f"   Will get: ~${target_usdt:,.2f} USDT")

    # Confirm
    print("\n[3/4] Confirm:")
    response = input(f"   Sell {btc_to_sell:.5f} BTC for ~${target_usdt:,.2f} USDT? (yes/no): ")

    if response.lower() != 'yes':
        print("\n   [CANCELLED] No trade executed")
        return

    # Execute sell order
    print("\n[4/4] Executing SELL order...")
    try:
        # Format quantity to 5 decimal places (string format for API)
        result = executor.place_market_order('SELL', quantity=float(f"{btc_to_sell:.5f}"))

        print(f"\n   [SUCCESS] Order executed!")
        print(f"   Sold: {result['executed_qty']:.6f} BTC")
        print(f"   Price: ${result['executed_price']:,.2f}")
        print(f"   Received: ${result['executed_value']:,.2f} USDT")

        # Show new balances
        print("\n" + "="*60)
        print("NEW BALANCES:")
        print("="*60)

        btc_balance = executor.get_balance('BTC')
        usdt_balance = executor.get_balance('USDT')

        print(f"   BTC: {btc_balance['total']:.6f} (${btc_balance['total'] * current_price:,.2f})")
        print(f"   USDT: ${usdt_balance['total']:,.2f} <- Ready for DCA/Swing!")

    except Exception as e:
        print(f"\n   [ERROR] Order failed: {e}")

    print("\n" + "="*60)
    print("[COMPLETE] You can now test DCA and Swing strategies!")
    print("="*60)

if __name__ == "__main__":
    main()

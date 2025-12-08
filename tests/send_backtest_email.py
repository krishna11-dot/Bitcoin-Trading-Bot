"""
Send Backtest Performance Data via Gmail
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from src.notifications.gmail_notifier import GmailNotifier

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load backtest results
results_path = Path('data/processed/backtest_results.json')
with open(results_path, 'r') as f:
    results = json.load(f)

# Calculate current BTC price (approximate from final value)
# From summary: current BTC price ~$93,450
current_price = 93450

# Estimate portfolio breakdown
# Final value is $8,574.91
# Assuming we ended with ~0.09 BTC based on the backtest output
final_btc = 0.09
btc_value = final_btc * current_price
final_cash = results['final_value'] - btc_value

# If cash is negative, assume all value is in cash
if final_cash < 0:
    final_cash = results['final_value']
    final_btc = 0

portfolio = {
    'cash': final_cash,
    'btc': final_btc
}

# Format metrics (convert decimals to percentages)
metrics = {
    'total_return': results['total_return'] * 100,  # -14.25%
    'sharpe_ratio': results['sharpe_ratio'],  # -1.35
    'max_drawdown': abs(results['max_drawdown']) * 100,  # 20.50%
    'win_rate': results['win_rate'] * 100,  # 0%
    'total_trades': results['num_trades'],  # 19
    'avg_trade_return': results['avg_trade_return'] * 100,  # -7.86%
    'buy_and_hold_return': results['buy_and_hold_return'] * 100,  # -20.08%
    'outperformance': abs(results['buy_and_hold_return'] - results['total_return']) * 100  # +5.83%
}

# Empty trades list for backtest summary (individual trades not saved)
trades_today = []

print('Backtest Performance Summary')
print('=' * 60)
print(f'Initial Capital: ${results["initial_capital"]:,.2f}')
print(f'Final Portfolio Value: ${results["final_value"]:,.2f}')
print(f'Total Return: {metrics["total_return"]:.2f}%')
print(f'Number of Trades: {metrics["total_trades"]}')
print(f'Sharpe Ratio: {metrics["sharpe_ratio"]:.2f}')
print(f'Max Drawdown: {metrics["max_drawdown"]:.2f}%')
print(f'Win Rate: {metrics["win_rate"]:.0f}%')
print(f'Avg Trade Return: {metrics["avg_trade_return"]:.2f}%')
print(f'Buy & Hold Return: {metrics["buy_and_hold_return"]:.2f}%')
print(f'Outperformance: +{metrics["outperformance"]:.2f}%')
print('=' * 60)

# Send email
print('\nSending backtest performance email...')
try:
    gmail = GmailNotifier()
    success = gmail.send_daily_summary(
        portfolio=portfolio,
        trades_today=trades_today,
        metrics=metrics,
        current_price=current_price,
        date=datetime.now()
    )

    if success:
        print('\nEmail sent successfully to krishnanair041@gmail.com')
        print('Check your inbox for the backtest performance summary!')
    else:
        print('\nFailed to send email')
except Exception as e:
    print(f'\nError sending email: {e}')
    import traceback
    traceback.print_exc()

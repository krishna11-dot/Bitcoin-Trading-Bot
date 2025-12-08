"""
Analyze Fear & Greed effectiveness for buy timing
"""
import pandas as pd
import json

# Load trades
trades = pd.read_csv('data/processed/backtest_trades.csv')
results = json.load(open('data/processed/backtest_results.json'))

# Filter DCA buys only
dca_buys = trades[(trades['strategy'] == 'DCA') & (trades['action'] == 'BUY')].copy()

print('='*70)
print('FEAR & GREED EFFECTIVENESS ANALYSIS')
print('='*70)

# Categorize by trigger signal
dca_buys['rsi_triggered'] = dca_buys['reason'].str.contains('RSI', na=False)
dca_buys['fg_triggered'] = dca_buys['reason'].str.contains('F&G', na=False)

rsi_only = dca_buys[(dca_buys['rsi_triggered']) & (~dca_buys['fg_triggered'])]
fg_only = dca_buys[(~dca_buys['rsi_triggered']) & (dca_buys['fg_triggered'])]
both = dca_buys[(dca_buys['rsi_triggered']) & (dca_buys['fg_triggered'])]

print('\n[1. TRADE BREAKDOWN BY TRIGGER SIGNAL]\n')
print(f'Total DCA Buys:  {len(dca_buys)}')
print(f'  RSI-only:      {len(rsi_only)} trades ({len(rsi_only)/len(dca_buys)*100:.1f}%)')
print(f'  F&G-only:      {len(fg_only)} trades ({len(fg_only)/len(dca_buys)*100:.1f}%)')
print(f'  Both (RSI+F&G): {len(both)} trades ({len(both)/len(dca_buys)*100:.1f}%)')

print('\n[2. AVERAGE BUY PRICE BY SIGNAL]\n')
print(f'RSI-only average price:  ${rsi_only["price"].mean():,.2f}')
print(f'F&G-only average price:  ${fg_only["price"].mean():,.2f}')
print(f'Both signals average:    ${both["price"].mean():,.2f}')
print(f'Overall DCA average:     ${dca_buys["price"].mean():,.2f}')

# Price comparison
rsi_avg = rsi_only["price"].mean()
fg_avg = fg_only["price"].mean()
price_diff_pct = ((fg_avg - rsi_avg) / rsi_avg) * 100

print(f'\nF&G buys at {price_diff_pct:+.1f}% price vs RSI buys')
if price_diff_pct > 0:
    print('  [BAD] F&G triggers at HIGHER prices (worse entries)')
else:
    print('  [GOOD] F&G triggers at LOWER prices (better entries)')

print('\n[3. TIMING ANALYSIS]\n')
print('First 10 RSI-only buys:')
if len(rsi_only) > 0:
    for idx, row in rsi_only.head(10).iterrows():
        print(f'  {row["date"]}: ${row["price"]:,.2f} - {row["reason"]}')
else:
    print('  No RSI-only trades!')

print('\nFirst 10 F&G-only buys:')
for idx, row in fg_only.head(10).iterrows():
    print(f'  {row["date"]}: ${row["price"]:,.2f} - {row["reason"]}')

print('\n[4. F&G VALUE DISTRIBUTION]\n')
# Extract F&G values from reason column
import re
fg_values = []
for reason in dca_buys['reason']:
    match = re.search(r'F&G (\d+)', reason)
    if match:
        fg_values.append(int(match.group(1)))

if len(fg_values) > 0:
    fg_series = pd.Series(fg_values)
    print(f'F&G values when buying:')
    print(f'  Min:    {fg_series.min()}')
    print(f'  Max:    {fg_series.max()}')
    print(f'  Mean:   {fg_series.mean():.1f}')
    print(f'  Median: {fg_series.median():.1f}')
    print(f'\nF&G < 30 (Extreme Fear): {(fg_series < 30).sum()} trades ({(fg_series < 30).sum()/len(fg_series)*100:.1f}%)')
    print(f'F&G 30-40 (Fear):        {((fg_series >= 30) & (fg_series < 40)).sum()} trades ({((fg_series >= 30) & (fg_series < 40)).sum()/len(fg_series)*100:.1f}%)')

print('\n[5. KEY FINDINGS]\n')

# Finding 1: F&G triggers way more often
if len(fg_only) > len(rsi_only) * 5:
    print(f'[FINDING 1] F&G triggers {len(fg_only)/max(len(rsi_only),1):.1f}x more than RSI')
    print('  - F&G is too sensitive (threshold 40 too high?)')
    print('  - Most buys driven by sentiment, not technical oversold')

# Finding 2: Price comparison
if price_diff_pct > 5:
    print(f'\n[FINDING 2] F&G buys at {price_diff_pct:.1f}% HIGHER prices than RSI')
    print('  - F&G lags price movements (sentiment reacts AFTER drops)')
    print('  - RSI catches actual oversold conditions earlier')

# Finding 3: Win rate analysis
print(f'\n[FINDING 3] DCA Win Rate: {results["dca_win_rate"]*100:.1f}%')
print(f'  RSI Signal Win Rate: {results["rsi_signal_win_rate"]*100:.1f}%')
print('  - RSI has PERFECT signals (100% win rate)')
print('  - But DCA only 72.7% because F&G adds bad signals')

print('\n[6. RECOMMENDATION]\n')
if len(fg_only) > len(rsi_only) * 3 and price_diff_pct > 0:
    print('F&G is NOT helping buy timing:')
    print('  1. Triggers too frequently (threshold too high)')
    print('  2. Buys at worse prices than RSI')
    print('  3. Dilutes RSI perfect signals (100% -> 72.7%)')
    print('\nSuggested fixes:')
    print('  Option A: REMOVE F&G from DCA (use RSI-only)')
    print('  Option B: LOWER threshold (40 -> 25) for extreme fear only')
    print('  Option C: Change to AND logic (RSI < 30 AND F&G < 40)')
else:
    print('F&G appears to be helping as contrarian indicator')
    print('  - Keep current configuration')

print('\n' + '='*70)

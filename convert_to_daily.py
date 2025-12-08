#!/usr/bin/env python3
"""
Convert 15-Minute Binance Data to Daily Data

Reads btc_15m_data_2018_to_2025.csv and creates daily aggregated data
with custom features from raw Binance columns.
"""

import pandas as pd
from pathlib import Path

print("="*70)
print("CONVERTING 15-MIN DATA TO DAILY DATA")
print("="*70)

# Paths
raw_15min_path = Path(__file__).parent / "data" / "raw" / "btc_15m_data_2018_to_2025.csv"
output_daily_path = Path(__file__).parent / "data" / "raw" / "btc_daily_data_2018_to_2025.csv"

# Load 15-min data
print(f"\n[1/4] Loading 15-minute data...")
print(f"   File: {raw_15min_path}")

df = pd.read_csv(raw_15min_path)
print(f"   Loaded: {len(df):,} rows (15-minute candles)")

# Convert timestamp to datetime
if 'Open time' in df.columns:
    df['Date'] = pd.to_datetime(df['Open time'])
elif 'date' in df.columns:
    df['Date'] = pd.to_datetime(df['date'])
else:
    print("[ERROR] No date column found!")
    exit(1)

df = df.sort_values('Date')
print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# Rename columns to standard format
column_mapping = {
    'Open time': 'Open_time',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
    'Close time': 'Close_time',
    'Quote asset volume': 'Quote_volume',
    'Number of trades': 'Num_trades',
    'Taker buy base asset volume': 'Taker_buy_base',
    'Taker buy quote asset volume': 'Taker_buy_quote'
}

for old_col, new_col in column_mapping.items():
    if old_col in df.columns:
        df = df.rename(columns={old_col: new_col})

# Ensure required columns exist
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print(f"[ERROR] Missing required columns: {missing_cols}")
    exit(1)

# Set Date as index for resampling
df = df.set_index('Date')

print(f"\n[2/4] Resampling to daily frequency...")

# Resample to daily (1D)
df_daily = df.resample('1D').agg({
    'Open': 'first',           # First open of the day
    'High': 'max',             # Highest price of the day
    'Low': 'min',              # Lowest price of the day
    'Close': 'last',           # Last close of the day
    'Volume': 'sum',           # Total volume for the day
    'Num_trades': 'sum' if 'Num_trades' in df.columns else 'first',
    'Taker_buy_base': 'sum' if 'Taker_buy_base' in df.columns else 'first',
    'Taker_buy_quote': 'sum' if 'Taker_buy_quote' in df.columns else 'first'
})

# Remove rows with missing data (weekends/gaps)
df_daily = df_daily.dropna(subset=['Close'])

print(f"   Daily rows: {len(df_daily):,}")
print(f"   Compression: {len(df):,} -> {len(df_daily):,} ({len(df)/len(df_daily):.1f}x smaller)")

# Reset index to have Date as column
df_daily = df_daily.reset_index()

# Rename Close to Price (standard format)
df_daily['Price'] = df_daily['Close']

print(f"\n[3/4] Creating custom features from raw columns...")

# ============================================================================
# CUSTOM FEATURES FROM RAW BINANCE DATA
# ============================================================================

# 1. Price-based features
df_daily['price_change_pct'] = df_daily['Close'].pct_change()
df_daily['high_low_range'] = df_daily['High'] - df_daily['Low']
df_daily['body_ratio'] = abs(df_daily['Close'] - df_daily['Open']) / (df_daily['high_low_range'] + 0.0001)
df_daily['upper_shadow'] = df_daily['High'] - df_daily[['Open', 'Close']].max(axis=1)
df_daily['lower_shadow'] = df_daily[['Open', 'Close']].min(axis=1) - df_daily['Low']

# 2. Volume-based features
df_daily['volume_ma_20'] = df_daily['Volume'].rolling(window=20).mean()
df_daily['volume_spike'] = df_daily['Volume'] / (df_daily['volume_ma_20'] + 0.0001)
df_daily['volume_change_pct'] = df_daily['Volume'].pct_change()
df_daily['volume_trend'] = df_daily['Volume'].pct_change(periods=7)

# 3. Buy/Sell pressure (if available)
if 'Taker_buy_base' in df_daily.columns and df_daily['Taker_buy_base'].notna().any():
    df_daily['buy_sell_ratio'] = df_daily['Taker_buy_base'] / (df_daily['Volume'] + 0.0001)
else:
    df_daily['buy_sell_ratio'] = 0.5  # Neutral if not available

# 4. Trade intensity (if available)
if 'Num_trades' in df_daily.columns and df_daily['Num_trades'].notna().any():
    df_daily['trade_intensity'] = df_daily['Num_trades'] / (df_daily['Volume'] + 0.0001)
else:
    df_daily['trade_intensity'] = 0  # Not available

# 5. Moving averages & trend
df_daily['sma_50'] = df_daily['Close'].rolling(window=50).mean()
df_daily['sma_200'] = df_daily['Close'].rolling(window=200).mean()
df_daily['sma_ratio'] = df_daily['sma_50'] / (df_daily['sma_200'] + 0.0001)

# 6. Momentum
df_daily['roc_7d'] = df_daily['Close'].pct_change(periods=7)
df_daily['momentum_oscillator'] = (df_daily['Close'] - df_daily['Close'].shift(14)) / df_daily['Close'].shift(14)

# 7. Volatility
df_daily['rolling_std'] = df_daily['Close'].pct_change().rolling(window=20).std()

# 8. Market structure
df_daily['higher_highs'] = (df_daily['High'] > df_daily['High'].shift(1)).astype(int)
df_daily['lower_lows'] = (df_daily['Low'] < df_daily['Low'].shift(1)).astype(int)

print(f"   Created features:")
print(f"      - Price features: price_change_pct, high_low_range, body_ratio, shadows")
print(f"      - Volume features: volume_spike, volume_trend, buy_sell_ratio, trade_intensity")
print(f"      - Trend features: SMA 50/200, sma_ratio, momentum")
print(f"      - Volatility features: rolling_std, market structure")

# Fill NaN values (from rolling calculations)
print(f"\n[4/4] Cleaning data...")
print(f"   Rows before cleaning: {len(df_daily):,}")

# Drop rows with NaN in critical columns (first 200 days due to SMA_200)
df_daily = df_daily.dropna(subset=['sma_200', 'Close'])

print(f"   Rows after cleaning: {len(df_daily):,}")
print(f"   Final date range: {df_daily['Date'].min().date()} to {df_daily['Date'].max().date()}")

# Select and order columns for output
output_columns = [
    'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Price',
    # Custom features
    'price_change_pct', 'high_low_range', 'body_ratio', 'upper_shadow', 'lower_shadow',
    'volume_spike', 'volume_trend', 'buy_sell_ratio', 'trade_intensity',
    'sma_50', 'sma_200', 'sma_ratio', 'roc_7d', 'momentum_oscillator',
    'rolling_std', 'higher_highs', 'lower_lows'
]

df_daily_output = df_daily[output_columns].copy()

# Save to CSV
output_daily_path.parent.mkdir(parents=True, exist_ok=True)
df_daily_output.to_csv(output_daily_path, index=False)

print(f"\n[SAVED] Daily data saved to:")
print(f"   {output_daily_path}")
print(f"   Rows: {len(df_daily_output):,}")
print(f"   Columns: {len(df_daily_output.columns)}")

print("\n" + "="*70)
print("[OK] CONVERSION COMPLETE")
print("="*70)

print(f"""
Summary:
- Input:  {len(df):,} 15-minute candles
- Output: {len(df_daily_output):,} daily candles
- Compression: {len(df)/len(df_daily_output):.1f}x smaller
- Features: {len(output_columns)} columns (7 raw + {len(output_columns)-7} custom)
- Date range: {df_daily_output['Date'].min().date()} to {df_daily_output['Date'].max().date()}

Next steps:
1. Update data_loader.py to use daily data
2. Run backtest with daily data:
   python main.py --months 12
""")

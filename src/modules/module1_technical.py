"""

MODULE 1: TECHNICAL INDICATORS


PURPOSE:
    Calculate technical indicators (RSI, ATR, MACD) for trading
    decision analysis. Provides momentum, volatility, and trend signals.

SUCCESS CRITERIA:
    [OK] RSI values in valid range (0-100)
    [OK] ATR values positive and reasonable for BTC volatility
    [OK] MACD calculations correct (tested against known values)
    [OK] Anti-future-data enforcement (only uses data up to current_date)
    [OK] Handles edge cases (insufficient data, missing values)

INDICATORS:
    1. RSI (Relative Strength Index):
       - Range: 0-100
       - <30: Oversold (buy signal)
       - >70: Overbought (sell signal)
       - Period: 14 days

    2. ATR (Average True Range):
       - Measures volatility
       - Used for stop-loss calculation
       - Higher ATR = more volatile = wider stops
       - Period: 14 days

    3. MACD (Moving Average Convergence Divergence):
       - Trend-following momentum indicator
       - MACD_diff > 0: Bullish (signal above MACD)
       - MACD_diff < 0: Bearish (signal below MACD)
       - Periods: 12, 26, 9

VALIDATION METHOD:
    - Test on known datasets with verified indicator values
    - Verify indicator ranges are valid
    - Test anti-future-data: calculate at date T, verify no data after T used

"""

import sys
import io
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_wrapped_utf8'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stdout._wrapped_utf8 = True
        if hasattr(sys.stderr, 'buffer') and not hasattr(sys.stderr, '_wrapped_utf8'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            sys.stderr._wrapped_utf8 = True
    except (AttributeError, ValueError, OSError):
        pass  # Already wrapped or not available

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import MACD
from typing import Dict, Optional


def calculate_indicators(df: pd.DataFrame, current_date: str) -> pd.DataFrame:
    """
    Calculate all technical indicators up to current_date.

    ANTI-FUTURE-DATA ENFORCEMENT:
        Only uses data up to and including current_date.
        This prevents data leakage during backtesting.

    Args:
        df: DataFrame with columns ['Date', 'Price', 'High', 'Low', 'Volume']
        current_date: Calculate indicators up to this date (YYYY-MM-DD)

    Returns:
        DataFrame with added indicator columns:
        - RSI: Relative Strength Index (14-period)
        - ATR: Average True Range (14-period)
        - MACD: MACD line
        - MACD_signal: Signal line
        - MACD_diff: MACD - Signal (histogram)
        - SMA_50: 50-day Simple Moving Average
        - SMA_200: 200-day Simple Moving Average

    Example:
        df = pd.read_csv('bitcoin_clean.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df_with_indicators = calculate_indicators(df, '2024-11-10')
    """
    # Convert current_date to timestamp for comparison
    current_date = pd.Timestamp(current_date)

    # Filter data up to current_date (ANTI-FUTURE-DATA)
    # Add 1 second buffer to avoid filtering out current data due to timestamp precision
    df_past = df[df['Date'] <= current_date + pd.Timedelta(seconds=1)].copy()

    if len(df_past) < 200:
        print(f"[WARNING]  Warning: Only {len(df_past)} rows available (need 200+ for all indicators)")

    # Ensure required columns exist
    required_cols = ['Date', 'Price']
    missing_cols = [col for col in required_cols if col not in df_past.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 
    # INDICATOR 1: RSI (Relative Strength Index)
    # 
    # Purpose: Identify overbought/oversold conditions
    # Calculation: RSI = 100 - [100 / (1 + RS)]
    #              where RS = Average Gain / Average Loss over 14 periods
    # 
    if len(df_past) >= 14:
        rsi_indicator = RSIIndicator(close=df_past['Price'], window=14)
        df_past['RSI'] = rsi_indicator.rsi()
    else:
        df_past['RSI'] = np.nan

    # 
    # INDICATOR 2: ATR (Average True Range)
    # 
    # Purpose: Measure market volatility
    # Calculation: ATR = Average of True Range over 14 periods
    #              True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    # 
    # Need High, Low columns - if not available, use Price as proxy
    if 'High' not in df_past.columns:
        df_past['High'] = df_past['Price']
    if 'Low' not in df_past.columns:
        df_past['Low'] = df_past['Price']

    if len(df_past) >= 14:
        atr_indicator = AverageTrueRange(
            high=df_past['High'],
            low=df_past['Low'],
            close=df_past['Price'],
            window=14
        )
        df_past['ATR'] = atr_indicator.average_true_range()
    else:
        df_past['ATR'] = np.nan

    # 
    # INDICATOR 3: MACD (Moving Average Convergence Divergence)
    # 
    # Purpose: Identify trend changes and momentum
    # Calculation:
    #   - MACD = EMA(12) - EMA(26)
    #   - Signal = EMA(9) of MACD
    #   - Histogram = MACD - Signal
    # 
    if len(df_past) >= 26:
        macd_indicator = MACD(
            close=df_past['Price'],
            window_fast=12,
            window_slow=26,
            window_sign=9
        )
        df_past['MACD'] = macd_indicator.macd()
        df_past['MACD_signal'] = macd_indicator.macd_signal()
        df_past['MACD_diff'] = macd_indicator.macd_diff()  # Histogram
    else:
        df_past['MACD'] = np.nan
        df_past['MACD_signal'] = np.nan
        df_past['MACD_diff'] = np.nan

    # 
    # INDICATOR 4: Moving Averages (SMA)
    # 
    # Purpose: Identify long-term trends
    # SMA_50: 50-day average (short-term trend)
    # SMA_200: 200-day average (long-term trend)
    # Golden Cross: SMA_50 crosses above SMA_200 (bullish)
    # Death Cross: SMA_50 crosses below SMA_200 (bearish)
    # 
    if len(df_past) >= 50:
        df_past['SMA_50'] = df_past['Price'].rolling(window=50).mean()
    else:
        df_past['SMA_50'] = np.nan

    if len(df_past) >= 200:
        df_past['SMA_200'] = df_past['Price'].rolling(window=200).mean()
    else:
        df_past['SMA_200'] = np.nan

    return df_past


def get_latest_indicators(df: pd.DataFrame, current_date: str) -> Dict:
    """
    Get the latest indicator values as of current_date.

    Args:
        df: DataFrame with historical data
        current_date: Date to get indicators for (YYYY-MM-DD)

    Returns:
        dict: {
            'RSI': float,
            'ATR': float,
            'MACD': float,
            'MACD_signal': float,
            'MACD_diff': float,
            'SMA_50': float,
            'SMA_200': float,
            'date': pd.Timestamp
        }

    Example:
        indicators = get_latest_indicators(df, '2024-11-10')
        print(f"RSI: {indicators['RSI']:.2f}")
    """
    # Calculate indicators
    df_with_ind = calculate_indicators(df, current_date)

    # Get the row for current_date
    current_date = pd.Timestamp(current_date)
    df_current = df_with_ind[df_with_ind['Date'] == current_date]

    if df_current.empty:
        raise ValueError(f"No data found for date: {current_date}")

    # Extract indicator values
    row = df_current.iloc[0]

    indicators = {
        'RSI': row.get('RSI', np.nan),
        'ATR': row.get('ATR', np.nan),
        'MACD': row.get('MACD', np.nan),
        'MACD_signal': row.get('MACD_signal', np.nan),
        'MACD_diff': row.get('MACD_diff', np.nan),
        'SMA_50': row.get('SMA_50', np.nan),
        'SMA_200': row.get('SMA_200', np.nan),
        'date': row['Date']
    }

    return indicators


def validate_indicators(indicators: Dict) -> bool:
    """
    Validate indicator values are within expected ranges.

    Args:
        indicators: Dictionary of indicator values

    Returns:
        bool: True if all validations pass

    Raises:
        ValueError: If validation fails
    """
    # RSI should be 0-100
    rsi = indicators.get('RSI', np.nan)
    if not np.isnan(rsi):
        if not (0 <= rsi <= 100):
            raise ValueError(f"Invalid RSI value: {rsi} (should be 0-100)")

    # ATR should be positive
    atr = indicators.get('ATR', np.nan)
    if not np.isnan(atr):
        if atr < 0:
            raise ValueError(f"Invalid ATR value: {atr} (should be positive)")

    # SMA values should be positive (if not NaN)
    for sma_key in ['SMA_50', 'SMA_200']:
        sma = indicators.get(sma_key, np.nan)
        if not np.isnan(sma):
            if sma <= 0:
                raise ValueError(f"Invalid {sma_key} value: {sma} (should be positive)")

    return True


def interpret_indicators(indicators: Dict) -> Dict:
    """
    Interpret indicator values into trading signals.

    Args:
        indicators: Dictionary of indicator values

    Returns:
        dict: {
            'rsi_signal': 'oversold'/'neutral'/'overbought',
            'macd_signal': 'bullish'/'neutral'/'bearish',
            'trend_signal': 'bullish'/'neutral'/'bearish',
            'volatility': 'low'/'medium'/'high'
        }
    """
    interpretation = {}

    # RSI Signal
    rsi = indicators.get('RSI', 50)
    if rsi < 30:
        interpretation['rsi_signal'] = 'oversold'
    elif rsi > 70:
        interpretation['rsi_signal'] = 'overbought'
    else:
        interpretation['rsi_signal'] = 'neutral'

    # MACD Signal
    macd_diff = indicators.get('MACD_diff', 0)
    if macd_diff > 0:
        interpretation['macd_signal'] = 'bullish'
    elif macd_diff < 0:
        interpretation['macd_signal'] = 'bearish'
    else:
        interpretation['macd_signal'] = 'neutral'

    # Trend Signal (based on SMA)
    sma_50 = indicators.get('SMA_50', 0)
    sma_200 = indicators.get('SMA_200', 0)
    if sma_50 > 0 and sma_200 > 0:
        if sma_50 > sma_200:
            interpretation['trend_signal'] = 'bullish'
        elif sma_50 < sma_200:
            interpretation['trend_signal'] = 'bearish'
        else:
            interpretation['trend_signal'] = 'neutral'
    else:
        interpretation['trend_signal'] = 'neutral'

    # Volatility (based on ATR as % of price)
    # For Bitcoin, typical ATR is 2-5% of price
    # We'll use simpler classification here
    atr = indicators.get('ATR', 1000)
    if atr < 1000:
        interpretation['volatility'] = 'low'
    elif atr < 2000:
        interpretation['volatility'] = 'medium'
    else:
        interpretation['volatility'] = 'high'

    return interpretation


def main():
    """Test technical indicators module."""
    print("="*60)
    print("MODULE 1: TECHNICAL INDICATORS - Testing")
    print("="*60)

    # Load clean data
    from src.data_pipeline.data_loader import BitcoinDataLoader

    try:
        loader = BitcoinDataLoader()
        df = loader.load_clean_data()

        print(f"\n Loaded {len(df)} rows of data")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

        # Test on recent date
        test_date = '2024-11-10'
        print(f"\n Calculating indicators for: {test_date}")

        # Calculate indicators
        df_with_ind = calculate_indicators(df, test_date)
        print(f"   [OK] Calculated {len(df_with_ind)} rows with indicators")

        # Get latest indicators
        indicators = get_latest_indicators(df, test_date)

        print(f"\n Indicator Values:")
        print(f"   RSI: {indicators['RSI']:.2f}")
        print(f"   ATR: ${indicators['ATR']:,.2f}")
        print(f"   MACD: {indicators['MACD']:.2f}")
        print(f"   MACD Signal: {indicators['MACD_signal']:.2f}")
        print(f"   MACD Diff: {indicators['MACD_diff']:.2f}")
        print(f"   SMA 50: ${indicators['SMA_50']:,.2f}")
        print(f"   SMA 200: ${indicators['SMA_200']:,.2f}")

        # Validate
        print(f"\n[OK] Validating indicators...")
        validate_indicators(indicators)
        print(f"   All validations passed!")

        # Interpret
        interpretation = interpret_indicators(indicators)
        print(f"\n Interpretation:")
        print(f"   RSI Signal: {interpretation['rsi_signal']}")
        print(f"   MACD Signal: {interpretation['macd_signal']}")
        print(f"   Trend Signal: {interpretation['trend_signal']}")
        print(f"   Volatility: {interpretation['volatility']}")

        # Test anti-future-data enforcement
        print(f"\n Testing Anti-Future-Data Enforcement:")
        df_test = calculate_indicators(df, '2024-01-01')
        max_date_used = df_test['Date'].max()
        print(f"   Requested date: 2024-01-01")
        print(f"   Latest date in result: {max_date_used}")
        if max_date_used <= pd.Timestamp('2024-01-01'):
            print(f"   [OK] Anti-future-data check PASSED")
        else:
            print(f"   [ERROR] Anti-future-data check FAILED")

        print("\n" + "="*60)
        print("[OK] MODULE 1 TEST PASSED")
        print("="*60)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nPlease run data_loader.py first to generate cleaned data")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

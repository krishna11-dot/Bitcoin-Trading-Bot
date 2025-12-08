# RandomForest for Time Series: Feature Engineering Review

## Executive Summary

Your implementation of RandomForest for Bitcoin price prediction demonstrates good awareness of time series challenges, but there are several areas for improvement to better handle temporal dependencies.

## Current Implementation Analysis

### What You're Doing Right ✅

1. **Rolling Window Approach**
   - Using 7-day windows with aggregated features (min, max, avg)
   - Predicting 7 days ahead (realistic horizon)
   - Anti-future-data enforcement (no data leakage)

2. **Feature Engineering Categories**
   - Volatility: `rolling_std`, `high_low_range`
   - Trend: `price_change_pct`, `sma_ratio`
   - Momentum: `roc_7d`, `momentum_oscillator`
   - Volume: `volume_spike`
   - Market Structure: `higher_highs`, `lower_lows`
   - Moving Averages: `sma_30`

3. **Direction Classification**
   - Using RandomForest classifier for UP/DOWN prediction (better than price regression)
   - Skipping flat movements (<2% change) improves signal quality
   - Providing confidence scores

4. **Known Limitations**
   - You acknowledge extrapolation problems (all-time highs)
   - Using ML as ONE signal, not the only signal
   - Combining with technical indicators and sentiment

### Critical Issues with Current Approach ⚠️

#### 1. **Loss of Temporal Information**

**Problem**: Aggregating features with min/max/avg loses temporal sequence information.

```python
# Current approach
window_features[f'{feat}_min'] = window[feat].min()
window_features[f'{feat}_max'] = window[feat].max()
window_features[f'{feat}_avg'] = window[feat].mean()
```

**Why it's a problem**:
- `[10, 20, 30]` and `[30, 20, 10]` have same min/max/avg but opposite trends
- RandomForest can't distinguish between rising and falling sequences with same statistics

**Recommendation**: Add explicit lag features and trend indicators.

#### 2. **Missing Explicit Lag Features**

RandomForest for time series needs explicit temporal context through lag features.

**What's Missing**:
```python
# Should add these features:
'price_lag_1',    # Price 1 day ago
'price_lag_3',    # Price 3 days ago
'price_lag_7',    # Price 7 days ago
'rsi_lag_1',      # RSI 1 day ago
'volume_lag_1',   # Volume 1 day ago
```

**Why it matters**:
- Lag features give RandomForest explicit temporal context
- Helps model learn "if price was X yesterday and Y today, what happens tomorrow?"
- Standard practice for RF on time series

#### 3. **Missing Trend and Momentum Features**

**What to add**:
```python
# Trend strength
'trend_direction',     # +1 if uptrend, -1 if downtrend, 0 if sideways
'trend_strength',      # How strong is current trend (0-1)
'days_since_trend_change',  # Time since last trend reversal

# Momentum acceleration
'momentum_change',     # Change in momentum (2nd derivative)
'rsi_change',          # Change in RSI
'volume_momentum',     # Is volume increasing with price?
```

#### 4. **Extrapolation Problem Not Addressed**

**Current situation**:
- Model trained on $20k-$90k may fail at $120k
- You acknowledge this but don't have a solution

**Recommendations**:
1. **Normalize by recent price range**:
   ```python
   # Instead of absolute price features
   'price_position_in_range',  # Where is price in recent 30-day range (0-1)
   'distance_from_sma_pct',    # Percentage distance from SMA (normalized)
   ```

2. **Use percentage changes, not absolute values**:
   ```python
   # Instead of: window_features['current_price'] = current_price
   window_features['price_vs_30d_avg'] = current_price / sma_30 - 1
   window_features['price_vs_90d_high'] = current_price / rolling_90d_high
   ```

3. **Add regime detection**:
   ```python
   'volatility_regime',  # Low/Medium/High volatility regime
   'price_regime',       # Accumulation/Markup/Distribution/Markdown
   ```

## Recommended Feature Engineering Improvements

### Priority 1: Add Explicit Lag Features

```python
def add_lag_features(df, cols_to_lag, lags=[1, 3, 7]):
    """Add lag features for temporal context."""
    for col in cols_to_lag:
        for lag in lags:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    return df

# Apply to key features
cols_to_lag = ['Price', 'RSI', 'volume_spike', 'momentum_oscillator']
df = add_lag_features(df, cols_to_lag, lags=[1, 3, 7])
```

### Priority 2: Add Trend Features

```python
def add_trend_features(df):
    """Add trend direction and strength."""
    # Trend direction (simple SMA crossover)
    df['trend_direction'] = np.where(
        df['SMA_50'] > df['SMA_200'], 1,
        np.where(df['SMA_50'] < df['SMA_200'], -1, 0)
    )

    # Trend strength (normalized slope of SMA)
    df['sma_50_slope'] = df['SMA_50'].diff(5) / df['SMA_50']
    df['trend_strength'] = df['sma_50_slope'].abs()

    # Price momentum over multiple timeframes
    df['momentum_3d'] = df['Price'].pct_change(3)
    df['momentum_7d'] = df['Price'].pct_change(7)
    df['momentum_14d'] = df['Price'].pct_change(14)

    return df
```

### Priority 3: Normalize for Extrapolation

```python
def add_normalized_features(df):
    """Add normalized features to handle extrapolation."""
    # Price position in recent range (0 = low, 1 = high)
    rolling_30d_high = df['High'].rolling(30).max()
    rolling_30d_low = df['Low'].rolling(30).min()
    df['price_position_30d'] = (
        (df['Price'] - rolling_30d_low) /
        (rolling_30d_high - rolling_30d_low)
    )

    # Distance from moving averages (percentage)
    df['price_vs_sma50_pct'] = (df['Price'] / df['SMA_50']) - 1
    df['price_vs_sma200_pct'] = (df['Price'] / df['SMA_200']) - 1

    # Volatility regime (normalized by historical volatility)
    df['vol_30d'] = df['Price'].rolling(30).std()
    df['vol_90d'] = df['Price'].rolling(90).std()
    df['volatility_regime'] = df['vol_30d'] / df['vol_90d']

    return df
```

### Priority 4: Add Rate of Change Features

```python
def add_roc_features(df):
    """Add multi-timeframe rate of change."""
    timeframes = [3, 7, 14, 30]

    for tf in timeframes:
        # Price ROC
        df[f'roc_{tf}d'] = df['Price'].pct_change(tf)

        # RSI ROC
        df[f'rsi_change_{tf}d'] = df['RSI'].diff(tf)

        # Volume ROC
        if 'Volume' in df.columns:
            df[f'volume_roc_{tf}d'] = df['Volume'].pct_change(tf)

    return df
```

## Updated Feature List Recommendation

### Core Features (Keep)
```python
'rolling_std', 'high_low_range',
'price_change_pct', 'sma_ratio',
'roc_7d', 'momentum_oscillator',
'volume_spike', 'higher_highs', 'lower_lows',
'sma_30'
```

### Add These Features
```python
# Lag features (12 features)
'price_lag_1', 'price_lag_3', 'price_lag_7',
'rsi_lag_1', 'rsi_lag_3', 'rsi_lag_7',
'volume_lag_1', 'volume_lag_3', 'volume_lag_7',
'momentum_lag_1', 'momentum_lag_3', 'momentum_lag_7',

# Trend features (6 features)
'trend_direction', 'trend_strength', 'sma_50_slope',
'momentum_3d', 'momentum_7d', 'momentum_14d',

# Normalized features (5 features)
'price_position_30d', 'price_vs_sma50_pct', 'price_vs_sma200_pct',
'volatility_regime', 'price_vs_90d_high',

# Rate of change features (4 features)
'roc_3d', 'roc_14d', 'roc_30d', 'rsi_change_7d'
```

**Total: 10 (current) + 27 (new) = 37 features**

## Implementation Strategy

### Phase 1: Quick Wins (Do First)
1. Add lag features for Price, RSI, Volume
2. Add trend_direction and trend_strength
3. Add price_position_30d (normalized price)

**Expected Impact**: +5-10% directional accuracy

### Phase 2: Comprehensive Upgrade
1. Add all recommended features
2. Test feature importance (remove low-importance features)
3. Tune RandomForest hyperparameters

**Expected Impact**: +10-15% directional accuracy

### Phase 3: Advanced Techniques
1. Consider LGBM or XGBoost (better for time series than RandomForest)
2. Add ensemble with LSTM for capturing longer-term trends
3. Implement walk-forward validation

## Alternative: Why Not LSTM or GRU?

**RandomForest Advantages**:
- Fast training (<30 seconds)
- Interpretable (feature importance)
- No need for normalization
- Works with small datasets

**LSTM/GRU Advantages**:
- Natural temporal modeling
- Can learn long-term dependencies
- Better extrapolation (can adapt to new price ranges)

**Recommendation**:
- Keep RandomForest for now (it's working)
- Add better features (lag, trend, normalized)
- Consider LSTM as Phase 3 upgrade if needed

## Key Takeaways

1. **RandomForest CAN work for time series** with proper feature engineering
2. **Critical missing features**: Lag features, trend indicators, normalized features
3. **Your approach is 70% correct**, just needs better temporal features
4. **Don't overthink it**: Adding 10-15 well-chosen features will help more than switching models

## Testing Your Changes

After adding new features, validate with:

```bash
# Test directional accuracy with new features
python -m src.modules.module3_prediction

# Expected improvements:
# - Directional Accuracy: >70% (currently ~65%)
# - High Confidence Accuracy: >80% (currently ~70%)
# - RMSE: Should stay similar or improve slightly
```

## Questions to Consider

1. **Are you using the right horizon?**
   - 7 days might be too long for 15-minute data
   - Consider: 1-day, 3-day, 7-day predictions separately

2. **Are you handling imbalanced data?**
   - If market is mostly UP, model might just predict UP
   - Use `class_weight='balanced'` in RandomForestClassifier

3. **Are you validating correctly?**
   - Use walk-forward validation (train on past, test on future)
   - Never shuffle time series data

## Summary

Your RandomForest implementation is on the right track, but needs better temporal features to truly work for time series forecasting. The main issue is that aggregating features (min/max/avg) loses temporal sequence information. Adding lag features, trend indicators, and normalized features will significantly improve performance.

**Priority fixes**:
1. Add lag features (Priority 1)
2. Add trend direction/strength (Priority 1)
3. Normalize price features (Priority 2)
4. Test and iterate (Priority 1)

Remember: **RandomForest + Good Features > LSTM + Bad Features**

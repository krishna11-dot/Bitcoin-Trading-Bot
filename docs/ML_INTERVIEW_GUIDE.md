# ML Model Interview Guide - Complete Q&A

**Purpose**: Interview-ready explanations of your hybrid Linear Regression + RandomForest model based on actual code.

**Key Insight from Swarnabha Ghosh**:
> "The moment you say I am using two models, I would want to know: What is each individual model predicting? What is input feature? What is target feature? And how are you combining? Why are you combining? You need to be very sure of what you are doing."

---

## Table of Contents

1. [Quick Reference Card](#quick-reference-card)
2. [Complete Answers](#complete-answers)
3. [Code Line References](#code-line-references)
4. [Visual Diagrams](#visual-diagrams)
5. [Common Follow-up Questions](#common-follow-up-questions)

---

## Quick Reference Card

### **The 30-Second Pitch**

> "I use a hybrid approach with Linear Regression for feature engineering and two separate RandomForest models. Linear Regression creates lr_trend and lr_residual features that can extrapolate to all-time highs - solving RandomForest's interpolation limitation. Then RandomForest Regressor predicts the price 7 days ahead, and RandomForest Classifier predicts direction (UP/DOWN) with confidence. Both use the same 16 features created from a 7-day rolling window aggregation."

---

### **Key Numbers**

| Metric | Value | Code Reference |
|--------|-------|----------------|
| **Base Features** | 5 | [module3_prediction.py:731-736](../src/modules/module3_prediction.py#L731-L736) |
| **Total Features** | 16 | 5 features × 3 aggregations + current_price |
| **Window Size** | 7 days | [module3_prediction.py:693](../src/modules/module3_prediction.py#L693) |
| **Prediction Horizon** | 7 days ahead | [module3_prediction.py:693](../src/modules/module3_prediction.py#L693) |
| **UP Threshold** | >2% gain | [module3_prediction.py:775](../src/modules/module3_prediction.py#L775) |
| **DOWN Threshold** | <-2% loss | [module3_prediction.py:777](../src/modules/module3_prediction.py#L777) |
| **Target Accuracy** | >60% direction | [module3_prediction.py:66](../src/modules/module3_prediction.py#L66) |
| **Target MAPE** | <8% price | [module3_prediction.py:1629](../src/modules/module3_prediction.py#L1629) |

---

## Complete Answers

### Q1: "What does each model predict?"

**Answer**:
> "I have two separate RandomForest models. The first is a RandomForest Regressor that predicts the actual BTC price 7 days ahead in USD. The second is a RandomForest Classifier that predicts the direction - UP if price will gain more than 2%, DOWN if it will lose more than 2%, and we skip FLAT movements during training to focus on clear signals. Both use the same 16 input features but have different target variables."

**Code Evidence**:
```python
# RandomForest Regressor - Predicts PRICE
# Line 1150: module3_prediction.py
predicted_price = self.model.predict(X_pred)[0]

# RandomForest Classifier - Predicts DIRECTION
# Lines 1156-1158: module3_prediction.py
direction_pred = self.direction_classifier.predict(df, str(current_date_ts.date()))
direction = direction_pred['direction']  # "UP", "DOWN"
confidence = direction_pred['confidence']  # 0.0-1.0
```

**Key Points**:
- Two SEPARATE models (not one combined model)
- Same features, different targets, different RandomForest types
- Regressor outputs: `predicted_price` (e.g., $73,000)
- Classifier outputs: `direction` ("UP"/"DOWN"), `confidence` (0.72)

---

### Q2: "What are your input features?"

**Answer**:
> "I use 5 base features that I engineered: lr_trend and lr_residual from linear regression, rolling_std for 7-day volatility, volume_spike for trading activity, and high_low_range for intraday volatility. Each feature is aggregated over a 7-day rolling window using min, max, and average, giving me 16 total features including the current price."

**The 5 Base Features**:

| # | Feature | Formula | What It Measures | Example Value |
|---|---------|---------|------------------|---------------|
| 1 | **lr_trend** | `slope × window_size + intercept` | Where linear trend is heading | $75,000 |
| 2 | **lr_residual** | `actual_price - predicted_by_LR` | Deviation from trend | +$2,000 |
| 3 | **rolling_std** | 7-day standard deviation | Price volatility | $3,500 |
| 4 | **volume_spike** | `volume / avg_volume` | Trading activity relative to average | 1.5 (50% above avg) |
| 5 | **high_low_range** | `(High - Low) / Price` | Intraday volatility | 0.03 (3% range) |

**Aggregation to 16 Features**:

```python
# Lines 786-790: module3_prediction.py
for feat in features:
    window_features[f'{feat}_min'] = window[feat].min()
    window_features[f'{feat}_max'] = window[feat].max()
    window_features[f'{feat}_avg'] = window[feat].mean()

window_features['current_price'] = current_price
```

**Calculation**: 5 features × 3 aggregations + 1 current_price = **16 total features**

**Why These 5?**:
- ✅ **lr_trend**: ONLY feature that can extrapolate to all-time highs
- ✅ **lr_residual**: Captures anomalies/deviations from trend
- ✅ **rolling_std**: Unique measure of volatility
- ✅ **volume_spike**: Unique measure of trading interest
- ✅ **high_low_range**: Unique measure of intraday volatility

**Removed Features** (redundant):
- ❌ price_change_pct (redundant with lr_trend)
- ❌ sma_ratio (redundant with lr_trend)
- ❌ higher_highs, lower_lows (low importance binary flags)

---

### Q3: "What's your target column?"

**Answer**:
> "For the regressor, the target is the Bitcoin price 7 days in the future. For the classifier, the target is binary - 1 for UP if price gains more than 2%, and 0 for DOWN if it loses more than 2%. I skip flat movements below 2% change during training to help the classifier focus on clear directional moves."

**Regressor Target** (Price Prediction):

```python
# Lines 1028, 1046: module3_prediction.py
target_price = df.iloc[target_idx]['Price']  # Price 7 days ahead
y = pd.Series(y_list, name='target_price')
```

**Example**: If current price is $70,000, target might be $73,000 (7 days later)

**Classifier Target** (Direction Prediction):

```python
# Lines 772-780: module3_prediction.py
price_change_pct = (future_price - current_price) / current_price

if price_change_pct > 0.02:
    direction = 1  # UP (>2% gain)
elif price_change_pct < -0.02:
    direction = 0  # DOWN (<-2% loss)
else:
    continue  # Skip FLAT movements
```

**Why Skip FLAT?**:
- Focuses classifier on clear signals
- Reduces noise in training data
- Improves accuracy on actual trading decisions (DCA vs HOLD)

---

### Q4: "How do you combine the outputs from both models?"

**Answer**:
> "I don't mathematically combine them - both models run independently and return separate predictions. The Decision Box receives both the predicted price and the direction with confidence score as independent signals, along with technical indicators like RSI and MACD. This gives the trading logic multiple perspectives to make better decisions."

**Code Evidence**:

```python
# Lines 1184-1192: module3_prediction.py
return {
    'predicted_price': predicted_price,        # From RandomForest Regressor
    'direction': direction,                    # From RandomForest Classifier
    'direction_confidence': direction_confidence,  # From Classifier
    'up_probability': up_probability,
    'down_probability': down_probability,
    'prediction_date': prediction_date,
    'current_date': current_date_ts,
    'horizon_days': self.horizon
}
```

**No Combination Logic**:
- Both predictions returned separately
- Decision Box uses BOTH as independent signals
- No weighted average, no ensemble, no voting
- Each provides different information (price level vs direction)

**How Decision Box Uses Them**:
```python
# Decision Box receives:
ml_prediction = {
    'predicted_price': 73000,      # From Regressor
    'direction': 'UP',             # From Classifier
    'direction_confidence': 0.68   # From Classifier
}

# Combines with other signals:
if direction == 'UP' and direction_confidence > 0.70 and RSI < 60:
    action = 'SWING_BUY'  # High-confidence ML signal + favorable RSI
elif fear_greed < 40 and RSI < 60:
    action = 'DCA_BUY'    # Low ML confidence, use defensive DCA
```

---

### Q5: "How did you convert time series data to tabular?"

**Answer**:
> "I use a rolling window approach. For each 7-day window, I aggregate the 5 features using min, max, and average over that window. The target is set to the price 7 days after the window ends. This sliding window moves forward one day at a time, creating training samples. For example, if my window is days 1-7, my target is the price on day 14. This ensures no future data leakage while converting temporal dependencies into tabular features that RandomForest can learn from."

**Visual Explanation**:

```
TIME SERIES DATA (Sequential):
═══════════════════════════════════════════════════════════
Day 1:  Price=$60K, lr_trend=$61K, volatility=$2.0K
Day 2:  Price=$62K, lr_trend=$63K, volatility=$2.5K
Day 3:  Price=$64K, lr_trend=$65K, volatility=$3.0K
Day 4:  Price=$66K, lr_trend=$67K, volatility=$2.8K
Day 5:  Price=$68K, lr_trend=$69K, volatility=$3.2K
Day 6:  Price=$70K, lr_trend=$71K, volatility=$3.5K
Day 7:  Price=$72K, lr_trend=$73K, volatility=$3.0K
        ...
Day 14: Price=$78K ← TARGET

                    ↓ TRANSFORMATION ↓

TABULAR DATA (For RandomForest):
═══════════════════════════════════════════════════════════
Sample 1:
  Features (X):
    lr_trend_min:       $61K  (min of days 1-7)
    lr_trend_max:       $73K  (max of days 1-7)
    lr_trend_avg:       $67K  (avg of days 1-7)
    volatility_min:     $2.0K
    volatility_max:     $3.5K
    volatility_avg:     $2.86K
    ... (16 features total)

  Target (y):
    target_price:       $78K  (day 14)
```

**Code Implementation**:

```python
# Lines 1019-1048: module3_prediction.py
for i in range(len(df) - self.window_size - self.horizon):
    # Extract 7-day window
    window = df.iloc[i:i + self.window_size]

    # Target = price 7 days AFTER window ends
    target_idx = i + self.window_size + self.horizon - 1
    target_price = df.iloc[target_idx]['Price']

    # Aggregate features over window
    window_features = {}
    for feat in features:
        window_features[f'{feat}_min'] = window[feat].min()
        window_features[f'{feat}_max'] = window[feat].max()
        window_features[f'{feat}_avg'] = window[feat].mean()

    X_list.append(window_features)
    y_list.append(target_price)
```

**Anti-Future-Data Leakage**:
- Window: Days 1-7 (PAST)
- Target: Day 14 (FUTURE, 7 days after window)
- No overlap between features and target
- Simulates real-world prediction scenario

---

### Q6: "What is lr_trend exactly?"

**Answer**:
> "lr_trend is the linear regression trend line extrapolated to the next time step. I calculate the slope and intercept using a closed-form formula on the 7-day window, then predict where the trend is heading. For example, if the price went from $60K to $70K over 7 days with a steady uptrend, lr_trend would predict around $75K for the next step."

**Mathematical Formula**:

```python
# Lines 589-595: module3_prediction.py

# Step 1: Calculate slope using closed-form linear regression
numerator = Σ((x - x̄)(y - ȳ))
denominator = Σ((x - x̄)²)
slope = numerator / denominator

# Step 2: Calculate intercept
intercept = y_mean - slope * x_mean

# Step 3: Extrapolate to next step
lr_trend = slope * window_size + intercept
```

**Example Calculation**:

```
Historical Prices (7 days):
Day 0: $60K
Day 1: $62K
Day 2: $64K
Day 3: $66K
Day 4: $68K
Day 5: $70K
Day 6: $72K

Linear Fit:
  slope = +$2K per day
  intercept = $58K

lr_trend = slope × 7 + intercept
         = $2K × 7 + $58K
         = $14K + $58K
         = $72K

This is where the LINEAR TREND says price is heading.
```

**Why This Matters**:
- Linear Regression CAN extrapolate to new price ranges
- RandomForest alone CANNOT (only interpolates within training data)
- lr_trend feature allows RandomForest to work at all-time highs

---

### Q7: "What is lr_residual?"

**Answer**:
> "lr_residual is how much the actual price deviates from the linear trend prediction. It captures anomalies - when the price is significantly above or below the trend line. For example, if the trend says the price should be $70K but it's actually $72K, the residual is +$2K, indicating the price is running ahead of the trend."

**Formula**:

```python
# Lines 598-600: module3_prediction.py
predicted_current = slope * (window_size - 1) + intercept
residual = actual_price - predicted_current
lr_residual.append(residual)
```

**Example**:

```
Linear Trend predicts: $70K
Actual Current Price:  $72K
lr_residual = $72K - $70K = +$2K (price ahead of trend)

OR

Linear Trend predicts: $70K
Actual Current Price:  $68K
lr_residual = $68K - $70K = -$2K (price behind trend)
```

**What It Captures**:
- Positive residual: Price accelerating faster than trend
- Negative residual: Price lagging behind trend
- Large residual: Market anomaly, potential reversal signal

---

### Q8: "What metrics do you use to evaluate performance?"

**Answer**:
> "For price prediction, I use MAPE - Mean Absolute Percentage Error - because it's scale-independent and easy to interpret as a percentage. For direction prediction, I use directional accuracy - the percentage of correct UP/DOWN predictions. My success criteria are MAPE below 8%, directional accuracy above 65%, and training time under 30 seconds."

**Metrics Breakdown**:

| Model | Metric | Formula | Target | Code Reference |
|-------|--------|---------|--------|----------------|
| **Regressor** | MAPE | `mean(abs((pred - actual) / actual))` | <8% | [Line 1491](../src/modules/module3_prediction.py#L1491) |
| **Classifier** | Directional Accuracy | `mean(predictions_correct)` | >65% | [Line 1368](../src/modules/module3_prediction.py#L1368) |
| **Classifier** | Avg Confidence | `mean(confidence_scores)` | >0.5 | [Line 1369](../src/modules/module3_prediction.py#L1369) |
| **Both** | Training Time | Time to fit model | <30s | [Line 1631](../src/modules/module3_prediction.py#L1631) |

**MAPE Example**:

```python
# Line 1491: module3_prediction.py
predictions = [98000, 102000, 95000]
actuals =     [100000, 100000, 100000]

mape = mean([
    abs((98000 - 100000) / 100000),   # 2%
    abs((102000 - 100000) / 100000),  # 2%
    abs((95000 - 100000) / 100000)    # 5%
])
mape = (0.02 + 0.02 + 0.05) / 3 = 0.03 = 3%
```

**Directional Accuracy Example**:

```python
# Line 1368: module3_prediction.py
predictions = ['UP', 'DOWN', 'UP', 'UP']
actuals =     ['UP', 'UP',   'UP', 'DOWN']
correct =     [True, False,  True, False]

directional_accuracy = 2 / 4 = 0.50 = 50%
```

**Why These Metrics?**:
- **MAPE**: Percentage-based, intuitive ("off by 5%")
- **Not RMSE**: Harder to interpret ($3,000 error - is that good?)
- **Not R²**: Doesn't directly answer "how accurate?"
- **Directional Accuracy**: What matters for trading (buy/sell decision)

---

### Q9: "Why Linear Regression + RandomForest instead of just one model?"

**Answer**:
> "RandomForest alone couldn't extrapolate to all-time highs - it gave 49.7% accuracy when BTC hit $100K because it was trained on $20K-$90K range. RandomForest can only interpolate within its training data. I use Linear Regression to create trend features (lr_trend and lr_residual) that CAN extrapolate beyond the training range. Then RandomForest learns when to trust the trend and when to adjust based on volatility and volume patterns. This hybrid approach achieved 60% directional accuracy even at new price levels."

**The Problem** (RandomForest Alone):

```
Training Data: BTC prices $20K - $90K
              ┌─────────────────────────┐
              │  RandomForest Training  │
              │  Range: $20K - $90K     │
              └─────────────────────────┘
                        ▲
                        │
                        │ Can only interpolate
                        │ within this range
                        ▼
Test at $100K: ❌ FAIL (49.7% accuracy - worse than random!)

Why? RandomForest sees $100K and thinks:
"I've never seen prices above $90K. I don't know what happens here."
```

**The Solution** (Hybrid Approach):

```
Linear Regression Features:
  lr_trend: Captures LINEAR TREND (CAN extrapolate)
    ┌────────────────────────────────────┐
    │ If price went $60K → $70K → $80K   │
    │ Trend says: $90K → $100K → $110K   │
    │                                    │
    │ ✅ This WORKS at $100K+            │
    └────────────────────────────────────┘

RandomForest:
  Uses lr_trend as INPUT feature
    ┌────────────────────────────────────┐
    │ "Trend says $105K, but...          │
    │  - Volatility is HIGH ($5K std)    │
    │  - Volume spike (1.8x average)     │
    │  - Residual is +$3K (overheated)   │
    │                                    │
    │ Prediction: Correction to $98K"    │
    └────────────────────────────────────┘

Result: ✅ 60% accuracy at all-time highs
```

**Evidence from Code**:

```python
# Lines 7-9: module3_prediction.py
"""
PURPOSE:
    Predict Bitcoin price direction (UP/DOWN) using a hybrid approach:
    - Linear Regression: Captures trends (can extrapolate to all-time highs)
    - RandomForest: Captures patterns (non-linear deviations from trend)
"""

# Lines 50-58: module3_prediction.py
"""
WHY HYBRID APPROACH?
    RandomForest Limitation:
    - Trained on $20k-$90k -> Fails at $100k (never seen before)
    - Only interpolates (predicts WITHIN training range)
    - Cannot extrapolate (predict OUTSIDE training range)

    Linear Regression Solution:
    - Captures linear trends (e.g., $60k->$70k = uptrend)
    - CAN extrapolate to new ranges ($80k, $100k, etc.)
    - Provides baseline trend for RandomForest to adjust
"""
```

---

### Q10: "Are the features the same for both RandomForest models?"

**Answer**:
> "Yes, both the RandomForest Regressor (price prediction) and RandomForest Classifier (direction prediction) use the exact same 16 input features. They differ only in their target variables - one predicts a continuous price value, the other predicts a binary direction label. Using the same features ensures consistency and allows both models to learn complementary patterns from the same underlying data."

**Code Evidence**:

```python
# Lines 731-736 (DirectionClassifier):
self.feature_cols = [
    'lr_trend', 'lr_residual',
    'rolling_std',
    'volume_spike',
    'high_low_range'
]

# Lines 965-970 (BitcoinPricePredictor):
self.feature_cols = [
    'lr_trend', 'lr_residual',  # SAME
    'rolling_std',               # SAME
    'volume_spike',              # SAME
    'high_low_range'             # SAME
]
```

**Both Models See**:
```
Input Features (16 total):
  lr_trend_min, lr_trend_max, lr_trend_avg
  lr_residual_min, lr_residual_max, lr_residual_avg
  rolling_std_min, rolling_std_max, rolling_std_avg
  volume_spike_min, volume_spike_max, volume_spike_avg
  high_low_range_min, high_low_range_max, high_low_range_avg
  current_price

Regressor learns:    features → price ($73,000)
Classifier learns:   features → direction (UP, confidence=0.68)
```

---

## Code Line References

### Key Sections

| Concept | File | Lines | What It Does |
|---------|------|-------|--------------|
| **5 Base Features** | module3_prediction.py | 731-736 | Defines lr_trend, lr_residual, rolling_std, volume_spike, high_low_range |
| **lr_trend Calculation** | module3_prediction.py | 589-595 | Closed-form linear regression to extrapolate trend |
| **lr_residual Calculation** | module3_prediction.py | 598-600 | Deviation from linear trend |
| **Rolling Window Aggregation** | module3_prediction.py | 786-790 | Converts 5 features → 16 via min/max/avg |
| **Regressor Target** | module3_prediction.py | 1028, 1046 | target_price = future price 7 days ahead |
| **Classifier Target** | module3_prediction.py | 772-780 | direction = 1 (UP >2%) or 0 (DOWN <-2%) |
| **MAPE Calculation** | module3_prediction.py | 1491 | mean(abs((predictions - actuals) / actuals)) |
| **Directional Accuracy** | module3_prediction.py | 1368 | mean(predictions_correct) |
| **Time Series → Tabular** | module3_prediction.py | 1019-1048 | Sliding window transformation |
| **Success Criteria** | module3_prediction.py | 1629-1631 | MAPE <8%, Accuracy >65%, Time <30s |

---

## Visual Diagrams

### Complete Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: RAW DATA                                             │
│ ════════════════                                             │
│ Date, Price, High, Low, Volume                               │
│ 2024-01-01, $60000, $61000, $59000, 1.2M                     │
│ 2024-01-02, $62000, $63000, $61000, 1.5M                     │
│ ...                                                          │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: FEATURE ENGINEERING                                  │
│ ══════════════════════════                                   │
│ 2a. Linear Regression (Closed-form formula)                  │
│     → lr_trend: $72K (where trend is heading)                │
│     → lr_residual: +$2K (deviation from trend)               │
│                                                              │
│ 2b. Volatility Features                                      │
│     → rolling_std: $3.5K (7-day std dev)                     │
│     → high_low_range: 0.03 (3% daily range)                  │
│                                                              │
│ 2c. Volume Features                                          │
│     → volume_spike: 1.5 (50% above average)                  │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: ROLLING WINDOW AGGREGATION                           │
│ ══════════════════════════════════                           │
│ 7-day window × 5 features × 3 aggregations = 15 features     │
│                                                              │
│ lr_trend:       min=$61K, max=$73K, avg=$67K                 │
│ lr_residual:    min=-$1K, max=$2K,  avg=$0.5K                │
│ rolling_std:    min=$2K,  max=$3.5K, avg=$2.86K              │
│ volume_spike:   min=1.0,  max=1.8,  avg=1.4                  │
│ high_low_range: min=0.02, max=0.04, avg=0.03                 │
│                                                              │
│ + current_price: $72K                                        │
│ ────────────────────────                                     │
│ Total: 16 features                                           │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
         ┌───────────┴───────────┐
         ↓                       ↓
┌──────────────────────┐  ┌──────────────────────┐
│ MODEL 1: REGRESSOR   │  │ MODEL 2: CLASSIFIER  │
│ ═══════════════════  │  │ ══════════════════   │
│                      │  │                      │
│ Input: 16 features   │  │ Input: 16 features   │
│                      │  │ (SAME as Model 1)    │
│ RandomForest         │  │                      │
│ Regressor            │  │ RandomForest         │
│ (100 trees)          │  │ Classifier           │
│                      │  │ (100 trees)          │
│ Target: Price        │  │ Target: Direction    │
│ (continuous)         │  │ (binary: 0 or 1)     │
│                      │  │                      │
│ Output:              │  │ Output:              │
│ predicted_price:     │  │ direction: "UP"      │
│   $73,000            │  │ confidence: 0.68     │
│                      │  │ up_prob: 0.68        │
│                      │  │ down_prob: 0.32      │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           └────────┬────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: PREDICTIONS (NOT COMBINED)                           │
│ ══════════════════════════════════                           │
│ {                                                            │
│   'predicted_price': 73000,       ← From Regressor           │
│   'direction': 'UP',              ← From Classifier          │
│   'direction_confidence': 0.68,   ← From Classifier          │
│   'up_probability': 0.68,         ← From Classifier          │
│   'down_probability': 0.32        ← From Classifier          │
│ }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 5: DECISION BOX (Uses both predictions separately)      │
│ ══════════════════════════════════════════════════════       │
│ if direction == 'UP' and confidence > 0.70 and RSI < 60:     │
│     action = 'SWING_BUY'  # High-confidence ML + good RSI    │
│ elif fear_greed < 40 and RSI < 60:                           │
│     action = 'DCA_BUY'    # Defensive strategy               │
│ else:                                                        │
│     action = 'HOLD'                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Common Follow-up Questions

### "Why not use LSTM or ARIMA for time series?"

**Answer**:
> "ARIMA assumes stationarity and linear relationships, which don't hold for Bitcoin's volatile price movements. LSTM would require significantly more data and computational resources for marginal accuracy gains. RandomForest with proper time-series-to-tabular conversion gives me 60% directional accuracy with 20-second training time, which is acceptable for this trading strategy. The key was solving the extrapolation problem with linear regression features, not choosing a more complex model architecture."

---

### "How do you prevent data leakage?"

**Answer**:
> "I use strict temporal splits - the training window (days 1-7) only uses past data, and the target (day 14) is always 7 days in the future. During backtesting, I train the model up to the current date and predict forward, never using future data in features. The rolling window transformation maintains this temporal integrity by only aggregating historical values."

**Code Evidence**:
```python
# Lines 1023-1028: module3_prediction.py
window = df.iloc[i:i + self.window_size]  # PAST (days 1-7)
target_idx = i + self.window_size + self.horizon - 1  # FUTURE (day 14)
target_price = df.iloc[target_idx]['Price']  # 7 days after window
```

---

### "What if the model is overfitting?"

**Answer**:
> "I reduced features from 31 to 16 (48% reduction) to minimize overfitting risk. RandomForest hyperparameters like max_depth=10 and min_samples_leaf=5 prevent individual trees from memorizing training data. The rolling window validation simulates real-world conditions - train on past, predict future - which would expose overfitting if it existed. My 60% directional accuracy is modest, suggesting the model generalizes rather than memorizes."

---

### "Why 7-day window and 7-day horizon?"

**Answer**:
> "I chose 7 days based on Bitcoin's trading patterns - weekly cycles align with human behavior (weekday vs weekend trading). A shorter window (3 days) wouldn't capture enough trend information, and a longer window (14 days) would be too slow to react to market changes. The 7-day horizon matches the typical holding period for swing trades in my strategy while still allowing the model to predict meaningful price movements."

---

## Interview Preparation Checklist

Before your interview, make sure you can:

- [ ] Explain what each model predicts (price vs direction) in one sentence
- [ ] List all 5 base features from memory
- [ ] Describe the rolling window aggregation (5 → 16 features)
- [ ] Explain why you use Linear Regression features (extrapolation)
- [ ] Describe your target columns for both models
- [ ] Explain that models DON'T combine mathematically
- [ ] Describe time series → tabular conversion with an example
- [ ] State your metrics (MAPE <8%, accuracy >65%)
- [ ] Explain the extrapolation problem and solution
- [ ] Draw the data flow diagram from memory

---

## Key Takeaways

**What Swarnabha Wants to Hear**:

1. ✅ **Clarity on what each model does**
   - Regressor: Predicts price (continuous)
   - Classifier: Predicts direction (binary)

2. ✅ **Understanding of your features**
   - 5 base features, each with a specific purpose
   - No redundancy (removed 5 features after analysis)
   - lr_trend is the "secret sauce" for extrapolation

3. ✅ **Knowledge of your transformation**
   - Time series → tabular via rolling windows
   - Anti-future-data leakage through temporal splits
   - Aggregation creates richer feature space

4. ✅ **Reasoning behind your choices**
   - Hybrid because RandomForest alone fails at ATH
   - 7-day window matches Bitcoin trading cycles
   - Skip FLAT to focus classifier on clear signals

5. ✅ **Honest about limitations**
   - 60% accuracy is modest but acceptable
   - Models work independently (no ensemble magic)
   - Used reasoning, not statistical feature selection

**What NOT to Say**:

- ❌ "I used two models because it's better" (vague)
- ❌ "They get combined somehow" (you don't know your own system)
- ❌ "I'm not sure why I chose these features" (lack of reasoning)
- ❌ "It just works" (no understanding of nuances)

---

## References

- **Main Implementation**: [src/modules/module3_prediction.py](../src/modules/module3_prediction.py)
- **Architecture Explanation**: [docs/WHY_LINEAR_REGRESSION_RANDOMFOREST.md](WHY_LINEAR_REGRESSION_RANDOMFOREST.md)
- **Agent Architecture**: [docs/AGENT_ARCHITECTURE_NUANCES.md](AGENT_ARCHITECTURE_NUANCES.md)

---

**Version**: 1.0
**Last Updated**: 2025-12-13
**Prepared for**: ML Engineering / Data Science Interviews

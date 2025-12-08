# Testing Guide - BTC Intelligent Trader

## Quick Reference - All Test Commands

### Main Commands

#### Full System Tests
```bash
# Full backtest (6 months)
python main.py --mode backtest

# Backtest with custom parameters
python main.py --mode backtest --months 12 --capital 20000

# Live trading (Testnet)
python main.py --mode live

# Natural language chat interface
python main.py --mode chat

# Test API connections
python main.py --mode test-apis
```

---

##  Individual Module Tests

### Module 1: Technical Indicators
```bash
python test_module1_individual.py
```
**Tests:**
- RSI calculation
- ATR calculation
- MACD calculation
- SMA 50/200 calculation
- Anti-future-data enforcement

---

### Module 2: Sentiment Analysis
```bash
python test_module2_individual.py
```
**Tests:**
- Fear & Greed Index fetching
- RAG (FAISS) index building
- RAG similarity search
- Sentiment proxy generation

---

### Module 3: Price Prediction
```bash
# Full test (thorough)
python test_module3_individual.py

# Quick test (faster)
python test_module3_quick.py
```
**Tests:**
- Feature engineering (13 custom features)
- Linear Regression price prediction
- Random Forest direction classification
- Rolling window validation
- MAPE and directional accuracy

---

##  Component Tests

### Decision Box & Trading Logic
```bash
python test_strategies.py
```
**Tests:**
- DCA strategy logic
- Swing trading strategy
- ATR stop-loss logic
- Signal combination
- Risk management

---

### API Keys Validation
```bash
python test_api_keys.py
```
**Tests:**
- Binance API connection
- Fear & Greed API
- .env configuration

---

### Live Trading (Quick Test)
```bash
python test_live_quick.py
```
**Tests:**
- Live trader initialization
- API connections
- Portfolio tracking
- Decision making loop

---

##  Utility Scripts

### Convert 15-min to Daily Data
```bash
python convert_to_daily.py
```
Converts `btc_15m_data_2018_to_2025.csv` → `btc_daily_data_2018_to_2025.csv`

---

## Data Pipeline Tests

### Test Data Loader
```bash
python src/data_pipeline/data_loader.py
```
**Tests:**
- CSV loading
- Data cleaning
- Validation
- Output to processed/

---

##  Module Tests (Direct)

### Test Technical Module
```bash
python src/modules/module1_technical.py
```

### Test Sentiment Module
```bash
python src/modules/module2_sentiment.py
```

### Test Prediction Module
```bash
python src/modules/module3_prediction.py
```

---

## [REFRESH]Backtest Engine Test

### Test Backtest Engine Standalone
```bash
python src/backtesting/backtest_engine.py
```
**Tests:**
- Rolling window backtesting
- Portfolio tracking
- Metrics calculation
- Trade execution

---

##  Expected Outputs

### Successful Test Output
```
 Module loads without errors
 Functions return expected types
 Validation passes
 Anti-future-data enforcement works
[OK] TEST COMPLETE
```

### Common Issues
- **FileNotFoundError**: Place CSV data in `data/raw/`
- **API Error**: Check `.env` file has valid keys
- **Import Error**: Run `pip install -r requirements.txt`

---

##  Recommended Test Sequence

1. **Test APIs First**
   ```bash
   python test_api_keys.py
   ```

2. **Test Individual Modules**
   ```bash
   python test_module1_individual.py
   python test_module2_individual.py
   python test_module3_quick.py
   ```

3. **Test Decision Logic**
   ```bash
   python test_strategies.py
   ```

4. **Run Full Backtest**
   ```bash
   python main.py --mode backtest --months 6
   ```

5. **Test Live Trading (Optional)**
   ```bash
   python main.py --mode test-apis
   python test_live_quick.py
   ```

---

## Notes

- All tests use data from `data/raw/btc_daily_data_2018_to_2025.csv` (daily) or `btc_15m_data_2018_to_2025.csv` (15-min)
- Model: Linear Regression (price) + Random Forest (direction)
- No LSTM, no LightGBM - simple and fast!

#!/usr/bin/env python3
"""Test Binance API Keys"""

import os
from dotenv import load_dotenv
from src.data_pipeline.api_client import APIClient

load_dotenv()

print('='*60)
print('TESTING API KEYS')
print('='*60)
print(f'API Key (first 20 chars): {os.getenv("BINANCE_API_KEY")[:20]}...')
print()

api = APIClient()

# Test 1: Binance Testnet
print('[TEST 1] Binance Testnet API')
try:
    price_data = api.get_btc_price(use_testnet=True)
    print(f'   Status: WORKING')
    print(f'   BTC Price: ${price_data["price"]:,.2f}')
except Exception as e:
    print(f'   Status: FAILED')
    print(f'   Error: {e}')

print()

# Test 2: Fear & Greed API
print('[TEST 2] Fear & Greed API')
try:
    fg_data = api.get_fear_greed_index()
    print(f'   Status: WORKING')
    print(f'   Score: {fg_data["value"]}/100 ({fg_data["classification"]})')
except Exception as e:
    print(f'   Status: FAILED')
    print(f'   Error: {e}')

print()
print('='*60)

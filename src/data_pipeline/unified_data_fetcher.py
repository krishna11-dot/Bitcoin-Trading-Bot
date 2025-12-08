"""
Unified Data Fetcher - Smart Data Source Selection

PURPOSE:
    Intelligently fetch Bitcoin data from the best available source:
    1. Try CoinGecko MCP (live data) first
    2. Fall back to CSV (historical data) if MCP unavailable

USE CASES:
    - Natural language interface (chat mode): prefers live data
    - Backtesting: always uses CSV (historical consistency)
    - Live trading: uses MCP for current price, CSV for history

SUCCESS CRITERIA:
    - Returns valid data from either source
    - Seamless fallback if primary source fails
    - Clear logging of which source was used
    - No application crashes due to data unavailability
    - Backtest mode ONLY uses CSV (never MCP)

"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

from src.data_pipeline.coingecko_mcp import CoinGeckoMCP
from src.data_pipeline.data_loader import BitcoinDataLoader


class UnifiedDataFetcher:
    """
    Unified data fetcher with intelligent source selection.

    Priority:
    1. CoinGecko MCP (live data) - for current market data
    2. CSV (historical data) - fallback or backtesting

    Example Usage:
        fetcher = UnifiedDataFetcher()

        # Get current price (tries MCP, falls back to CSV)
        current_price = fetcher.get_current_price()

        # Get historical data (always CSV)
        df = fetcher.get_historical_data()

        # Get both live and historical
        data = fetcher.get_combined_data()
    """

    def __init__(self, force_csv: bool = False):
        """
        Initialize unified data fetcher.

        Args:
            force_csv: If True, only use CSV (for backtesting)
                      If False, try MCP then fall back to CSV
        """
        self.force_csv = force_csv

        # Initialize MCP client (if not forced to CSV)
        if not force_csv:
            self.mcp = CoinGeckoMCP()
            if self.mcp.enabled:
                print("[DATA] MCP enabled - will use live data when available")
            else:
                print("[DATA] MCP disabled - using CSV only")
        else:
            self.mcp = None
            print("[DATA] Forced CSV mode (backtesting)")

        # Initialize data loader
        self.data_loader = BitcoinDataLoader()

        # Path to processed CSV
        self.csv_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'bitcoin_clean.csv'

    def get_current_price(self) -> Tuple[float, str]:
        """
        Get current Bitcoin price from best available source.

        Priority:
        1. CoinGecko MCP (live price)
        2. CSV latest row (fallback)

        Returns:
            (price, source) tuple
            - price: Current BTC price in USD
            - source: 'mcp' or 'csv'

        Example:
            fetcher = UnifiedDataFetcher()
            price, source = fetcher.get_current_price()
            print(f"BTC: ${price:,.2f} (source: {source})")
        """
        # Try MCP first (if not forced to CSV)
        if not self.force_csv and self.mcp and self.mcp.enabled:
            live_data = self.mcp.get_bitcoin_price()
            if live_data:
                price = live_data['price']
                print(f"[MCP] LIVE Bitcoin price: ${price:,.2f} (as of {datetime.now().strftime('%Y-%m-%d %H:%M')})")
                return price, 'mcp'
            else:
                print("[MCP] FAILED to fetch live price, falling back to CSV")

        # Fallback to CSV
        df = self.get_historical_data()
        if df is not None and len(df) > 0:
            price = df.iloc[-1]['Price']
            date = df.iloc[-1]['Date']
            print(f"[DATA] Current price from CSV (as of {date.date()}): ${price:,.2f}")
            return price, 'csv'

        # No data available
        raise ValueError("No price data available from any source")

    def get_historical_data(self) -> Optional[pd.DataFrame]:
        """
        Get historical Bitcoin data from CSV.

        This always uses CSV for consistency in backtesting.
        Never uses MCP for historical data (MCP is for live data only).

        Returns:
            DataFrame with historical price data
            None if data unavailable

        Example:
            fetcher = UnifiedDataFetcher()
            df = fetcher.get_historical_data()
            print(f"Historical data: {len(df)} rows")
        """
        try:
            if not self.csv_path.exists():
                print("[DATA] CSV not found - attempting to generate from raw data")
                self.data_loader.clean_and_save()

            df = pd.read_csv(self.csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')

            print(f"[DATA] Loaded historical data: {len(df)} rows ({df['Date'].min().date()} to {df['Date'].max().date()})")
            print(f"[INFO] Historical data used for technical indicators (RSI, MACD, ATR)")

            return df

        except Exception as e:
            print(f"[DATA] Error loading historical data: {e}")
            return None

    def get_combined_data(self) -> Dict:
        """
        Get both live and historical data.

        Returns:
            {
                'live': {
                    'price': 98234.56,
                    'market_cap': 1934567890123,
                    'volume_24h': 45678901234,
                    'price_change_24h': 2.5,
                    'source': 'mcp' or 'csv'
                },
                'historical': DataFrame
            }

        Example:
            fetcher = UnifiedDataFetcher()
            data = fetcher.get_combined_data()

            if data['live']:
                print(f"Live: ${data['live']['price']:,.2f}")

            if data['historical'] is not None:
                print(f"Historical: {len(data['historical'])} rows")
        """
        # Get live data
        live_data = None
        if not self.force_csv and self.mcp and self.mcp.enabled:
            mcp_data = self.mcp.get_bitcoin_price()
            if mcp_data:
                print(f"[MCP] LIVE Bitcoin price: ${mcp_data['price']:,.2f} (as of {datetime.now().strftime('%Y-%m-%d %H:%M')})")
                live_data = {
                    **mcp_data,
                    'source': 'mcp'
                }
            else:
                print("[MCP] FAILED to fetch live price, falling back to CSV")

        # If MCP failed or not available, use CSV latest
        if live_data is None:
            df = self.get_historical_data()
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                live_data = {
                    'price': latest['Price'],
                    'market_cap': latest.get('Market Cap', None),
                    'volume_24h': latest.get('Volume', None),
                    'price_change_24h': None,
                    'timestamp': latest['Date'].isoformat(),
                    'source': 'csv'
                }

        # Get historical data
        historical_data = self.get_historical_data()

        return {
            'live': live_data,
            'historical': historical_data
        }

    def get_market_summary(self) -> Dict:
        """
        Get comprehensive market summary.

        Returns:
            {
                'current_price': 98234.56,
                'price_source': 'mcp' or 'csv',
                '24h_change': 2.5,  # percentage
                'latest_rsi': 45.0,  # if available
                'latest_fear_greed': 32,  # if available
                'data_range': ('2018-01-01', '2025-12-07'),
                'total_rows': 2685
            }

        Example:
            fetcher = UnifiedDataFetcher()
            summary = fetcher.get_market_summary()
            print(f"BTC: ${summary['current_price']:,.2f} ({summary['price_source']})")
        """
        # Get combined data
        data = self.get_combined_data()

        # Build summary
        summary = {}

        # Current price
        if data['live']:
            summary['current_price'] = data['live']['price']
            summary['price_source'] = data['live']['source']
            summary['24h_change'] = data['live'].get('price_change_24h')
        else:
            summary['current_price'] = None
            summary['price_source'] = None

        # Historical data info
        if data['historical'] is not None:
            df = data['historical']
            summary['data_range'] = (
                df['Date'].min().date().isoformat(),
                df['Date'].max().date().isoformat()
            )
            summary['total_rows'] = len(df)

            # Latest technical indicators (if available)
            latest = df.iloc[-1]
            summary['latest_rsi'] = latest.get('RSI')
            summary['latest_fear_greed'] = latest.get('Fear_Greed')
        else:
            summary['data_range'] = None
            summary['total_rows'] = 0

        return summary


def main():
    """
    Test unified data fetcher.

    SUCCESS CRITERIA:
        - Fetches data from available sources
        - Falls back gracefully if primary source unavailable
        - Returns data in correct format
        - Clear logging of data sources
    """
    print("="*60)
    print("UNIFIED DATA FETCHER - Test Mode")
    print("="*60)

    # Test 1: Normal mode (tries MCP, falls back to CSV)
    print("\nTest 1: Normal mode (MCP enabled)")
    print("-"*60)
    fetcher = UnifiedDataFetcher(force_csv=False)

    price, source = fetcher.get_current_price()
    print(f"[OK] Current price: ${price:,.2f} (source: {source})")

    # Test 2: Get historical data
    print("\nTest 2: Historical data")
    print("-"*60)
    df = fetcher.get_historical_data()
    if df is not None:
        print(f"[OK] Historical data: {len(df)} rows")
        print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        print(f"  Price range: ${df['Price'].min():,.2f} to ${df['Price'].max():,.2f}")
    else:
        print("[FAILED] Could not load historical data")

    # Test 3: Combined data
    print("\nTest 3: Combined data")
    print("-"*60)
    data = fetcher.get_combined_data()

    if data['live']:
        print(f"[OK] Live data:")
        print(f"  Price: ${data['live']['price']:,.2f}")
        print(f"  Source: {data['live']['source']}")
        if data['live'].get('24h_change'):
            print(f"  24h Change: {data['live']['24h_change']:+.2f}%")

    if data['historical'] is not None:
        print(f"[OK] Historical data: {len(data['historical'])} rows")

    # Test 4: Market summary
    print("\nTest 4: Market summary")
    print("-"*60)
    summary = fetcher.get_market_summary()

    print(f"[OK] Market Summary:")
    print(f"  Current Price: ${summary.get('current_price', 0):,.2f}")
    print(f"  Price Source: {summary.get('price_source')}")
    if summary.get('24h_change'):
        print(f"  24h Change: {summary['24h_change']:+.2f}%")
    if summary.get('latest_rsi'):
        print(f"  Latest RSI: {summary['latest_rsi']:.1f}")
    if summary.get('data_range'):
        print(f"  Data Range: {summary['data_range'][0]} to {summary['data_range'][1]}")
    print(f"  Total Rows: {summary.get('total_rows', 0)}")

    # Test 5: Forced CSV mode (backtesting)
    print("\nTest 5: Forced CSV mode (backtesting)")
    print("-"*60)
    fetcher_csv = UnifiedDataFetcher(force_csv=True)

    price_csv, source_csv = fetcher_csv.get_current_price()
    print(f"[OK] Price from CSV: ${price_csv:,.2f} (source: {source_csv})")

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    if price and df is not None:
        print("[OK] Unified data fetcher working correctly")
    else:
        print("[WARNING] Some data sources unavailable")


if __name__ == "__main__":
    main()

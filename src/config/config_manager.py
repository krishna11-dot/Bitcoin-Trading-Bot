#!/usr/bin/env python3
"""
Configuration Manager - Google Sheets Integration

Fetches trading configuration from Google Sheets with local JSON fallback.

Architecture:
1. Try to fetch from Google Sheets
2. If successful, cache locally
3. If failed, use local cache
4. If no cache, use hardcoded defaults
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


class ConfigManager:
    """
    Manages trading configuration with Google Sheets sync and local fallback.

    Usage:
        config_mgr = ConfigManager()
        config = config_mgr.get_config()

        # Access values
        dca_percent = config['dca_buy_amount_percent']
        atr_multiplier = config['atr_stop_loss_multiplier']
    """

    def __init__(
        self,
        service_account_path: str = "config/service_account.json",
        cache_path: str = "config/trading_config.json",
        sheet_id: Optional[str] = None
    ):
        """
        Initialize configuration manager.

        Args:
            service_account_path: Path to Google service account JSON
            cache_path: Path to local cache file
            sheet_id: Google Sheet ID (from .env if not provided)
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.service_account_path = self.project_root / service_account_path
        self.cache_path = self.project_root / cache_path

        # Load .env file
        env_path = self.project_root / '.env'
        load_dotenv(env_path)

        # Get sheet ID from env or parameter
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')

        # Google Sheets client (initialized on demand)
        self._client = None

    def get_config(self, force_remote: bool = False) -> Dict[str, Any]:
        """
        Get configuration with fallback chain:
        1. Google Sheets (if available and not stale)
        2. Local cache (if exists)
        3. Hardcoded defaults (last resort)

        Args:
            force_remote: Force fetch from Google Sheets (ignore cache)

        Returns:
            Configuration dictionary
        """
        # Try Google Sheets first
        if not force_remote:
            # Check if cache is fresh (< 5 minutes old)
            if self._is_cache_fresh():
                print("[CONFIG] Using local cache (fresh)")
                return self._load_cache()

        # Try fetching from Google Sheets
        if GSPREAD_AVAILABLE:
            try:
                print("[CONFIG] Fetching from Google Sheets...")
                config = self._fetch_from_sheets()

                # Save to cache
                self._save_cache(config)
                print("[CONFIG] OK - Config loaded from Google Sheets")
                return config

            except Exception as e:
                print(f"[CONFIG] WARNING: Failed to fetch from Google Sheets: {e}")
        else:
            print("[CONFIG] WARNING: gspread not installed - skipping Google Sheets")

        # Fallback to local cache
        if self.cache_path.exists():
            print("[CONFIG] Using local cache (fallback)")
            return self._load_cache()

        # Last resort: hardcoded defaults
        print("[CONFIG] WARNING: Using hardcoded defaults (no cache available)")
        return self._get_defaults()

    def _fetch_from_sheets(self) -> Dict[str, Any]:
        """
        Fetch configuration from Google Sheets.

        Sheet structure (2 columns):
        | Key                       | Value  |
        |---------------------------|--------|
        | initial_capital           | 10000  |
        | dca_buy_amount_percent    | 0.05   |
        | atr_stop_loss_multiplier  | 2.0    |
        | ...                       | ...    |

        Returns:
            Configuration dictionary
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError("gspread not installed. Run: pip install gspread google-auth")

        if not self.service_account_path.exists():
            raise FileNotFoundError(
                f"Service account file not found: {self.service_account_path}\n"
                f"Download from Google Cloud Console and place at this location."
            )

        if not self.sheet_id:
            raise ValueError(
                "GOOGLE_SHEET_ID not set in .env\n"
                "Get it from your Google Sheet URL: "
                "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
            )

        # Initialize client if needed
        if self._client is None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            creds = Credentials.from_service_account_file(
                str(self.service_account_path),
                scopes=scopes
            )
            self._client = gspread.authorize(creds)

        # Open sheet
        sheet = self._client.open_by_key(self.sheet_id).sheet1

        # Read all rows (skip header)
        rows = sheet.get_all_values()[1:]  # Skip header row

        # Convert to dict
        config = {}
        for row in rows:
            if len(row) >= 2 and row[0]:  # Must have key and value
                key = row[0].strip()
                value = row[1].strip()

                # Type conversion
                config[key] = self._parse_value(value)

        return config

    def _parse_value(self, value: str) -> Any:
        """
        Parse string value from sheet to appropriate Python type.

        Args:
            value: String value from sheet

        Returns:
            Parsed value (int, float, bool, or str)
        """
        # Try boolean
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False

        # Try int
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _load_cache(self) -> Dict[str, Any]:
        """Load configuration from local cache."""
        with open(self.cache_path, 'r') as f:
            return json.load(f)

    def _save_cache(self, config: Dict[str, Any]) -> None:
        """Save configuration to local cache."""
        # Ensure directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.cache_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _is_cache_fresh(self, max_age_seconds: int = 300) -> bool:
        """
        Check if cache is fresh (< max_age_seconds old).

        Args:
            max_age_seconds: Maximum age in seconds (default: 5 minutes)

        Returns:
            True if cache is fresh, False otherwise
        """
        if not self.cache_path.exists():
            return False

        import time
        cache_age = time.time() - self.cache_path.stat().st_mtime
        return cache_age < max_age_seconds

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Get hardcoded default configuration.

        Last resort fallback if Google Sheets and cache both fail.
        """
        return {
            # Capital
            'initial_capital': 10000,

            # DCA Strategy
            'dca_buy_amount_percent': 0.05,  # 5% of capital per buy
            'dca_enabled': True,

            # Swing Strategy
            'swing_enabled': False,  # Disabled by default
            'swing_buy_percent': 0.10,

            # Stop-Loss
            'atr_stop_loss_multiplier': 2.0,
            'stop_loss_enabled': True,

            # Take Profit
            'take_profit_threshold': 0.15,  # 15% profit
            'take_profit_enabled': True,

            # Risk Management
            'max_drawdown_circuit_breaker': 0.25,  # 25%
            'max_position_size': 0.95,  # 95% of capital

            # Technical Indicators
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'rsi_neutral_low': 40,
            'rsi_neutral_high': 60,

            # Sentiment
            'fear_greed_buy_threshold': 40,
            'fear_greed_sell_threshold': 75,

            # Data Fetching
            'data_fetch_interval_seconds': 300,  # 5 minutes

            # Logging
            'verbose': True,
            'log_level': 'INFO'
        }


# Convenience function for one-liner usage
def load_config() -> Dict[str, Any]:
    """
    Load configuration (convenience function).

    Returns:
        Configuration dictionary
    """
    manager = ConfigManager()
    return manager.get_config()


if __name__ == "__main__":
    # Test configuration manager
    print("="*60)
    print("TESTING CONFIGURATION MANAGER")
    print("="*60)

    manager = ConfigManager()
    config = manager.get_config()

    print("\n[CONFIG] Loaded configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print("\n[OK] Configuration manager working!")

"""

DATA LOADER - Bitcoin Historical Data Cleaning


PURPOSE:
    Load and clean the Bitcoin historical CSV data, ensuring data
    quality and consistency for downstream modules.

SUCCESS CRITERIA:
    - Loads CSV without errors
    - Handles missing values correctly
    - Removes duplicates
    - Validates date ranges
    - Ensures numeric columns are properly typed
    - Outputs clean dataset to processed/ directory

VALIDATION METHOD:
    - Check row count (expected: ~1771 rows)
    - Verify no null values in critical columns (Date, Price, Volume)
    - Confirm date is sorted ascending
    - Validate price and volume are positive

"""

import sys
import io
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple

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


class BitcoinDataLoader:
    """
    Loads and cleans Bitcoin historical data from CSV.

    Handles:
    - Missing values
    - Duplicate dates
    - Data type conversions
    - Date sorting
    - Basic validation
    """

    def __init__(self, raw_data_path: str = None, dataset_type: str = 'binance_daily'):
        """
        Initialize data loader.

        Args:
            raw_data_path: Path to raw CSV file. If None, uses default location.
            dataset_type: Type of dataset:
                - 'binance_daily': Daily aggregated data (RECOMMENDED - fast)
                - 'binance_15m': 15-minute data (slow, high-frequency trading)
        """
        if raw_data_path is None:
            # Default path
            project_root = Path(__file__).parent.parent.parent
            if dataset_type == 'binance_daily':
                raw_data_path = project_root / "data" / "raw" / "btc_daily_data_2018_to_2025.csv"
            elif dataset_type == 'binance_15m':
                raw_data_path = project_root / "data" / "raw" / "btc_15m_data_2018_to_2025.csv"
            else:
                # Default to daily if unknown type
                raw_data_path = project_root / "data" / "raw" / "btc_daily_data_2018_to_2025.csv"

        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = self.raw_data_path.parent.parent / "processed" / "bitcoin_clean.csv"
        self.dataset_type = dataset_type

    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw CSV data.

        Returns:
            Raw DataFrame

        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        if not self.raw_data_path.exists():
            raise FileNotFoundError(
                f"Bitcoin historical data not found at: {self.raw_data_path}\n"
                f"Please place the CSV data file in data/raw/ directory"
            )

        print(f" Loading raw data from: {self.raw_data_path}")
        df = pd.read_csv(self.raw_data_path)
        print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")

        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the raw data.

        Steps:
        1. Convert date column to datetime
        2. Handle missing values
        3. Remove duplicates
        4. Sort by date
        5. Validate numeric columns
        6. Reset index

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned DataFrame
        """
        print("\n Cleaning data...")

        # 
        # STEP 1: Identify and rename columns
        # 
        # Expected columns: Date, Price, Open, High, Low, Volume, etc.
        # Make column names consistent
        df.columns = df.columns.str.strip()  # Remove whitespace

        # Print available columns
        print(f"   Available columns: {list(df.columns)}")

        # Handle different dataset formats
        if self.dataset_type == 'binance_15m':
            # Binance format: Open time, Open, High, Low, Close, Volume, ...
            # Rename to standard format
            column_mapping = {
                'Open time': 'Date',
                'Close': 'Price',  # Use Close as primary price
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Volume': 'Volume'
            }

            # Apply renaming
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and old_col != new_col:
                    df = df.rename(columns={old_col: new_col})

            # Drop unnecessary columns for cleaner dataset
            cols_to_keep = ['Date', 'Price', 'Open', 'High', 'Low', 'Volume']
            extra_cols = [col for col in df.columns if col not in cols_to_keep]
            if extra_cols:
                df = df.drop(columns=extra_cols)
                print(f"   Dropped extra columns: {extra_cols}")

        # Print updated columns
        print(f"   Standardized columns: {list(df.columns)}")

        # 
        # STEP 2: Convert Date column to datetime
        # 
        date_column = self._find_date_column(df)
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

        # Remove rows with invalid dates
        invalid_dates = df[date_column].isna().sum()
        if invalid_dates > 0:
            print(f"   [WARNING] Removing {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=[date_column])

        # Rename to standard 'Date'
        if date_column != 'Date':
            df = df.rename(columns={date_column: 'Date'})

        # 
        # STEP 3: Handle numeric columns
        # 
        numeric_columns = ['Price', 'Open', 'High', 'Low', 'Volume', 'Market Cap']

        for col in numeric_columns:
            if col in df.columns:
                # For binance_15m, volume is already numeric
                if self.dataset_type == 'binance_15m' and col == 'Volume':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                # For historical_daily, need to remove commas and K/M/B suffixes
                elif df[col].dtype == 'object':
                    df[col] = df[col].str.replace(',', '')
                    # Handle K/M/B suffixes for historical data
                    if col == 'Volume' and self.dataset_type != 'binance_15m':
                        # Will be handled by _convert_volume_to_numeric if needed
                        pass
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        # 
        # STEP 4: Handle missing values
        # 
        print(f"   Missing values before cleaning:")
        missing_before = df.isnull().sum()
        for col, count in missing_before.items():
            if count > 0:
                print(f"     - {col}: {count}")

        # Strategy: Forward fill for price data (assumes last known price)
        price_cols = ['Price', 'Open', 'High', 'Low']
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill')

        # Volume: Fill with 0 if missing (no trading)
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].fillna(0)

        # Market Cap: Can be calculated or filled
        if 'Market Cap' in df.columns:
            df['Market Cap'] = df['Market Cap'].fillna(method='ffill')

        # Drop any remaining rows with missing critical data
        critical_cols = ['Date', 'Price']
        df = df.dropna(subset=critical_cols)

        # 
        # STEP 5: Remove duplicates
        # 
        duplicates = df.duplicated(subset=['Date']).sum()
        if duplicates > 0:
            print(f"   [WARNING] Removing {duplicates} duplicate dates")
            df = df.drop_duplicates(subset=['Date'], keep='last')

        # 
        # STEP 6: Sort by date
        # 
        df = df.sort_values('Date').reset_index(drop=True)

        # 
        # STEP 7: Validate data
        # 
        self._validate_data(df)

        print(f"\n[OK] Cleaning complete: {len(df)} rows")
        print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

        return df

    def _find_date_column(self, df: pd.DataFrame) -> str:
        """Find the date column (case-insensitive)."""
        date_candidates = ['date', 'Date', 'DATE', 'timestamp', 'Timestamp']

        for col in df.columns:
            if col in date_candidates:
                return col

        # If not found, check if first column looks like a date
        first_col = df.columns[0]
        try:
            pd.to_datetime(df[first_col].iloc[0])
            return first_col
        except:
            pass

        raise ValueError(
            f"Could not find date column. Available columns: {list(df.columns)}"
        )

    def _validate_data(self, df: pd.DataFrame):
        """
        Validate cleaned data meets quality standards.

        Checks:
        - No missing values in critical columns
        - Prices are positive
        - Dates are sorted
        - Volume is non-negative
        """
        # Check critical columns exist
        required_cols = ['Date', 'Price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Check no nulls in critical columns
        nulls = df[required_cols].isnull().sum()
        if nulls.any():
            raise ValueError(f"Null values found in critical columns: {nulls[nulls > 0]}")

        # Check prices are positive
        if (df['Price'] <= 0).any():
            raise ValueError("Found non-positive prices")

        # Check dates are sorted
        if not df['Date'].is_monotonic_increasing:
            raise ValueError("Dates are not sorted in ascending order")

        # Check volume is non-negative (if exists)
        if 'Volume' in df.columns:
            if (df['Volume'] < 0).any():
                raise ValueError("Found negative volume values")

        print("   [OK] Data validation passed")

    def save_cleaned_data(self, df: pd.DataFrame):
        """
        Save cleaned data to processed directory.

        Args:
            df: Cleaned DataFrame
        """
        # Create processed directory if it doesn't exist
        self.processed_data_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to CSV
        df.to_csv(self.processed_data_path, index=False)
        print(f"\n[SAVED] Saved cleaned data to: {self.processed_data_path}")
        print(f"   File size: {self.processed_data_path.stat().st_size / 1024:.1f} KB")

    def load_clean_data(self) -> pd.DataFrame:
        """
        Load previously cleaned data.

        Returns:
            Cleaned DataFrame

        Raises:
            FileNotFoundError: If cleaned data doesn't exist
        """
        if not self.processed_data_path.exists():
            raise FileNotFoundError(
                f"Cleaned data not found at: {self.processed_data_path}\n"
                f"Run clean_and_save() first to generate cleaned data"
            )

        df = pd.read_csv(self.processed_data_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    def clean_and_save(self) -> pd.DataFrame:
        """
        Complete pipeline: load → clean → save.

        Returns:
            Cleaned DataFrame
        """
        # Load raw data
        df_raw = self.load_raw_data()

        # Clean data
        df_clean = self.clean_data(df_raw)

        # Save cleaned data
        self.save_cleaned_data(df_clean)

        return df_clean

    def get_summary_stats(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics of the data.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary of summary stats
        """
        stats = {
            'num_rows': len(df),
            'date_range': (df['Date'].min(), df['Date'].max()),
            'price_range': (df['Price'].min(), df['Price'].max()),
            'avg_price': df['Price'].mean(),
            'median_price': df['Price'].median(),
            'dataset_type': self.dataset_type
        }

        if 'Volume' in df.columns:
            stats['avg_volume'] = df['Volume'].mean()
            stats['total_volume'] = df['Volume'].sum()

        return stats


def main():
    """Main function to test data loader."""
    print("="*60)
    print("BITCOIN DATA LOADER - Testing")
    print("="*60)

    # Initialize loader
    loader = BitcoinDataLoader()

    # Clean and save data
    try:
        df = loader.clean_and_save()

        # Print summary statistics
        print("\n Summary Statistics:")
        stats = loader.get_summary_stats(df)
        print(f"   Rows: {stats['num_rows']}")
        print(f"   Date Range: {stats['date_range'][0].date()} to {stats['date_range'][1].date()}")
        print(f"   Price Range: ${stats['price_range'][0]:,.2f} to ${stats['price_range'][1]:,.2f}")
        print(f"   Average Price: ${stats['avg_price']:,.2f}")
        print(f"   Median Price: ${stats['median_price']:,.2f}")

        if 'avg_volume' in stats:
            print(f"   Average Volume: {stats['avg_volume']:,.0f}")

        # Show first few rows
        print("\n First 5 rows:")
        print(df.head())

        # Show last few rows
        print("\n Last 5 rows:")
        print(df.tail())

        print("\n" + "="*60)
        print("[COMPLETE] DATA LOADER TEST PASSED")
        print("="*60)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nPlease ensure the CSV data file is in data/raw/ directory")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

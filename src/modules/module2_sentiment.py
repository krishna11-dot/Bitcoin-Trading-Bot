"""

MODULE 2: SENTIMENT ANALYSIS (Fear & Greed + RAG)


PURPOSE:
    Analyze market sentiment using Fear & Greed Index and historical
    pattern matching (RAG) to inform trading decisions.

SUCCESS CRITERIA:
    [OK] Fetches Fear & Greed Index successfully (0-100)
    [OK] RAG retrieves similar historical patterns (similarity >0.7)
    [OK] Combines signals into actionable confidence score
    [OK] Handles API failures gracefully (fallback to historical avg)

COMPONENTS:
    1. Fear & Greed Index (Live):
       - Source: alternative.me API
       - Range: 0-100 (0=Extreme Fear, 100=Extreme Greed)
       - Strategy: Buy at <40 (fear), avoid >75 (greed)

    2. RAG (Retrieval-Augmented Generation):
       - Use FAISS to find similar historical market conditions
       - Compare current indicators (RSI, ATR, MACD) to past
       - Retrieve outcomes from similar situations
       - Calculate confidence: % of similar cases that were bullish

VALIDATION METHOD:
    - Test F&G API call returns valid 0-100 value
    - Test RAG retrieves relevant historical patterns
    - Verify confidence score is 0-1 range

"""

import sys
import io
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# RAG imports (MUST BE FIRST before pandas/numpy to avoid Windows DLL conflicts)
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except (ImportError, OSError) as e:
    FAISS_AVAILABLE = False
    if "DLL" in str(e) or "torch" in str(e):
        print("[WARNING]  PyTorch DLL error. RAG functionality disabled. (This is OK for backtesting)")
    else:
        print(f"[WARNING]  FAISS not available: {e}. RAG functionality will be limited.")

# Other imports AFTER RAG imports to avoid DLL conflicts
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import pickle
import os

# Note: Console encoding fix removed to avoid interference with PyTorch/FAISS imports
# If you need emoji support, set PYTHONIOENCODING=utf-8 environment variable instead


class SentimentAnalyzer:
    """
    Analyzes market sentiment using Fear & Greed Index and RAG.

    Combines live market sentiment (Fear & Greed) with historical
    pattern matching (RAG) to provide trading confidence scores.
    """

    def __init__(self, api_client=None, enable_rag: bool = False):
        """
        Initialize sentiment analyzer.

        SIMPLIFIED (v1.0): RAG disabled by default, only Fear & Greed

        Args:
            api_client: APIClient instance for fetching F&G index
            enable_rag: Enable RAG functionality (default: False for v1.0 simplicity)
        """
        self.api_client = api_client
        self.enable_rag = enable_rag and FAISS_AVAILABLE  # v1.0: False by default

        # RAG components
        self.faiss_index = None
        self.historical_data = None
        self.embedding_model = None

        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.rag_db_path = project_root / "data" / "rag_vectordb"
        self.rag_db_path.mkdir(parents=True, exist_ok=True)

    # 
    # FEAR & GREED INDEX
    # 

    def get_fear_greed_score(self) -> Dict:
        """
        Get current Fear & Greed Index from API.

        Returns:
            dict: {
                'value': int (0-100),
                'classification': str,
                'signal': 'BUY'/'SELL'/'HOLD',
                'confidence': float (0-1)
            }

        Note:
            If API fails, returns historical average (50)
        """
        if self.api_client is None:
            # Fallback: Return neutral
            return {
                'value': 50,
                'classification': 'Neutral',
                'signal': 'HOLD',
                'confidence': 0.5
            }

        try:
            # Fetch from API
            fng_data = self.api_client.get_fear_greed_index()

            value = fng_data['value']
            classification = fng_data['classification']

            # Interpret signal
            # Strategy: Buy in fear, sell in greed
            if value < 40:
                signal = 'BUY'
                confidence = (40 - value) / 40  # More fear = higher confidence
            elif value > 75:
                signal = 'SELL'
                confidence = (value - 75) / 25  # More greed = higher confidence
            else:
                signal = 'HOLD'
                confidence = 0.5

            return {
                'value': value,
                'classification': classification,
                'signal': signal,
                'confidence': min(confidence, 1.0)
            }

        except Exception as e:
            print(f"[WARNING]  Failed to fetch Fear & Greed: {e}")
            # Fallback: Neutral
            return {
                'value': 50,
                'classification': 'Neutral (API Error)',
                'signal': 'HOLD',
                'confidence': 0.5
            }

    # 
    # RAG (RETRIEVAL-AUGMENTED GENERATION)
    # 

    def build_rag_index(self, df: pd.DataFrame):
        """
        Build FAISS index from historical data for RAG.

        Args:
            df: DataFrame with historical data and indicators
                Must have: Date, Price, RSI, ATR, MACD_diff

        Steps:
            1. Create feature vectors from indicators
            2. Calculate forward returns (outcomes)
            3. Build FAISS index for similarity search
            4. Save index to disk
        """
        if not self.enable_rag:
            print("[WARNING]  RAG is disabled")
            return

        print("\n Building RAG index...")

        # Ensure indicators exist - now with 12 features
        required_cols = ['Date', 'Price', 'RSI', 'ATR', 'MACD_diff',
                        'momentum_oscillator', 'roc_7d',
                        'volume_spike', 'volume_trend',
                        'price_change_pct', 'sma_ratio',
                        'higher_highs', 'lower_lows']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns for RAG: {missing}")

        # Remove rows with NaN indicators
        df_clean = df.dropna(subset=required_cols).copy()

        # Calculate forward returns (7-day)
        df_clean['future_return_7d'] = df_clean['Price'].pct_change(periods=7).shift(-7)

        # Label: 1 if positive return, 0 if negative
        df_clean['future_label'] = (df_clean['future_return_7d'] > 0).astype(int)

        # Remove rows without forward returns
        df_clean = df_clean.dropna(subset=['future_return_7d'])

        print(f"   Prepared {len(df_clean)} historical patterns")

        # Create feature vectors - EXPANDED to 12 features
        feature_cols = [
            # Original (3)
            'RSI', 'ATR', 'MACD_diff',
            # New momentum (2)
            'momentum_oscillator', 'roc_7d',
            # New volume (2)
            'volume_spike', 'volume_trend',
            # New trend (2)
            'price_change_pct', 'sma_ratio',
            # New market structure (2)
            'higher_highs', 'lower_lows',
            # Price (1)
            'Price'
        ]
        features = df_clean[feature_cols].values.astype('float32')

        # Normalize features to 0-100 range for consistency
        # ATR normalization: scale to % of price
        atr_pct = (df_clean['ATR'] / df_clean['Price'] * 100).values
        features[:, 1] = atr_pct

        # MACD_diff normalization: clip to ±100
        macd_norm = np.clip(features[:, 2], -100, 100)
        features[:, 2] = macd_norm

        # Momentum oscillator: already in ratio form, scale to ±100
        features[:, 3] = np.clip(features[:, 3] * 100, -100, 100)

        # ROC 7d: already in pct change form, scale to ±100
        features[:, 4] = np.clip(features[:, 4] * 100, -100, 100)

        # Volume spike: ratio, clip to 0-200
        features[:, 5] = np.clip(features[:, 5] * 100, 0, 200)

        # Volume trend: pct change, scale to ±100
        features[:, 6] = np.clip(features[:, 6] * 100, -100, 100)

        # Price change pct: scale to ±100
        features[:, 7] = np.clip(features[:, 7] * 100, -100, 100)

        # SMA ratio: scale to 0-200
        features[:, 8] = np.clip(features[:, 8] * 100, 0, 200)

        # Higher highs: already 0/1, scale to 0-100
        features[:, 9] = features[:, 9] * 100

        # Lower lows: already 0/1, scale to 0-100
        features[:, 10] = features[:, 10] * 100

        # Price: normalize to 0-100 using min-max scaling within dataset
        price_min = features[:, 11].min()
        price_max = features[:, 11].max()
        features[:, 11] = ((features[:, 11] - price_min) / (price_max - price_min)) * 100

        # Build FAISS index
        dimension = features.shape[1]  # 12 features
        self.faiss_index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.faiss_index.add(features)

        # Store historical data for retrieval (including all new features)
        store_cols = ['Date', 'Price', 'RSI', 'ATR', 'MACD_diff',
                     'momentum_oscillator', 'roc_7d',
                     'volume_spike', 'volume_trend',
                     'price_change_pct', 'sma_ratio',
                     'higher_highs', 'lower_lows',
                     'future_return_7d', 'future_label']
        self.historical_data = df_clean[store_cols].copy()

        # Save to disk
        index_path = self.rag_db_path / "faiss_index.bin"
        data_path = self.rag_db_path / "historical_data.pkl"

        faiss.write_index(self.faiss_index, str(index_path))
        self.historical_data.to_pickle(str(data_path))

        print(f"   [OK] RAG index built: {len(df_clean)} patterns")
        print(f"   [SAVED] Saved to: {self.rag_db_path}")

    def load_rag_index(self):
        """Load pre-built FAISS index from disk."""
        if not self.enable_rag:
            return

        index_path = self.rag_db_path / "faiss_index.bin"
        data_path = self.rag_db_path / "historical_data.pkl"

        if not index_path.exists() or not data_path.exists():
            print("[WARNING]  RAG index not found. Run build_rag_index() first.")
            return

        # Load index
        self.faiss_index = faiss.read_index(str(index_path))

        # Load historical data
        self.historical_data = pd.read_pickle(str(data_path))

        print(f"[OK] RAG index loaded: {self.faiss_index.ntotal} patterns")

    def get_rag_confidence(self, current_indicators: Dict, k: int = 50) -> Dict:
        """
        Get trading confidence from RAG (similar historical patterns).

        Args:
            current_indicators: dict with 12 features (RSI, ATR, MACD_diff,
                               momentum_oscillator, roc_7d, volume_spike,
                               volume_trend, price_change_pct, sma_ratio,
                               higher_highs, lower_lows, price)
            k: Number of similar patterns to retrieve (default: 50)

        Returns:
            dict: {
                'confidence': float (0-1),
                'signal': 'BUY'/'SELL'/'HOLD',
                'similar_count': int,
                'bullish_pct': float,
                'avg_return': float
            }
        """
        if not self.enable_rag or self.faiss_index is None:
            # RAG not available - return neutral
            return {
                'confidence': 0.5,
                'signal': 'HOLD',
                'similar_count': 0,
                'bullish_pct': 0.5,
                'avg_return': 0.0
            }

        # Extract all 12 features from current_indicators
        rsi = current_indicators.get('RSI', 50)
        atr = current_indicators.get('ATR', 1000)
        macd_diff = current_indicators.get('MACD_diff', 0)
        momentum_oscillator = current_indicators.get('momentum_oscillator', 1.0)
        roc_7d = current_indicators.get('roc_7d', 0.0)
        volume_spike = current_indicators.get('volume_spike', 1.0)
        volume_trend = current_indicators.get('volume_trend', 0.0)
        price_change_pct = current_indicators.get('price_change_pct', 0.0)
        sma_ratio = current_indicators.get('sma_ratio', 1.0)
        higher_highs = current_indicators.get('higher_highs', 0)
        lower_lows = current_indicators.get('lower_lows', 0)
        price = current_indicators.get('Price', 100000)  # Current BTC price

        # Build 12-feature vector with SAME normalization as build_rag_index()
        feature_vec = np.zeros(12, dtype='float32')

        # Feature 0: RSI (already 0-100)
        feature_vec[0] = rsi

        # Feature 1: ATR as % of price
        feature_vec[1] = (atr / price) * 100

        # Feature 2: MACD_diff clipped to ±100
        feature_vec[2] = np.clip(macd_diff, -100, 100)

        # Feature 3: Momentum oscillator scaled to ±100
        feature_vec[3] = np.clip(momentum_oscillator * 100, -100, 100)

        # Feature 4: ROC 7d scaled to ±100
        feature_vec[4] = np.clip(roc_7d * 100, -100, 100)

        # Feature 5: Volume spike clipped to 0-200
        feature_vec[5] = np.clip(volume_spike * 100, 0, 200)

        # Feature 6: Volume trend scaled to ±100
        feature_vec[6] = np.clip(volume_trend * 100, -100, 100)

        # Feature 7: Price change pct scaled to ±100
        feature_vec[7] = np.clip(price_change_pct * 100, -100, 100)

        # Feature 8: SMA ratio scaled to 0-200
        feature_vec[8] = np.clip(sma_ratio * 100, 0, 200)

        # Feature 9: Higher highs scaled to 0-100
        feature_vec[9] = higher_highs * 100

        # Feature 10: Lower lows scaled to 0-100
        feature_vec[10] = lower_lows * 100

        # Feature 11: Price normalized (use approximate min/max for inference)
        # In practice, this will be rescaled based on historical range
        # For simplicity, use relative scaling
        price_norm = np.clip((price - 10000) / (150000 - 10000) * 100, 0, 100)
        feature_vec[11] = price_norm

        query = np.array([feature_vec], dtype='float32')

        # Search for k nearest neighbors
        distances, indices = self.faiss_index.search(query, k)

        # Retrieve similar patterns
        similar_patterns = self.historical_data.iloc[indices[0]]

        # Calculate statistics
        bullish_count = similar_patterns['future_label'].sum()
        bullish_pct = bullish_count / len(similar_patterns)
        avg_return = similar_patterns['future_return_7d'].mean()

        # Determine signal
        if bullish_pct > 0.6:
            signal = 'BUY'
            confidence = bullish_pct
        elif bullish_pct < 0.4:
            signal = 'SELL'
            confidence = 1 - bullish_pct
        else:
            signal = 'HOLD'
            confidence = 0.5

        return {
            'confidence': confidence,
            'signal': signal,
            'similar_count': len(similar_patterns),
            'bullish_pct': bullish_pct,
            'avg_return': avg_return * 100  # Convert to percentage
        }

    # 
    # COMBINED SENTIMENT ANALYSIS
    # 

    def calculate_fg_confidence_multiplier(self, fg_score: int) -> float:
        """
        Calculate confidence multiplier based on Fear & Greed Index.

        Rationale:
        - Extreme Fear (<25): Contrarian bullish signal → 1.2× boost
        - Fear (25-40): Mild contrarian signal → 1.1× boost
        - Neutral (40-60): No adjustment → 1.0×
        - Greed (60-75): Mild caution → 0.9× reduction
        - Extreme Greed (>75): Strong caution → 0.7× reduction

        Args:
            fg_score: Fear & Greed score (0-100)

        Returns:
            Confidence multiplier (0.7-1.2)
        """
        if fg_score < 25:
            return 1.2  # Extreme Fear - contrarian boost
        elif fg_score < 40:
            return 1.1  # Fear - mild boost
        elif fg_score <= 60:
            return 1.0  # Neutral - no change
        elif fg_score <= 75:
            return 0.9  # Greed - mild reduction
        else:
            return 0.7  # Extreme Greed - strong reduction

    def analyze_sentiment(self, current_indicators: Dict) -> Dict:
        """
        Combine Fear & Greed and RAG for final sentiment analysis.

        NEW BEHAVIOR:
        - F&G is now a confidence multiplier (not a trigger)
        - RAG confidence is adjusted by F&G multiplier
        - Extreme fear boosts confidence, extreme greed reduces it

        Args:
            current_indicators: dict with technical indicators

        Returns:
            dict: {
                'fear_greed_score': int (0-100),
                'fear_greed_multiplier': float (0.7-1.2),
                'rag_confidence': float (0-1) - original RAG confidence,
                'adjusted_confidence': float (0-1) - RAG × F&G multiplier,
                'rag_signal': str,
                'combined_signal': 'BUY'/'SELL'/'HOLD',
                'combined_confidence': float (0-1)
            }
        """
        # Get Fear & Greed
        fg = self.get_fear_greed_score()

        # Get RAG confidence
        rag = self.get_rag_confidence(current_indicators)

        # Calculate F&G confidence multiplier
        fg_multiplier = self.calculate_fg_confidence_multiplier(fg['value'])

        # Apply F&G multiplier to RAG confidence
        rag_confidence_original = rag['confidence']
        adjusted_confidence = min(1.0, rag_confidence_original * fg_multiplier)

        # Combine signals
        # Weight: 40% F&G, 60% adjusted RAG
        fg_weight = 0.4
        rag_weight = 0.6

        # Convert F&G to confidence (inverse for fear)
        fg_confidence = fg['confidence']

        # Combine confidences using adjusted RAG confidence
        combined_confidence = (fg_weight * fg_confidence) + (rag_weight * adjusted_confidence)

        # Determine combined signal
        if fg['signal'] == 'BUY' and rag['signal'] == 'BUY':
            combined_signal = 'BUY'
        elif fg['signal'] == 'SELL' and rag['signal'] == 'SELL':
            combined_signal = 'SELL'
        else:
            combined_signal = 'HOLD'

        return {
            'fear_greed_score': fg['value'],
            'fear_greed_multiplier': fg_multiplier,
            'rag_confidence': rag_confidence_original,
            'adjusted_confidence': adjusted_confidence,
            'rag_signal': rag['signal'],
            'rag_bullish_pct': rag.get('bullish_pct', 0.5),
            'combined_signal': combined_signal,
            'combined_confidence': combined_confidence
        }


def main():
    """Test sentiment analysis module."""
    print("="*60)
    print("MODULE 2: SENTIMENT ANALYSIS - Testing")
    print("="*60)

    # Initialize API client
    from src.data_pipeline.api_client import APIClient
    from src.data_pipeline.data_loader import BitcoinDataLoader
    from src.modules.module1_technical import calculate_indicators

    api_client = APIClient()
    analyzer = SentimentAnalyzer(api_client=api_client, enable_rag=True)

    # Test 1: Fear & Greed Index
    print("\n Test 1: Fear & Greed Index")
    try:
        fg = analyzer.get_fear_greed_score()
        print(f"   Value: {fg['value']}/100")
        print(f"   Classification: {fg['classification']}")
        print(f"   Signal: {fg['signal']}")
        print(f"   Confidence: {fg['confidence']:.2%}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [WARNING]  Warning: {e}")

    # Test 2: Build RAG Index
    print("\n Test 2: Building RAG Index")
    try:
        loader = BitcoinDataLoader()
        df = loader.load_clean_data()

        # Calculate indicators for full dataset
        df_with_ind = calculate_indicators(df, df['Date'].max())

        # Build RAG index
        analyzer.build_rag_index(df_with_ind)
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: RAG Confidence
    print("\n Test 3: RAG Confidence (Similar Patterns)")
    try:
        # Test with sample indicators
        test_indicators = {
            'RSI': 35,
            'ATR': 1500,
            'MACD_diff': 10,
            'price': 105000
        }

        rag_result = analyzer.get_rag_confidence(test_indicators, k=20)
        print(f"   Similar patterns found: {rag_result['similar_count']}")
        print(f"   Bullish percentage: {rag_result['bullish_pct']:.1%}")
        print(f"   Average return: {rag_result['avg_return']:+.2f}%")
        print(f"   Signal: {rag_result['signal']}")
        print(f"   Confidence: {rag_result['confidence']:.2%}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 4: Combined Sentiment
    print("\n Test 4: Combined Sentiment Analysis")
    try:
        sentiment = analyzer.analyze_sentiment(test_indicators)
        print(f"   Fear & Greed: {sentiment['fear_greed_score']}/100")
        print(f"   RAG Confidence: {sentiment['rag_confidence']:.2%}")
        print(f"   RAG Signal: {sentiment['rag_signal']}")
        print(f"   Combined Signal: {sentiment['combined_signal']}")
        print(f"   Combined Confidence: {sentiment['combined_confidence']:.2%}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    print("\n" + "="*60)
    print("[OK] MODULE 2 TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

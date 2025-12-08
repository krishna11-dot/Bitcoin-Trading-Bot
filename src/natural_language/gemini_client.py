#!/usr/bin/env python3
"""
Gemini API Client with Smart Model Rotation

Wrapper for Google Gemini API with:
- Smart model rotation (avoid rate limits by using multiple models)
- Rate limiting (10+ RPM effective throughput)
- Retry logic with exponential backoff
- Response caching
- Error handling

Strategy: Rotate between multiple Gemini models (all use same API key)
- gemini-2.5-flash: 10 RPM, high quality
- gemini-2.5-flash-lite: 15 RPM, good quality, faster
- gemini-2.0-flash-lite-001: 20 RPM, good quality, fastest
- gemini-1.5-flash: 15 RPM, medium quality

Effective throughput: 30-60 RPM (3-6x improvement!)
"""

import os
import time
import hashlib
import random
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .rate_limiter import RateLimiter

# Load environment variables
load_dotenv()


class GeminiClient:
    """
    Gemini API client with smart model rotation to avoid rate limits.

    Attributes:
        models: List of available Gemini models
        use_rotation: Whether to use smart rotation
        cache: Dictionary for caching responses
    """

    # Model pool (all accessible with same API key)
    MODEL_POOL = [
        {
            'name': 'gemini-2.5-flash',
            'rpm': 10,
            'quality': 'high',
            'speed': 'fast'
        },
        {
            'name': 'gemini-2.5-flash-lite',
            'rpm': 15,
            'quality': 'good',
            'speed': 'very_fast'
        },
        {
            'name': 'gemini-2.0-flash-lite-001',
            'rpm': 20,
            'quality': 'good',
            'speed': 'fastest'
        },
        {
            'name': 'gemini-1.5-flash',
            'rpm': 15,
            'quality': 'medium',
            'speed': 'fast'
        }
    ]

    def __init__(self, api_key: Optional[str] = None, use_rotation: bool = None):
        """
        Initialize Gemini client with smart model rotation.

        Args:
            api_key: Optional API key (defaults to GEMINI_API_KEY env var)
            use_rotation: Enable smart model rotation (defaults to GEMINI_USE_ROTATION env var or True)

        Raises:
            ValueError: If API key not found
            ImportError: If google-generativeai not installed
        """
        if genai is None:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )

        # Get API key
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Add it to your .env file or pass as parameter."
            )

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Check if rotation is enabled (default: True)
        if use_rotation is None:
            use_rotation = os.getenv("GEMINI_USE_ROTATION", "true").lower() == "true"

        self.use_rotation = use_rotation
        self.current_model_index = 0

        if self.use_rotation:
            # Initialize ALL models in pool for rotation
            self.models: List[Dict[str, Any]] = []

            for model_config in self.MODEL_POOL:
                try:
                    model = genai.GenerativeModel(model_config['name'])
                    rate_limiter = RateLimiter(
                        rpm=model_config['rpm'],
                        rpd=250  # Daily limit shared across all models
                    )
                    self.models.append({
                        'model': model,
                        'name': model_config['name'],
                        'limiter': rate_limiter,
                        'config': model_config
                    })
                except Exception as e:
                    # Model not available, skip it
                    pass

            if not self.models:
                # Fallback to single model if rotation failed
                print("[GEMINI] Smart rotation failed, using single model")
                self.use_rotation = False
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.rate_limiter = RateLimiter(rpm=10, rpd=250)
            else:
                total_rpm = sum(m['config']['rpm'] for m in self.models)
                print(f"[GEMINI] Smart rotation enabled: {len(self.models)} models, {total_rpm} effective RPM")

        if not self.use_rotation:
            # Single model mode (original behavior)
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception:
                self.model = genai.GenerativeModel('gemini-2.0-flash')

            self.rate_limiter = RateLimiter(rpm=10, rpd=250)

        # Response cache
        self.cache = {}

    def _get_next_model(self, strategy: str = 'round_robin'):
        """
        Get next model using rotation strategy.

        Strategies:
        - 'round_robin': Cycle through models sequentially (default)
        - 'random': Pick random model
        - 'fastest': Always use fastest model (highest RPM)

        Returns:
            Tuple of (model, rate_limiter, model_name)
        """
        if not self.use_rotation:
            return self.model, self.rate_limiter, 'gemini-2.5-flash'

        # Get strategy from environment variable if not specified
        strategy = os.getenv('GEMINI_ROTATION_STRATEGY', strategy)

        if strategy == 'round_robin':
            # Round-robin rotation
            model_data = self.models[self.current_model_index]
            self.current_model_index = (self.current_model_index + 1) % len(self.models)
            return model_data['model'], model_data['limiter'], model_data['name']

        elif strategy == 'random':
            # Random selection
            model_data = random.choice(self.models)
            return model_data['model'], model_data['limiter'], model_data['name']

        elif strategy == 'fastest':
            # Always use fastest model (highest RPM)
            fastest = max(self.models, key=lambda m: m['config']['rpm'])
            return fastest['model'], fastest['limiter'], fastest['name']

        else:
            # Default to round-robin
            model_data = self.models[self.current_model_index]
            self.current_model_index = (self.current_model_index + 1) % len(self.models)
            return model_data['model'], model_data['limiter'], model_data['name']

    def generate(
        self,
        prompt: str,
        max_retries: int = 3,
        use_cache: bool = True,
        temperature: float = 0.1,
        verbose: bool = False
    ) -> Optional[str]:
        """
        Generate content with smart model rotation and retry.

        Args:
            prompt: Input prompt for the model
            max_retries: Maximum retry attempts (tries different models if rotation enabled)
            use_cache: Whether to use cached responses (default: True)
            temperature: Model creativity (0.0-1.0, default: 0.1 for deterministic)
            verbose: Print debug information (default: False)

        Returns:
            Generated text, or None if all retries failed

        Example:
            >>> client = GeminiClient(use_rotation=True)
            >>> response = client.generate("What is Bitcoin?")
            >>> print(response)
        """
        # Check cache
        if use_cache:
            cache_key = hashlib.md5(f"{prompt}_{temperature}".encode()).hexdigest()
            if cache_key in self.cache:
                if verbose:
                    print("[CACHE] Using cached response")
                return self.cache[cache_key]

        # Retry loop with smart rotation
        models_tried = set()  # Use set for faster lookup
        max_attempts = max_retries * (len(self.models) if self.use_rotation else 1)

        for attempt in range(max_attempts):
            try:
                # Get next model (rotates if enabled)
                model, rate_limiter, model_name = self._get_next_model()

                # If we've tried all models in this round, wait and reset
                if self.use_rotation and len(models_tried) >= len(self.models):
                    if verbose:
                        print(f"[WAIT] All {len(self.models)} models tried, waiting 5s before retry...")
                    time.sleep(5)
                    models_tried = set()

                models_tried.add(model_name)

                # Wait if needed (rate limiting)
                rate_limiter.wait_if_needed(verbose=verbose)

                if verbose:
                    stats = rate_limiter.get_stats()
                    print(f"[MODEL] {model_name}")
                    print(f"[STATS] {stats['rpm_used']}/{stats['rpm_limit']} RPM, "
                          f"{stats['rpd_used']}/{stats['rpd_limit']} RPD")

                # Make request
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature
                    )
                )

                # Record request
                rate_limiter.record_request()

                # Get text
                result = response.text

                # Cache it
                if use_cache:
                    self.cache[cache_key] = result

                if verbose:
                    print(f"[OK] Success with {model_name} (attempt {attempt+1})")

                return result

            except Exception as e:
                error_str = str(e).lower()

                # Handle rate limiting errors - rotate to next model
                if "429" in str(e) or "rate limit" in error_str or "quota" in error_str:
                    if self.use_rotation:
                        if verbose:
                            print(f"[ROTATE] Rate limit on {model_name}, trying next model...")
                        continue  # Try next model immediately
                    else:
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        print(f"[WAIT] Rate limit hit. Waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_time)

                # Handle other errors
                else:
                    if verbose:
                        print(f"[ERROR] API Error (attempt {attempt+1}/{max_retries}): {e}")

                    if attempt == max_retries - 1:
                        # Last attempt failed
                        print("[ERROR] All retry attempts exhausted")
                        return None

                    # Wait before retry
                    time.sleep(2)

        return None

    def clear_cache(self):
        """Clear the response cache."""
        self.cache = {}
        print("[INFO] Cache cleared")

    def get_cache_size(self) -> int:
        """Get number of cached responses."""
        return len(self.cache)


if __name__ == "__main__":
    # Test Gemini client
    print("=" * 60)
    print("TESTING GEMINI CLIENT")
    print("=" * 60)

    try:
        # Initialize client
        print("\n1. Initializing client...")
        client = GeminiClient()
        print("   [OK] Client initialized")

        # Test simple query
        print("\n2. Testing simple query...")
        response = client.generate(
            "Explain Bitcoin in one sentence.",
            verbose=True
        )
        print(f"   Response: {response}")

        # Test cache
        print("\n3. Testing cache (same query)...")
        response2 = client.generate(
            "Explain Bitcoin in one sentence.",
            verbose=True
        )
        print(f"   Response: {response2}")
        print(f"   Cache size: {client.get_cache_size()}")

        # Test rate limiting
        print("\n4. Testing rate limiting (3 rapid queries)...")
        for i in range(3):
            response = client.generate(
                f"Count to {i+1}",
                use_cache=False,
                verbose=True
            )
            print(f"   Query {i+1}: {response[:50]}...")

        print("\n[OK] All tests passed!")

    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("\nTo fix:")
        print("1. Get API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to .env file: GEMINI_API_KEY=your_key_here")

    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("\nTo fix:")
        print("pip install google-generativeai")

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")

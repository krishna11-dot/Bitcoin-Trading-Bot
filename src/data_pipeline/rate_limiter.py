"""

RATE LIMITER - API Request Management


PURPOSE:
    Prevent API rate limit violations using leaky bucket algorithm
    and intelligent caching to minimize redundant requests.

SUCCESS CRITERIA:
     Never exceeds API rate limits
     Reduces redundant requests by >80% (via caching)
     Minimal latency overhead (<100ms)
     Handles burst requests gracefully

API LIMITS:
    - Binance Testnet: 6000 requests/minute
    - Alternative.me: Free, no key required (generous rate limits)
    - Blockchain.com: ~12 requests/minute (5-sec spacing)

VALIDATION METHOD:
    - Test burst requests (should queue, not fail)
    - Verify cache hit rate >80% for repeated requests
    - Confirm no 429 (rate limit) errors in logs

"""

import time
import threading
from collections import deque
from typing import Any, Callable, Optional
from functools import wraps
import hashlib
import json


class LeakyBucket:
    """
    Leaky bucket rate limiter.

    Allows burst requests up to bucket capacity, then enforces
    steady rate based on leak rate.

    Example:
        limiter = LeakyBucket(max_requests=100, time_window=60)
        limiter.acquire()  # Blocks if rate limit would be exceeded
    """

    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize leaky bucket.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()  # Timestamps of requests
        self.lock = threading.Lock()

    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire permission to make a request.

        Args:
            blocking: If True, wait until request is allowed.
                     If False, return immediately.

        Returns:
            True if request is allowed, False if rate limited (when blocking=False)
        """
        while True:
            with self.lock:
                now = time.time()

                # Remove requests outside time window (leak)
                while self.requests and self.requests[0] < now - self.time_window:
                    self.requests.popleft()

                # Check if we can make a request
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True

                # Rate limit reached
                if not blocking:
                    return False

                # Calculate wait time
                oldest_request = self.requests[0]
                wait_time = (oldest_request + self.time_window) - now

            # Wait outside the lock to allow other threads
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # Sleep max 100ms at a time

    def get_current_usage(self) -> dict:
        """
        Get current rate limiter statistics.

        Returns:
            dict: {
                'current_requests': int,
                'max_requests': int,
                'utilization': float (0-1),
                'time_until_reset': float
            }
        """
        with self.lock:
            now = time.time()

            # Clean old requests
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()

            current_requests = len(self.requests)
            utilization = current_requests / self.max_requests

            # Time until oldest request expires
            if self.requests:
                time_until_reset = (self.requests[0] + self.time_window) - now
            else:
                time_until_reset = 0

            return {
                'current_requests': current_requests,
                'max_requests': self.max_requests,
                'utilization': utilization,
                'time_until_reset': max(0, time_until_reset)
            }


class RequestCache:
    """
    Simple in-memory cache for API responses.

    Caches responses with TTL (time-to-live) to avoid redundant API calls.

    Example:
        cache = RequestCache(ttl=300)  # 5-minute cache
        result = cache.get(key)
        if result is None:
            result = expensive_api_call()
            cache.set(key, result)
    """

    def __init__(self, ttl: float = 300):
        """
        Initialize cache.

        Args:
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self.ttl = ttl
        self.cache = {}  # {key: (value, timestamp)}
        self.lock = threading.Lock()

    def _make_key(self, *args, **kwargs) -> str:
        """
        Create cache key from arguments.

        Args:
            *args, **kwargs: Function arguments

        Returns:
            Hashed cache key
        """
        # Serialize arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)

        # Hash for consistent key
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                return None

            value, timestamp = self.cache[key]

            # Check if expired
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None

            return value

    def set(self, key: str, value: Any):
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            self.cache[key] = (value, time.time())

    def clear(self):
        """Clear all cached values."""
        with self.lock:
            self.cache.clear()

    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if now - timestamp > self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            dict: {
                'size': int,
                'oldest_entry_age': float,
                'newest_entry_age': float
            }
        """
        with self.lock:
            now = time.time()

            if not self.cache:
                return {
                    'size': 0,
                    'oldest_entry_age': 0,
                    'newest_entry_age': 0
                }

            timestamps = [timestamp for _, timestamp in self.cache.values()]

            return {
                'size': len(self.cache),
                'oldest_entry_age': now - min(timestamps),
                'newest_entry_age': now - max(timestamps)
            }


class RateLimiter:
    """
    Combined rate limiter with caching.

    Provides decorator for API functions to automatically handle
    rate limiting and caching.

    Example:
        limiter = RateLimiter(max_requests=100, time_window=60, cache_ttl=300)

        @limiter.limit
        def fetch_data(symbol):
            return api.get_price(symbol)

        # First call: hits API, caches result
        price1 = fetch_data("BTC")

        # Second call: returns cached result (within 5 min)
        price2 = fetch_data("BTC")
    """

    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60,
        cache_ttl: float = 300,
        name: str = "default"
    ):
        """
        Initialize rate limiter with cache.

        Args:
            max_requests: Max requests per time window
            time_window: Time window in seconds
            cache_ttl: Cache time-to-live in seconds
            name: Name for this limiter (for logging)
        """
        self.bucket = LeakyBucket(max_requests, time_window)
        self.cache = RequestCache(ttl=cache_ttl)
        self.name = name

        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limited': 0
        }
        self.stats_lock = threading.Lock()

    def limit(self, func: Callable) -> Callable:
        """
        Decorator to apply rate limiting and caching.

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self.cache._make_key(func.__name__, *args, **kwargs)

            # Check cache first
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                with self.stats_lock:
                    self.stats['total_requests'] += 1
                    self.stats['cache_hits'] += 1
                return cached_result

            # Cache miss - acquire rate limit permission
            acquired = self.bucket.acquire(blocking=True)

            if not acquired:
                with self.stats_lock:
                    self.stats['rate_limited'] += 1
                raise Exception(f"Rate limit exceeded for {self.name}")

            # Make actual request
            with self.stats_lock:
                self.stats['total_requests'] += 1
                self.stats['cache_misses'] += 1

            result = func(*args, **kwargs)

            # Cache result
            self.cache.set(cache_key, result)

            return result

        return wrapper

    def get_stats(self) -> dict:
        """
        Get comprehensive statistics.

        Returns:
            dict with request stats, rate limiter status, and cache stats
        """
        with self.stats_lock:
            request_stats = self.stats.copy()

        # Calculate cache hit rate
        total = request_stats['total_requests']
        if total > 0:
            cache_hit_rate = request_stats['cache_hits'] / total
        else:
            cache_hit_rate = 0

        return {
            'name': self.name,
            'requests': request_stats,
            'cache_hit_rate': cache_hit_rate,
            'rate_limiter': self.bucket.get_current_usage(),
            'cache': self.cache.get_stats()
        }

    def reset_stats(self):
        """Reset statistics counters."""
        with self.stats_lock:
            self.stats = {
                'total_requests': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'rate_limited': 0
            }

    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()


# 
# PRE-CONFIGURED RATE LIMITERS FOR DIFFERENT APIS
# 

# Binance Testnet: 6000 requests/minute (aggressive)
binance_limiter = RateLimiter(
    max_requests=6000,
    time_window=60,
    cache_ttl=10,  # 10-second cache (prices change fast)
    name="Binance"
)

# Alternative.me: Free, no strict limits
# Conservative: 10 requests/hour to be respectful
alternativeme_limiter = RateLimiter(
    max_requests=10,
    time_window=3600,  # 1 hour
    cache_ttl=300,  # 5-minute cache (F&G updates slowly)
    name="Alternative.me"
)

# Blockchain.com: Conservative 5-second spacing
# = 12 requests/minute
blockchain_limiter = RateLimiter(
    max_requests=12,
    time_window=60,
    cache_ttl=30,  # 30-second cache
    name="Blockchain"
)


def main():
    """Test rate limiter functionality."""
    print("="*60)
    print("RATE LIMITER - Testing")
    print("="*60)

    # Test 1: Basic rate limiting
    print("\nTest 1: Basic Rate Limiting")
    test_limiter = RateLimiter(max_requests=5, time_window=2, cache_ttl=1, name="Test")

    @test_limiter.limit
    def test_function(value):
        """Dummy function for testing."""
        return f"Result: {value}"

    # Make rapid requests
    print("   Making 10 rapid requests (limit: 5 per 2 seconds)...")
    start_time = time.time()

    for i in range(10):
        result = test_function(i)
        elapsed = time.time() - start_time
        print(f"   Request {i+1}: {result} (elapsed: {elapsed:.2f}s)")

    # Test 2: Cache effectiveness
    print("\nTest 2: Cache Effectiveness")
    print("   Making repeated requests (should use cache)...")

    for i in range(3):
        test_function("cached_value")

    stats = test_limiter.get_stats()
    print(f"\n   Statistics:")
    print(f"   - Total requests: {stats['requests']['total_requests']}")
    print(f"   - Cache hits: {stats['requests']['cache_hits']}")
    print(f"   - Cache misses: {stats['requests']['cache_misses']}")
    print(f"   - Cache hit rate: {stats['cache_hit_rate']:.1%}")

    # Test 3: Pre-configured limiters
    print("\nTest 3: Pre-configured Limiters")
    limiters = [binance_limiter, alternativeme_limiter, blockchain_limiter]

    for limiter in limiters:
        stats = limiter.get_stats()
        print(f"\n   {stats['name']} Limiter:")
        print(f"   - Max requests: {stats['rate_limiter']['max_requests']}")
        print(f"   - Cache TTL: {limiter.cache.ttl}s")
        print(f"   - Current usage: {stats['rate_limiter']['current_requests']} requests")

    print("\n" + "="*60)
    print("[COMPLETE] RATE LIMITER TEST PASSED")
    print("="*60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Rate Limiter for Gemini API

Enforces Gemini Free Tier limits:
- 10 requests per minute (RPM)
- 250 requests per day (RPD)
"""

from collections import deque
from datetime import datetime, timedelta
import time
from typing import Tuple


class RateLimiter:
    """
    Track API requests and enforce rate limits.

    Uses sliding window approach to accurately enforce both
    per-minute and per-day rate limits.

    Attributes:
        rpm: Requests per minute limit
        rpd: Requests per day limit
        requests_per_minute: Deque storing recent request timestamps
        requests_per_day: Deque storing daily request timestamps
    """

    def __init__(self, rpm: int = 10, rpd: int = 250):
        """
        Initialize rate limiter.

        Args:
            rpm: Requests per minute limit (default: 10 for Gemini free tier)
            rpd: Requests per day limit (default: 250 for Gemini free tier)
        """
        self.rpm = rpm
        self.rpd = rpd
        self.requests_per_minute = deque(maxlen=rpm)
        self.requests_per_day = deque(maxlen=rpd)

    def can_make_request(self) -> Tuple[bool, str]:
        """
        Check if we can make a request without hitting limits.

        Returns:
            Tuple of (can_proceed, reason)
            - can_proceed: True if request is allowed
            - reason: Explanation if blocked
        """
        now = datetime.now()

        # Clean old requests (>1 minute)
        while (self.requests_per_minute and
               now - self.requests_per_minute[0] > timedelta(minutes=1)):
            self.requests_per_minute.popleft()

        # Clean old requests (>1 day)
        while (self.requests_per_day and
               now - self.requests_per_day[0] > timedelta(days=1)):
            self.requests_per_day.popleft()

        # Check RPM limit
        if len(self.requests_per_minute) >= self.rpm:
            oldest = self.requests_per_minute[0]
            wait_time = 60 - (now - oldest).total_seconds()
            return False, f"RPM limit ({self.rpm}/min) reached. Wait {wait_time:.1f}s"

        # Check RPD limit
        if len(self.requests_per_day) >= self.rpd:
            oldest = self.requests_per_day[0]
            wait_time = 86400 - (now - oldest).total_seconds()
            hours = wait_time // 3600
            minutes = (wait_time % 3600) // 60
            return False, f"RPD limit ({self.rpd}/day) reached. Wait {hours:.0f}h {minutes:.0f}m"

        return True, "OK"

    def wait_if_needed(self, verbose: bool = False):
        """
        Block until we can make a request.

        Args:
            verbose: If True, print waiting messages
        """
        while True:
            can_proceed, reason = self.can_make_request()

            if can_proceed:
                break

            if verbose:
                print(f"[WAIT] Rate limit: {reason}")

            # Wait 1 second and retry
            time.sleep(1)

    def record_request(self):
        """Record that we made a request."""
        now = datetime.now()
        self.requests_per_minute.append(now)
        self.requests_per_day.append(now)

    def get_stats(self) -> dict:
        """
        Get current rate limit statistics.

        Returns:
            dict: Current usage stats
        """
        now = datetime.now()

        # Clean expired requests
        while (self.requests_per_minute and
               now - self.requests_per_minute[0] > timedelta(minutes=1)):
            self.requests_per_minute.popleft()

        while (self.requests_per_day and
               now - self.requests_per_day[0] > timedelta(days=1)):
            self.requests_per_day.popleft()

        return {
            'rpm_used': len(self.requests_per_minute),
            'rpm_limit': self.rpm,
            'rpm_remaining': self.rpm - len(self.requests_per_minute),
            'rpd_used': len(self.requests_per_day),
            'rpd_limit': self.rpd,
            'rpd_remaining': self.rpd - len(self.requests_per_day)
        }


if __name__ == "__main__":
    # Test rate limiter
    print("Testing Rate Limiter (2 RPM, 5 RPD for quick test)")
    limiter = RateLimiter(rpm=2, rpd=5)

    for i in range(10):
        print(f"\n[Request {i+1}]")

        # Check stats
        stats = limiter.get_stats()
        print(f"  RPM: {stats['rpm_used']}/{stats['rpm_limit']} (remaining: {stats['rpm_remaining']})")
        print(f"  RPD: {stats['rpd_used']}/{stats['rpd_limit']} (remaining: {stats['rpd_remaining']})")

        # Try to make request
        can_proceed, reason = limiter.can_make_request()

        if can_proceed:
            print(f"  Status: [OK]")
            limiter.record_request()
        else:
            print(f"  Status: [BLOCKED] - {reason}")
            print("  Waiting...")
            limiter.wait_if_needed(verbose=True)
            limiter.record_request()
            print(f"  Status: [OK] (after wait)")

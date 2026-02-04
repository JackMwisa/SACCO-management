"""
Simple in-memory rate limiter for Django views.
For production with multiple servers, use django-ratelimit with Redis backend.
"""
import time
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self):
        self._cache = {}

    def _cleanup_old_entries(self, key, window_seconds):
        """Remove entries older than the window."""
        if key in self._cache:
            current_time = time.time()
            self._cache[key] = [
                t for t in self._cache[key]
                if current_time - t < window_seconds
            ]

    def is_rate_limited(self, key, max_requests, window_seconds):
        """
        Check if the key has exceeded the rate limit.

        Args:
            key: Unique identifier (e.g., IP address)
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = time.time()

        # Initialize if not exists
        if key not in self._cache:
            self._cache[key] = []

        # Cleanup old entries
        self._cleanup_old_entries(key, window_seconds)

        # Check if over limit
        if len(self._cache[key]) >= max_requests:
            return True

        # Record this request
        self._cache[key].append(current_time)
        return False

    def get_remaining(self, key, max_requests, window_seconds):
        """Get remaining requests allowed."""
        self._cleanup_old_entries(key, window_seconds)
        used = len(self._cache.get(key, []))
        return max(0, max_requests - used)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def ratelimit(max_requests=5, window_seconds=60, key_func=None, block=True):
    """
    Rate limiting decorator for Django views.

    Args:
        max_requests: Maximum requests allowed in the window (default: 5)
        window_seconds: Time window in seconds (default: 60)
        key_func: Function to extract key from request (default: IP address)
        block: If True, block the request; if False, set request.limited = True

    Usage:
        @ratelimit(max_requests=5, window_seconds=60)
        def login_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get the rate limit key (default: IP address)
            if key_func:
                key = key_func(request)
            else:
                # Get IP address, considering proxies
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    key = x_forwarded_for.split(',')[0].strip()
                else:
                    key = request.META.get('REMOTE_ADDR', 'unknown')

            # Check rate limit
            is_limited = _rate_limiter.is_rate_limited(
                key, max_requests, window_seconds
            )

            if is_limited:
                if block:
                    # For API endpoints
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'error': 'Too many requests. Please try again later.',
                            'retry_after': window_seconds
                        }, status=429)

                    # For regular views
                    messages.error(
                        request,
                        f"Too many attempts. Please wait {window_seconds} seconds before trying again."
                    )
                    # Return to the same page or login
                    return render(request, 'user_auths/login.html', status=429)
                else:
                    request.limited = True
            else:
                request.limited = False

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator

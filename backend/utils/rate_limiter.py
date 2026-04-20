from collections import defaultdict
import time

_request_log = defaultdict(list)
RATE_LIMIT = 10       # max requests per window
RATE_WINDOW = 60      # window in seconds


def is_rate_limited(user_id: str) -> bool:
    """Return True if user_id has exceeded RATE_LIMIT requests in RATE_WINDOW seconds."""
    now = time.time()
    window_start = now - RATE_WINDOW
    _request_log[user_id] = [t for t in _request_log[user_id] if t > window_start]
    if len(_request_log[user_id]) >= RATE_LIMIT:
        return True
    _request_log[user_id].append(now)
    return False

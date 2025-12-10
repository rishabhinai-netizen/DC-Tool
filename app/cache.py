# file: app/cache.py
import os
import time
import pickle
import pandas as pd
from typing import Optional
from app.logger import log_usage, log_error

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(ticker: str, period: str, auto_adjust: bool) -> str:
    safe = ticker.replace("/", "_").replace(" ", "_")
    adj = "adj" if auto_adjust else "raw"
    fname = f"{safe}_{period}_{adj}.pkl"
    return os.path.join(CACHE_DIR, fname)

def set_cache(ticker: str, period: str, df: pd.DataFrame, auto_adjust: bool = True) -> None:
    """Write dataframe to disk cache (overwrite)."""
    try:
        path = _cache_path(ticker, period, auto_adjust)
        with open(path, "wb") as f:
            pickle.dump({"ts": time.time(), "df": df}, f)
        log_usage(f"cache_set:{ticker}:{period}")
    except Exception as e:
        log_error(e, {"ticker": ticker, "action": "set_cache"})

def get_cached(ticker: str, period: str, auto_adjust: bool = True, ttl_seconds: int = 6*3600) -> Optional[pd.DataFrame]:
    """Return cached dataframe if exists and not expired, else None."""
    try:
        path = _cache_path(ticker, period, auto_adjust)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            payload = pickle.load(f)
        ts = payload.get("ts", 0)
        if (time.time() - ts) > ttl_seconds:
            # expired
            return None
        df = payload.get("df")
        if isinstance(df, pd.DataFrame):
            log_usage(f"cache_hit:{ticker}:{period}")
            return df
        return None
    except Exception as e:
        log_error(e, {"ticker": ticker, "action": "get_cached"})
        return None

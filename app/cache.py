# file: app/cache.py
import os
import pickle
import time
from datetime import datetime, timedelta
from app.logger import log_error

CACHE_DIR = "./data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(ticker, period, auto_adjust):
    safe_ticker = ticker.replace("=", "_").replace(".NS", "_NS")
    return os.path.join(CACHE_DIR, f"{safe_ticker}_{period}_{auto_adjust}.pkl")

def save_to_cache(ticker, df, period="2y", auto_adjust=True):
    """Saves dataframe to disk cache."""
    try:
        path = get_cache_path(ticker, period, auto_adjust)
        with open(path, 'wb') as f:
            pickle.dump(df, f)
    except Exception as e:
        log_error(e, f"Failed to save cache for {ticker}")

def load_from_cache(ticker, period="2y", auto_adjust=True, ttl_minutes=60):
    """Loads dataframe from disk if exists and not expired."""
    try:
        path = get_cache_path(ticker, period, auto_adjust)
        if not os.path.exists(path):
            return None
        
        # Check Expiry
        mtime = os.path.getmtime(path)
        cache_time = datetime.fromtimestamp(mtime)
        if datetime.now() - cache_time > timedelta(minutes=ttl_minutes):
            return None # Expired
        
        with open(path, 'rb') as f:
            df = pickle.load(f)
        return df
    except Exception as e:
        log_error(e, f"Failed to load cache for {ticker}")
        return None

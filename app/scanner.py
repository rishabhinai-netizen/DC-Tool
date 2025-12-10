# file: app/scanner.py
import yfinance as yf
import pandas as pd
import time
import os
import json
import uuid
import concurrent.futures
from app.indicators import add_indicators
from app.cache import load_from_cache, save_to_cache
from app.logger import log_error

JOBS_DIR = "./data/jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

def fetch_data_with_retry(ticker, period="2y", retries=3):
    """Fetch with exponential backoff and cache check."""
    # 1. Check Cache
    df = load_from_cache(ticker, period)
    if df is not None:
        return df
        
    # 2. Network Fetch
    delay = 1
    for i in range(retries):
        try:
            # yfinance download
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not df.empty:
                save_to_cache(ticker, df, period)
                return df
        except Exception as e:
            time.sleep(delay)
            delay *= 2
    return None

def scan_worker(job_id, ticker_list, use_trend, use_rsi, min_vol):
    """
    Worker function to process the scan.
    """
    results_buy = []
    results_sell = []
    total = len(ticker_list)
    processed = 0
    
    for ticker in ticker_list:
        try:
            df = fetch_data_with_retry(ticker)
            if df is None or len(df) < 50:
                processed += 1
                continue
            
            df = add_indicators(df)
            today = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Volume Filter
            if min_vol > 0 and today.get('Vol_30', 0) < min_vol:
                processed += 1
                continue

            # Logic
            display_name = ticker.replace('.NS', '').replace('=F', '')
            
            # Buy Logic
            if prev['Close'] < prev['Middle'] and today['Close'] > today['Middle']:
                valid = True
                if use_trend and today['Close'] < today['SMA_200']: valid = False
                if use_rsi and today['RSI'] > 70: valid = False
                
                if valid:
                    results_buy.append({
                        "Symbol": display_name,
                        "Price": round(today['Close'], 2),
                        "RSI": round(today['RSI'], 1),
                        "Volume": int(today['Volume']) if 'Volume' in today else 0,
                        "Trend": "Up" if today['Close'] > today['SMA_200'] else "Down"
                    })
            
            # Sell Logic (Long Only exits mostly, but tracking signal)
            elif prev['Close'] > prev['Middle'] and today['Close'] < today['Middle']:
                results_sell.append({
                    "Symbol": display_name,
                    "Price": round(today['Close'], 2),
                    "Date": today.name.strftime('%Y-%m-%d')
                })
        
        except Exception as e:
            log_error(e, f"Scanner error {ticker}")
        
        processed += 1
        # Update Job Progress
        if processed % 10 == 0:
            update_job_status(job_id, "running", processed / total)
            
    # Save Final Result
    final_res = {"buys": results_buy, "sells": results_sell}
    with open(os.path.join(JOBS_DIR, f"{job_id}_result.pkl"), 'wb') as f:
        import pickle
        pickle.dump(final_res, f)
        
    update_job_status(job_id, "completed", 1.0)

def update_job_status(job_id, status, progress):
    meta = {"status": status, "progress": progress, "updated": str(time.time())}
    with open(os.path.join(JOBS_DIR, f"{job_id}.json"), 'w') as f:
        json.dump(meta, f)

def submit_scan_job(ticker_list, use_trend, use_rsi, min_vol):
    job_id = str(uuid.uuid4())
    update_job_status(job_id, "queued", 0.0)
    
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(scan_worker, job_id, ticker_list, use_trend, use_rsi, min_vol)
    return job_id

def get_job_status(job_id):
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def get_job_result(job_id):
    path = os.path.join(JOBS_DIR, f"{job_id}_result.pkl")
    if os.path.exists(path):
        import pickle
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

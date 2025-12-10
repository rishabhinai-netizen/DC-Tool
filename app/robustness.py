# file: app/robustness.py
import pandas as pd
import numpy as np
from app.indicators import add_indicators
from app.backtest import run_trade_backtest
from app.logger import log_error

def check_parameter_stability(df_raw, windows=[15, 20, 25]):
    """
    Runs the strategy across different Donchian windows.
    Returns: DataFrame of metrics per parameter set.
    """
    results = []
    try:
        for w in windows:
            # We must recalculate indicators for each window
            temp_df = df_raw.copy()
            # Custom calc for efficiency or modify add_indicators to accept params
            # Here we manually adjust just for robustness check
            temp_df['High_X'] = temp_df['High'].rolling(w).max()
            temp_df['Low_X'] = temp_df['Low'].rolling(w).min()
            temp_df['Middle'] = (temp_df['High_X'] + temp_df['Low_X']) / 2
            
            # Simple Signal check
            _, metrics = run_trade_backtest(temp_df)
            metrics['window'] = w
            results.append(metrics)
            
        return pd.DataFrame(results)
    except Exception as e:
        log_error(e, "Stability Check Failed")
        return pd.DataFrame()

def bootstrap_simulation(trades_df, iterations=500):
    """
    Resamples trade returns with replacement to generate a distribution of Final Equity.
    """
    if trades_df.empty:
        return {}
    
    returns = trades_df['pnl_pct'].values
    final_equities = []
    
    try:
        n_trades = len(returns)
        for _ in range(iterations):
            sample = np.random.choice(returns, size=n_trades, replace=True)
            equity = np.prod(1 + sample)
            final_equities.append(equity)
        
        final_equities = np.array(final_equities)
        
        stats = {
            "mean_equity": np.mean(final_equities),
            "p5": np.percentile(final_equities, 5),
            "p95": np.percentile(final_equities, 95),
            "std_dev": np.std(final_equities)
        }
        return stats, final_equities
    except Exception as e:
        log_error(e, "Bootstrap Failed")
        return {}, []

def calculate_robustness_score(metrics, stability_df, vol_check):
    """
    Heuristic Score (0-100).
    """
    score = 0
    
    # 1. Base Performance (Max 40)
    ret = metrics.get('total_return', 0)
    score += min(max(ret, 0), 40) # Cap at 40
    
    # 2. Stability (Max 20)
    if not stability_df.empty:
        std_ret = stability_df['total_return'].std()
        if std_ret < 5: score += 20
        elif std_ret < 15: score += 10
        else: score += 0
        
    # 3. Win Rate Sanity (Max 20)
    wr = metrics.get('win_rate', 0)
    if 30 < wr < 70: score += 20 # Trend following usually has lower win rate, but too low is bad
    elif wr > 70: score += 15 # Suspiciously high?
    else: score += 5
    
    # 4. Volume/Liquidity (Max 20)
    if vol_check: score += 20
    
    return min(score, 100)

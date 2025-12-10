# file: app/indicators.py
import pandas as pd
import numpy as np

def calculate_rsi_wilder(series, period=14):
    """
    Calculates Wilder's RSI (Smooth Moving Average of Gains/Losses).
    """
    delta = series.diff()
    
    # separate gains and losses
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # First avg is simple mean
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Subsequent avgs are smoothed: (Previous Avg * (n-1) + Current) / n
    # We use pandas ewm with alpha=1/period to approximate Wilder's smoothing
    # Note: ewm adjust=False corresponds to Wilder's method essentially.
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_indicators(df, use_pandas_ta=False):
    """
    Adds Donchian (20), SMA (200), and RSI (14) to the dataframe.
    """
    try:
        # Configuration (could be parameterized)
        donchian_period = 20
        sma_period = 200
        rsi_period = 14

        if use_pandas_ta:
            import pandas_ta as ta
            df.ta.donchian(lower_length=donchian_period, upper_length=donchian_period, append=True)
            # Normalize names if using pandas_ta
            # pandas_ta creates DCL_20_20, DCM_20_20, DCU_20_20
            df['High_20'] = df[f'DCU_{donchian_period}_{donchian_period}']
            df['Low_20'] = df[f'DCL_{donchian_period}_{donchian_period}']
            df['Middle'] = df[f'DCM_{donchian_period}_{donchian_period}']
            df['SMA_200'] = ta.sma(df['Close'], length=sma_period)
            df['RSI'] = ta.rsi(df['Close'], length=rsi_period)
        else:
            # Custom Vectorized Implementation
            df['High_20'] = df['High'].rolling(donchian_period).max()
            df['Low_20'] = df['Low'].rolling(donchian_period).min()
            df['Middle'] = (df['High_20'] + df['Low_20']) / 2
            df['SMA_200'] = df['Close'].rolling(sma_period).mean()
            df['RSI'] = calculate_rsi_wilder(df['Close'], period=rsi_period)
        
        # Volume Average for filtering
        df['Vol_30'] = df['Volume'].rolling(30).mean()

        return df
    except Exception as e:
        # In a real app, circular import might prevent logger usage here directly if not careful,
        # but broadly safe in this structure.
        print(f"Error calculating indicators: {e}")
        return df

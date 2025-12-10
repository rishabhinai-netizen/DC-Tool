# file: app/explain.py

def explain_signal(symbol, df_row, prev_row):
    """
    Generates plain-language explanation for the signal.
    """
    reasons = []
    
    # 1. Price Action
    close = df_row['Close']
    mid = df_row['Middle']
    reasons.append(f"The closing price of **{close:.2f}** crossed above the Donchian Middle Band (**{mid:.2f}**).")
    
    # 2. Trend Context
    sma = df_row['SMA_200']
    if close > sma:
        reasons.append(f"The stock is in a long-term **Uptrend** (Price > 200 SMA at {sma:.2f}).")
    else:
        reasons.append(f"Note: The stock is below its 200 SMA ({sma:.2f}), indicating a counter-trend trade.")
        
    # 3. Momentum
    rsi = df_row['RSI']
    if rsi < 30:
        reasons.append(f"RSI is {rsi:.1f}, indicating oversold conditions (potential bounce).")
    elif rsi > 70:
        reasons.append(f"RSI is {rsi:.1f}, approaching overbought territory.")
    else:
        reasons.append(f"Momentum is neutral (RSI: {rsi:.1f}).")
        
    # 4. Volume
    vol = df_row.get('Volume', 0)
    avg_vol = df_row.get('Vol_30', 1)
    if vol > avg_vol * 1.5:
        reasons.append("Volume is significantly higher than average, confirming the breakout strength.")
        
    full_text = " ".join(reasons)
    return full_text

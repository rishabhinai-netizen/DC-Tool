# file: app/main.py
import streamlit as st
import pandas as pd
import time
import os
import json

# Import Modules
from app.scanner import submit_scan_job, get_job_status, get_job_result, fetch_data_with_retry
from app.indicators import add_indicators
from app.backtest import run_trade_backtest
from app.robustness import check_parameter_stability, bootstrap_simulation, calculate_robustness_score
from app.ui import render_interactive_table, plot_stock_chart
from app.explain import explain_signal
from app.alerts import save_alert, send_email_digest
from app.paper_trade import get_portfolio, execute_trade
from app.logger import log_error, log_usage

# --- CONFIG & ASSETS ---
st.set_page_config(page_title="DC - Pro Scanner", layout="wide", initial_sidebar_state="expanded")

NSE_500_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS',
    'AXISBANK.NS', 'HINDUNILVR.NS', 'TATAMOTORS.NS', 'BAJFINANCE.NS', 'MARUTI.NS'
    # ... In a real deployment, load the full list from a file or keep the original list.
    # Truncated here for brevity in the code block, but you should paste your full list back.
]

# Ensure data dirs
for d in ['./data/jobs', './data/cache', './data/logs', './data/digest']:
    os.makedirs(d, exist_ok=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Strategy Params")
    donchian_win = st.slider("Donchian Window", 10, 50, 20)
    sma_len = st.number_input("SMA Trend Filter", value=200)
    rsi_len = st.number_input("RSI Length", value=14)
    min_vol = st.number_input("Min Volume (30D Avg)", value=0)
    
    st.divider()
    st.subheader("Alerts & Email")
    smtp_user = st.text_input("SMTP Email")
    smtp_pass = st.text_input("SMTP Password", type="password")
    
    st.divider()
    dev_mode = st.toggle("Developer Mode")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Scanner", "🔍 Deep Dive", "📊 Backtest Lab", "💼 Paper Trade", "🛠️ Dev"])

# --- TAB 1: SCANNER ---
with tab1:
    st.header("Market Scanner")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("RUN SCAN", type="primary"):
            job_id = submit_scan_job(NSE_500_LIST, True, True, min_vol)
            st.session_state['scan_job_id'] = job_id
            st.rerun()

    with col2:
        if 'scan_job_id' in st.session_state:
            jid = st.session_state['scan_job_id']
            status = get_job_status(jid)
            
            if status:
                st.progress(status.get('progress', 0.0))
                st.caption(f"Status: {status.get('status')}")
                
                if status.get('status') == 'completed':
                    res = get_job_result(jid)
                    st.session_state['scan_results'] = res
                    del st.session_state['scan_job_id'] # Clear job
                    st.rerun()
            else:
                st.spinner("Waiting for worker...")
                time.sleep(2)
                st.rerun()

    if 'scan_results' in st.session_state:
        res = st.session_state['scan_results']
        st.subheader("Buy Signals")
        df_buy = pd.DataFrame(res['buys'])
        
        sel_row = render_interactive_table(df_buy, key="buy_grid")
        if sel_row:
            st.session_state['selected_ticker'] = sel_row['Symbol']
            st.success(f"Selected {sel_row['Symbol']} - Go to Deep Dive")
            
        st.subheader("Sell Signals (Long Exit)")
        st.dataframe(pd.DataFrame(res['sells']))

# --- TAB 2: DEEP DIVE ---
with tab2:
    ticker = st.text_input("Symbol", value=st.session_state.get('selected_ticker', 'RELIANCE'))
    if ticker:
        ticker = ticker if ticker.endswith('.NS') else ticker + '.NS'
        df = fetch_data_with_retry(ticker)
        
        if df is not None:
            df = add_indicators(df)
            
            # Layout
            c1, c2 = st.columns([3, 1])
            with c1:
                plot_stock_chart(df, ticker)
            
            with c2:
                # Signal Explanation
                curr = df.iloc[-1]
                prev = df.iloc[-2]
                explanation = explain_signal(ticker, curr, prev)
                st.info(f"💡 **Analysis:**\n{explanation}")
                
                # Robustness Score
                trades, metrics = run_trade_backtest(df)
                stab = check_parameter_stability(df)
                score = calculate_robustness_score(metrics, stab, True)
                st.metric("Robustness Score", f"{score}/100")
                
                # Actions
                if st.button("Add to Watchlist"):
                    save_alert(ticker, curr['Close'], "below") # Default logic
                    st.toast("Added to watchlist")
                    
                if st.button("Paper Buy 100 Qty"):
                    ok, msg = execute_trade("BUY", ticker, curr['Close'], 100)
                    if ok: st.toast(msg)
                    else: st.error(msg)

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("CAGR", f"{metrics.get('cagr')}%")
            m2.metric("Win Rate", f"{metrics.get('win_rate')}%")
            m3.metric("Max DD", f"{metrics.get('max_drawdown')}%")
            m4.metric("Total Trades", metrics.get('trades'))

# --- TAB 3: BACKTEST LAB ---
with tab3:
    st.header("Advanced Backtest")
    
    if 'scan_results' in st.session_state:
        st.write("Full ledger for last scan available.")
        # Logic to aggregate all trades from the scan would go here
        # For now, we show single stock deep backtest
    
    bt_ticker = st.text_input("Backtest Symbol", "TCS")
    if st.button("Run Simulation"):
        df_bt = fetch_data_with_retry(bt_ticker + ".NS")
        if df_bt is not None:
            df_bt = add_indicators(df_bt)
            trades, met = run_trade_backtest(df_bt)
            
            st.dataframe(trades)
            
            # Bootstrap
            stats, sims = bootstrap_simulation(trades)
            if stats:
                st.write("Bootstrap (500 runs) Final Equity Distribution:")
                st.bar_chart(sims[:100]) # simple vis
                st.json(stats)
            
            csv = trades.to_csv(index=False).encode('utf-8')
            st.download_button("Download Trade CSV", csv, "trades.csv", "text/csv")

# --- TAB 4: PAPER TRADE ---
with tab4:
    st.header("Paper Trading Portfolio")
    pf = get_portfolio()
    
    st.metric("Cash Balance", f"₹{pf['cash']:,.2f}")
    
    if pf['positions']:
        st.subheader("Open Positions")
        st.dataframe(pd.DataFrame(pf['positions']))
        
        # Close position UI
        st.divider()
        c_sym = st.selectbox("Select to Close", [p['symbol'] for p in pf['positions']])
        if st.button("Close Position"):
            # Find price
            df_c = fetch_data_with_retry(c_sym)
            curr_p = df_c['Close'].iloc[-1]
            ok, msg = execute_trade("SELL", c_sym, curr_p, 0) # Qty handled in function
            st.rerun()
            
    st.subheader("Trade History")
    st.write(pf['history'])

# --- TAB 5: DEV ---
with tab5:
    if dev_mode:
        st.subheader("Logs")
        if os.path.exists('./data/logs/error.log'):
            with open('./data/logs/error.log', 'r') as f:
                st.text(f.read())
        
        st.subheader("Active Jobs")
        # List files in jobs dir
        jobs = os.listdir('./data/jobs')
        st.write(jobs)
    else:
        st.warning("Enable Developer Mode in Sidebar to view logs.")

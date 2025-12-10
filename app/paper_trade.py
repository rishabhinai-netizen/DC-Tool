# file: app/paper_trade.py
import json
import os
from datetime import datetime
from app.logger import log_error

PORTFOLIO_FILE = "./data/paper_portfolio.json"

def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        # Initialize default
        init_state = {"cash": 100000, "positions": [], "history": []}
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(init_state, f)
        return init_state
    
    with open(PORTFOLIO_FILE, 'r') as f:
        return json.load(f)

def save_portfolio(data):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(data, f)

def execute_trade(action, symbol, price, qty, date=None):
    """
    Simulates Buy/Sell.
    """
    pf = get_portfolio()
    date = date or datetime.now().strftime("%Y-%m-%d")
    
    try:
        cost = price * qty
        
        if action == "BUY":
            if pf['cash'] >= cost:
                pf['cash'] -= cost
                pf['positions'].append({"symbol": symbol, "avg_price": price, "qty": qty, "date": date})
                pf['history'].append(f"BOUGHT {qty} {symbol} @ {price} on {date}")
                save_portfolio(pf)
                return True, "Trade Executed"
            else:
                return False, "Insufficient Cash"
                
        elif action == "SELL":
            # Simple FIFO or average logic. Here, simplified: remove matching symbol
            # Real impl would handle partial sells.
            for i, pos in enumerate(pf['positions']):
                if pos['symbol'] == symbol:
                    # Sell all for demo simplicity
                    proceeds = price * pos['qty']
                    pf['cash'] += proceeds
                    pf['positions'].pop(i)
                    pnl = proceeds - (pos['avg_price'] * pos['qty'])
                    pf['history'].append(f"SOLD {pos['qty']} {symbol} @ {price} on {date} (PnL: {pnl:.2f})")
                    save_portfolio(pf)
                    return True, "Trade Executed"
            return False, "Position not found"
            
    except Exception as e:
        log_error(e, "Paper Trade Error")
        return False, str(e)

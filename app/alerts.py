# file: app/alerts.py
import json
import os
import smtplib
from email.mime.text import MIMEText
from app.logger import log_error, log_usage

ALERTS_FILE = "./data/alerts.json"
DIGEST_FILE = "./data/digest/latest.json"

def save_alert(symbol, target_price, condition="above"):
    """Saves a price alert."""
    try:
        alerts = load_alerts()
        alerts.append({"symbol": symbol, "price": target_price, "condition": condition, "active": True})
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f)
        log_usage("Alert Created", f"{symbol} {condition} {target_price}")
        return True
    except Exception as e:
        log_error(e, "Save Alert")
        return False

def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []
    with open(ALERTS_FILE, 'r') as f:
        return json.load(f)

def check_alerts(current_price_map):
    """
    Checks saved alerts against current prices. 
    current_price_map: dict {symbol: price}
    """
    alerts = load_alerts()
    triggered = []
    updated_alerts = []
    
    for alert in alerts:
        if not alert['active']:
            updated_alerts.append(alert)
            continue
            
        sym = alert['symbol']
        if sym in current_price_map:
            price = current_price_map[sym]
            target = alert['price']
            
            hit = False
            if alert['condition'] == 'above' and price > target: hit = True
            elif alert['condition'] == 'below' and price < target: hit = True
            
            if hit:
                triggered.append(f"🚨 ALERT: {sym} is now {price} ({alert['condition']} {target})")
                alert['active'] = False # Disable after trigger
        
        updated_alerts.append(alert)
    
    with open(ALERTS_FILE, 'w') as f:
        json.dump(updated_alerts, f)
        
    return triggered

def send_email_digest(recipient_email, smtp_config, subject, body):
    """
    Sends email via user-provided SMTP.
    smtp_config: {server, port, user, password}
    """
    if not recipient_email or not smtp_config:
        return False, "Missing config"
        
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_config['user']
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['user'], smtp_config['password'])
            server.send_message(msg)
        return True, "Sent"
    except Exception as e:
        log_error(e, "Email Failed")
        return False, str(e)

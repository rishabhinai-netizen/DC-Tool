# file: app/logger.py
import logging
import os
from datetime import datetime

# Ensure log directories exist
LOG_DIR = "./data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    handler = logging.FileHandler(os.path.join(LOG_DIR, log_file))        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times in Streamlit re-runs
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

# Create specific loggers
error_logger = setup_logger('error_logger', 'error.log')
usage_logger = setup_logger('usage_logger', 'usage.log')
consent_logger = setup_logger('consent_logger', 'consent.log')

def log_error(e, context=""):
    """Logs exception with context."""
    error_logger.error(f"{context}: {str(e)}", exc_info=True)

def log_usage(action, details=""):
    """Logs user actions."""
    usage_logger.info(f"Action: {action} | Details: {details}")

def log_consent(user_id, action):
    """Logs legal consent for scraping."""
    consent_logger.info(f"User: {user_id} | Consent: {action} | Timestamp: {datetime.now()}")

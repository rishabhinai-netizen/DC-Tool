# file: app/logger.py
import os
import time
import traceback

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
ERROR_LOG = os.path.join(LOG_DIR, "error.log")
USAGE_LOG = os.path.join(LOG_DIR, "usage.log")
CONSENT_LOG = os.path.join(LOG_DIR, "consent.log")

def log_error(e: Exception, context: dict | None = None) -> None:
    """Append full exception traceback + context to error.log"""
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(f"---\nTIME: {time.asctime()}\n")
            if context:
                f.write(f"CONTEXT: {context}\n")
            f.write("EXCEPTION:\n")
            traceback.print_exc(file=f)
            f.write("\n")
    except Exception:
        # last-resort silence to avoid crashing app
        pass

def log_usage(msg: str) -> None:
    """Append a short usage / event line to usage.log"""
    try:
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.asctime()}\t{msg}\n")
    except Exception:
        pass

def log_consent(txt: str) -> None:
    """Log explicit user consent actions (eg. paywall scraping opt-in)"""
    try:
        with open(CONSENT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.asctime()}\t{txt}\n")
    except Exception:
        pass

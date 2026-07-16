import time   # <-- Bunu ekle

"""
Central Configuration & Structured Logging
Versiyon: v1.1

Amaç: Tüm scriptler için ortak konfigürasyon, logging standardı ve hata yönetimi
(retry mekanizması) sağlamak.

Bu modül, orchestrator.py, execution_engine.py ve monitor_and_alert.py ile
tam uyumlu çalışacak şekilde tasarlanmıştır.
"""

import logging
from pathlib import Path
import logging
from functools import wraps          # ← Bunu ekle (wraps hatası için)
from pathlib import Path

# Proje kökünü bul (src klasörünün bir üstü)
BASE_DIR = Path(__file__).parent.parent

# Artifact ve log klasörleri
ARTIFACTS_DIR = BASE_DIR / "artifacts"
LOGS_DIR = ARTIFACTS_DIR / "logs"

# Klasörleri oluştur
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# === Logging Configuration ===
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str) -> logging.Logger:
    """
    Tüm scriptler için standart logger döndürür.
    Handler'ların tekrar eklenmesini engeller.
    """
    logger = logging.getLogger(name)
    
    # Handler zaten varsa tekrar ekleme
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / "system.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)
    
    return logger

# === Rubric Thresholds ===
RUBRIC_LOW_THRESHOLD = 9.0
RUBRIC_CRITICAL_THRESHOLD = 8.5

# === Context Reset ===
CONTEXT_RESET_TURN_THRESHOLD = 20

# === Execution Engine Settings ===
DEFAULT_MODEL = "grok"
ENABLE_AUTO_CONTEXT_RESET = True
ENABLE_AUTO_LOGGING = True

# === Self-Evolving Settings ===
SELF_EVOLVING_APPLY_MODE = "manual"   # "auto" veya "manual" (varsayılan: manual = approval required)

# === Retry Configuration ===
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1

def retry_on_exception(
    max_retries: int = MAX_RETRIES,
    log_retries: bool = False,
    backoff: str = "fixed",
    base_delay: float = None
):
    if base_delay is None:
        base_delay = RETRY_DELAY_SECONDS

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            attempts = max_retries + 1   # max_retries=0 → sadece 1 deneme

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if log_retries and attempt < attempts - 1:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(f"Retry {attempt + 1}/{attempts} for {func.__name__}: {e}")

                    if attempt < attempts - 1:
                        if backoff == "exponential":
                            delay = base_delay * (2 ** attempt)
                        elif backoff == "linear":
                            delay = base_delay * (attempt + 1)
                        else:
                            delay = base_delay
                        time.sleep(delay)

            from errors import ResilienceError, ErrorCode
            raise ResilienceError(
                message=f"Retry exhausted after {max_retries} attempts",
                error_code=ErrorCode.RETRY_EXHAUSTED,
                details={"max_retries": max_retries, "last_error": str(last_exception)},
                recoverable=True
            )
        return wrapper
    return decorator
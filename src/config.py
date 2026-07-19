"""
Central Configuration & Structured Logging
Versiyon: v1.2

Bu modül, tüm scriptler için ortak konfigürasyon, logging standardı
ve hata yönetimi (retry mekanizması) sağlar.
"""

import logging
import time
from functools import wraps
from pathlib import Path

# === Dizin Tanımları ===
BASE_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
LOGS_DIR = ARTIFACTS_DIR / "logs"

# Log klasörünü oluştur
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# === Logging Yapılandırması ===
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Tüm scriptler için standart logger döndürür.
    Aynı logger'a tekrar handler eklenmesini engeller.
    """
    logger = logging.getLogger(name)

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


# === Rubric Eşik Değerleri ===
RUBRIC_LOW_THRESHOLD = 9.0
RUBRIC_CRITICAL_THRESHOLD = 8.5

# === Context Reset Ayarları ===
CONTEXT_RESET_TURN_THRESHOLD = 20
ENABLE_AUTO_CONTEXT_RESET = True

# === Self-Evolving Ayarları ===
SELF_EVOLVING_APPLY_MODE = "manual"  # "auto" veya "manual"

# === Retry Ayarları ===
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0


def retry_on_exception(
    max_retries: int = MAX_RETRIES,
    log_retries: bool = False,
    backoff: str = "fixed",
    base_delay: float = None,
):
    """
    Fonksiyonları otomatik yeniden deneme (retry) ile saran dekoratör.
    """
    if base_delay is None:
        base_delay = RETRY_DELAY_SECONDS

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            attempts = max_retries + 1

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if log_retries and attempt < attempts - 1:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(
                            f"Retry {attempt + 1}/{attempts} for {func.__name__}: {e}"
                        )

                    if attempt < attempts - 1:
                        if backoff == "exponential":
                            delay = base_delay * (2**attempt)
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
                recoverable=True,
            )

        return wrapper

    return decorator

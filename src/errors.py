"""
Structured Error Handling Model
Bu modül, sistem genelinde anlamlı ve tutarlı hata yönetimi sağlar.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """Merkezi hata kodları"""

    # Genel
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # Resilience
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    TIMEOUT = "TIMEOUT"

    # State
    STATE_READ_ERROR = "STATE_READ_ERROR"
    STATE_WRITE_ERROR = "STATE_WRITE_ERROR"
    STATE_CORRUPTED = "STATE_CORRUPTED"

    # LLM
    LLM_CALL_FAILED = "LLM_CALL_FAILED"
    LLM_TIMEOUT = "LLM_TIMEOUT"

    # Execution
    INITIALIZATION_FAILED = "INITIALIZATION_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class BaseAppError(Exception):
    """
    Tüm uygulama hatalarının temel sınıfı.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Hatanın JSON serileştirilebilir halini döndürür."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        return f"[{self.error_code.value}] {self.message}"


# === Özel Hata Sınıfları ===


class ConfigurationError(BaseAppError):
    """Konfigürasyon ile ilgili hatalar"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            recoverable=False,
        )


class ResilienceError(BaseAppError):
    """Resilience (Circuit Breaker, Retry, Timeout) ile ilgili hatalar"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.RETRY_EXHAUSTED,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            recoverable=recoverable,
        )


class StateError(BaseAppError):
    """State yönetimi ile ilgili hatalar"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.STATE_READ_ERROR,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            recoverable=recoverable,
        )


class LLMError(BaseAppError):
    """LLM Adapter ile ilgili hatalar"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.LLM_CALL_FAILED,
            details=details,
            recoverable=recoverable,
        )


class ExecutionError(BaseAppError):
    """Execution Engine ile ilgili hatalar"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.EXECUTION_FAILED,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            recoverable=recoverable,
        )

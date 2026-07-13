"""
Basit Circuit Breaker Implementasyonu
Resilience için temel koruma katmanı.
"""

import time
from enum import Enum
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Basit Circuit Breaker implementasyonu.

    - CLOSED: Normal çalışma
    - OPEN: Hata eşiği aşıldı, istekler reddediliyor
    - HALF_OPEN: Test amaçlı sınırlı istek izin veriliyor
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit Breaker → HALF_OPEN")
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Fonksiyonu Circuit Breaker koruması altında çağırır."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            from errors import ResilienceError, ErrorCode
            raise ResilienceError(
                message="Circuit Breaker is OPEN. İstek reddedildi.",
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                details={"state": current_state.value},
                recoverable=True
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Başarılı çağrı sonrası durum güncellenir."""
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            logger.info("Circuit Breaker → CLOSED (recovery successful)")
        self._failure_count = 0

    def _on_failure(self):
        """Hatalı çağrı sonrası durum güncellenir."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit Breaker → OPEN (failures: {self._failure_count})")

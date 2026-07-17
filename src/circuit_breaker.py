"""
Gelişmiş Circuit Breaker Implementasyonu
Hata türüne göre farklı eşik, kurtarma süresi ve recovery stratejisi destekler.
"""

import time
from enum import Enum
from typing import Callable, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerConfig:
    """Circuit Breaker için konfigürasyon sınıfı"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception,
        name: str = "default",
        recovery_strategy: str = "normal",  # normal, aggressive, conservative
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        self.recovery_strategy = recovery_strategy


class CircuitBreaker:
    """
    Gelişmiş Circuit Breaker implementasyonu.
    Hata türüne göre farklı konfigürasyon ve recovery stratejisi destekler.
    """

    DEFAULT_CONFIGS: Dict[str, CircuitBreakerConfig] = {
        "default": CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30.0,
            expected_exception=Exception,
            name="default",
            recovery_strategy="normal",
        ),
        "state_error": CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=60.0,
            expected_exception=Exception,
            name="state_error",
            recovery_strategy="conservative",  # State hatalarında daha temkinli
        ),
        "rubric_update": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=20.0,
            expected_exception=Exception,
            name="rubric_update",
            recovery_strategy="normal",
        ),
        "context_reset": CircuitBreakerConfig(
            failure_threshold=4,
            recovery_timeout=15.0,
            expected_exception=Exception,
            name="context_reset",
            recovery_strategy="aggressive",
        ),
    }

    def __init__(
        self,
        config_name: str = "default",
        custom_config: Optional[CircuitBreakerConfig] = None,
    ):
        if custom_config:
            self.config = custom_config
        else:
            self.config = self.DEFAULT_CONFIGS.get(
                config_name, self.DEFAULT_CONFIGS["default"]
            )

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._config_name = self.config.name
        self._half_open_test_done = False

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_test_done = False
                logger.info(f"Circuit Breaker [{self._config_name}] → HALF_OPEN")
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            from errors import ResilienceError, ErrorCode

            raise ResilienceError(
                message=f"Circuit Breaker [{self._config_name}] is OPEN. İstek reddedildi.",
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                details={
                    "state": current_state.value,
                    "config": self._config_name,
                    "failure_count": self._failure_count,
                },
                recoverable=True,
            )

        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_test_done:
                from errors import ResilienceError, ErrorCode

                raise ResilienceError(
                    message=f"Circuit Breaker [{self._config_name}] is HALF_OPEN. Sadece 1 test çağrısına izin verilir.",
                    error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                    details={"state": current_state.value},
                    recoverable=True,
                )
            self._half_open_test_done = True

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._half_open_test_done = False
            logger.info(
                f"Circuit Breaker [{self._config_name}] → CLOSED (recovery successful)"
            )
        self._failure_count = 0

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._half_open_test_done = False
            logger.warning(
                f"Circuit Breaker [{self._config_name}] → OPEN (HALF_OPEN test failed)"
            )
        elif self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit Breaker [{self._config_name}] → OPEN "
                f"(failures: {self._failure_count}/{self.config.failure_threshold})"
            )

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def config_name(self) -> str:
        return self._config_name

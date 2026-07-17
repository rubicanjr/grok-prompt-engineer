"""
Unit Tests for CircuitBreaker (Güncellenmiş)
"""
import unittest
import time
from circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker(unittest.TestCase):

    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker(config_name="default")
        self.assertEqual(breaker.state, CircuitState.CLOSED)

    def test_opens_after_failure_threshold(self):
        breaker = CircuitBreaker(config_name="default")

        def failing_func():
            raise ValueError("Simulated failure")

        for _ in range(5):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        self.assertEqual(breaker.state, CircuitState.OPEN)

    def test_rejects_calls_when_open(self):
        from errors import ResilienceError
        breaker = CircuitBreaker(config_name="default")

        def failing_func():
            raise ValueError("Fail")

        for _ in range(5):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        with self.assertRaises(ResilienceError):
            breaker.call(lambda: "should not run")

    def test_half_open_after_recovery_timeout(self):
        breaker = CircuitBreaker(config_name="default")

        def failing_func():
            raise ValueError("Fail")

        for _ in range(5):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        breaker._last_failure_time = time.time() - 31
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)

    def test_closes_after_success_in_half_open(self):
        breaker = CircuitBreaker(config_name="default")

        def sometimes_failing():
            if breaker._failure_count < 5:
                raise ValueError("Fail")
            return "success"

        for _ in range(5):
            try:
                breaker.call(sometimes_failing)
            except Exception:
                pass

        breaker._state = CircuitState.HALF_OPEN
        breaker._half_open_test_done = False

        result = breaker.call(sometimes_failing)
        self.assertEqual(result, "success")
        self.assertEqual(breaker.state, CircuitState.CLOSED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
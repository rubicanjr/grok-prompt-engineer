"""
Unit Tests for CircuitBreaker
"""
import unittest
import time
from circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker(unittest.TestCase):

    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        self.assertEqual(breaker.state, CircuitState.CLOSED)

    def test_opens_after_failure_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

        def failing_func():
            raise ValueError("Simulated failure")

        # First failure
        with self.assertRaises(ValueError):
            breaker.call(failing_func)

        # Second failure → should open
        with self.assertRaises(ValueError):
            breaker.call(failing_func)

        self.assertEqual(breaker.state, CircuitState.OPEN)

    def test_rejects_calls_when_open(self):
        from errors import ResilienceError

        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)

        def failing_func():
            raise ValueError("Fail")

        # Trigger open
        with self.assertRaises(ValueError):
            breaker.call(failing_func)

        # Should reject immediately with ResilienceError
        with self.assertRaises(ResilienceError) as context:
            breaker.call(lambda: "should not run")

        self.assertIn("Circuit Breaker is OPEN", str(context.exception))

    def test_half_open_after_recovery_timeout(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        def failing_func():
            raise ValueError("Fail")

        # Open the circuit
        with self.assertRaises(ValueError):
            breaker.call(failing_func)

        self.assertEqual(breaker.state, CircuitState.OPEN)

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should transition to HALF_OPEN
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)

    def test_closes_after_success_in_half_open(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        call_count = 0

        def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First fail")
            return "success"

        # First call fails → OPEN
        with self.assertRaises(ValueError):
            breaker.call(sometimes_failing)

        time.sleep(0.2)  # Wait for HALF_OPEN

        # Second call succeeds → should go back to CLOSED
        result = breaker.call(sometimes_failing)
        self.assertEqual(result, "success")
        self.assertEqual(breaker.state, CircuitState.CLOSED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
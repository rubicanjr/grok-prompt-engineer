"""
Unit Tests for Structured Error Model (errors.py)
"""

import unittest
from errors import (
    BaseAppError,
    ConfigurationError,
    ResilienceError,
    StateError,
    LLMError,
    ExecutionError,
    ErrorCode,
)


class TestStructuredErrors(unittest.TestCase):

    def test_base_app_error_creation(self):
        error = BaseAppError(
            message="Something went wrong",
            error_code=ErrorCode.UNKNOWN_ERROR,
            details={"key": "value"},
            recoverable=True,
        )
        self.assertEqual(error.message, "Something went wrong")
        self.assertEqual(error.error_code, ErrorCode.UNKNOWN_ERROR)
        self.assertTrue(error.recoverable)
        self.assertIn("key", error.details)

    def test_base_app_error_to_dict(self):
        error = BaseAppError(
            message="Test error",
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details={"config_key": "timeout"},
            recoverable=False,
        )
        data = error.to_dict()
        self.assertEqual(data["error_code"], "CONFIGURATION_ERROR")
        self.assertEqual(data["message"], "Test error")
        self.assertFalse(data["recoverable"])

    def test_configuration_error(self):
        error = ConfigurationError("Invalid config value")
        self.assertEqual(error.error_code, ErrorCode.CONFIGURATION_ERROR)
        self.assertFalse(error.recoverable)

    def test_resilience_error(self):
        error = ResilienceError(
            message="Retry limit reached",
            error_code=ErrorCode.RETRY_EXHAUSTED,
            recoverable=True,
        )
        self.assertEqual(error.error_code, ErrorCode.RETRY_EXHAUSTED)
        self.assertTrue(error.recoverable)

    def test_state_error(self):
        error = StateError(
            message="State file corrupted",
            error_code=ErrorCode.STATE_CORRUPTED,
            recoverable=False,
        )
        self.assertEqual(error.error_code, ErrorCode.STATE_CORRUPTED)
        self.assertFalse(error.recoverable)

    def test_llm_error(self):
        error = LLMError("LLM call failed", details={"model": "grok"})
        self.assertEqual(error.error_code, ErrorCode.LLM_CALL_FAILED)
        self.assertTrue(error.recoverable)

    def test_execution_error(self):
        error = ExecutionError("Execution failed")
        self.assertEqual(error.error_code, ErrorCode.EXECUTION_FAILED)


if __name__ == "__main__":
    unittest.main(verbosity=2)

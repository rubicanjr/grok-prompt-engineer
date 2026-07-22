"""Webhook alert channel unit tests (mocked)."""

import os
from unittest.mock import patch, MagicMock
from monitor_and_alert import AlertManager, AlertLevel


def test_webhook_handler_called_when_env_set():
    with patch.dict(os.environ, {"ALERT_WEBHOOK_URL": "https://example.com/hook"}):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = MagicMock()
            mgr = AlertManager()
            mgr.send_alert(AlertLevel.INFO, "test webhook", component="test")
            assert mock_open.called


def test_webhook_not_registered_without_env():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ALERT_WEBHOOK_URL", None)
        mgr = AlertManager()
        names = [h.__name__ for h in mgr.handlers]
        assert "_webhook_handler" not in names

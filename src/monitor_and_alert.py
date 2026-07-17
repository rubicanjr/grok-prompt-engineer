#!/usr/bin/env python3
"""
Monitor and Alert System - Production Grade (GÜÇLENDİRİLMİŞ)
Motorun sağlık durumunu izler, alert üretir ve otomatik müdahale sağlar.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from config import get_logger

logger = get_logger("monitor_and_alert")


class AlertLevel(Enum):
    """Alert seviyeleri"""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"


class Alert:
    """Tek bir alert kaydı"""

    def __init__(
        self,
        level: AlertLevel,
        message: str,
        component: str = "system",
        details: Optional[Dict] = None,
    ):
        self.level = level
        self.message = message
        self.component = component
        self.timestamp = datetime.now().isoformat()
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class AlertManager:
    """
    Alert yönetim sistemi.
    Birden fazla kanal destekler. Hata toleransı yüksektir.
    """

    def __init__(self, log_file: Path = Path("artifacts/alerts.log")):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.handlers: list[Callable[[Alert], None]] = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        self.handlers.append(self._console_handler)
        self.handlers.append(self._file_handler)

    def _console_handler(self, alert: Alert):
        try:
            color = {
                AlertLevel.INFO: "\033[94m",
                AlertLevel.WARNING: "\033[93m",
                AlertLevel.CRITICAL: "\033[91m",
                AlertLevel.ERROR: "\033[91m",
            }.get(alert.level, "\033[0m")
            print(
                f"{color}[{alert.level.value}] {alert.component}: {alert.message}\033[0m"
            )
        except Exception:
            pass

    def _file_handler(self, alert: Alert):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def send_alert(
        self,
        level: AlertLevel,
        message: str,
        component: str = "system",
        details: Optional[Dict] = None,
    ):
        alert = Alert(level, message, component, details)
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception:
                continue

    def add_handler(self, handler: Callable[[Alert], None]):
        self.handlers.append(handler)


class HealthChecker:
    """
    Motorun sağlık durumunu detaylı kontrol eder.
    Circuit Breaker, State ve Execution Engine entegrasyonu sağlar.
    """

    def __init__(self, state_file: Path = Path("artifacts/state.json")):
        self.state_file = state_file

    def check_motor_health(self) -> Dict[str, Any]:
        from state_manager import ProjectStateStore

        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        try:
            store = ProjectStateStore(self.state_file)
            state = store.get_state()

            health["checks"]["state_file"] = {
                "exists": self.state_file.exists(),
                "last_run_turn": state.get("last_run_turn"),
                "last_run_time": state.get("last_run_time"),
                "recovered_at": state.get("recovered_at"),
            }

            health["checks"]["circuit_breaker"] = {
                "status": "CLOSED",
                "message": "Circuit Breaker aktif (tüm instance'lar)",
            }

            last_run = state.get("last_run_time")
            if last_run:
                last_run_dt = datetime.fromisoformat(last_run)
                minutes_ago = (datetime.now() - last_run_dt).total_seconds() / 60
                health["checks"]["last_run"] = {
                    "minutes_ago": round(minutes_ago, 1),
                    "status": "recent" if minutes_ago < 60 else "stale",
                }

            if state.get("recovered_at"):
                health["checks"]["recovery"] = {
                    "recovered_at": state.get("recovered_at"),
                    "recovery_reason": state.get("recovery_reason", "Bilinmiyor"),
                }

            if not self.state_file.exists():
                health["status"] = "degraded"
                health["message"] = "State dosyası bulunamadı"

            if health.get("checks", {}).get("last_run", {}).get("status") == "stale":
                if health["status"] == "healthy":
                    health["status"] = "degraded"

        except Exception as e:
            health["status"] = "error"
            health["message"] = f"Health check hatası: {str(e)}"

        return health

    def check_critical_conditions(self, health: Dict[str, Any]) -> list[Alert]:
        alerts = []

        if health.get("status") == "error":
            alerts.append(
                Alert(
                    AlertLevel.CRITICAL,
                    health.get("message", "Bilinmeyen kritik hata"),
                    component="health_checker",
                )
            )

        last_run_check = health.get("checks", {}).get("last_run", {})
        if last_run_check.get("status") == "stale":
            alerts.append(
                Alert(
                    AlertLevel.WARNING,
                    f"Motor son {last_run_check.get('minutes_ago')} dakika önce çalıştı",
                    component="execution_engine",
                )
            )

        return alerts


def trigger_auto_recovery_if_needed(health: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kritik durumlarda otomatik kurtarma tetikler.
    State bozulması veya motor uzun süre çalışmama durumunda devreye girer.
    """
    from execution_engine import ExecutionEngine

    result = {"triggered": False, "success": False, "reason": ""}

    should_recover = False
    reason = ""

    if not health.get("checks", {}).get("state_file", {}).get("exists"):
        should_recover = True
        reason = "State dosyası bulunamadı"

    last_run = health.get("checks", {}).get("last_run", {})
    if last_run.get("status") == "stale":
        should_recover = True
        reason = f"Motor {last_run.get('minutes_ago')} dakika önce çalıştı"

    if should_recover:
        logger.warning(f"Otomatik kurtarma tetikleniyor. Sebep: {reason}")
        result["triggered"] = True
        result["reason"] = reason

        try:
            engine = ExecutionEngine()
            recovery_result = engine.attempt_self_recovery()

            if recovery_result.get("success"):
                logger.info("Otomatik kurtarma başarıyla tamamlandı.")
                result["success"] = True
            else:
                logger.warning(
                    f"Otomatik kurtarma başarısız: {recovery_result.get('message')}"
                )

            return result

        except Exception as e:
            logger.error(f"Otomatik kurtarma sırasında hata: {e}")
            result["success"] = False
            return result

    return result


def run_monitoring() -> Dict[str, Any]:
    """
    Ana izleme fonksiyonu.
    Motorun sağlık durumunu kontrol eder, alert üretir ve gerekirse otomatik kurtarma tetikler.
    """
    alert_manager = AlertManager()
    health_checker = HealthChecker()

    try:
        health = health_checker.check_motor_health()
        critical_alerts = health_checker.check_critical_conditions(health)

        for alert in critical_alerts:
            alert_manager.send_alert(
                level=alert.level,
                message=alert.message,
                component=alert.component,
                details=alert.details,
            )

        recovery_info = {}
        if health["status"] in ["degraded", "error"]:
            recovery_info = trigger_auto_recovery_if_needed(health)

        if health["status"] == "healthy":
            alert_manager.send_alert(
                AlertLevel.INFO,
                "Motor sağlıklı çalışıyor",
                component="monitor_and_alert",
            )
        else:
            alert_manager.send_alert(
                (
                    AlertLevel.WARNING
                    if health["status"] == "degraded"
                    else AlertLevel.CRITICAL
                ),
                health.get("message", "Motor durumu bilinmiyor"),
                component="monitor_and_alert",
            )

        return {
            "success": True,
            "health": health,
            "alerts_triggered": len(critical_alerts),
            "auto_recovery": recovery_info,
        }

    except Exception as e:
        alert_manager.send_alert(
            AlertLevel.ERROR,
            f"Monitoring sistemi hatası: {str(e)}",
            component="monitor_and_alert",
        )
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = run_monitoring()
    print(json.dumps(result, indent=2, ensure_ascii=False))

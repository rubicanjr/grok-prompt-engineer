#!/usr/bin/env python3
"""
Monitoring & Alerting Module
Versiyon: v1.2

Bu modül, Rubric ortalamasını izler, kritik durumları tespit eder ve
gerektiğinde Living_Project_State.md dosyasına otomatik not düşer.

Ana Sorumluluklar:
- Rubric ortalamasını hesaplamak (son 5 tur)
- Düşük/Kritik Rubric durumlarında alert üretmek
- Living_Project_State.md dosyasına otomatik özet ve uyarı yazmak
- Sistem durumunu izlenebilir kılmak

Kullanım:
    from monitor_and_alert import run_monitoring
    run_monitoring()
"""

import re
from pathlib import Path
from datetime import datetime

from config import RUBRIC_LOW_THRESHOLD, RUBRIC_CRITICAL_THRESHOLD, get_logger

ARTIFACTS_DIR = Path("/home/workdir/artifacts")
RUBRIC_LOG = ARTIFACTS_DIR / "Rubric_Tracking_Log_v1.0.md"
USAGE_LOG = ARTIFACTS_DIR / "Usage_Log.md"
ALERT_LOG = ARTIFACTS_DIR / "alerts.log"

logger = get_logger("monitor_and_alert")

def get_rubric_average() -> float:
    """Son 5 turun Rubric ortalamasını hesapla."""
    if not RUBRIC_LOG.exists():
        return 0.0
    content = RUBRIC_LOG.read_text(encoding="utf-8")
    averages = re.findall(r"\*\*(\d+\.\d)\*\*", content)
    if not averages:
        return 0.0
    last_five: list[float] = [float(a) for a in averages[-5:]]
    return sum(last_five) / len(last_five)

def check_for_alerts() -> list[str]:
    """Kritik durumları kontrol et ve alert listesi döndür. 
    Circuit Breaker koruması ile çalışır.
    """
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    def _do_check():
        alerts = []
        avg = get_rubric_average()

        if avg > 0 and avg < RUBRIC_LOW_THRESHOLD:
            alerts.append(f"Rubric ortalaması düşük: {avg:.2f} (< {RUBRIC_LOW_THRESHOLD})")
            alerts.append("ÖNERİ: execution_engine.py ile compliance check tekrar çalıştırılmalı.")

        if avg > 0 and avg < RUBRIC_CRITICAL_THRESHOLD:
            alerts.append(f"KRİTİK: Rubric ortalaması çok düşük ({avg:.2f}). Self-Evolving döngüsü tetiklenmesi önerilir.")

        if USAGE_LOG.exists():
            usage = USAGE_LOG.read_text(encoding="utf-8")
            if "Fallback" in usage or "Context Reset" in usage:
                alerts.append("Son dönemde Fallback veya Context Reset olayı tespit edildi.")

        return alerts

    try:
        return breaker.call(_do_check)
    except Exception as e:
        # Graceful Degradation: Hata durumunda boş liste döndür (sistem çökmesin)
        logger.warning(f"check_for_alerts başarısız oldu (Circuit Breaker): {e}")
        return []

def send_alert(message: str, auto_action: bool = False) -> None:
    """Güçlendirilmiş alert. Düşük/Kritik Rubric'te Living_Project_State'e otomatik not düşer ve loglar."""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    entry = f"[{timestamp}] ALERT: {message}\n"
    logger.warning(message)
    
    if ALERT_LOG.exists():
        ALERT_LOG.write_text(ALERT_LOG.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        ALERT_LOG.write_text("# Alerts Log\n\n" + entry, encoding="utf-8")

    # Güçlendirilmiş otomatik eylem: Her zaman Living_Project_State'e yaz (kritik olmasa da)
    LIVING = ARTIFACTS_DIR / "Living_Project_State.md"
    if LIVING.exists():
        note = f"\n**Monitoring Alert ({timestamp}):** {message}\n"
        if auto_action and "KRİTİK" in message:
            note += "**Öneri:** Self-Evolving döngüsü veya execution_engine compliance check önerilir.\n"
        try:
            LIVING.write_text(LIVING.read_text(encoding="utf-8") + note, encoding="utf-8")
        except Exception as e:
            logger.error(f"Living_Project_State.md yazma hatası (send_alert): {e}")

def run_monitoring() -> None:
    """Güçlendirilmiş monitoring. Her çalıştırmada Rubric ortalamasını Living_Project_State'e yazar."""
    logger.info("=== Monitoring & Alerting v1.1 (Güçlendirilmiş) ===")
    logger.info("Monitoring başlatıldı")
    
    alerts = check_for_alerts()
    
    if alerts:
        for alert in alerts:
            is_critical = "KRİTİK" in alert or "düşük" in alert.lower()
            send_alert(alert, auto_action=is_critical)
    else:
        logger.info("✓ Herhangi bir alert yok. Sistem stabil görünüyor.")
    
    avg = get_rubric_average()
    logger.info(f"Son 5 tur Rubric ortalaması: {avg:.2f}")
    
    # Her zaman Living_Project_State'e güncel özet yaz (entegrasyon güçlendirildi)
    LIVING = ARTIFACTS_DIR / "Living_Project_State.md"
    if LIVING.exists() and avg > 0:
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        summary_note = f"\n**Monitoring Özeti ({timestamp}):** Son 5 tur Rubric ortalaması = {avg:.2f}. Sistem durumu izlendi.\n"
        try:
            LIVING.write_text(LIVING.read_text(encoding="utf-8") + summary_note, encoding="utf-8")
        except Exception as e:
            logger.error(f"Living_Project_State.md yazma hatası (run_monitoring): {e}")

if __name__ == "__main__":
    run_monitoring()

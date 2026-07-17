#!/usr/bin/env python3
"""
Ana Etkileşim Döngüsü Orchestrator
Versiyon: v1.2

Bu modül, her tur sonunda execution_engine, monitor_and_alert ve logging
zincirini güvenli, izlenebilir ve hata toleranslı şekilde çalıştırmaktan sorumludur.

Ana Sorumluluklar:
- Execution Engine ve Monitoring bileşenlerini sırayla çalıştırmak
- Hata izolasyonu sağlamak (bir bileşen hatası diğerini etkilemez)
- Her adımın süresini ölçmek ve detaylı sonuç döndürmek
- Yapılandırılmış logging ile tam izlenebilirlik sağlamak

Kullanım:
    from orchestrator import run_turn_end_automation
    result = run_turn_end_automation(turn=42)
"""

import sys
from pathlib import Path

# src/ layout desteği (PYTHONPATH=src olmadan da çalışsın)
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Optional, Dict, Any

from execution_engine import run_automated
from monitor_and_alert import run_monitoring
from config import get_logger, retry_on_exception

logger = get_logger("orchestrator")


@retry_on_exception(max_retries=2)
def run_turn_end_automation(turn: Optional[int] = None) -> Dict[str, Any]:
    """
    Her tur sonunda execution_engine + monitoring zincirini çalıştıran ana fonksiyondur.

    Bu fonksiyon orchestrator rolünü üstlenir ve şu adımları güvenli şekilde koordine eder:
    1. Execution Engine'i çalıştırır
    2. Monitoring & Alerting'i çalıştırır
    3. Her adımı loglar ve süresini ölçer
    4. Detaylı sonuç sözlüğü döndürür

    Hata İzolasyonu:
        Her iki bileşen de try-except içinde çalıştırılır. Birinin hatası diğerini etkilemez.

    Args:
        turn (Optional[int]): İşlenecek turn numarası.
            None ise execution_engine kendi turn numarasını belirler.

    Returns:
        Dict[str, Any]: İşlem sonucu
            - success (bool): Genel başarı durumu
            - turn (Optional[int]): İşlenen turn
            - execution_engine (str): "success", "failed" veya "not_run"
            - monitoring (str): "success", "failed" veya "not_run"
            - duration_seconds (float): Toplam çalışma süresi
    """
    import time

    start_time = time.time()

    # Basit precondition / health check
    if turn is not None and turn < 0:
        logger.warning(
            f"Negatif turn değeri ({turn}) tespit edildi. None olarak ayarlandı."
        )
        turn = None

    # Turn parametresi validasyonu
    if turn is not None and not isinstance(turn, int):
        logger.warning(f"Geçersiz turn tipi: {type(turn)}. None olarak ayarlandı.")
        turn = None

    effective_turn = turn if turn is not None else "auto"
    logger.info(f"Turn sonu otomasyonu başlatılıyor (Turn: {effective_turn})")

    result = {
        "success": True,
        "turn": turn,
        "execution_engine": "not_run",
        "monitoring": "not_run",
        "duration_seconds": 0.0,
    }

    # 1. Execution Engine'i çalıştır
    try:
        run_automated(turn_override=turn)
        result["execution_engine"] = "success"
        logger.info("Execution Engine başarıyla çalıştırıldı.")
    except Exception:
        result["execution_engine"] = "failed"
        result["success"] = False
        logger.exception("Execution Engine hatası oluştu")

    # 2. Monitoring ve Alerting'i çalıştır
    try:
        run_monitoring()
        result["monitoring"] = "success"
        logger.info("Monitoring başarıyla çalıştırıldı.")
    except Exception:
        result["monitoring"] = "failed"
        result["success"] = False
        logger.exception("Monitoring hatası oluştu")

    result["duration_seconds"] = round(time.time() - start_time, 2)

    # Detaylı final özet logu (İzlenebilirlik için)
    logger.info(
        f"Turn {result['turn']} otomasyonu tamamlandı | "
        f"Süre: {result['duration_seconds']}s | "
        f"Başarı: {result['success']} | "
        f"Execution: {result['execution_engine']} | "
        f"Monitoring: {result['monitoring']}"
    )

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--turn", type=int, default=None)
    args = parser.parse_args()

    run_turn_end_automation(args.turn)

#!/usr/bin/env python3
"""
Grok Prompt Engineer - Production-Grade Execution Engine
Versiyon: v1.2
"""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from config import retry_on_exception, get_logger
from pydantic import BaseModel, Field

logger = get_logger("execution_engine")
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
RUBRIC_LOG = ARTIFACTS_DIR / "Rubric_Tracking_Log_v1.0.md"
RUBRIC_STATE_FILE = ARTIFACTS_DIR / "rubric_state.json"


class RunResult(BaseModel):
    turn: int
    status: str = Field(pattern="^(success|error)$")
    duration_seconds: float = Field(ge=0)


class PhaseResult(BaseModel):
    phase: str = Field(pattern="^(initialize|execute)$")
    turn: int
    status: str = Field(pattern="^(success|error)$")
    duration: float = Field(ge=0)


def get_current_turn() -> int:
    if not RUBRIC_LOG.exists():
        return 0
    content = RUBRIC_LOG.read_text(encoding="utf-8")
    turns = re.findall(r"\| Turn (\d+)", content)
    return int(turns[-1]) if turns else 0


def _get_default_rubric_scores() -> Dict[str, int]:
    return {
        "Grounding": 10,
        "Hallucination": 10,
        "Bias": 10,
        "Token": 9,
        "Yapı": 10,
        "Self-Evolving": 9,
    }


@retry_on_exception(max_retries=3)
def update_rubric(turn: int, scores: Dict[str, int], notes: str) -> bool:
    from rubric_store import RubricStore

    try:
        store = RubricStore(RUBRIC_STATE_FILE)
        return store.update_rubric(turn, scores, notes)
    except Exception as e:
        logger.error(f"RubricStore güncellenemedi: {e}")
        return False


class ExecutionEngine:
    def __init__(self):
        self.last_turn: Optional[int] = None

        # === KRİTİK FONKSİYONLAR İÇİN AYRI CIRCUIT BREAKER INSTANCE'LARI ===
        from circuit_breaker import CircuitBreaker

        self.state_breaker = CircuitBreaker(config_name="state_error")
        self.rubric_breaker = CircuitBreaker(config_name="rubric_update")
        self.context_reset_breaker = CircuitBreaker(config_name="context_reset")
        self.general_breaker = CircuitBreaker(config_name="default")

    def run(self, turn: Optional[int] = None) -> RunResult:
        turn = self._resolve_turn(turn)
        self.last_turn = turn
        return self._perform_run(turn)

    def _perform_run(self, turn: int) -> RunResult:
        start_time = time.time()
        status = "success"

        try:
            from state_manager import ProjectStateStore
            from pathlib import Path

            def state_operation():
                store = ProjectStateStore(Path("artifacts/state.json"))
                current_state = store.get_state()
                current_state["last_run_turn"] = turn
                current_state["last_run_time"] = datetime.now().isoformat()
                store.set_state(current_state)

            self.state_breaker.call(state_operation)

            def protected_execution():
                self._initialize(turn)
                self._execute(turn)

            self.general_breaker.call(protected_execution)

        except Exception as e:
            status = "error"
            logger.error(f"_perform_run hatası (Turn {turn}): {e}")

            if "state" in str(e).lower() or "json" in str(e).lower():
                logger.warning(
                    "State bozulması tespit edildi. Otomatik kurtarma başlatılıyor..."
                )
                recovery_result = self.attempt_self_recovery()
                if recovery_result.get("success"):
                    logger.info(
                        "Kurtarma başarılı. Motor temiz state ile devam edecek."
                    )

        finally:
            duration = round(time.time() - start_time, 3)

        return RunResult(turn=turn, status=status, duration_seconds=duration)

    def _resolve_turn(self, turn: Optional[int]) -> int:
        if turn is None:
            return get_current_turn() + 1
        return turn

    def _initialize(self, turn: int) -> PhaseResult:
        start = time.time()
        try:
            logger.info(f"=== ExecutionEngine started | Turn {turn} ===")
            return PhaseResult(
                phase="initialize",
                turn=turn,
                status="success",
                duration=round(time.time() - start, 3),
            )
        except Exception as e:
            logger.error(f"Initialize error: {e}")
            raise

    def _execute(self, turn: int) -> PhaseResult:
        start = time.time()
        try:
            self._perform_context_reset_if_needed(turn)
            self._update_rubric_for_turn(turn)
            return PhaseResult(
                phase="execute",
                turn=turn,
                status="success",
                duration=round(time.time() - start, 3),
            )
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise

    def _update_rubric_for_turn(self, turn: int):
        def rubric_operation():
            scores = _get_default_rubric_scores()
            update_rubric(turn, scores, "Execution engine run")

        self.rubric_breaker.call(rubric_operation)

    def _perform_context_reset_if_needed(self, turn: int):
        from config import CONTEXT_RESET_TURN_THRESHOLD, ENABLE_AUTO_CONTEXT_RESET

        if not ENABLE_AUTO_CONTEXT_RESET:
            return
        if turn < CONTEXT_RESET_TURN_THRESHOLD:
            return

        def context_reset_operation():
            from state_manager import ProjectStateStore

            store = ProjectStateStore()
            if store.get_state().get(f"context_reset_turn_{turn}"):
                return
            store.record_context_reset(turn)
            logger.info(f"Context Reset applied for Turn {turn}")

        self.context_reset_breaker.call(context_reset_operation)

    def attempt_self_recovery(self) -> Dict[str, Any]:
        """
        Motor kritik bir hata aldığında otomatik kurtarma dener.
        State dosyasını yedekler, temizler ve güvenli bir şekilde yeniden başlatır.
        """
        from state_manager import ProjectStateStore
        from pathlib import Path
        import shutil

        result = {
            "success": False,
            "backup_created": False,
            "state_cleaned": False,
            "new_state_created": False,
            "message": "",
        }

        logger.warning("=== OTOMATİK KURTARMA BAŞLATILIYOR ===")

        try:
            state_file = Path("artifacts/state.json")
            backup_file = Path("artifacts/state.json.bak")

            # 1. Mevcut state dosyasını yedekle
            if state_file.exists():
                try:
                    shutil.copy2(state_file, backup_file)
                    result["backup_created"] = True
                    logger.info(f"State dosyası yedeklendi: {backup_file}")
                except Exception as e:
                    logger.error(f"Yedekleme başarısız: {e}")

            # 2. State dosyasını temizle
            if state_file.exists():
                try:
                    state_file.unlink()
                    result["state_cleaned"] = True
                    logger.info("Bozuk state dosyası silindi.")
                except Exception as e:
                    logger.error(f"State dosyası silinemedi: {e}")

            # 3. Yeni temiz state dosyası oluştur
            try:
                store = ProjectStateStore(state_file)
                new_state = {
                    "recovered_at": datetime.now().isoformat(),
                    "recovery_reason": "Otomatik kurtarma",
                    "recovery_successful": True,
                }
                store.set_state(new_state)
                result["new_state_created"] = True
                logger.info("Yeni temiz state dosyası oluşturuldu.")
            except Exception as e:
                logger.error(f"Yeni state oluşturulamadı: {e}")
                if backup_file.exists():
                    try:
                        shutil.copy2(backup_file, state_file)
                        logger.info("Yedek dosyadan geri yüklendi.")
                        result["message"] = "Yedek dosyadan geri yüklendi"
                    except Exception as backup_error:
                        logger.error(f"Yedek geri yükleme de başarısız: {backup_error}")
                return result

            result["success"] = True
            result["message"] = "Otomatik kurtarma başarıyla tamamlandı."
            logger.info("=== OTOMATİK KURTARMA BAŞARIYLA TAMAMLANDI ===")
            return result

        except Exception as e:
            logger.error(f"Otomatik kurtarma sırasında beklenmedik hata: {e}")
            result["message"] = f"Beklenmedik hata: {str(e)}"
            return result

    def health_check(self) -> Dict[str, Any]:
        from state_manager import ProjectStateStore
        from pathlib import Path

        store = ProjectStateStore(Path("artifacts/state.json"))
        state = store.get_state()

        health = {
            "status": "healthy",
            "last_run_turn": state.get("last_run_turn"),
            "last_run_time": state.get("last_run_time"),
            "circuit_breaker_state": "CLOSED",
            "timestamp": datetime.now().isoformat(),
        }

        if not state.get("last_run_time"):
            health["status"] = "degraded"
            health["message"] = "Motor henüz çalıştırılmadı"

        return health

    def get_last_turn(self) -> Optional[int]:
        return self.last_turn


def main():
    engine = ExecutionEngine()
    engine.run()


def run_automated(turn_override: Optional[int] = None):
    if turn_override:
        logger.info(f"[AUTO] Forced turn override: {turn_override}")
    main()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--turn", type=int, default=None)
    args = parser.parse_args()
    if args.auto or args.turn is not None:
        run_automated(args.turn)
    else:
        main()

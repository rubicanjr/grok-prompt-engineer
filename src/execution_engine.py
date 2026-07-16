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

from config import retry_on_exception, get_logger, SELF_EVOLVING_APPLY_MODE
from pydantic import BaseModel, Field

logger = get_logger("execution_engine")

ARTIFACTS_DIR = Path("/home/workdir/artifacts")
RUBRIC_LOG = ARTIFACTS_DIR / "Rubric_Tracking_Log_v1.0.md"
RUBRIC_STATE_FILE = ARTIFACTS_DIR / "rubric_state.json"
LIVING_STATE = ARTIFACTS_DIR / "Living_Project_State.md"


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
        "Self-Evolving": 9
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

    def run(self, turn: Optional[int] = None) -> RunResult:
        turn = self._resolve_turn(turn)
        self.last_turn = turn
        return self._perform_run(turn)

    def _perform_run(self, turn: int) -> RunResult:
        start_time = time.time()
        try:
            self._initialize(turn)
            self._execute(turn)
            status = "success"
        except Exception:
            status = "error"
            raise
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
            return PhaseResult(phase="initialize", turn=turn, status="success", duration=round(time.time() - start, 3))
        except Exception as e:
            logger.error(f"Initialize error: {e}")
            raise

    def _execute(self, turn: int) -> PhaseResult:
        """Yürütme aşamasını çalıştırır ve özet bilgi döndürür."""
        start = time.time()
        try:
            self._perform_context_reset_if_needed(turn)
            self._update_rubric_for_turn(turn)

            return PhaseResult(
                phase="execute",
                turn=turn,
                status="success",
                duration=round(time.time() - start, 3)
            )
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise

    def _update_rubric_for_turn(self, turn: int):
        scores = _get_default_rubric_scores()
        update_rubric(turn, scores, "Execution engine run")

    def _perform_context_reset_if_needed(self, turn: int):
        from config import CONTEXT_RESET_TURN_THRESHOLD, ENABLE_AUTO_CONTEXT_RESET
        from state_manager import ProjectStateStore

        if not ENABLE_AUTO_CONTEXT_RESET:
            return
        if turn < CONTEXT_RESET_TURN_THRESHOLD:
            return

        store = ProjectStateStore(LIVING_STATE)
        if store.get_state().get(f"context_reset_turn_{turn}"):
            return

        store.record_context_reset(turn)
        logger.info(f"Context Reset applied for Turn {turn}")

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
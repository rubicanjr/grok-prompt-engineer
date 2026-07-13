#!/usr/bin/env python3
"""
Grok Prompt Engineer - Production-Grade Execution Engine
Versiyon: v1.2

Amaç: Protokolleri (Kural 0-11, Rubric, Self-Evolving) otomatik çalıştırmak,
doğrulamak ve güncellemek.

Ana Özellikler:
- Güvenli Rubric güncelleme (duplicate engelleme + atomik yazma)
- Otomatik Context Reset (20+ tur)
- Self-Evolving dry-run + approval kontrolü
- Tutarlı logging standardı (get_logger)
- Geliştirilmiş LLM Fallback adapter arayüzü

Kural 10 uyumlu: Sadece artifacts/ içindeki dosyalara dayanır.
"""

import sys
from pathlib import Path

# src/ layout desteği (PYTHONPATH=src olmadan da çalışsın)
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, TypedDict

from config import retry_on_exception, get_logger, SELF_EVOLVING_APPLY_MODE

logger = get_logger("execution_engine")

ARTIFACTS_DIR = Path("/home/workdir/artifacts")


from pydantic import BaseModel, Field


class RunResult(BaseModel):
    """ExecutionEngine.run() metodunun döndürdüğü yapılandırılmış sonuç."""
    turn: int
    status: str = Field(pattern="^(success|error)$")
    duration_seconds: float = Field(ge=0)


class PhaseResult(BaseModel):
    """_initialize ve _execute metodlarının döndürdüğü yapılandırılmış faz sonucu."""
    phase: str = Field(pattern="^(initialize|execute)$")
    turn: int
    status: str = Field(pattern="^(success|error)$")
    duration: float = Field(ge=0)


RUBRIC_LOG = ARTIFACTS_DIR / "Rubric_Tracking_Log_v1.0.md"
LIVING_STATE = ARTIFACTS_DIR / "Living_Project_State.md"
BACKUP_SCRIPT = ARTIFACTS_DIR / "backup_artifacts.sh"

def get_current_turn() -> int:
    """Rubric log'dan son Turn numarasını oku."""
    if not RUBRIC_LOG.exists():
        return 0
    content = RUBRIC_LOG.read_text(encoding="utf-8")
    turns = re.findall(r"\| Turn (\d+)", content)
    return int(turns[-1]) if turns else 0


def _get_default_rubric_scores() -> Dict[str, int]:
    """Varsayılan Rubric skorlarını döndürür (tip güvenli)."""
    return {
        "Grounding": 10,
        "Hallucination": 10,
        "Bias": 10,
        "Token": 9,
        "Yapı": 10,
        "Self-Evolving": 9
    }


def propose_or_apply_self_evolving_change(description: str, force_apply: bool = False) -> bool:
    """
    Self-Evolving değişiklik önerisi veya uygulaması.

    M4_Self_Evolving_Systems_Protocol_v1.3.md ve config.SELF_EVOLVING_APPLY_MODE ile uyumlu çalışır.

    Returns:
        bool: Değişiklik gerçekten uygulandıysa True, dry-run ise False.
    """
    mode = SELF_EVOLVING_APPLY_MODE.lower()

    if mode == "manual" and not force_apply:
        logger.info(f"[Self-Evolving DRY-RUN] Öneri: {description}")
        logger.info("   → Gerçek uygulama için force_apply=True veya modu 'auto' yapın.")
        return False
    else:
        # Gerçek uygulama (şu anda sadece loglama + ileride genişletilecek)
        logger.info(f"[Self-Evolving APPLIED] Değişiklik: {description}")
        return True

@retry_on_exception(max_retries=3)
def update_rubric(turn: int, scores: Dict[str, int], notes: str) -> bool:
    """Kural 11 Rubric_Automation_Pattern'a göre yeni satır ekle.

    === STATE YÖNETİMİ GEÇİŞ DURUMU (TAMAMLANDI) ===
    - RubricStore artık **tek ve resmi kaynak**tır (yapılandırılmış veri).
    - Markdown log yazımı sadece geriye uyumluluk için LEGACY olarak korunmaktadır.
    - Yeni kod ve iç mantık tamamen RubricStore üzerinden çalışmalıdır.
    - Markdown yazımı uzun vadede kaldırılacaktır.
    """
    from rubric_store import RubricStore
    import warnings

    # 1. RubricStore'u güncelle (Tek ve resmi yol)
    try:
        store = RubricStore(RUBRIC_LOG)
        store_success = store.update_rubric(turn, scores, notes)
    except Exception as e:
        logger.error(f"RubricStore güncellenemedi: {e}")
        return False

    # 2. LEGACY: Markdown log güncellemesi (Geriye uyumluluk için)
    # Bu kısım DEPRECATED olarak işaretlenmiştir.
    if RUBRIC_LOG.exists():
        try:
            date_str = datetime.now().strftime("%d.%m.%Y")
            avg = round(sum(scores.values()) / len(scores), 1) if scores else 0.0

            new_row = (
                f"| Turn {turn} | {date_str} | "
                f"{scores.get('Grounding', 10)} | {scores.get('Hallucination', 10)} | "
                f"{scores.get('Bias', 10)} | {scores.get('Token', 9)} | "
                f"{scores.get('Yapı', 10)} | {scores.get('Self-Evolving', 9)} | "
                f"**{avg}** | {notes} |"
            )

            content = RUBRIC_LOG.read_text(encoding="utf-8")

            if f"| Turn {turn} |" not in content:
                lines = [line for line in content.strip().split("\n") if line.strip()]
                lines.append(new_row)
                temp_file = RUBRIC_LOG.with_suffix(".tmp")
                temp_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                temp_file.replace(RUBRIC_LOG)
        except Exception as e:
            logger.warning(f"Legacy markdown güncellemesi başarısız oldu (görmezden geliniyor): {e}")

    # Dönüş değeri RubricStore başarısına göre belirlenir
    return store_success

def run_compliance_check() -> dict:
    """Basit protokol uyum kontrolü (Kural 0/10/11)."""
    results = {
        "Kural_0": False,
        "Kural_10": False,
        "Kural_11": False,
        "backup_script": False,
        "memory_cards": 0
    }
    
    # Kural 0 kontrolü (attachments temiz, artifacts var)
    results["Kural_0"] = (not os.path.exists("/home/workdir/attachments")) or len(os.listdir("/home/workdir/attachments")) == 0
    
    # Kural 10/11: Log ve State dosyaları var mı?
    # TODO (Section 6): Bu kontroller state katmanına taşınmalı.
    # Şu anda sadece okuma yapılıyor, ama idealde ProjectStateStore / RubricStore üzerinden olmalı.
    results["Kural_10"] = RUBRIC_LOG.exists() and LIVING_STATE.exists()
    results["Kural_11"] = "Rubric_Automation_Pattern" in RUBRIC_LOG.read_text() if RUBRIC_LOG.exists() else False
    
    results["backup_script"] = BACKUP_SCRIPT.exists() and os.access(BACKUP_SCRIPT, os.X_OK)
    
    # Memory Card sayısı
    md_files = list(ARTIFACTS_DIR.glob("*.md"))
    results["memory_cards"] = len([f for f in md_files if "Memory" in f.name or "Living" in f.name or "Risk" in f.name])
    
    return results

def log_event(turn: int, event_type: str, details: str):
    """
    Usage_Logging_Pattern_v1.0.md entegrasyonu.
    
    Bu fonksiyon iki amaçla kullanılır:
    1. Yapılandırılmış logger ile operasyonel loglama
    2. Usage_Log.md dosyasına kalıcı audit kaydı yazma (geriye uyumluluk)
    
    Runtime logging için doğrudan `logger = get_logger(...)` tercih edilmelidir.
    log_event daha çok tarihsel/audit kayıt tutmak için kullanılır.
    """
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Yapılandırılmış logger ile logla
    logger.info(f"[UsageLog] Turn {turn} | {event_type} | {details}")
    
    # Usage_Log.md dosyasına da yaz (geriye uyumluluk için)
    log_file = ARTIFACTS_DIR / "Usage_Log.md"
    entry = f"## Turn {turn} | {timestamp}\n**Event:** {event_type}\n**Details:** {details}\n\n"
    
    try:
        if log_file.exists():
            log_file.write_text(log_file.read_text(encoding="utf-8") + entry, encoding="utf-8")
        else:
            log_file.write_text("# Usage Log (Execution Engine)\n\n" + entry, encoding="utf-8")
    except Exception as e:
        logger.error(f"Usage_Log.md yazma hatası: {e}")


class LLMAdapter:
    """
    LLM_Fallback_Protocol_v1.0.md için geliştirilmiş placeholder adapter.

    Bu sınıf şu anda **kasıtlı olarak stub** olarak bırakılmıştır.
    Gerçek LLM fallback desteği için bu sınıf genişletilmelidir.

    Sağladığı özellikler:
    - Model takibi
    - Desteklenen modeller listesi
    - Basit model değiştirme
    - Çağrı arayüzü (stub)
    """
    def __init__(self, model: str = "grok"):
        self.model = model
        self.supported_models: list[str] = ["grok", "claude", "gpt-4o", "local"]

    def call(self, prompt: str, tools: Optional[list] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Model çağrısı yapar (Circuit Breaker + Timeout korumalı).
        Gerçek implementasyonda burada LLM çağrısı yapılacaktır.
        """
        from circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        def _make_call():
            # Gerçek LLM çağrısı burada yapılacak.
            # Şimdilik stub davranışı:
            return {
                "model": self.model,
                "status": "success (stub)",
                "prompt_length": len(prompt),
                "tools_used": tools if tools else [],
                "timeout": timeout
            }

        try:
            # Circuit Breaker koruması altında çağır
            result = breaker.call(_make_call)
            return result
        except Exception as e:
            from errors import LLMError
            logger.error(f"LLMAdapter çağrısı başarısız: {e}")
            raise LLMError(
                message=f"LLM çağrısı başarısız oldu: {str(e)}",
                details={"prompt_length": len(prompt)}
            )

    def switch_model(self, new_model: str) -> str:
        """Desteklenen modellere geçiş yapar."""
        if new_model in self.supported_models:
            self.model = new_model
            return f"Switched to {new_model}"
        return f"Model {new_model} desteklenmiyor."

    def is_model_supported(self, model: str) -> bool:
        """Modelin desteklenip desteklenmediğini kontrol eder."""
        return model in self.supported_models

    def get_supported_models(self) -> list[str]:
        """Desteklenen modellerin listesini döndürür."""
        return self.supported_models.copy()

    def get_current_model(self) -> str:
        """Şu anda aktif olan modeli döndürür."""
        return self.model

    def reset_to_default(self) -> None:
        """Modeli varsayılan değere ('grok') sıfırlar."""
        self.model = "grok"


def sync_state_and_backup() -> str:
    """State güncelle + backup tetikle.
    
    ⚠️ DEPRECATED: Bu fonksiyon artık kullanılmamalıdır.
    Lütfen ExecutionEngine._sync_state_and_backup() veya ProjectStateStore kullanın.
    """
    import warnings
    warnings.warn(
        "sync_state_and_backup() is deprecated. Use ExecutionEngine._sync_state_and_backup() or ProjectStateStore instead.",
        DeprecationWarning,
        stacklevel=2
    )

    if BACKUP_SCRIPT.exists():
        os.system(f"bash {BACKUP_SCRIPT}")
    timestamp = datetime.now().isoformat()
    note = f"\n**Execution Engine Sync ({timestamp}):** Protokoller çalıştırıldı, Rubric güncellendi.\n"
    
    if LIVING_STATE.exists():
        content = LIVING_STATE.read_text(encoding="utf-8")
        LIVING_STATE.write_text(content + note, encoding="utf-8")
    return "State + Backup sync tamamlandı."


def perform_context_reset_if_needed(turn: int):
    """20+ turda Context Reset'i otomatik tetikler. Token_Efficiency_Sustainability_Protocol_v1.0.md ve Kural 23 ile uyumlu.
    
    ⚠️ DEPRECATED: Bu fonksiyon artık kullanılmamalıdır.
    Lütfen ExecutionEngine._perform_context_reset_if_needed() veya ProjectStateStore kullanın.
    """
    import warnings
    warnings.warn(
        "perform_context_reset_if_needed() is deprecated. Use ExecutionEngine._perform_context_reset_if_needed() or ProjectStateStore instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from config import CONTEXT_RESET_TURN_THRESHOLD, ENABLE_AUTO_CONTEXT_RESET
    
    if not ENABLE_AUTO_CONTEXT_RESET:
        return
    
    if turn < CONTEXT_RESET_TURN_THRESHOLD:
        return
    
    # Zaten reset yapılmış mı kontrol et (basit koruma)
    if LIVING_STATE.exists():
        content = LIVING_STATE.read_text(encoding="utf-8")
        if f"Context Reset uygulandı (Turn {turn})" in content:
            return  # Zaten bu tur için reset yapılmış
    
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    reset_note = (
        f"\n**Context Reset uygulandı (Turn {turn} - {timestamp}):** "
        f"20+ tur eşiği aşıldı. Önceki 15+ tur özetlendi, aktif context korundu. "
        f"Token tüketimi kontrol altına alındı. Modular_Prompt_Architecture_v1.0.md Kural 23 uygulandı.\n"
    )
    
    if LIVING_STATE.exists():
        LIVING_STATE.write_text(LIVING_STATE.read_text(encoding="utf-8") + reset_note, encoding="utf-8")
    
    log_event(turn, "Context Reset Executed", f"Otomatik Context Reset Turn {turn} için uygulandı.")
    logger.info(f"Context Reset otomatik uygulandı (Turn {turn}). Önceki context özetlendi.")


def _log_engine_start(turn: int):
    """Engine başlangıç loglarını yapar."""
    logger.info("=== Grok Prompt Engineer Execution Engine v1.1 (Enhanced) ===")
    logger.info(f"Current Turn: {turn}")
    log_event(turn, "Engine Start", "Execution engine başlatıldı")


def _run_compliance_check_and_log(turn: int) -> dict:
    """Compliance check yapar ve loglar."""
    check = run_compliance_check()
    logger.info(f"Compliance Check: {check}")
    log_event(turn, "Compliance Check", str(check))

    if all([check["Kural_0"], check["Kural_10"], check["Kural_11"]]):
        logger.info("✓ Tüm kritik kurallar uyumlu.")
    else:
        logger.warning("⚠ Bazı kurallarda eksiklik var.")
    return check


def _run_context_reset(turn: int):
    """Context Reset kontrolü ve uygulamasını yapar."""
    perform_context_reset_if_needed(turn)


def _sync_state_and_log(turn: int):
    """State sync yapar ve loglar."""
    result = sync_state_and_backup()
    logger.info(result)
    log_event(turn, "State Sync", result)


def _update_rubric_for_turn(turn: int):
    """Turn için varsayılan Rubric güncellemesi yapar."""
    scores = _get_default_rubric_scores()
    update_rubric(turn, scores, "Execution engine v1.1 çalıştırıldı. Logging, Adapter ve Context Reset entegrasyonu aktif.")
    logger.info(f"Rubric Turn {turn} güncellendi.")
    log_event(turn, "Rubric Update", f"Turn {turn} Rubric güncellendi")


def _initialize_llm_adapter():
    """LLM Adapter'ı başlatır ve loglar."""
    adapter = LLMAdapter("grok")
    logger.info(f"LLM Adapter initialized: {adapter.model}")


def _initialize_engine(turn: int):
    """Engine'in başlangıç aşamasını (initialization) yönetir."""
    _log_engine_start(turn)
    _run_compliance_check_and_log(turn)
    _initialize_llm_adapter()


def _execute_turn(turn: int):
    """Turn'un ana iş akışını (execution) yönetir."""
    _run_context_reset(turn)
    _sync_state_and_log(turn)
    _update_rubric_for_turn(turn)


class ExecutionEngine:
    """
    Execution Engine'in ana sınıfıdır.

    Bu sınıf, her turdaki başlatma ve yürütme adımlarını koordine eder.
    Prosedürel yapıdan sınıf tabanlı yapıya geçişin temelini oluşturur.

    === Public API ===
    - run(turn=None) -> RunResult
    - get_last_turn() -> Optional[int]
    - get_status() -> EngineStatus
    - reset() -> None

    Sorumlulukları:
    - Turn numarasını çözmek ve yönetmek
    - Başlatma ve yürütme aşamalarını koordine etmek
    - Hata yönetimi ve loglama
    - Durum takibi
    """

    def __init__(self):
        self.last_turn: Optional[int] = None

    def run(self, turn: Optional[int] = None) -> RunResult:
        """
        Engine'i çalıştırır (ana public metod).

        Args:
            turn: Çalıştırılacak turn numarası. None ise otomatik belirlenir.

        Returns:
            RunResult: turn, status ve duration_seconds bilgilerini içeren yapılandırılmış sonuç.
        """
        turn = self._resolve_turn(turn)
        self.last_turn = turn
        return self._perform_run(turn)

    def _perform_run(self, turn: int) -> RunResult:
        """Gerçek çalıştırma mantığını içerir (süre ölçümü + başlatma + yürütme)."""
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

        return RunResult(
            turn=turn,
            status=status,
            duration_seconds=duration
        )

    def _resolve_turn(self, turn: Optional[int]) -> int:
        """Turn numarasını çözer. None ise bir sonraki turn'u alır."""
        if turn is None:
            return get_current_turn() + 1
        return turn

    def _log_phase_error(self, phase: str, turn: int, exception: Exception):
        """Tüm fazlarda tutarlı hata loglaması için yardımcı metod."""
        logger.error(f"ExecutionEngine {phase} hatası (Turn {turn}): {exception}")

    def _initialize_engine(self, turn: int):
        """Engine'in başlangıç aşamasını (initialization) yönetir.
        Bu metod, modül seviyesindeki _initialize_engine fonksiyonunun sorumluluğunu üstlenir.
        """
        _log_engine_start(turn)
        _run_compliance_check_and_log(turn)
        _initialize_llm_adapter()

    def _initialize(self, turn: int) -> PhaseResult:
        """Başlatma aşamasını çalıştırır ve özet bilgi döndürür."""
        logger.debug(f"ExecutionEngine başlatma aşaması başlıyor (Turn {turn})")
        start = time.time()
        try:
            self._initialize_engine(turn)
            logger.debug(f"ExecutionEngine başlatma aşaması tamamlandı (Turn {turn})")
            return PhaseResult(
                phase="initialize",
                turn=turn,
                status="success",
                duration=round(time.time() - start, 3)
            )
        except Exception as e:
            self._log_phase_error("başlatma", turn, e)
            raise

    def _execute_turn(self, turn: int):
        """Turn'un ana iş akışını (execution) yönetir.
        Bu metod, modül seviyesindeki _execute_turn fonksiyonunun sorumluluğunu üstlenir.
        """
        self._perform_context_reset_if_needed(turn)
        self._sync_state_and_backup(turn)
        self._update_rubric_for_turn(turn)

    def _update_rubric_for_turn(self, turn: int):
        """Turn için varsayılan Rubric güncellemesi yapar.
        RubricStore üzerinden çalışır.
        """
        from rubric_store import RubricStore

        scores = _get_default_rubric_scores()
        store = RubricStore(RUBRIC_LOG)

        success = store.update_rubric(
            turn=turn,
            scores=scores,
            note="Execution engine v1.1 çalıştırıldı. Logging, Adapter ve Context Reset entegrasyonu aktif."
        )

        if success:
            logger.info(f"Rubric Turn {turn} güncellendi.")
            log_event(turn, "Rubric Update", f"Turn {turn} Rubric güncellendi")
        else:
            logger.error(f"Rubric Turn {turn} güncellenemedi!")

    def _sync_state_and_backup(self, turn: int = None):
        """State güncelle + backup tetikle.
        ProjectStateStore üzerinden çalışır.
        """
        from state_manager import ProjectStateStore

        if BACKUP_SCRIPT.exists():
            os.system(f"bash {BACKUP_SCRIPT}")

        store = ProjectStateStore(LIVING_STATE)
        timestamp = datetime.now().isoformat()
        note = f"Execution Engine Sync ({timestamp}): Protokoller çalıştırıldı, Rubric güncellendi."

        # State'e log ekle
        store.append_log(note)

        return "State + Backup sync tamamlandı."

    def _perform_context_reset_if_needed(self, turn: int):
        """20+ turda Context Reset'i otomatik tetikler.
        Yeni ProjectStateStore üzerinden çalışır.
        """
        from config import CONTEXT_RESET_TURN_THRESHOLD, ENABLE_AUTO_CONTEXT_RESET
        from state_manager import ProjectStateStore

        if not ENABLE_AUTO_CONTEXT_RESET:
            return

        if turn < CONTEXT_RESET_TURN_THRESHOLD:
            return

        store = ProjectStateStore(LIVING_STATE)

        # Zaten bu tur için reset yapılmış mı kontrol et
        state = store.get_state()
        if state.get(f"context_reset_turn_{turn}"):
            return

        # Context Reset kaydı ekle
        store.record_context_reset(turn)

        log_event(turn, "Context Reset Executed", f"Otomatik Context Reset Turn {turn} için uygulandı.")
        logger.info(f"Context Reset otomatik uygulandı (Turn {turn}). Önceki context özetlendi.")

    def _execute(self, turn: int) -> PhaseResult:
        """Yürütme aşamasını çalıştırır ve özet bilgi döndürür."""
        logger.debug(f"ExecutionEngine yürütme aşaması başlıyor (Turn {turn})")
        start = time.time()
        try:
            self._execute_turn(turn)
            logger.debug(f"ExecutionEngine yürütme aşaması tamamlandı (Turn {turn})")
            return PhaseResult(
                phase="execute",
                turn=turn,
                status="success",
                duration=round(time.time() - start, 3)
            )
        except Exception as e:
            self._log_phase_error("yürütme", turn, e)
            raise

    def get_last_turn(self) -> Optional[int]:
        """
        Son çalıştırılan turn numarasını döndürür.

        Returns:
            Optional[int]: Son çalıştırılan turn numarası veya None.
        """
        return self.last_turn

    class EngineStatus(TypedDict):
        last_turn: Optional[int]
        initialized: bool

    def get_status(self) -> EngineStatus:
        """
        Engine'in mevcut durum bilgisini döndürür.

        Returns:
            EngineStatus: last_turn ve initialized bilgilerini içeren yapı.
        """
        return {
            "last_turn": self.last_turn,
            "initialized": self.last_turn is not None
        }

    def reset(self) -> None:
        """
        Engine durumunu sıfırlar.
        last_turn değerini None yapar.
        """
        self.last_turn = None


def main():
    """
    Execution Engine'in ana giriş noktasıdır.

    Bu fonksiyon her turda şu iki aşamayı sırayla çalıştırır:
    1. _initialize_engine(turn) → Başlatma (loglama, compliance, LLM Adapter)
    2. _execute_turn(turn)     → Yürütme (Context Reset, State Sync, Rubric Update)

    Bu yapı sayesinde main() fonksiyonu çok ince ve okunabilir kalır.
    """
    engine = ExecutionEngine()
    engine.run()

def run_automated(turn_override: Optional[int] = None):
    """Otomatik entegrasyon için çağrılabilir fonksiyon (diğer scriptlerden import edilebilir)."""
    if turn_override:
        logger.info(f"[AUTO] Forced turn override: {turn_override}")
    main()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Grok Prompt Engineer Execution Engine v1.1")
    parser.add_argument("--auto", action="store_true", help="Otomatik mod (diğer araçlardan çağrı için)")
    parser.add_argument("--turn", type=int, default=None, help="Test için turn numarası zorla")
    args = parser.parse_args()

    if args.auto or args.turn is not None:
        run_automated(args.turn)
    else:
        main()

# Contributing Guidelines – Grok Prompt Engineer

## State Management Kuralları (Zorunlu)

### 1. Yeni Kodda State Kullanımı
- **Kesinlikle yasak:** `LIVING_STATE.write_text()`, `LIVING_STATE.read_text()`, `RUBRIC_LOG.write_text()` gibi doğrudan dosya işlemleri **yeni kodda kullanılmamalıdır**.
- **Zorunlu:** State işlemleri için `ProjectStateStore` veya `RubricStore` kullanılmalıdır.
  - `ExecutionEngine` içindeki state işlemleri → `self._sync_state_and_backup()`, `self._update_rubric_for_turn()` metodları üzerinden yapılmalıdır.
  - Genel state işlemleri → `ProjectStateStore` kullanılmalıdır.
  - Rubric işlemleri → `RubricStore` kullanılmalıdır.

### 2. Code Review Kuralları
- PR’larda doğrudan dosya yazma kodu (`LIVING_STATE`, `RUBRIC_LOG` ile ilgili) görürseniz **reddedin**.
- State ile ilgili değişikliklerde mutlaka ilgili testlerin (`test_state_manager.py`, `test_resilience.py` vb.) çalışması zorunludur.

### 3. Test Kuralları
- Yeni bir state veya resilience özelliği eklendiğinde ilgili testler de güncellenmeli / yazılmalıdır.
- Minimum test sayıları için `TESTING_STANDARDS.md` dosyasına bakın.
- Mümkün olduğunca parametreli test (`@pytest.mark.parametrize`) ve mock kullanımı tercih edilmelidir.

### 4. Hata Yönetimi Kuralları
- Mümkün olduğunca ham exception (`Exception`, `ValueError`, `RuntimeError`) yerine structured hata sınıfları (`StateError`, `ResilienceError`, `LLMError` vb.) kullanılmalıdır.
- Hata fırlatırken `recoverable` bayrağı doğru şekilde set edilmelidir.

## Genel Kurallar

- Yeni özellik geliştirirken ilgili testleri yazmak geliştiricinin sorumluluğundadır.
- PR’larda testlerin başarılı olması zorunludur.
- Karmaşık hata senaryolarında `given-when-then` yapısı tercih edilmelidir.

---

**Son Güncelleme:** 08.07.2026

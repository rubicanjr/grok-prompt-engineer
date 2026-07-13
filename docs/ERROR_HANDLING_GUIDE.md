# Error Handling Guide & Code Catalog

## 1. Amaç
Bu doküman, projede tutarlı ve anlamlı hata yönetimi sağlamak için hata kodlarını, hata sınıflarını ve kullanım kurallarını tanımlar.

## 2. Hata Sınıfları ve Kullanım Alanları

| Hata Sınıfı          | Kullanım Alanı                          | Recoverable | Örnek Durumlar |
|----------------------|-----------------------------------------|-------------|----------------|
| `BaseAppError`       | Genel temel hata                        | Değişken    | Diğer sınıfların atası |
| `ConfigurationError` | Konfigürasyon hataları                  | Hayır       | Yanlış threshold, eksik ayar |
| `ResilienceError`    | Circuit Breaker, Retry, Timeout         | Evet        | Retry bitti, Circuit açık |
| `StateError`         | State dosyası okuma/yazma hataları      | Değişken    | JSON bozuk, dosya kilitli |
| `LLMError`           | LLM Adapter çağrı hataları              | Evet        | LLM timeout, model hatası |
| `ExecutionError`     | Execution Engine içindeki hatalar       | Genellikle Hayır | Başlatma veya yürütme hatası |

## 3. Hata Kodları Kataloğu (`ErrorCode`)

| Kod                          | Açıklama                                      | Kullanıldığı Yerler                  |
|-----------------------------|-----------------------------------------------|--------------------------------------|
| `UNKNOWN_ERROR`             | Tanımlanmamış hata                            | `BaseAppError` default               |
| `CONFIGURATION_ERROR`       | Konfigürasyon hatası                          | `ConfigurationError`                 |
| `CIRCUIT_BREAKER_OPEN`      | Circuit Breaker açık                          | `CircuitBreaker`                     |
| `RETRY_EXHAUSTED`           | Retry denemeleri tükendi                      | `retry_on_exception`                 |
| `TIMEOUT`                   | İşlem zaman aşımına uğradı                    | Gelecekte eklenecek                  |
| `STATE_READ_ERROR`          | State dosyası okunamadı                       | `StateManager.read()`                |
| `STATE_WRITE_ERROR`         | State dosyasına yazılamadı                    | `StateManager.write()`               |
| `STATE_CORRUPTED`           | State dosyası bozuk (JSON parse hatası)       | `StateManager.read()`                |
| `LLM_CALL_FAILED`           | LLM çağrısı başarısız                         | `LLMAdapter.call()`                  |
| `LLM_TIMEOUT`               | LLM çağrısı timeout                           | Gelecekte eklenecek                  |
| `INITIALIZATION_FAILED`     | Execution Engine başlatılamadı                | `ExecutionEngine`                    |
| `EXECUTION_FAILED`          | Execution sırasında hata                      | `ExecutionError`                     |

## 4. Kullanım Kuralları

### 4.1 Ne Zaman Hangi Hata Sınıfı Kullanılmalı?

- **ConfigurationError**: Config değerleri yanlış veya eksik olduğunda
- **ResilienceError**: Circuit Breaker açık, retry bitti, timeout olduğunda
- **StateError**: Dosya okuma/yazma, JSON parse hatalarında
- **LLMError**: LLM Adapter çağrılarında hata oluştuğunda
- **ExecutionError**: Execution Engine'in kritik akışlarında hata oluştuğunda

### 4.2 Hata Fırlatma Kuralları

- Mümkün olduğunca **raw exception** (`Exception`, `ValueError`, `RuntimeError`) yerine structured hata sınıfları kullanılmalıdır.
- `recoverable` bayrağı doğru şekilde set edilmelidir:
  - Kurtarılabilir hatalar → `recoverable=True` (örnek: Circuit Breaker açık, retry bitti)
  - Kritik/kurtarılamaz hatalar → `recoverable=False` (örnek: State bozuk, config hatası)
- Hata detayları (`details`) mümkün olduğunca zengin tutulmalıdır.

### 4.3 Loglama

- Hata loglanırken mümkün olduğunca `error.to_dict()` veya structured bilgi kullanılmalıdır.
- Sadece hata mesajı değil, `error_code` ve `recoverable` bilgisi de loglanmalıdır.

## 5. Code Review Kuralları

- Yeni kodda **raw exception** fırlatılıyorsa, neden structured hata kullanılmadığı sorulmalıdır.
- Kritik modüllerde (`execution_engine.py`, `orchestrator.py`, `state_manager.py`, `LLMAdapter`) hata yönetimi structured model ile uyumlu olmalıdır.
- `recoverable` bayrağı ve `details` alanı anlamlı şekilde doldurulmalıdır.

## 6. Gelecek İyileştirmeler

- `TIMEOUT` ve `LLM_TIMEOUT` kodları için aktif destek eklenecek.
- Merkezi hata loglama / observability entegrasyonu yapılacak.
- API yanıtlarında structured hata formatı standardize edilecek.

---

**Sürüm:** 1.0  
**Son Güncelleme:** 08.07.2026

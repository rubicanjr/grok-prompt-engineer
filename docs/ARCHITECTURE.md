# Grok Prompt Engineer - Sistem Mimarisi

**Versiyon:** v1.1  
**Tarih:** 06.07.2026

## Genel Bakış

Bu sistem, Grok ile etkileşim sırasında **protokol uyumunu**, **güvenilirliği** ve **otomatik yönetimi** sağlamak amacıyla tasarlanmış bir execution + governance katmanıdır.

Sistem, her "turn" sonunda belirli adımları otomatik olarak çalıştırarak:
- Rubric takibini güvenli şekilde yapar
- Context Reset'i otomatik tetikler
- Monitoring ve alerting üretir
- Self-Evolving değişikliklerini kontrollü şekilde önerir

## Ana Bileşenler ve Sorumlulukları

| Bileşen                    | Dosya                          | Ana Sorumluluk |
|---------------------------|--------------------------------|----------------|
| **Orchestrator**          | `orchestrator.py`              | Execution Engine + Monitoring zincirini güvenli ve izlenebilir şekilde koordine eder. Hata izolasyonu sağlar. |
| **Execution Engine**      | `execution_engine.py`          | Rubric güncelleme, Context Reset, State sync ve LLM Adapter yönetimini yapar. `ExecutionEngine` sınıfı ile yapılandırılmıştır. Sınıf basit durum yönetimi (`last_turn`) de sağlar. |
| **Monitor & Alert**       | `monitor_and_alert.py`         | Rubric ortalamasını izler, düşük/kritik durumlarda alert üretir ve `Living_Project_State.md`'ye otomatik not yazar. |
| **Configuration**         | `config.py`                    | Ortak logger (`get_logger`), retry mekanizması (`retry_on_exception`) ve sistem ayarlarını sağlar. |
| **Testler**               | `test_execution_engine.py`     | Rubric, Context Reset, Monitoring ve Orchestrator entegrasyon testlerini içerir. |

## Turn Akışı (Yüksek Seviye)

1. `orchestrator.run_turn_end_automation(turn)` çağrılır.
2. `ExecutionEngine.run()` çalışır:
   - `_initialize_engine()` → Loglama, Compliance Check, LLM Adapter başlatılır.
   - `_execute_turn()` → Context Reset, State Sync, Rubric güncellemesi yapılır.
3. `monitor_and_alert.run_monitoring()` çalışır:
   - Rubric ortalaması kontrol edilir.
   - Gerekirse `Living_Project_State.md`'ye alert/özet yazılır.
4. Sonuçlar yapılandırılmış şekilde loglanır ve döndürülür.

## Önemli Tasarım Kararları

- **Hata İzolasyonu**: Orchestrator, Execution Engine ve Monitoring birbirinden bağımsız çalışır. Birinin hatası diğerini etkilemez.
- **Self-Evolving Güvenliği**: `propose_or_apply_self_evolving_change()` fonksiyonu ile dry-run / force_apply kontrolü sağlanır.
- **Logging Standardı**: Tüm modüller `config.get_logger()` kullanır. Tutarlı ve izlenebilir loglama hedeflenir.
- **Rubric Güvenliği**: `update_rubric()` fonksiyonu duplicate kontrolü + atomik yazma ile korunur.
- **Context Reset Otomasyonu**: 20+ turda otomatik tetiklenir (`perform_context_reset_if_needed`).

## Dosya Yapısı

```
artifacts/
├── execution_engine.py          # Ana execution mantığı + ExecutionEngine sınıfı
├── orchestrator.py              # Turn sonu otomasyonu (ana giriş noktası)
├── monitor_and_alert.py         # Rubric izleme ve alerting
├── config.py                    # Logger, retry ve sistem ayarları
├── test_execution_engine.py     # Entegrasyon testleri
├── ARCHITECTURE.md              # Bu dosya
├── M4_Self_Evolving_Systems_Protocol_v1.3.md
├── Production_Readiness_Checklist.md
└── *.md                         # Diğer protokol ve durum dosyaları
```

## Gelecek Gelişim Alanları

- Test kapsamının daha da derinleştirilmesi (hata enjeksiyonu ve karmaşık senaryolar)
- `LLMAdapter` gerçek fallback implementasyonu
- `ExecutionEngine` sınıfının daha fazla sorumluluk alması (sürekli geliştirme alanı)
- Mimari dokümantasyonun (`ARCHITECTURE.md`) güncelliğinin korunması

---

**Not:** Bu sistem production-ready değildir. Gelişmiş prototip + sağlam execution katmanı seviyesindedir.
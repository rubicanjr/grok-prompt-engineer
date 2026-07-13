# Testing Standards – Grok Prompt Engineer

## Amaç
Bu doküman, test derinliği ve kalitesinin **kalıcı ve sürdürülebilir** olmasını sağlamak için minimum kuralları tanımlar.

---

## 1. Minimum Test Sayıları (Kritik Alanlar)

| Alan | Minimum Test Sayısı | Zorunlu | Açıklama |
|------|---------------------|---------|----------|
| **Resilience** | **12** | Evet | Circuit Breaker, Retry, Graceful Degradation, Timeout |
| **Config Edge Case** | **20** | Evet | Negatif, 0, çok büyük, string, None, eksik değer |
| **Multi-Component Failure** | **8** | Evet | Execution + Monitoring + Context Reset + State Store kombinasyonları |
| **State Management** | **10** | Evet | `ProjectStateStore` ve `RubricStore` testleri |
| **ExecutionEngine** | **10** | Evet | Temel akış + hata senaryoları |

> **Not:** Bu sayılar minimumdur. Yeni özellik eklendiğinde sayı artırılmalıdır.

---

## 2. Test Yazım Kuralları (Zorunlu)

- Yeni bir **resilience**, **config** veya **state** ile ilgili özellik eklendiğinde ilgili testler **mutlaka** yazılmalıdır.
- PR’larda ilgili testlerin **başarıyla geçmesi** zorunludur. Test geçmeden merge edilemez.
- Karmaşık hata senaryolarında `given-when-then` yapısı **tercih edilmelidir**.
- Mümkün olduğunca `@pytest.mark.parametrize` kullanılmalıdır.
- Gerçek dosya yazımlarından (`Living_Project_State`, `Rubric_Tracking_Log` vb.) mümkün olduğunca kaçınılmalı; `mock` veya `tempfile` tercih edilmelidir.

---

## 3. Test Kategorizasyonu (Markers)

| Marker | Kullanım Alanı |
|--------|----------------|
| `@pytest.mark.resilience` | Circuit Breaker, Retry, Graceful Degradation, Timeout testleri |
| `@pytest.mark.config_edge` | Config edge case testleri |
| `@pytest.mark.multi_component` | Multi-component failure testleri |
| `@pytest.mark.edge_case` | Genel edge case testleri |
| `@pytest.mark.slow` | Uzun süren testler |

---

## 4. Code Review ve PR Kuralları (Kalıcılık İçin Kritik)

### Code Review Kuralı
Resilience, Config Edge Case, Multi-Component Failure veya State Management ile ilgili değişikliklerde:
- İlgili testlerin çalışması **zorunludur**.
- Test kapsamının azalmaması beklenir.

### PR Kuralı
- Yeni bir özellik eklenirken ilgili testler yazılmadan PR **kabul edilmez**.
- Test yazılmadan merge edilirse Code Review’da reddedilir.

---

## 5. Periyodik Kontrol

- Her **2-3 sprintte bir** Test Derinliği Denetimi yapılmalıdır.
- Resilience, Config Edge Case ve Multi-Component alanlarındaki test sayıları minimumların altına düşmemelidir.
- `pytest-cov` ile branch coverage takibi önerilir (özellikle `execution_engine.py` ve `config.py`).

---

## 6. Sorumluluk

- Yeni özellik geliştiren kişi, ilgili testleri yazmakla **yükümlüdür**.
- Code Review sırasında test kalitesi de kontrol edilmelidir.
- Test standardına uymayan PR’lar reddedilmelidir.

---

**Son Güncelleme:** 08.07.2026  
**Sürüm:** 2.0 (Test Derinliği Kalıcı Çözüm)
| `@pytest.mark.multi_failure` | Multi-component failure testleri |
| `@pytest.mark.slow` | Uzun süren testler |

## 4. Periyodik Kontrol

- Her 2-3 sprintte bir test derinliği gözden geçirilmelidir.
- Resilience ve Config Edge Case testlerinin sayısı minimumların altına düşmemelidir.
- Coverage raporu (`pytest-cov`) periyodik olarak kontrol edilmelidir (özellikle `execution_engine.py` ve `config.py`).

## 5. Sorumluluk

- Yeni özellik geliştiren kişi, ilgili testleri yazmakla yükümlüdür.
- Code Review sırasında test kalitesi de kontrol edilmelidir.

---

**Son Güncelleme:** 08.07.2026
**Sürüm:** 1.0

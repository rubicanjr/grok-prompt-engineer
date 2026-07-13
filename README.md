# Grok Prompt Engineer

**Versiyon:** v1.9.2  
**Tarih:** 09.07.2026

Production-grade prompt engineering governance ve otomasyon sistemi.

## Özellikler

- Modular Prompt Architecture
- Self-Evolving Systems Protocol
- Execution Engine + Monitoring + Retry Mekanizması
- Token Efficiency & Context Reset (20+ tur)
- LLM Fallback Protocol
- Fully Automatic Rubric Scoring (RubricStore)

## Klasör Yapısı
grok-prompt-engineer/
├── .github/workflows/
│   ├── ci.yml
│   └── schedule-orchestrator.yml
├── src/                      # Ana kaynak kod
│   ├── execution_engine.py
│   ├── orchestrator.py
│   ├── state_manager.py
│   ├── rubric_store.py
│   ├── monitor_and_alert.py
│   ├── config.py
│   ├── errors.py
│   └── circuit_breaker.py
├── tests/                    # Test dosyaları
├── docs/                     # Dokümantasyon
├── artifacts/                # Çıktılar ve state dosyaları
├── requirements.txt
├── README.md
└── LICENSE

## Kurulum

```bash
git clone <repo-url>
cd grok-prompt-engineer

# Bağımlılıkları kur
pip install -r requirements.txt

# Testleri çalıştır
PYTHONPATH=src pytest tests/ -v

# Execution Engine'i manuel çalıştır
PYTHONPATH=src python src/execution_engine.py --auto
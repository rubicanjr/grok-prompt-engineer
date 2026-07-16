# Grok Prompt Engineer

[![CI](https://github.com/rubicanjr/grok-prompt-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/rubicanjr/grok-prompt-engineer/actions/workflows/ci.yml)

**Grok Prompt Engineer**, Grok ile çalışırken kullanılan prompt’ları, protokolleri ve sistematik süreçleri yönetmek için geliştirilmiş production-grade bir araçtır.

## Özellikler

- **Kural Tabanlı Çalışma** (Kural 0–11): Token verimliliği, grounding, hallucination kontrolü, bias önleme gibi protokolleri otomatik uygular.
- **Rubric Otomasyonu**: Her tur için yapılandırılmış değerlendirme skorları tutar (`RubricStore`).
- **Self-Evolving Sistem**: Kendi kendini geliştirme ve iyileştirme döngülerini destekler.
- **Execution Engine**: Tüm süreci güvenli, izlenebilir ve hata toleranslı şekilde çalıştırır.
- **State Yönetimi**: `StateManager` ve `RubricStore` ile güvenilir dosya tabanlı durum yönetimi.
- **CI/CD Entegrasyonu**: GitHub Actions ile otomatik test ve çalıştırma.
- **Test Altyapısı**: `pytest` ile kapsamlı birim ve entegrasyon testleri.

## Proje Yapısı
grok-prompt-engineer/
├── .github/workflows/     # CI/CD pipeline dosyaları
├── src/                   # Ana kaynak kod
│   ├── execution_engine.py
│   ├── state_manager.py
│   ├── rubric_store.py
│   ├── orchestrator.py
│   └── config.py
├── tests/                 # Test dosyaları
├── docs/                  # Dokümantasyon
├── artifacts/             # Çalışma çıktıları (gitignore)
└── README.md

## Kurulum

```bash
git clone https://github.com/rubicanjr/grok-prompt-engineer.git
cd grok-prompt-engineer

# Sanal ortam oluştur (opsiyonel ama önerilir)
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

pip install -r requirements.txt
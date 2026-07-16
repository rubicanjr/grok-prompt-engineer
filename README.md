# Grok Prompt Engineer

[![CI Status](https://github.com/rubicanjr/grok-prompt-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/rubicanjr/grok-prompt-engineer/actions)

**Grok Prompt Engineer**, Grok ile çalışırken kullanılan prompt yönetimini, protokolleri ve sistematik süreçleri otomatikleştirmek için geliştirilmiş production-grade bir araçtır.

## Özellikler

- **Kural Tabanlı Çalışma (Kural 0-11)**: Token verimliliği, grounding, hallucination kontrolü, bias önleme gibi protokolleri otomatik uygular.
- **Rubric Otomasyonu**: Her tur için yapılandırılmış değerlendirme skorları tutar (`RubricStore`).
- **Self-Evolving Sistem**: Kendi kendini geliştirme ve iyileştirme döngülerini destekler.
- **Execution Engine**: Tüm süreci güvenli, izlenebilir ve hata toleranslı şekilde çalıştırır.
- **Gelişmiş State Yönetimi**: `StateManager` ve `RubricStore` ile güvenilir JSON tabanlı durum yönetimi.
- **CI/CD Entegrasyonu**: GitHub Actions ile otomatik test ve çalıştırma.
- **Kapsamlı Test Altyapısı**: `pytest` ile birim ve entegrasyon testleri.

## Kurulum

```bash
git clone https://github.com/rubicanjr/grok-prompt-engineer.git
cd grok-prompt-engineer

# Opsiyonel: Sanal ortam oluştur
python -m venv .venv
source .venv/bin/activate     # Windows için: .venv\Scripts\activate

pip install -r requirements.txt

<!-- Test commit for CI status check -->
# GitHub Transition Guide

**Proje:** Grok Prompt Engineer  
**Tarih:** 09.07.2026  
**Durum:** Bu ortamda yapılabilecek işler tamamlanmıştır. GitHub + CI/CD tarafına geçişe hazırdır.

---

## 1. Önerilen GitHub Repo Klasör Yapısı

grok-prompt-engineer/
├── src/                          # Ana kaynak kod
│   ├── execution_engine.py
│   ├── state_manager.py
│   ├── rubric_store.py
│   ├── circuit_breaker.py
│   ├── errors.py
│   ├── config.py
│   └── orchestrator.py
├── tests/                        # Tüm testler
│   ├── test_resilience.py
│   ├── test_multi_component_failure.py
│   ├── test_config_edge_cases.py
│   ├── test_state_manager.py
│   └── conftest.py
├── docs/                         # Dokümantasyon
│   ├── TESTING_STANDARDS.md
│   ├── CONTRIBUTING.md
│   ├── ERROR_HANDLING_GUIDE.md
│   └── GITHUB_TRANSITION_GUIDE.md
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml (ileride)
├── README.md
├── requirements.txt
└── LICENSE


**Not:** `test_execution_engine.py` dosyası migration nedeniyle minimal tutulmalı veya tamamen kaldırılmalıdır.

---

## 2. Taşınması Gereken Önemli Dosyalar

| Dosya / Klasör | Durum | Açıklama |
|----------------|-------|----------|
| `src/` klasörü | Taşınmalı | Ana iş mantığı |
| `tests/` klasörü | Taşınmalı | Tüm testler |
| `docs/` klasörü | Taşınmalı | Dokümantasyon |
| `test_execution_engine.py` | Migration | Eski dosya, migration notuyla minimal tutulmalı |
| `GITHUB_TRANSITION_GUIDE.md` | Taşınmalı | Bu dosya |
| `TESTING_STANDARDS.md` | Taşınmalı | Test kuralları |
| `CONTRIBUTING.md` | Taşınmalı (varsa) | Katkı kuralları |

---

## 3. Temel CI/CD Pipeline (.github/workflows/ci.yml)

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short
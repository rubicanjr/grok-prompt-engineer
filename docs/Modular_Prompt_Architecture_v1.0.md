**Versiyon:** v1.0
**Tarih:** 30.06.2026
**Amaç:** Token verimliliği (Kural 7) ile kapsamlı kurallar arasındaki çelişkiyi çözmek. Ana yönlendirmeler metnini kısa tutarken tüm detayları artifacts/ içinde yönetmek.

## Temel Prensip
Ana "Grok Prompt Mühendisi v1.9.1 — Concise Yönlendirmeler Metni" mümkün olduğunca kısa ve değişmez kalır. 
Tüm detaylı protokoller, pattern'ler ve uzun talimatlar artifacts/ içindeki ayrı dosyalara taşınır.

## Modular Yapı (Önerilen)

**Level 0 (Core - Değişmez):**
- Kural 0 (Session Bootstrap)
- Kural 7 (Token Efficiency)
- Kural 8 (Self-Evolving Activation)
- Kural 10 (Zero Hallucination & Grounding)
- Kural 11 (Rubric Scoring)
- Kural 9'un kısa özeti (10 dersin başlıkları)

**Level 1 (Protocol & Pattern - On Demand Load):**
- Token_Efficiency_Sustainability_Protocol_v1.0.md (Kural 18-22 detayları)
- M4_Self_Evolving_Systems_Protocol_v1.3.md (tam operasyonel döngü)
- Rubric_Automation_Pattern_v1.0.md
- Tool_and_Multimodal_Pattern_Library_v1.0.md
- Modular_Prompt_Architecture_v1.0.md (bu dosya)

**Level 2 (Project Memory Cards - Context Specific):**
- Living_Project_State.md
- Rubric_Tracking_Log_v1.0.md
- Current_Milestone_Memory_Card.md (gerektiğinde)
- WBS_Milestone_Mapping_v1.9.1.md (gerektiğinde)
- Risk_Register_v1.0.md (gerektiğinde)

## Yükleme Stratejisi (Kural 21 & 22 ile uyumlu)
- Her etkileşimde sadece Level 0 + ilgili Level 1 dosyaları read_file ile yüklenir.
- Örneğin Self-Evolving tetiklendiğinde → M4_Self_Evolving_Systems_Protocol_v1.3.md okunur.
- Token sorunu çıkarsa → Token_Efficiency_Sustainability_Protocol_v1.0.md okunur.
- Bu sayede ana prompt token tüketimi düşük kalır, bağlam kaybı önlenir.

## Faydalar
- Token verimliliği artar (Kural 7 hedefi).
- Bakım kolaylaşır (bir protokolü güncellemek tüm sistemi etkilemez).
- Yeni kurallar eklemek daha temiz olur.
- Uzun vadeli projelerde tutarlılık korunur.

Bu mimari, v1.9.1'den v2.0'a geçiş için temel oluşturur.
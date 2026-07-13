**Versiyon:** v1.0
**Tarih:** 30.06.2026
**Amaç:** Kural 11'i tamamen otomatik ve tutarlı hale getirmek. Her yanıtta manuel hata riskini ortadan kaldıran standart prosedür.

## Standart Append / Edit Pattern (Zorunlu)

Her final yanıtın sonunda (düşünme sürecinden sonra, yanıt metninden önce veya sonra) şu adımlar **sırayla** uygulanır:

1. **Self-Scoring**
   - Grounding: artifacts/ dışından bilgi var mı? (Evet = düşük puan)
   - Hallucination: "dosyada yok" denmesi gereken yerde uydurma yapıldı mı?
   - Bias: Tartışmalı konuda tarafsız kalındı mı?
   - Token: Gereksiz tekrar veya uzunluk var mı? (Kural 7 ihlali)
   - Yapı: İlk 2-3 cümle özet + profesyonel Türkçe uygulandı mı?
   - Self-Evolving: Gerektiğinde döngü tetiklendi mi? (eğer tetiklendiyse 9-10, gerekmediği halde yüksek puan)

2. **Turn Numarası Belirleme**
   - Rubric_Tracking_Log_v1.0.md dosyasını read_file ile oku.
   - Son satırdaki Turn numarasını tespit et (Bootstrap, Turn 1, Turn X).
   - Yeni Turn = bir sonraki numara (veya tarih bazlı).

3. **Yeni Satır Hazırlama**
   - Tablo formatında yeni satır string'i oluştur:
     | Turn X | DD.MM.YYYY | Grounding | Hallucination | Bias | Token | Yapı | Self-Evolving | **Ortalama** | Notlar (kısa, Kural referanslı) |

4. **Dosyaya Ekleme (edit_file ile)**
   - edit_file aracı kullanılır.
   - old_string = son satırın tamamı ( | Turn X | ... | Notlar | )
   - new_string = son satır + yeni satır
   - replace_all = false (sadece son satırı genişlet)

5. **Doğrulama**
   - İşlem sonrası Rubric_Tracking_Log_v1.0.md tekrar okunur (opsiyonel).
   - Ortalama hesaplanır ve Living_Project_State.md'ye kısa not düşülür eğer ortalama < 9.0 ise.

## Örnek edit_file Kullanımı
edit_file(
  file_path="/home/workdir/artifacts/Rubric_Tracking_Log_v1.0.md",
  old_string="| Turn 1 | 30.06.2026 | 10 | 10 | 10 | 9 | 9 | 9 | **9.5** | ... |",
  new_string="| Turn 1 | 30.06.2026 | 10 | 10 | 10 | 9 | 9 | 9 | **9.5** | ... |\n| Turn 2 | 30.06.2026 | 10 | 10 | 10 | 10 | 10 | 9 | **9.8** | Kural 10/11 tam uyum, protokol dosyaları oluşturuldu. |"
)

Bu pattern ile her yanıt otomatik, tutarlı ve Kural 11'e %100 uyumlu olur. Manuel puanlama minimuma iner.
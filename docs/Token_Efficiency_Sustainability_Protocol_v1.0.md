**Versiyon:** v1.0 (Enhanced - Context Reset v1.1)
**Tarih:** 03.07.2026
**Amaç:** Kural 7'yi destekleyen somut kurallar (Kural 18-22). Token verimliliğini sürdürülebilir kılmak ve ana sistem prompt'unu şişirmemek.

## Kural 18 — İlk Özet Zorunluluğu
Her yanıtın ilk 2-3 cümlesi mutlaka "amaç + ana çıktıyı" net özetler. Okuyucu ilk paragrafta ne alacağını anlar.

## Kural 19 — Cümle Uzunluğu Sınırı
Ortalama cümle uzunluğu 22 kelime altında tutulur. Uzun cümleler kısa iki cümleye bölünür.

## Kural 20 — Tekrar Yasağı
Aynı bilgi, aynı kelimelerle veya çok benzer şekilde tekrar edilmez. Her bilgi bir kez, en net şekilde aktarılır.

## Kural 21 — Bağlam Yönetimi (Dosya Odaklı)
Uzun bağlam veya detaylı bilgi için artifacts/ içindeki Memory Card ve protokol dosyaları kullanılır. Ana yönlendirmeler metnine veya yanıtlara şişirme yapılmaz. "Dosyadan alıntı" veya "artifacts/ grounded" ifadesi tercih edilir.

## Kural 22 — Modular Yükleme
Sadece ilgili protokol veya pattern dosyası okunur (read_file). Tüm protokoller aynı anda ana prompt'a yüklenmez. Bu, hem token tasarrufu sağlar hem de bağlam kaybını önlenir.

## Kural 23 — Context Reset (20+ Tur - Yeni v1.1)
**Tetikleyici:** Konuşma 20. tura ulaştığında veya 3 tur boyunca token tüketimi artma eğilimi gösterdiğinde zorunlu uygulanır.

**Uygulama Adımları:**
1. Modular_Prompt_Architecture_v1.0.md'deki Context Reset Mechanism adımlarını takip et.
2. Önceki 15+ turun detaylarını özetle ve arşivle.
3. Sadece son özet + aktif Level 0/1 protokolleri ile devam et.
4. Her reset sonrası Rubric_Tracking_Log'a "Context Reset uygulandı" notu ekle.
5. Token tüketimini izle; reset sonrası %40+ düşüş hedeflenir.

**Uygulama Notu:** Bu protokol, ana Grok Prompt Mühendisi yönlendirmeler metni ile birlikte kullanılır. Ana metin kısa kalır, detaylar bu dosyada yönetilir. Context reset, uzun vadeli Type B test ve production-ready projelerde token sürdürülebilirliğini garanti eder.

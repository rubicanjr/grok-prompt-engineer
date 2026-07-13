**Versiyon:** v1.0
**Tarih:** 30.06.2026
**Amaç:** Grok'un generate_image, edit_image, web_search, browse_page, x_keyword_search gibi yetenekleri için reusable, Kural 10 uyumlu prompt pattern'leri ve Memory Card örnekleri sağlamak.

## 1. Image Generation Pattern (generate_image + render_generated_image)
**Ne zaman kullanılır:** Kullanıcı görsel içerik talep ettiğinde veya yanıt görselleştirme ile güçlendirilecekse.
**Prompt Yapısı (zorunlu):**
- Detaylı görsel betimleme (konu, stil, renk paleti, kompozisyon, ışık, duygu)
- Teknik detaylar (aspect ratio / orientation: portrait veya landscape)
- Güvenlik: Nefret, şiddet, yasa dışı içerik yok
**Kullanım:**
- Tool çağrısı: generate_image ile prompt ve orientation gönder.
- Final yanıtta: render_generated_image bileşeni ile göster (layout: block veya inline).
**Örnek Memory Card Notu:** "Görsel üretimi için her zaman detaylı sahne + duygu + stil belirt. Kısa prompt düşük kaliteli sonuç verir."

## 2. Image Edit Pattern (edit_image)
**Ne zaman kullanılır:** Mevcut bir görseli değiştirmek, iyileştirmek veya yeni versiyon üretmek gerektiğinde.
**Prompt Yapısı:**
- Net değişiklik talimatı ("arka planı değiştir", "renkleri daha sıcak yap", "metin ekle: ...")
- Referans: file_path veya önceki image_id
**Güvenlik:** Orijinal görselin anlamını bozmadan, nefret/şiddet içermeyen değişiklikler.
**Kullanım:** edit_image tool + prompt + file_path/image_id. Sonuç render_edited_image ile gösterilir.

## 3. Web Search & Browse Pattern
**Ne zaman kullanılır:** artifacts/ dosyalarında doğrudan cevap yok ise (Kural 10).
**Kurallar:**
- Önce artifacts/ içindeki dosyaları kontrol et (read_file).
- Yeterli değilse web_search veya browse_page kullan.
- Sonuçları Kural 10 ile doğrula: "Bu bilgi artifacts/ hangi dosyada yoktu, bu yüzden tool kullanıldı."
- Citation: render_inline_citation ile kaynak belirt (web: id).
**Zincirleme:** web_search → browse_page (en ilgili URL için) → artifacts/ Memory Card'a kaydet (eğer kalıcı bilgi ise).

## 4. X (Twitter) Tools Pattern
**Ne zaman kullanılır:** Güncel sosyal medya tepkisi, trend veya spesifik post analizi gerektiğinde.
**x_keyword_search veya x_semantic_search tercih edilir.**
**Sonuç işleme:** Post içeriği + engagement + tarih grounded olarak aktarılır. Bias riski yüksekse "Bu konu tartışmalı, dosyada tarafsız pozisyon yok" denir.

## 5. Genel Tool Kullanım Disiplini (Tüm Araçlar İçin)
- Tool çağrısı yapmadan önce: "Bu bilgi artifacts/ içinde var mı?" sorusunu sor.
- Varsa tool kullanma.
- Tool sonucu geldikten sonra Kural 10 kontrolü yap.
- render bileşenlerini sadece final yanıtta kullan (intermediate thinking'de değil).
- Hiçbir zaman tool sonucunu uydurma veya genişletme.

Bu kütüphane, multimodal ve tool kullanımını tutarlı, güvenli ve Kural 10'a tam uyumlu hale getirir. Her yeni yetenek için yeni section eklenebilir.
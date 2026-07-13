**Versiyon:** v1.3 Operational
**Tarih:** 30.06.2026
**Amaç:** Kural 8'i tamamen operasyonel hale getirmek. Gerçek senaryolarda tutarsızlık riskini ortadan kaldırmak için adım adım, denetlenebilir süreç tanımlar.

## 1. Aktivasyon Tetikleyicileri (Kural 8)
Self-Evolving döngüsü şu durumlarda **otomatik** devreye girer:
- Rubric ortalaması 3 tur boyunca < 9.0 ise
- Herhangi bir kriter 3 tur boyunca < 8.5 ise
- Bias / tarafsızlık uyarısı varsa
- Milestone kriterleri karşılanamıyorsa veya kritik artifact eksikse
- Kullanıcı "Self-Evolving uygula" veya "sistemi iyileştir" talebinde bulunursa

## 2. Döngü Adımları (Zorunlu Sıra)

### Adım 1: Monitor (İzleme)
- Rubric_Tracking_Log_v1.0.md dosyasını read_file ile oku.
- Living_Project_State.md dosyasını oku.
- Son 3-5 turun ortalama puanlarını, düşük kriterleri ve notları tespit et.
- artifacts/ klasöründeki diğer protokol ve Memory Card'ları tara (eksik dosya var mı?).

### Adım 2: Diagnose (Teşhis)
- Düşük puanın kök nedenini belirle (örnek: "Rubric otomasyonu manuel yapılıyor → tutarsızlık", "eksik protokol dosyası → Kural 10 riski", "token verimsizliği → Kural 7 ihlali").
- Kural 10 kontrolü yap: "Bu teşhis artifacts/ içindeki hangi dosyada doğrudan destekleniyor?"
- Eğer teşhis net değilse döngüyü durdur ve "dosyada doğrudan mevcut değildir" notu düş.

### Adım 3: Propose (Öneri)
- Somut değişiklik önerisi hazırla:
  - Yeni dosya içeriği (write_file için)
  - Mevcut dosyada edit edilecek bölüm (edit_file için)
  - Hangi Kural'ı güçlendireceği
- Öneri, Kural 10'a %100 uyumlu olmalı (uydurma bilgi içermemeli).

### Adım 4: Apply (Uygula)
- Onay beklemeden doğrudan uygula (Kural 8 gereği).
- write_file veya edit_file aracı ile değişiklikleri artifacts/ içine işle.
- Her Apply işleminden sonra Living_Project_State.md'ye "Self-Evolving Apply: [kısa özet] — [tarih]" notu ekle.
- Değişiklik sonrası hemen yeni Rubric satırı ekle (Kural 11).

### Adım 5: Validator (Doğrulama)
- Yeni Rubric puanlarını hesapla.
- Ortalama önceki 3 turdan yüksek mi? Kriterler iyileşti mi?
- İyileşme varsa döngüyü kapat ve "Self-Evolving cycle closed successfully" notu düş.
- İyileşme yoksa veya yeni düşük kriter çıkarsa döngüyü tekrar başlat (maksimum 2 iterasyon).

## 3. Tutarsızlık Riskini Ortadan Kaldıran Kontroller
- Her adımda Kural 10 doğrulaması zorunlu.
- Tüm Apply işlemleri Rubric_Tracking_Log_v1.0.md'ye kaydedilir.
- Bias riski olan konularda "Bu konu proje dosyalarında tarafsız ve net şekilde ele alınmamıştır" ifadesi kullanılır.
- Hiçbir zaman "muhtemelen", "genelde" gibi ifadelerle bilgi genişletilmez.

## 4. Kayıt ve İzlenebilirlik
Her Self-Evolving aktivasyonu Living_Project_State.md ve Rubric_Tracking_Log_v1.0.md'de belgelenir. Bu sayede 3. parti inceleme veya gelecek turlar için tam şeffaflık sağlanır.

## 5. Human Approval Gate for Apply Step (Yeni - Güvenlik İyileştirmesi)
Kural 8 gereği Apply adımı onay beklemeden çalışsa da, üretim güvenliği için aşağıdaki kurallar zorunludur:

**Varsayılan Davranış:**  
Self-Evolving döngüsünün Apply adımı **varsayılan olarak "manual/approval required" modunda** çalışır.

**Uygulama Kuralları:**
- execution_engine veya ilgili scriptlerde `SELF_EVOLVING_APPLY_MODE` ayarı bulunur (`auto` | `manual`).
- `manual` modda Apply adımı **dry-run** yapar, önerilen değişiklikleri Living_Project_State.md ve Rubric_Tracking_Log_v1.0.md'ye yazar, ancak gerçek dosya değişikliği yapmaz.
- Gerçek Apply işlemi sadece kullanıcı onayı (`apply_mode=auto` veya manuel onay) sonrası gerçekleştirilir.
- Onay mekanizması olmadığı durumlarda sistem **hiçbir zaman otomatik Apply yapmaz**.

Bu kural, Self-Evolving'in risksiz çalışmasını sağlar ve üretimde istenmeyen otomatik değişiklikleri engeller.

**Sonuç:** Bu protokol ile Self-Evolving döngüsü manuel yorumlara kapalı, tamamen dosya tabanlı, denetlenebilir ve tutarlı hale getirilmiştir. Human Approval Gate ile Apply adımı üretim güvenliği açısından kontrol altına alınmıştır.
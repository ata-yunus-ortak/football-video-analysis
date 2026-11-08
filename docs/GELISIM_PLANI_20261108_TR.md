# Ölçümden sahipliğe gelişim planı — 8 Kasım 2026

Mevcut darboğaz görüntüde top ölçümünün doğruluğudur. Sıkı kutu eşleşmesinde
parçalı tarama 525 referansın 250'sini buluyor. Geometri/güven filtresi bazı
yanlış adayları azaltıyor fakat tüm kabul koşullarını geçmedi. Tek epoch
eğitim çalışabilirliği doğrulandı; doğruluğu yeterli değil. Bu nedenle
daha uzun eğitim veya daha fazla kural eklemekten önce ölçüm nedenlerini ayıracağız.

1. **Çözünürlük deneyi V015:** aynı Nano ağırlığı, aynı GPU, aynı RGB kare,
   eşik 0,3 ve örtüşme 0,2. Yalnız parçaları 512×768'den 384×384'e değiştir.
   Her beşinci kare, içerik görmeden belirlenen örnekleme. Tüm tahminleri
   referans puanlamadan önce dondur. Her kaynak maçta eşleşme ≥%20 artmalı,
   eşleşmeyenler ≤%25 artmalı. Ayrı kaynak maç 9 sabit kontrol; önceki
   erişimler nedeniyle yeni bağımsız test sayılmaz. Başarılıysa daha uzun
   dış doğrulama aşamasına geç; doğrudan teslim modelini değiştirme.
2. **Veri çeşitliliği ve eğitim:** mevcut üç kısa kaynak maçın yetersizliğini
   koruyarak yeni izinli dış maçları maç bazında ayır. Küçük top için
   çözünürlük stratejisini ve COCO top başlığının aktarımını ayrı deneylerle
   sınayacak eğitim planı kaydet. Eksik etiketleri negatif yapma; ticari
   yayın veya yarışma verisini AI hizmetine yükleme. Yeni sınıf ID'lerini
   eski kişi/top eşlemesine bağlama.
3. **Zamansal top takibi:** ölçülmüş tespit ve tahmin ayrımını koru. Kamera
   kesmesi, uzun kayıp, ayak yakınlığı, yön değiştirme ve aday çoğalmasında
   hata ölç. Kısa tahminin yeni top teması veya oyuncu sahipliği üretmesine
   izin verme. Önce dış görüntüde kimlik değişimi ve yanlış iz süresi ölç.
4. **Kimlik ve iki kamera:** otomatik tracking kimliği, zaman ve homografi
   doğrulanmadan görüntü konumunu kesin oyuncu etiketi sayma. Yayın ölçümü
   yalnız hizalama, görünürlük ve canlı oyun koşulları geçtiğinde tamamlayıcı.
   Tekrar/dar kadraj/uyuşmazlıkta taktik kaynağa dön; kaynak değişimini temas
   veya hız sıçraması olarak yorumlama.
5. **Sahiplik ve D:** top kontrolü, göreli hareket ve ulaşma süresi kanıtını
   zamansal takım kararında birleştir. Temasla pası uçuş yakınlığından ayır.
   Smart Tag yalnız aday duruş aralığı sağlar; tam başlangıç/bitiş ayrıca
   ölçülür. Mevcut D modelleri sınır/aktarım koşullarını geçmediği için
   belirsizliği gizlemek üzere kullanılmayacak.
6. **Birleşik aday ve teslim:** her bileşenin katkısını aç/kapat deneyiyle
   ölç, kaynak/lisans ve hash kaydını tamamla. Sürümü dış veriyle seçip
   dondur; sağlanan maçta yalnız otomatik çıkarım ve yapısal kontrol yap.
   Sağlanan çıktı-video karşılaştırması veya ona göre ayar yapılmaz.

Sahiplik, D veya görüntü başarısı birbirinin yerine geçmez. Testlerin geçmesi
futbol doğruluğu anlamına gelmez. Kusursuzluk/yarışmayı kazanma garantisi yoktur;
gelişme iddiası karşılaştırmalı dış ölçüme dayanacaktır. Önceki deneylerin
kabul koşulları sonuçlara göre gevşetilmez. Ham veri ve ağırlıklar yerelde,
kod ve özet raporlar ekip deposunda kalır.

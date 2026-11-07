# Barcelona yerel bütünleşik gösterim — 7 Kasım 2026

**7 Kasım düzeltmesi:** Tarihsel üretim kaydıdır. Öncelikli 3 Kasım e-postası
çıktıyı sağlanan videoyla karşılaştırmayı yasaklıyor; 8776 sunucusu kapatıldı.
Bu gösterim doğrulama/seçim için kullanılmaz. [Güncel süreç](OTONOM_GELISTIRME_TR.md).

Kullanıcının açık görüntüleme talebi için `tools.visual_local_review` çalıştırıldı.
Gösterim: `http://127.0.0.1:8776/`. Taktik ve yayın kaydı kendi görüntü
dedektörü, kişi/top ölçümü ve zamansal top takip durumuyla yan yanadır.
Birlikte oynatma, duraklatma ve kare adımı yalnız sunumu değiştirir.

İlk yeterli otomatik eşleme aralığı deterministik seçildi. Taktik videonun
50 karesine yaklaşık eşlenen yayın kareleri kullanıldı. Her kamera kendi
ardışık native kareleriyle işlendi; gösterim için yayın kare seçimi tekrar
örneklenirken algoritmaya atlanmış/tekrarlanmış kare girdisi verilmedi.
İki videonun her birinde 50 gösterim karesi, 5 FPS / 10 saniye, 1280×720
olduğu piksel içeriği incelenmeden yeniden çözülerek doğrulandı.

## Kesin karar ve varsayım görünümü

`strict decision` mevcut doğrulama koşullarındaki görüntü sahiplik akışıdır.
Zaman/kalibrasyon/canlılık doğrulanmış sayılmadığından X kalır.
Mevcut iki kamera eşlemesi ±0,4 saniyelik inceleme adayıdır; ±0,02 saniye
kabul sınırını geçmez. Yayın nihai kararda birleştirilmedi.

`ASSUMPTION VIEW` yalnız kimlik/kontrol hesabının mantığını görünür yapmak
için ayrı işlem durumudur: native saat, sağlayıcı homografisi ve canlılık
varsayımıyla çalışır. Bu açık varsayımlar bağımsız doğrulama değildir.
Ekrandaki bütün bu sonuçlar aday olarak işaretlenir. Asıl akışın doğrulama
bayrakları ve kaynak eşleme belirsizliği değiştirilmez; varsayım çıktısı
teslim dosyasına, yayın birleştirmesine veya seçilmiş modele girmez.

Oyuncu yanı H/A ve forma numarası XML/tracking eşleme adayıdır; görsel
kimlik tanıma veya hakem sınıflandırması değildir. Gri artı işaretleri ham
otomatik oyuncu koordinatlarının nominal homografi izdüşümüdür. Top konumu
yalnız dedektördendir; tracking top segmenti ayrıştırılmadı. Tahmin ve
gerçek tespit çizimleri ayrı tutulur. Duran oyun/pas uçuşu bu ilk görüntü
kontrol kuralının dışında kalır.

## Kaynak ve kullanım sınırı

Daha önce tamamlanmış dış koşunun tam dedektör ayarları/ağırlığı ve değişmemiş
top/sahiplik planları kullanıldı. Dosya/kod/ayar hash'leri çözmeden önce
kaydedildi ve çalışma sonunda tekrar kontrol edildi. Parametre seçimi,
başarıya göre kesit seçimi, insan etiketi, düzeltme veya doğruluk ölçümü yoktur.
Kare düzeyinde gözlem/sahiplik JSON'u veya CSV'si dışa aktarılmadı; yalnız
yerel çizimli videolar ve yapısal kayıtlar tutuldu. Görüntüler dış servise
aktarılmadı. Sağlanan maç gösteriminden geliştirme sonucu çıkarılmadı.

Özel çıktı:
`C:/Users/Abra/FootballPrivate/local-view-only-20261106/barcelona-integrated-review-v3`.
Kaynak kaydı `registration.json`, tamamlanma `complete.json`, oynatım kontrolü
`playback-verification.json`. Tüm test paketi: 198 test, 197 geçti, 1 isteğe
bağlı AV atlaması. Bunlar futbol doğruluğu veya gerçek eşleme başarısı değildir.

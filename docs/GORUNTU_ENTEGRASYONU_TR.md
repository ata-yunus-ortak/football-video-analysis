# Görüntü ölçüm katmanının projeye bağlanması

7 Kasım 2026. Giriş: `tools.match_analysis`; ortak ölçüm sözleşmesi:
`development.image_analysis.ImageAnalysis`. Model hâlâ mevcut RF-DETR Nano,
isteğe bağlı SAHI ve kişi takibi için ByteTrack'tir. Yeni model eğitilmedi,
dedektör ayarları değiştirilmedi. Donmuş sahiplik sürümü korunur.

## Tek analiz girişi

Yeni izinli dış videoyu kayıtlı ayarlarıyla görüntü ortamında çalıştır:

```powershell
python -m tools.match_analysis --video C:/private/other-match.mkv --config C:/private/vision-config.json --out C:/private/new-match-analysis
```

Bu komut aynı akışta `detector/` tespitlerini ve `analysis/` proje ölçümlerini
üretir. Mevcut tamamlanmış koşuyu model yeniden çalıştırılmadan bağlamak için:

```powershell
python -m tools.match_analysis --vision-run C:/private/completed-vision-run --out C:/private/new-project-analysis
```

Yeni çıktı dizini depo dışında olmalıdır. Video/config kaydı mevcut dış/sentetik
veri koşullarını kullanır. Sağlanan yarışma maçı geliştirme girdisi olarak kabul
edilmez. Video yolu/hash'i, dedektör kaynak hash'leri, ayarlar ve gözlem dosyasının
kimliği denetlenir. Dönüştürme kaydı, çıktı hash'i ve temel model bütünlüğü tutulur.

## Projenin aldığı veri

`frames.jsonl`, her kare için kaynak/zaman/FPS, kamera epoch'u ve nesne adaylarını
taşır. Her adayın kutusu, görüntü konumu, güveni ve varsa piksel hız vektörü vardır.
İz kimlikleri kaynak video + ayar hash'i + kamera epoch'u ile adlandırılır;
başka videodaki aynı iz numarası aynı kişi kabul edilmez. Boş kareler korunur.
Bütün top adayları saklanır; en yüksek güvenli kutu kendiliğinden oyundaki top
seçilmez. Çift/belirsiz izde kimlik ve hız bilinmiyor kalır.

Kişi hâlâ `person_candidate`; `person_role=unknown`, takım ve kalıcı oyuncu
kimliği yoktur. Hakem/oyuncu/takım sınıfı bu dedektörün çıktısı değildir.
Referans/etiket/olay alanları bu ölçüm girdisinde reddedilir. Saha izdüşümü
varsa yalnız adaydır; piksel konumu metre sayılmaz. Topun zemin/yükseklik ve
oyundaki top seçimi bilinmiyorsa sahiplik girdisi üretilmez. V1 sözleşmesi
`fusion_eligible=false` ve eksik doğrulama nedenlerini taşır.

Dolayısıyla bu entegrasyon görüntü ölçüm katmanıdır. Hibrit sahiplik için ayrı
otomatik rol/takım, top adayı seçimi, kalibrasyon ve zaman/kimlik doğrulaması
gereklidir. Referans etiketlerinin doğru görünmesi bunların model tarafından
çözüldüğü anlamına gelmez. Sınıflandırıcı ve hibrit kabulü sonraki sürümdür.

## Bağlı inceleme ekranı

`tools.vision_review --project-analysis C:/private/project-analysis` modellerin
kutularını artık ortak proje çıktısından okur. Kaynak gözlemleriyle dosya
hash'leri bağlanır; referans paneli ayrı kalır ve model girdisine dönüşmez.
Model panelleri kişi/top adayı, yeşil panel veri setinin oyuncu/hakem etiketidir.

Bu bilgisayardaki tamamlanmış çıktı:
`C:/Users/Abra/FootballPrivate/project-image-integration-20261107`.
Sekiz kesitin iki yöntemi için 16 koşu / 1.200 karelik çıktı, ayrıca önceki kısa
örnek için iki adet 25 karelik çıktı üretildi. Aynı 600 kaynak karesinin iki
yöntemde işlenmesi 1.200 farklı kaynak karesi anlamına gelmez.
Galeri `http://127.0.0.1:8770/`, dokuz seçeneğin tamamında bu çıktıyı okur.
Yenileyince üst bilgi “Proje analiz akışı” ile başlar.

147 testlik paket 1 isteğe bağlı AV atlamasıyla başarılı; referans alanı/rol
sızması, kaynaklar arası iz çakışması, çift iz, kamera epoch'u, eksik kare,
boş kare/top adayları ve uçtan uca proje çıktısı–görünüm bağlantısı kapsandı.
Resmî doğruluk, hakem/takım başarısı veya sahiplik iyileşmesi ölçülmedi.

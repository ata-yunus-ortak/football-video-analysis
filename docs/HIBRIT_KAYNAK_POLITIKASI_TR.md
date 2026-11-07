# Taktik öncelikli hibrit kaynak politikası

`development/hybrid_tracking.py` iki kaynaktan gelen ölçümleri taktik video
zamanında birleştiren deneysel katmandır. `development/hybrid_pipeline.py`
bu girdiyi mevcut temas/pas/hareket akışına bağlar. Donmuş H/A/X modeli veya
`model.json` değiştirilmez; yeni bir teslim sürümü seçilmiş değildir.

## Kaynak seçimi

- Her kare taktik ölçümlerinin kopyasıyla başlar. Ham dosyalar değiştirilmez.
- Yayın ancak doğrulanmış otomatik zaman eşlemesi, canlı görüntü bilgisi,
  geçerli kalibrasyon, yeterli görünür oyuncu/takım kapsamı ve tutarlı
  konum/hareket eşleşmesiyle katkı verir. Bir süre kesintisiz destek aranır.
- Uygun yayında görülen ve güvenilir şekilde ilişkilendirilen oyuncunun
  ölçümü tercih edilir. Görünmeyen, belirsiz ilişkilendirilen veya tekil
  sıçrama yapan oyuncu taktik kaynaktan kalır. Koordinatlar ortalanmaz.
- İki oyunculu/dar yakın çekim, tekrar, boş görüntü, bilinmeyen kadraj/canlılık,
  düşük kapsam, kaynak çelişkisi, geçersiz homografi ve toplu aşırı hareket
  yayın katkısını kapatır. Toplu hareketin hangi kamera olayından geldiği
  kesin olarak sınıflandırılmış sayılmaz.
- Retten sonra yayın hemen geri açılmaz; yeniden istikrarlı destek gerekir.
  Oyuncu yuvası numaraları iki kamerada aynı kişi kabul edilmez. Takım
  metadata'sı ortak sıraya çevrilmiş olmalı; aynı takım içinde karşılıklı
  yakınlık, belirsizlik payı, hız uyumu ve ardışık ilişki desteği aranır.
- Taktik oyuncu kısa süre kayıpsa, yalnız yakın zamanda kurulmuş hâlâ tutarlı
  ilişki ve gerçekten gözlenen yayın noktası kullanılabilir. İlişki süresi
  dolunca eksik nokta eksik kalır; oyuncu konumu tahmin edilip doldurulmaz.
- Topun görünürlüğü, ölçüm güveni, hareketi ve saha düzlemine dönüşüm geçerliliği
  ayrıca kontrol edilir. Taktik topla belirgin çelişkide taktik ölçüm korunur.
  Taktik top kayıpsa uygun gözlenen yayın topu kullanılabilir. Havadaki topun
  görüntü merkezine homografi uygulamak geçerli zemin noktası veya yükseklik
  ölçümü sayılmaz; belirsiz projeksiyon yayın topunu devre dışı bırakır.

Görüntünün daha detaylı oluşu tek başına koordinat doğruluğu kanıtı değildir.
ATD'deki sonlu noktalar da gerçek görsel görünürlük bayrağı değildir. Bu nedenle
görünürlük bilgisi eksikse veya yalnız ATD finiteness/homografi kadraj tahmininden
geliyorsa katman taktik veriyi korur.

## Hareket akışını koruma

Çıktı, her oyuncu/top için kaynak, yayın karesi/yuvası ve ret/seçim nedenini
saklar. İlişki bir yayın yuvasını aynı karede iki oyuncuya bağlayamaz.
`ball_pair_valid` ve `player_pair_valid` kaynak değişimini, kaynakta atlanan
kareyi ve kamera/devre kesintisini bildirir. Bu maskeler kaybedilirse hibrit
girdinin özellik çıkarımı hata verir.

`development/continuity.py` üzerinden hız, dripling, erişim süresi, temas,
pas, uzun top ve duran top sürekliliği bu sınırlara uyar. Böylece iki kaynağın
ölçüm farkı vuruş, yön değişimi, pas, takım ivmesi veya yeniden başlama gibi
yorumlanmaz. Kaynak değişiminde hareket vektörü geçici olarak bilinmez; o
karenin ölçülen konumu saklanır. Eksik top ve görünürlük kaybı D etiketi değildir.

İlk sürüm aynı FPS ve ardışık yerel kare eşlemesi ister. Farklı FPS, tekrar
kullanılan veya atlanan kaynak karelerinde veri taktikten kalır; sahte hız
oluşturacak zaman yeniden örneklemesi yapılmaz.

## Görüntü işleme katmanının sağlayacağı girdiler

`predict_hybrid(tactical, broadcast, alignment, view, hybrid_config,
tactical_baseline_labels, motion_config, **motion_options)` giriş noktasıdır.
Takip girdileri mevcut `inputs.npz` sözleşmesindeki saha metreleri, takım
yuvaları, gözlem maskeleri, FPS, devre ve ardışık kare dizilerini taşır.

`alignment` her taktik kare için yerel `broadcast_frame` indeksi veya -1,
`verified`, bağımsız doğrulanmış `error_bound_s` ve otomatik kaynak açıklaması
sağlar. Gerçek otomatik eşlemelerde dış çift kamera doğrulama raporunun
provenansı/hash'i gerekir; elle eşleme kabul edilmez.

`view` yayın kaydının kendi saatinde şunları sağlar:

- Bağımsız otomatik görüntü gözlemlerinden `player_visible`, `ball_visible`
  ve ölçüm güveni; sonlu koordinattan türetilmez.
- `frame_kind`: live/replay/close_up/no_picture/unknown ve `camera_epoch`.
- `calibration_valid`; top için ayrıca `ball_ground_valid`. Genel bir
  tespit kutusu bu geçerlilikleri tek başına kanıtlamaz.

Mevcut RF-DETR/ByteTrack prototipi henüz bu kanıtların tamamını sağlamaz.
Bu alanları gerçek videoda üretecek ve dış maçlarda doğrulayacak görüntü
işleme prosedürü sonraki adımdır. Alanlar bulunana kadar bilinmeyen değerler
yayını kapalı tutar. Bu davranış doğruluğu doğrulanmamış bir düzeltmeyi nihai
sahiplik akışına sessizce taşımayı önler.

## Mevcut durum ve kontrollü çalışma

Önceki saat eşleme çıktısının bütün bağlantıları `usable_for_possession=false`
durumundadır. 82,8 dakikalık aday kapsamı yeni katmana kullanım onayı sayılmaz.
`automatic_review_candidates` türü her durumda taktik girdiyi korur. Bu
entegrasyonda sağlanan yarışma maçında yayın düzeltmesi etkinleştirilmedi.

`hybrid-data-plan.json` sayıları sentetik mühendislik değerleridir; yarışma
maçında veya public pencerede seçilmedi. İki Metrica dış maçının ilk 1.500'er
karesinde yedi kontrollü senaryo çalıştırıldı: görünür alt küme, iki oyuncu,
tekrar, geometri çelişkisi, toplu sıçrama, yalnız inceleme eşlemesi ve bilinmeyen
görünürlük. 14 koşul/21.000 senaryo karesi işlendi. Pozitif durumda görünür
ölçümler kullanıldı, görünmeyenler taktikten korundu. İki oyuncu, tekrar,
geometri çelişkisi, inceleme eşlemesi ve bilinmeyen görünürlük koşullarında
yayın katkısı sıfır oldu; toplu sıçrama bölümü reddedildi.

İkinci görünüm aynı tracking'den kontrollü olarak türetilmiştir. Görünürlük,
canlılık ve zemin geçerliliği bayrakları sentetik fixture özellikleridir;
gerçek video üzerinde doğrulanmış kamera tespiti değildir. Bu çalışma iki
bağımsız gerçek kamerada doğruluk, daha iyi sahiplik skoru veya seçilmiş
eşikler göstermez. Aynı dış maçlara önceki erişim bilindiğinden bunlar yeni,
dokunulmamış testler diye sunulmaz. Ham Metrica verisi yeniden dağıtılmaz.

Tekrarlama, ana numpy ortamıyla:

```powershell
python -m tools.hybrid_experiment --audit-dir C:/private/metrica-audit --plan hybrid-data-plan.json --out C:/private/hybrid-controlled-v1
python -m unittest discover -s tests -v
```

Çıktı yeni ve kaynak deposunun dışında olmalı. Koşucu kaynak commit'i,
hazırlanan dosya hash'leri, train/validation ayrımı, ayarlar ve kaynak kod
hash'lerini kaydeder; sağlanan maç girdisini reddeder. Ham girdiler,
ölçüm/provenans dizileri ve üretilen çıktılar Git'e alınmaz.

Kural dayanağı: [organizatör FAQ — yayın verisi ve kendi tracking'i](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/FAQ.md#can-i-use-the-broadcast-video-and-its-tracking).
Yayın verisi kullanılabilir; eşleme taktik saate geri dönmelidir ve sağlanan
maç elle düzeltilmez. Geliştirme/ayarlar başka maçlarda yapılır; sağlanan
görüntü/veri veya kırpmaları uzak LLM'ye yüklenmez. Bu uygulama mevcut
sağlayıcı/sohbet temizliği bekleyenlerini tamamlandığı iddiasıyla değiştirmez.
Veri kaynağı: [Metrica Sports Sample Data](https://github.com/metrica-sports/sample-data).

# LONG BALL destekli ölçülmüş uzun top dizileri

4 Kasım 2026. `development/long_ball.py` otomatik LONG BALL aralıklarında
hızlı, uzun mesafeli, tutarlı top hareketi arar. Etiket tek başına uzun top
kararı değildir. Yeni katman `development.motion_possession.predict` içine
bağlıdır; dondurulmuş `clean_model/` veya `model.json` değiştirilmez.

## Arama ve sahiplik

- Yalnız otomatik LONG BALL aralığının içindeki ölçümler değerlendirilir.
  Etiket sınırları dışında hareket eklenmez.
- Ardışık gerçek top konumlarından metre/saniye hız hesaplanır. Hız ve süre
  alt sınırları, net yer değiştirme ve yolun tutarlılığı birlikte aranır.
- Tutarlılık, net yer değiştirme / toplam yol uzunluğudur. Sağa-sola giden
  ölçüm gürültüsünün toplam yolunu uzun pas gibi yorumlamamak içindir.
- Büyük yön dönüşü hareketi ikiye ayırır. Dönüş noktasında olası temas
  incelenebilir; bu nokta uçuşun içi sayılmaz.
- Kayıp nokta, devre değişimi, saha dışı veya fiziksel hız üst sınırını aşan
  sıçrama diziyi keser. Kayıp aralıklar enterpole edilmez. Boşluğun iki ucunu
  birleştirerek uzun top kararı verilmez.
- D bölümleri ve doğrulanmış birlikte hareket/dripling ölçümleri aramadan
  çıkarılır. Hızlı ve uzun bir dripling yanlışlıkla uçuş sayılmamalıdır.
- Desteklenen dizinin yalnız iç karelerinde yakınlığa/temel modele dayalı
  sahiplik X'e çekilir; gerekçe `long_ball_no_proximity_ownership` olur.
  Başlangıç/bitiş temasları, hareket değişimine dayalı temas kanıtı ve
  doğrulanmış aynı takım pası korunur. Yakından geçme yeni temas sayılmaz.
- LONG BALL etiketinin Team alanı tek başına H/A atamaz. Topun havada
  olduğu veya oyuncunun üzerinden geçtiği iki boyutlu tracking ile doğrulanmaz.

## Bağlantı ve çıktı

`predict(..., long_ball_config=LongBallConfig(...), automatic_tags=...)` ile
etkinleşir. D katmanından bağımsız veya onunla birlikte açılabilir. Otomatik
etiketlerin kaynak türü, FPS'i ve kare uzunluğu kontrol edilir; olaylar
koordinat özelliklerine veya öğrenme hedeflerine karıştırılmaz.

Zorunlu ayarlar: `min_speed_mps`, `max_speed_mps`, `min_distance_m`,
`min_duration_s`, `min_straightness`, `max_turn_degrees`. Seçilmiş futbol
varsayılanları yoktur; test değerleri yalnız sentetik mühendislik örnekleridir.

Çıktılarda `long_ball_events`, `long_ball_flight_mask` ve
`long_ball_unresolved_tags` bulunur. Her aday başlangıç/bitiş kareleri,
süre, net yer değiştirme, toplam yol, ortalama hız ve ilgili tag kimliklerini
taşır. `end_frame` son gözlenen noktadır; `end_frame_exclusive=end_frame+1`.
Uçuş maskesi iki uç noktayı dışarıda bırakır. Aynı sınırları veren etiketler
bir kayıtta birleştirilir; farklı örtüşen aralıklar kaynak ilişkileriyle korunur.

`tools.motion_experiment` yapılandırmasında `long_ball_parameters` ve mevcut
`automatic_tag_files` kaydı kullanılır. D olmadan da tag dosyası yüklenebilir.
Kaynak/provenance ve dosya hash'i doğrulanır; ayarlar/source hash'leri
manifestte, olaylar `*-events.json`, kare maskesi `*-long-ball.npz` içinde
kaydedilir. Ham veriler ve çıktılar kaynak deposunun dışında kalır.

## Seçim durumu

72 yazılım testi geçti: yakın rakibin yanından geçiş, mesafe/hız/süre,
eksik ölçüm, devre, sıçrama, yön dönüşü, dripling çatışması, yinelenen tag ve
25 FPS aktarımı ile uçtan uca çıktı/ayar kaydı sınandı. Bağımsız dış maçlarda
long-ball/temas/sahiplik doğruluğu henüz değerlendirilmedi. Sayısal ayar veya
teslim sürümü seçilmedi; verilen maçın görüntü veya public sonuçlarıyla
parametre ayarlanmadı. Bu katman henüz doğrulanmış teslim sürümü değildir.

# Smart Tagging destekli deneysel D katmanı

4 Kasım 2026. `development/set_piece_dead_ball.py`, otomatik SET PIECES
etiketlerini takip verisiyle birleştirir. Etiket aralığı D gerçeği değildir;
yeniden başlama çevresinde arama yapmayı sağlayan bir ön bilgidir.

## Algoritma

Desteklenen türler: Throw-in, Goal Kick, Free Kick, Corner Kick ve Kick Off
(Start/After Goal dahil). Tekrar alınan, eksik veya birbiriyle çelişen türler
belirsiz kalır. Diğer oyun bölgesi/faz etiketleri bu aşamada D'ye çevrilmez.

1. Etiketin öncesine/sonrasına yapılandırılmış arama penceresi eklenir.
2. Gözlenen top noktalarından hız hesaplanır. Kayıp noktalar enterpole edilmez;
   gerçekçi olmayan hız adımlarının iki ucu güvenilmez sayılır.
3. Yeterince uzun, konumu da dar bir alanda kalan ölçülmüş bekleme aranır.
   Ardından etiket civarında birkaç ölçüm süren yeniden hareket beklenir.
   Bekleme ile hareket arasında ölçüm kaybı, devre değişimi veya başka yere
   taşınma varsa bu ikisi birleştirilmez. Bekleme noktasında gözlenmiş yakın
   bir oyuncu da bulunmalıdır.
4. Taçta yan çizgi, kornerde köşe, autta uç çizgi bölgesi, santrada saha merkezi
   yakınlığı kontrol edilir. Serbest vuruş için saha içi konum aranır. Bunlar
   iki boyutlu nokta konumu ipuçlarıdır; kural ihlali/temas doğrulaması değildir.
5. Bekleme başlangıcı D adayı başlangıcıdır. Taç/aut/korner için kesintisiz
   ölçülmüş ve arada başka hızlı başlangıç bulunmayan daha erken saha dışı
   çıkış varsa başlangıç oraya genişletilebilir. Tek bir uygun yeniden başlama
   varsa `[başlangıç, yeniden_hareket)` D olur. Birden fazla olasılık belirsizdir.

**Bu başlangıç kesin düdük veya gerçek durma anı iddiası taşımaz.** Çoğu durumda
yalnız ölçülebilen bekleme kısmını kapsar; duruşun daha erken kısmını kaçırabilir.
Yanlış otomatik etiket, canlı oyunda kısa beklemeyi de yanlış D yapabilir.
Bu yüzden bu henüz doğrulanmış bir teslim sınıflandırıcısı değildir.

Etiket tek başına D üretmez. Topun eksik olduğu kareler D'ye dönüştürülmez.
Etiketin Team alanı, özellikle N/A ise, H/A sahipliği dayatmaz. Yeniden başlama
karesinde normal hareket/sahiplik katmanı çalışmaya devam eder.

## Mevcut deney algoritmasına bağlantı

`development.motion_possession.predict` şu iki ek keyword argümanını alır:

- `dead_ball_config=DeadBallConfig(...)`
- `automatic_tags=load_tags(xml_path, fps, frame_count)`

İkisi birlikte verilmelidir; etiket kaynağı otomatik/sentetik olarak tanımlı ve
FPS/kare uzunluğu girişle aynı olmalıdır. Etiketler ayrı argümandır; koordinat
özelliklerine veya öğrenme hedeflerine karıştırılmaz. D son karar önceliğidir;
D içindeki temas/dripling sahipliği ve D'yi aşan pas zincirleri üretilmez.

Çıktı: H/A/D/X etiketleri, `dead_ball_mask`, tag başına karar gerekçesi,
aday duruş başlangıcı ve yeniden hareket karesi. D kayıtlarında
`exact_whistle_time_verified=false` ve seçim/doğruluk durumu açıktır.

## Ayarlar ve dış deney

Sayısal futbol varsayılanları yoktur; bütün ayarlar zorunludur:

| Ayar | Anlamı |
| --- | --- |
| `lookback_s`, `lookahead_s` | Etiket çevresindeki arama sınırları |
| `stationary_s` | Asgari ölçülen bekleme süresi |
| `still_speed_mps` | Bekleme hız sınırı |
| `stationary_radius_m` | Bekleme/preparasyon noktasından uzaklaşma sınırı |
| `restart_speed_mps` | Yeniden hareket alt sınırı |
| `restart_confirmation_s` | Hareketin doğrulanma süresi |
| `launch_gap_s` | Son yavaş ölçüm ile hareket arasındaki üst süre |
| `max_ball_speed_mps` | Güvenilmez adım hız sınırı |
| `contact_radius_m` | Gözlenen oyuncunun bekleme noktasına uzaklığı |
| `restart_region_m` | Türe bağlı saha bölgesi toleransı |

`tools.motion_experiment` yapılandırmasına `dead_ball_parameters` ve maç
başına `automatic_tag_files` eklenebilir. Her dosya kaydında `fixture_id`,
`path`, `sha256`, `source_kind=automatic_provider_tags` ve üretim/kaynak
açıklaması olan `provenance` gerekir. Başka maça ait tag dosyası veya elle
üretilmiş hedefler bu otomatik veri girdisi yerine geçirilmemelidir.
Dosya hash'i doğrulanır; kaynak/ayar kayıtları ve D kararları çıktı dosyalarına
girer. Bunlar kaynak deposu dışında tutulur.

D001'deki Metrica örneklerine karşılık gelen bağımsız otomatik Smart Tagging
dosyaları henüz kayıtlı değildir. D001'deki olaylardan türetilmiş aday duruş
aralıkları otomatik Smart Tagging dosyası veya kesin D hedefi diye kullanılmaz.
Bu adım yalnız sentetik testlerle doğrulanmıştır. Gerçek dış maç D/canlı oyun
hedefleriyle ayar seçimi ve doğruluk değerlendirmesi ayrıca gerekir. Yeni
pipeline seçilip dondurulduktan sonra tam maç üretilecektir.

63 test geçti; beş tür, bölge uyumsuzluğu, eksik top, devre sınırı, sıçrama,
birden fazla başlangıç, N/A takım, 25 FPS aktarımı ve uçtan uca kayıt/girdi
kontrolleri sınandı. Test sayıları sentetiktir; yarışma maçındaki gözlemlerden
üretilmemiştir. Dondurulmuş temel H/A/X kaynakları ve `model.json` korunmuştur.

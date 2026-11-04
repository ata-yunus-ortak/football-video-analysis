# Hareket, aday temas ve aday pas

4 Kasım 2026. Kullanıcının önerisi `development/motion_possession.py` içinde
ayrı sahiplik deneyi olarak uygulandı. D katmanı ve dondurulmuş temel model
değişmez. Sayısal futbol ayarları henüz seçilmemiştir.

## Karar sırası

1. Metre cinsinden ardışık x/y'den işaretli `vx`, `vy` hesaplanır (m/s).
   Ham `s` hız büyüklüğüdür (km/saat). `+5 -> 0 -> -5` bir hız bileşenine
   aittir; hız büyüklüğünün negatif olması gerekmez.
2. Hızlı uçuşta temel modelin salt yakınlık/önceki sahiplik kararı X'e çekilir.
   Süreklilikle doğrulanan oyuncu/top birlikte hareketi bu engeli aşabilir.
3. Önce/sonra pencerelerin medyan hız vektörü farkı yön dönüşünü, hızlanmayı
   veya yavaşlamayı aday temas yapar. Komşu adayların tekrarları bastırılır.
   Bu çevrimdışı yöntem sonraki kareleri de kullanır.
4. Yakın ve diğer oyunculardan yeterince ayrışan gözlenmiş takip kaydı varsa
   aday temas o takıma bağlanır. Oyuncunun hemen önce/sonra da ölçülmesi
   gerekir. Belirsiz değişimde oyuncu atanmaz.
5. Ardışık iki temas aynı takımın farklı takip kayıtlarına bağlanırsa, arada
   top/iki oyuncu ölçümleri kesilmemişse, devre/saha sınırı aşılmamışsa ve
   süre sınırı uygunsa aday pas çıkarılır. Bu aralık H/A sahiplik kanıtı olur.
   Araya rakip veya belirsiz temas girerse pas kurulmaz.

Eksik top enterpole edilmez. Saha dışı noktalar ve hız üst sınırını aşan
adımların iki ucu güvenilmez sayılır. Sekme ve takip hatası temas adayı
üretebilir. Takip kaydı kişi kimliği olmadığından aday pas kesin gerçek
değildir. Yükseklik olmadan bu belirsizlikler bütünüyle giderilemez.

## Kullanım

`predict(inputs, baseline_labels, MotionConfig(...))` H/A/X etiketleri,
gerekçeler, işaretli hızlar, hız vektörü farkları, aday temaslar ve aday
paslar döndürür. Etiket/olaylar özellik girdisi değildir. D üretilmez.

Parametreler zorunludur; seçilmiş varsayılan futbol eşikleri yoktur:

| Parametre | Anlamı |
| --- | --- |
| `window_s` | Önce/sonra hız penceresi, saniye |
| `fast_speed_mps` | Salt yakınlığı bastıran hız, m/s |
| `max_speed_mps` | Güvenilmez adım sınırı, m/s |
| `min_delta_velocity_mps` | Aday hız vektörü değişimi, m/s |
| `contact_radius_m` | Temas adayı oyuncu uzaklığı, metre |
| `player_margin_m` | İkinci oyuncuya göre uzaklık farkı, metre |
| `refractory_s` | Komşu adayları bastırma süresi, saniye |
| `max_pass_s` | İki temas arası azami süre, saniye |

Test sayıları yalnız sentetik mühendislik örnekleridir. Sonraki adımda dış
eğitim maçlarında aday ayarlar üretilecek, ayrı doğrulama maçlarında temas,
pas ve sahiplik hedefleriyle değerlendirilecektir. Aday sayısı başarı değildir.
Bu aşamada yarışma maçında ayar seçilmedi veya yeni teslim sürümü üretilmedi.

```powershell
python -m tools.motion_experiment --audit-dir C:/external/audit-v1 --config C:/external/motion-config.json --out C:/external/motion-run-1
```

JSON yapılandırması `parameters` nesnesi ve seçim durumunu açıklayan
`rationale` metni içermelidir. Araç D001 Metrica kapsam raporunun girdi
hash'lerini ve temel model kaynaklarını doğrular. Ayar/kaynak/girdi raporu ve
temel model hash'lerini çıktıdan önce kaydeder. Etiket/gerekçe CSV'leri ile
aday temas/pas JSON'ları kaynak deposu dışında saklanır.

## Oyuncuyla birlikte hareket ve takım bağlamı — M002

`development/player_motion.py` oyuncu x/y konumlarından işaretli hız çıkarır.
`predict` fonksiyonuna dördüncü argüman olarak `DribbleConfig` verilmesi bu
katmanı açar. Yakın, diğer oyunculardan ayrışan aynı takip kaydı belirli süre
boyunca şu koşulları sağlarsa dripling/sahiplik kanıtı oluşur:

- Uzaklık ve `norm(v_top - v_oyuncu)` sınır içindedir; hız ve yön uyuşmalıdır.
- İkisi de asgari hareket hızını aşar; sabit durma dripling sayılmaz.
- Ölçümler süreklidir; devre sınırı, kayıp ve gerçekçi olmayan sıçrama diziyi keser.

Doğrulanan dizi ilk destekli hız örneğine kadar geri yazılır. Bu çevrimdışı
bir katmandır. Rakibin birlikte hareket kanıtı üzerinden pas aralığı yazılmaz.
Mevcut temas kararları kendi karelerinde önceliklidir. Ham `s` kullanılmaz.

Katman açıldığında ayarlar zorunludur: `radius_m`, `velocity_error_mps`,
`min_speed_mps`, `max_player_speed_mps`, `confirmation_s`, `player_margin_m`,
`min_team_players`. Seçilmiş varsayılan futbol eşikleri yoktur.

Takım başına güvenilir ardışık ölçümlerden `team_mean_velocity_mps` (x/y
vektör ortalaması), `team_mean_speed_mps` (hız büyüklüğü ortalaması) ve
`team_velocity_counts` (katılan takip yuvası sayısı) ayrı çıkarılır. Yeterli
kapsam yoksa ortalama NaN kalır; eksik oyuncu sıfır hızlı sayılmaz. Yinelenmiş
takip yuvaları ortalamayı etkileyebilir; gerçek kişilerin tamamı iddiası yoktur.

Takım özetleri doğrudan H/A üretmez. İki takım aynı yönde ilerlerken sahiplik
herhangi birinde olabilir; geriye pas, pres ve geri koşular bu çıkarımı
belirsiz yapar. Saha ekseni, takım/devre hücum yönü bilinmeden hücum yönü
olarak yorumlanmaz.

Çalıştırıcı JSON'unda `dribble_parameters` verilirse katman etkinleşir.
Oyuncu hızları, dripling yuvaları, vektör hataları ve takım özetleri
`*-player-motion.npz` içinde, ayarlar kayıt manifestinde saklanır.

## Takım hareketindeki değişim — M003

`development/team_transitions.py` iki takımın önce/sonra kısa pencerelerdeki
hız büyüklüğü ve hız vektörü değişimlerini ayrı ölçer. Her karşılaştırmada
yalnız pencerelerin tamamında güvenilir hızı olan AYNI takip yuvaları
kullanılır. Böylece görünür oyuncu kümesinin değişmesi davranış değişimi
sayılmaz. İki takım da değişim göstermeli; yeterli kapsam bulunmalıdır.
Komşu adaylar bastırılır; devre sınırları aşılmaz. Gelecek pencere kullanıldığı
için bu da çevrimdışı bir analizdir.

Takım hareketi tek başına sahipliği değiştirmez. Adayın önce/sonrasında yakın
zamanda temas veya doğrulanmış birlikte hareket kanıtı farklı takımları
gösteriyorsa `supported_turnover_candidate` kaydedilir; diğer durumlarda
`team_motion_change_only` kalır. Temel modelin kendi H/A tahminleri bu ek
doğrulamanın yerine geçmez. Takım hareketinin tepkisi gecikebileceğinden
olay karesi kesin top kazanma anı olarak kullanılmaz ve sahiplik sınırı buraya
geri taşınmaz. H/A etiketleri yeniden yazılmaz; uygun top kanıtının gerekçesi
takım değişimi desteğiyle açıklanır. D çıkarımı yapılmaz.

JSON'a `transition_parameters` eklenerek etkinleşir; `dribble_parameters`
de gereklidir. Zorunlu ayarlar: `window_s`, `vector_change_mps`,
`speed_change_mps`, `refractory_s`, `evidence_window_s`, `min_team_players`.
Seçilmiş futbol varsayılanı yoktur. Adaylar olay JSON'una, değişim büyüklükleri
ve ortak yuva sayıları `*-team-transitions.npz` dosyasına kaydedilir. Bütün
ayarlar ve yeni kaynak hash'i çalıştırma kaydına girer.

Bu hipotez pres, geri koşu veya oyunun durmasıyla da açıklanabilir. Dış maçta
gerçek sahiplik geçişlerine göre ayrıca ölçülmeden başarı iddiası yapılmaz.

## Ham ATD alanları

Tactical ve broadcast XML kanal şemaları:

| Alan | Tanım | Birim |
| --- | --- | --- |
| Kare kimliği | 1'den başlayan video kare numarası | 25 kayıt/saniye |
| Oyuncu `x` | `position_x` | Normalize saha koordinatı |
| Oyuncu `y` | `position_y` | Normalize saha koordinatı |
| Oyuncu `s` | `speed_kph` | km/saat |
| Top `x` | `position_x` | Normalize saha koordinatı |
| Top `y` | `position_y` | Normalize saha koordinatı |
| Top `s` | `speed_kph` | km/saat |

Tactical metadata'sında 46 oyuncu takip yuvası vardır. Ham satır:
`kare:oyuncu1_x,oyuncu1_y,oyuncu1_s;...:top_x,top_y,top_s`.
Eksik koordinatlar NaN olabilir. Takım, takip yuvası kimliği, saha boyutu ve
FPS ayrı XML metadata içindedir. Takip yuvası kalıcı kişi kimliği değildir.
Zaman saniyesi, `vx/vy`, ivme, temas ve pas ayrı ham sütunlar değildir;
hesaplanırlar. Yükseklik `z`, tespit güven skoru ve gerçek sahiplik etiketi
ham satırda yoktur.

Temel model yalnız x/y kullanır. Yeni katman hız vektörünü x/y'den türetir;
ham `s` henüz kullanılmaz. Ham `s` ile türetilen hızın uyumu ayrı dış veri
güvenilirlik deneyi gerektirir.

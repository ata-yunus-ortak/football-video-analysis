# Hareket, aday temas ve aday pas

4 Kasım 2026. Kullanıcının önerisi `development/motion_possession.py` içinde
ayrı sahiplik deneyi olarak uygulandı. D katmanı ve dondurulmuş temel model
değişmez. Sayısal futbol ayarları henüz seçilmemiştir.

## Karar sırası

1. Metre cinsinden ardışık x/y'den işaretli `vx`, `vy` hesaplanır (m/s).
   Ham `s` hız büyüklüğüdür (km/saat). `+5 -> 0 -> -5` bir hız bileşenine
   aittir; hız büyüklüğünün negatif olması gerekmez.
2. Hızlı uçuşta temel modelin salt yakınlık/önceki sahiplik kararı X'e çekilir.
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

## ATD alanları

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

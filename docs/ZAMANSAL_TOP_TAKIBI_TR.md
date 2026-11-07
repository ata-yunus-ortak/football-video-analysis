# Zamansal top adayı takibi

7 Kasım 2026. Deneysel piksel takibi: `development.ball_tracking`.
Barcelona görüntüsü/tracking'i bu geliştirmede kullanılmadı. Sayısal ayarlar
`ball-tracking-plan.json` içinde, dış kesit koşularından önce sabitlendi.
Bunlar sentetik mühendislik değerleridir; doğrulukla seçilmiş teslim modeli değildir.

## Çalışma

Bütün ham top adayları korunur. Takip için düşük güvenli adaylar kullanılmaz;
neredeyse aynı yerdeki yüksek örtüşmeli kutular ilişkilendirmede tek aday sayılır.
Bu elemenin nedenleri kaydedilir, ham kutular silinmez. Kaynak/kamera epoch'u
ile sınırlı birden fazla top adayı izi tutulabilir; oyundaki tek top seçilmez.

Bir sonraki aday, sabit hız öngörüsüne yakınlık, kutu boyutu değişimi ve tespit
güveni ile değerlendirilir. Eşleştirme karşılıklı en iyi aday ister. Yakın maliyetli
birden fazla çözüm varsa iz belirsiz sayılıp kapatılır; oyuncu/olay/takım veya
referans etiketi eşleştirmeye girmez. Piksel hareketi kamera hareketini de
içerebilir; fiziksel top hızı değildir. Pan/zoom telafisi henüz yoktur.

Üç tutarlı ölçümle onaylanan iz kısa kayıpta en fazla 0,2 saniye öngörü üretir.
Süre aşımında, kamera/çözünürlük/saat kopmasında ve görüntü dışına çıkan
öngörüde iz kapanır. Süre dolduktan sonra gelen aday eski kimliği canlandırmaz.
Kayıp kare dizisi standart proje dönüştürücüsünde ayrıca reddedilir; bağımsız
takip sınıfında saat boşluğu hareket geçmişini sıfırlar.

## Ölçüm ve tahmin

`frames.jsonl` içindeki ayrı `ball_tracking` alanı şu durumları taşır:

| Durum | Ölçülmüş konum | Tahmin konumu | Anlamı |
| --- | --- | --- | --- |
| `tentative` | Var | Yok | Tespit var, iz henüz onaylanmadı |
| `observed` | Var | Yok | Onaylanmış izde mevcut tespit |
| `predicted` | Yok | Var | Tespit yok; kısa süreli hareket modeli tahmini |
| `lost` / `ambiguous` | Yok | Yok | İz kapandı veya ilişki belirsiz |

Tahmin kaydında `measurement=false`, `detection_id=null` olur. Tahmin ham
nesne listesine eklenmez. Son gerçek tespitin güveni ayrı adlandırılır;
tahmine yeni dedektör güveni uydurulmaz. Hız `estimated_velocity_px_s`,
arama yarıçapı mühendislik kapısıdır; kalibre edilmiş belirsizlik aralığı değildir.
`selected_in_play_ball=false`, `fusion_eligible=false` ve sahiplik bilinmiyor kalır.

## Kullanma ve izleme

```powershell
python -m tools.match_analysis --vision-run C:/private/completed-vision-run --ball-tracking-config ball-tracking-plan.json --out C:/private/new-temporal-analysis
```

Aynı seçenek kayıtlı `--video ... --config ...` yolunda da çalışır. Ayar
verilmezse önceki ölçüm akışı korunur. Galeri `--project-analysis` ile yeni
çıktı köküne bağlanabilir.

Bu bilgisayarda `http://127.0.0.1:8774/`: sekiz dış kesit ve önceki kısa
örnek. “Top adayı izleri” düz çemberle ölçümü, sarıyla onaylanmamış izi,
pembe kesikli çemberle tahmini gösterir. Her top adayı kutusu aynı zamanda
ham çıktı olarak kalır. Birden fazla iz olması oyunda birden fazla top bulunduğu
veya oyundaki topun seçildiği anlamına gelmez.

## Kontrol ve sınırlar

161 testlik paket 1 isteğe bağlı AV atlamasıyla başarılı. Güven/konum seçimi,
kısa kayıptan dönüş, zaman aşımı, çift kutu, iki topun belirsiz geçişi,
kamera/çözünürlük/saat kopması ve görüntü sınırı kapsandı. Gerçek dış koşularda
tahminlerin hiçbirinin ölçüm/detection_id olarak yazılmadığı ayrıca denetlendi.

Önceden görülen üç kaynak maçtaki sekiz eğitim kesiti, iki modda 1.200 çıktı
karesi verir. Referanslar yalnız tahmin dosyaları hash'leri kaydedildikten sonraki
betimleyici ölçümde okundu. IoU ≥0,5 ile SAHI tarafında 525 referans kutusunun
248'i ilişkili ölçümle eşleşti, 229'u onaylı izdeydi; 830 ilişkili ölçüm referans
kutusuyla eşleşmedi. Referans bulunan anlardaki 216 tahmin gözleminin 27 merkezi
bir referans top kutusunun içindeydi. Bu gözlemler tekrarlıdır ve başka/yedek
top adaylarını da içerebilir; resmî metrik veya bağımsız test değildir. Etiket
bulunmayan anlar kesin negatif sayılmaz. Sonuçlar oyundaki topu güvenilir biçimde
seçtiğimizi göstermiyor; yanlış adaylar ve parçalanan izler hâlâ önemli sınırlardır.

Konum yakınlığını doğrudan sahipliğe çevirmiyoruz. Oyundaki top seçimi, daha uzun
bağımsız maçlarda kimlik/örtüşme değerlendirmesi ve kamera hareketi telafisi ayrı
geliştirmelerdir. Bu katman donmuş sahiplik modelini veya hibrit kabulünü değiştirmez.

Özel kayıt: `C:/Users/Abra/FootballPrivate/temporal-ball-development-20261107`.
`before-run.json`, `report.json`, `association-audit-v1`, `viewer-verification.json`
ve kesit/yöntem başına proje çıktıları. Ham videolar/tahminler Git dışında kalır.

## Kullanıcının istediği yerel Barcelona gösterimi

`tools.vision_local_demo --ball-tracking-plan ball-tracking-plan.json` mevcut
dış koşunun dedektör/ağırlık ayarlarını ve değişmemiş zamansal takip planını
yalnız yerel görüntüleme için kullanabilir. Daha önceki otomatik saat adayı
listesinin ilk yeterli aralığı deterministik seçilir; başarıya göre kesit aranmaz.
50 kaynak kare 5 kat yavaşlatılmış videoya çizilir. Tespitler/tahminler bellekte
işlenir; kare düzeyinde gözlem JSON'u, etiket veya doğruluk skoru yazılmaz.
Bu gösterimden ayar seçimi, eğitim veya performans iddiası yapılmaz.

Yerel sayfa: `http://127.0.0.1:8775/`. Yeşil çember gözlenen/onaylı izi,
sarı henüz onaylanmamış adayı, pembe kesikli çember kısa tahmini gösterir.
Tracking destekli aday seçimi, iki kamera birleştirmesi ve sahiplik bu gösterimde
etkin değildir. Tüm tespitler oyundaki top veya tanınmış futbolcu sayılmaz.
Görüntüler dış servise yüklenmez; doğrulama yalnız dosya/video yapısına ilişkindir.

Çıktı: `C:/Users/Abra/FootballPrivate/local-view-only-20261106/barcelona-temporal-demo-v2`.
Görüntüleme kodu değişikliği sonrası 178 test 1 isteğe bağlı AV atlamasıyla geçti.

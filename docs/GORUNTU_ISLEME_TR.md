# Görüntüden kişi/top adayları ve konum ölçümü

İlk yerel modül çalışıyor: RF-DETR Nano/Small tespit, isteğe bağlı SAHI
dilimleme ve ByteTrack kişi takibi. Modül doğrudan video piksellerini okur;
tespit kutusunu veya görüntüdeki konumu ATD'den almaz. Tespit motoru önceden
eğitilmiş açık kaynak modeldir; bizim sıfırdan eğittiğimiz model diye sunulmaz.

## Çıktı ve anlamı

- Her kaynak kare için video sunum zamanı, boyut/FPS ve bütün tespitler.
  Tespit yoksa boş kayıt da korunur; görüntü olmadığı varsayılarak doldurulmaz.
- Kişiler için kutu, güven puanı ve alt orta ayak noktası adayı; top için
  kutu ve merkez. Bütün top adayları saklanır; tek bir doğru top seçilmiş sayılmaz.
- Doğrulanan takiplerde `camera_epoch:track_id` anahtarı. Eksik/kararsız
  takip kimliği bilinmiyor kalır; aynı iz numarasının aynı karede iki tespitte
  görünmesi hız/kimlik kanıtı sayılmaz.
- Kesintisiz izde piksel hızı. Kaybolma, atlanan kare, görüntü boyut değişimi
  veya kamera kesmesi adayında bağ kesilir; eski nokta yeni kareye taşınmaz.
- Kaynağı ve hash'i aynı videoya bağlı homografi verilirse kişi ayak noktasının
  saha metre konumu ve hareketi için **düzlem izdüşümü adayı**. Geçersiz/eksik
  matris, kırpılmış ayak noktası ve ufuk dönüşümü eksik kalır.

Kişi sınıfı futbolcu anlamına gelmez: hakem, teknik ekip, yedek ve kenardaki
insanlar da görülebilir. Takım/rol ve kalıcı gerçek kişi kimliği atanmıyor.
Topun havada olup olmadığı bilinmediğinden top merkezi homografiyle kesin
zemin konumuna veya yüksekliğe çevrilmiyor.

`frame_evidence`, kişi/top aday sayısını, izlenen kişi sayısını, kamera
sürekliliğini ve izdüşüm durumunu saklar. Basit görüntü değişimi kontrolü yalnız
kesme adayıdır; canlı oyun/tekrar sınıflandırıcısı değildir. `frame_kind=unknown`,
`calibration_validated=false` ve `hybrid_ready=false` açıkça korunur. Bu
gözlemler bağımsız görünürlük kanıtının başlangıcıdır; hibrit katmanın bütün
kalite/kimlik/kalibrasyon koşullarını tek başına tamamlamaz.

## Çalıştırma

Önce mevcut ayrı `.venv-vision` ortamı ve kaydedilmiş Nano/Small ağırlığı
kullanılır. Donmuş numpy-only ana ortam değiştirilmez. Deney koşucusu
izinli dış veya sentetik video, kaynak açıklaması, video/ağırlık SHA-256'sı,
açık ayarlar ve yeni bir özel çıktı dizini ister:

```powershell
.\.venv-vision\Scripts\python -m tools.vision_experiment --video C:/private/other-match.mp4 --config C:/private/vision-config.json --out C:/private/vision-run-v2 --device cpu
.\.venv-vision\Scripts\python -m tools.vision_preview --observations C:/private/vision-run-v2 --out C:/private/vision-preview-v2 --slowdown 5 --credit "Dataset / author / license"
```

`vision-config.json`, mevcut `VisionConfig` parametreleri, `fixture`, `weights`,
`start_frame`, `max_frames`, `rationale` alanlarını taşır. İsteğe bağlı:

```json
{
  "scene_change_parameters": {
    "pixel_difference_threshold": 0.35,
    "changed_fraction_threshold": 0.6,
    "max_pair_gap_s": 0.08
  },
  "geometry": {
    "path": "C:/private/other-match-homography.csv",
    "sha256": "<dosyanın SHA-256 değeri>",
    "fixture_id": "<aynı dış maç/klip kimliği>",
    "source_video_sha256": "<aynı video SHA-256 değeri>",
    "pitch_m": [105.0, 68.0]
  }
}
```

Bu sayılar mühendislik örneğidir; seçilmiş futbol eşikleri değildir. Homografi
biçimi sıfır tabanlı kare ve normalize saha → görüntü pikseli 3×3 matristir;
modül tersini ve saha ölçeğini uygular. Video/lens koordinatları da bu matrisle
uyumlu olmalı. Bozuk/lens etkisi giderilmemiş geniş açı için tek bir düzlem
matrisinin tüm sahayı doğru kalibre ettiği varsayılmaz.

`observations.jsonl`, `registration.json` ve `summary.json` ölçüm dizinindedir.
Önizleme dizini `detections.mp4`, ilk kare JPG'si, kaynak hash'leri ve kodlama
kontrolünü içerir. `--slowdown 5`, yalnız gösterimi 5 kat yavaşlatır; ölçüm
zamanları ve kaynak kareleri değişmez, yeni tespit üretmez. İlk gösterim
etiketleri kalabalık görünürse kutu verisini değiştirmeden görsel etiketler
çakışmayı azaltacak şekilde seyrek yerleştirilir.

## 6 Kasım çalışma kontrolü

SoccerTrack 117092 eğitim klibinin önceden kaydedilmiş ilk 125 karesi, mevcut
byte-range önbelleğinden yeni ağ isteği olmadan çözüldü. Kaynak RGB hash'leri
kayıpsız kliple eşleşti; ilk 10 kare önceki kayıtla da eşleşti. Kaynak klibin
tamamı indirilmiş/hash-doğrulanmış sayılmaz. Tam referans/şema denetimi hâlâ
tamamlanmadığından doğruluk değerlendirmesi yapılmadı.

- Native: 125 karede 783 kişi adayı gözlemi, 0 top adayı.
- SAHI: ilk 25 karede 1.418 kişi adayı gözlemi, 3 karede toplam 3 top adayı.
- Sayılar karelerde tekrarlanan tespitlerdir; farklı kişi sayısı veya doğru
  tespit sayısı değildir. Özellikle kenardaki insanlar ve yedek toplar da
  aday olabilir; oyundaki top/oyuncu seçimi henüz doğrulanmadı.
- Dış klibe saha homografisi sağlanmadı; gerçek saha metre koordinatı
  uydurulmadı. İzdüşüm matematiği sentetik matrislerle sınandı.
- CPU'da çalıştı; 25 FPS veya gerçek zamanlı çalışma iddiası yok. Model yükü
  dahil eşzamanlı koşu süreleri native yaklaşık 79 sn, SAHI yaklaşık 196 sn;
  bunlar temsil edici performans benchmark'ı değildir.
- 126 test geçti; kamera kesmesi, kayıp iz, eksik kare, yanlış kaynak
  homografisi, havadaki/belirsiz top ve kırpılmış nokta durumları kapsandı.

Bu, sağlanan yarışma maçında model/eşik seçimi değildir. Mevcut donmuş
sahiplik modeli ve hibrit güven koşulları değiştirilmedi. Sonraki geliştirme
on-pitch oyuncu/rol/takım ayrımı, oyundaki topun zamansal seçimi, bağımsız
kalibrasyon ve başka maçlarda ölçülen doğruluktur.

Kaynaklar: [RF-DETR kodu](https://github.com/roboflow/rf-detr),
[Nano/Small Apache-2.0 lisansı](https://roboflow.com/model-licenses/rf-detr),
[SoccerTrack v2 / AtomScott](https://github.com/AtomScott/SoccerTrack-v2),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Örnek videolar SoccerTrack v2 kaynağından türetilmiş otomatik kutu/yavaşlatılmış
gösterimidir; orijinal kaynak ve lisans önizleme kaydında/altyazısında belirtilir.
Ham veri ve ağırlıklar kaynak deposunda yeniden dağıtılmaz.

## Kullanıcının istediği yerel izleme gösterimi

6 Kasım'da kullanıcı geliştirme değil, mevcut çıktıyı görmek istediğini açıkladı.
`tools.vision_local_demo` tamamlanmış izinli dış koşunun aynı kaynak hash'lerini,
ağırlığını ve ayarlarını kullanarak yalnız yerel bir gösterim üretir. Otomatik
eşleştirmedeki ilk uygun kesitten 50 kare seçilir; gösterim 5 kat yavaştır.
Yarışma görüntüsü sohbete yüklenmez; çıktı özel yerel klasördedir. Bu işlem
eğitim, insan etiketi, doğruluk değerlendirmesi veya eşik/model seçimi değildir.
Deney ve dış veri önizleme araçlarının kaynak kısıtları korunur. Donmuş model
değişmez. Gösterim dosyasının tamamlanması, tespitlerin doğru olduğu anlamına
gelmez; kişi ve top kutuları mevcut modelin aday tahminleridir.

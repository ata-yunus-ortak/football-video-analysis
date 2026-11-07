# Ölçülmüş sahiplik sistemi geliştirme — 7 Kasım 2026

Amaç: izinli dış maçlarda ölçülerek seçilen, yeniden üretilebilir H/A/D/X
sistemi. Kazanma veya kusursuz doğruluk garantisi değildir. Dondurulmuş
`model.json` ve `clean_model/` korunur. Çalışma dalı:
`feature/external-possession-selection`.

## Öncelikli organizatör açıklaması

3 Kasım 2026 12:23 UTC tarihli “Clarification of the rules for the Initial
Challenge” e-postası, önceki belgeler/yanıtların üzerinde olduğunu açıkça
belirtiyor. 7 Kasım'da yeniden okundu. Çıktıyı sağlanan videoyla karşılaştırmak,
sağlanan maçı elle etiketlemek, sağlanan veriyi AI hizmetlerine yüklemek ve
sağlanan video/gerçek sahiplik üzerinden eğitim/ayar yapmak yasak.
Otomatik çıkarımda video, tracking ve otomatik tag kullanmak; dış verilerde
eğitim/ayar yapmak mümkün. Lisans ve erişilebilirlik ayrıca kontrol edilir.

Bu açıklama, önceki yerel çizimli Barcelona gösterimlerinin “yalnız görmek”
gerekçesiyle koşulsuz uygun sayılmasını desteklemiyor. Önceki üretim kayıtları
silinmedi veya yeniden yazılmadı. 8776/8777 karşılaştırma sunucuları kapatıldı;
bu çıktılar seçim/doğrulama girdisi değildir. İleride sağlanan maçta yalnız
dondurulmuş otomatik çıkarım ve yapısal kontroller yapılacak. Organizatör
koşullarının tamamlandığı iddia edilmez. Yeni bir e-posta gönderilmedi.

## İş sırası ve kabul koşulları

1. **Sahiplik sürekliliği:** Dış maçlarda kontrol kanıtını zaman içinde
   biriktiren takım simetrili model; eski model ve zamansız karşılaştırma.
   12 eğitim / 4 doğrulama ayrımı korunur. Daha önce erişilmiş maçlar yeni
   test diye sunulmaz. Model ve ayarlar sonuçlara bakmadan kayda alınır.
2. **Ek dış kontrol:** Seçilen aday sabitlenir; seçim dışında kalan, eski temel
   model için daha önce erişilmiş dört maçta tekrar kontrol edilir. Bütün
   tahminler değerlendirmeden önce dondurulur. Bu kontrol sonrası bu aday
   değiştirilemez; bağımsız yeni test iddiası yapılmaz.
3. **Duran top:** Gerçek D/canlı oyun ve sınır hedefleri bulunan izinli dış
   kaynak edinilir. Eksik top veya sağlayıcının X değeri D değildir. Otomatik
   tag yalnız arama aralığı; ölçülmüş durma/yeniden başlama kanıtı ayrı.
4. **Görüntü ve iki kamera:** Gerçek dış görüntülerde top/oyuncu, kimlik,
   zaman, kalibrasyon ve canlı/tekrar ayrımı ölçülür. Zaman katmanı aynı
   arayüzle görüntü kanıtı tüketebilir; tracking deneyi görüntü başarısı
   yerine geçirilmez. Taktik öncelikli, doğrulanmış yayın tamamlayıcıdır.
5. **Birleşik aday:** Bileşen açık/kapalı karşılaştırmaları, kaynak/lisans
   manifesti, veri ayrımı, hata analizi, deterministik çalıştırma ve teknik
   rapor. Dış başarıyla seçilir; sağlanan maç çıktısıyla yeniden ayarlanmaz.
6. **Teslim hazırlığı:** Kaynak ve bağımlılıklar sabitlenir, tam maç CSV
   otomatik üretilir; satır/saat/etiket ve tekrar üretim kontrol edilir.
   Kod ve özet rapor GitHub'a; maç verisi/ara kareler/çıktı görüntüleri yerelde.

## İlk deneyin sınırı

`sequence-selection-plan.json` ve `tools.sequence_selection`, yalnız
SkillCorner dış maçlarını kullanır. Otomatik sağlayıcı sahipliği bir proxy'dir;
bağımsız insan doğruluğu veya yarışmanın özel gerçek etiketleri değildir.
Yeni modelin bu çalışması tracking tabanlıdır. Kullanıcının istediği görüntü
temelli karar yolu ayrı kalır; onun doğrulandığı söylenmez.

İki takımın mesafe/yakınlık kanıtı simetriktir; isteğe bağlı göreli oyuncu-top
hızı kanıtı azaltır. Dinamik program, kanıt toplamını ve gereksiz sahiplik
değişimlerinin maliyetini birlikte değerlendirir. Hızlı bir rakip yakınlığı
tek başına değişim olmak zorunda değildir. Devre/kare kopmasında sıfırlanır.
Eksik gözlemde yeni top konumu üretilmez; bilinmeyen kare X kalır.

Değerlendirmede bilinmeyen sağlayıcı hedefi sınırları korunur. Tahmin X'leri
yalnız bilinen hedef bloklarının içinde önceki cevapla doldurularak ikinci
bir bölüm metriği hesaplanır. Eski proxy de ayrıca raporlanır. Bu protokol
resmî yarışma skoru olarak adlandırılmaz; D hedefi yoktur.

Çalıştırma:

```powershell
python -m tools.sequence_selection --local-plan /external/local-plan.json --out /private/new-study
python -m tools.sequence_recheck --candidate /private/new-study/result.json --source-root /external/previous-fresh-check --out /private/new-recheck
python -m unittest discover -s tests -v
```

Kaynaklar: [yarışma kuralları](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/RULES.md),
[sahiplik tanımı](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/CHALLENGE.md),
[SkillCorner](https://github.com/SkillCorner/opendata).
Öncelikli e-postanın hesabı/ileti kimliği özel kural denetim kaydındadır.

# Deney kaydı

## K005 — Kayıt düzeltmesi: Metrica vekil etiketlerinde eşzamanlı olayların sırası, 11 Kasım 2026

**Özet.** Yalnız raporlama amaçlı üç kayıt, duran top aralıklarının yaklaşık yarısını yitirmiş Metrica vekil
etiketleriyle puanlanmıştı: K003'ün tam boy provası, K003'ün slot / çift izleme ölçümü ve K004'ü başlatan
kaleci teşhisi. Hiçbir seçim, eşik, doğrulama ya da ayrılmış test etkilenmedi; sürüm değişmedi. Etiket
betiği düzeltildi, üç kayıt yeniden hesaplandı (`possession-label-order-correction.json`). İlk sayılar
`possession-rehearsal-results.json` ve `possession-v210-plan.json` içinde olduğu gibi duruyor.

**Nasıl bulundu.** K004'ün tam boy provasında, kaleci kimlikleri değiştirilmiş paket (deney ortamında
kuruldu) K003'ün A paketinden yüksek puan aldı; oysa içerikleri aynı. İki paketin etiket dosyaları 17.448
karede farklıydı ve hepsinde A paketi H/A, yeni paket D diyordu.

**Neden.** `metrica_labels.labels_from_events` olayları `Start Frame`'e göre varsayılan sıralamayla
diziyordu; bu sıralama *kararlı* değildir, yani aynı karede başlayan olayların sırası kütüphane sürümüne
bağlıdır. Metrica'nın olay dosyalarında bir duran top (`SET PIECE`) ile onu kullanan pas aynı karede başlar.
Betik, bir duruşun sonunu "sonraki `SET PIECE`" diye arar; pas öne geçerse duran top aralığı hiç
kaydedilmez ve o kareler H/A kalır. Deney ortamında (Python 3.13, pandas 3.0.5, numpy 2.5.3) varsayılan
sıralama dosya sırasını koruyor; sürümün Python 3.10 ortamında (pandas 2.1.4, numpy 1.26.4) korumuyor.

| maç | olay / aynı karede başlayan olay | Python 3.10 ortamı: D kare (pay) / sahiplik sayısı | dosya sırası (deney ortamı): D kare (pay) / sahiplik sayısı | farklı kare |
|---|---|---|---|---|
| MET1 | 1.745 / 622 | 33.311 (%23,0) / 369 | 47.605 (%32,8) / 379 | 14.294 |
| MET2 | 1.935 / 701 | 25.667 (%18,2) / 356 | 39.931 (%28,3) / 364 | 14.264 |
| MET3 | 3.620 / 1.894 | 17.309 (%12,0) / 397 | 34.090 (%23,7) / 404 | 16.781 |

**Etkilenmeyenler ve kanıtı.** v2.1'den v2.11'e bütün planlar, eşikler, doğrulama satırları ve ayrılmış
testler deney ortamında çalıştı. Kanıt: (1) ilk doğrulamayla birlikte saklanan sahiplik sayıları
(`possession-v2-results.json`: dört doğrulama maçının ortalaması 403,25, ayrılmış maç 3 için 404) yalnız
dosya sırasındaki etiketlerle tutuyor (ortalama 403,25 ve 404); Python 3.10 etiketleriyle 398,75 ve 397
olurdu. (2) Doğrulama modelleri scikit-learn nesneleridir ve scikit-learn yalnız deney ortamında kurulu.
(3) Metrica satırı içeren bütün sonuç dosyalarında macroF1 0,78-0,85 düzeyinde; bozuk etiketlerle aynı
sistem 0,70-0,75 alıyor. (4) Bugünkü iki doğrulama `/usr/bin/python3` (3.13) ile başlatıldı. Sürümün
modelleri hiç Metrica etiketiyle eğitilmedi.

**Düzeltme.** Betik artık `kind='stable'` ile sıralıyor; iki ortam da deney ortamının öteden beri verdiği
etiketleri veriyor (maç başına SHA-256 düzeltme dosyasında).

*1. K003 tam boy provası (aynı çıktı dosyaları, dosya sırasındaki etiketlerle yeniden puanlandı):*

| çıktı | ilk yazılan spellF1 / macroF1 | düzeltilmiş | D için F1 |
|---|---|---|---|
| paket A, teslim dosyası (v2.9 zinciri) | 0,7151 / 0,7370 | 0,7631 / 0,8728 | 0,544 → 0,827 |
| paket A, bellek içi başvuru (paketleme ve yayın yok) | 0,6955 / 0,7338 | 0,7442 / 0,8694 | 0,543 → 0,826 |
| paket A, yalnız taktik kamera (dosyadan) | 0,6953 / 0,7343 | 0,7441 / 0,8700 | 0,544 → 0,827 |
| paket A, yedek zincir (v2.9g) | 0,7107 / 0,7341 | 0,7584 / 0,8706 | 0,537 → 0,823 |
| paket B, teslim dosyası (v2.9 zinciri) | 0,6861 / 0,7278 | 0,7322 / 0,8623 | 0,538 → 0,820 |
| paket B, bellek içi başvuru | 0,6634 / 0,7262 | 0,7093 / 0,8585 | 0,542 → 0,817 |
| paket B, yalnız taktik kamera (dosyadan) | 0,6641 / 0,7262 | 0,7100 / 0,8583 | 0,542 → 0,817 |

Organizatörün `run_evaluation.py` betiği düzeltilmiş etiketlerle A için 0,763100 / 0,872779, B için
0,732246 / 0,862326 veriyor; bizim puanlayıcımızla aynı. Olumsuz denetimler (A): takımlar değiştirilince
0,0074 (ilk yazılan 0,0045); satırlar 1 kare kayınca 0,7606 (0,7132); 1 sn kayınca 0,5707 / 0,5732
(0,5444 / 0,5404); 5 sn kayınca 0,2458 / 0,2381 (0,2380 / 0,2223). Paketleme etkisi (dosyadan yalnız
taktik − bellek içi): A −0,0001, B +0,0007; yayın doldurmanın etkisi: A +0,019, B +0,022.
Provanın amacı (bağlantı, sabit dal, boyut, süre, bellek) ve sonucu değişmedi; değişen, dış etiketlere
göre yazılan düzeylerdir.

*2. Slot / çift izleme ölçümü (MET1-3, aynı kopyalar, deney ortamında yeniden çalıştırıldı), ortalama spellF1:*

| düzen | ilk yazılan | fark | düzeltilmiş | fark | maç başına fark (MET1 / MET2 / MET3) |
|---|---|---|---|---|---|
| base: her oyuncu kendi sütununda (doğrulamalardaki düzen) | 0,6360 |  | 0,6845 |  |  |
| sticky: 46 slota paketli; kaybolan iz 1 sn içinde slotuna döner | 0,6360 | 0,0000 | 0,6845 | 0,0000 | 0,0000 / 0,0000 / 0,0000 |
| lru: paketli; iz slotuna hiç dönmez | 0,6338 | −0,0022 | 0,6824 | −0,0021 | −0,0046 / −0,0001 / −0,0016 |
| swap: paketli; yeni iz en son boşalan slotu alır | 0,6357 | −0,0003 | 0,6843 | −0,0002 | 0,0000 / −0,0013 / +0,0008 |
| dup1: çift izleme, prova paketindeki oranda | 0,6360 | 0,0000 | 0,6847 | +0,0002 | −0,0023 / 0,0000 / +0,0030 |
| dup5: çift izleme, beş katı | 0,6336 | −0,0024 | 0,6824 | −0,0021 | −0,0060 / −0,0020 / +0,0018 |

Düzeltilmiş ölçümde en büyük tekil değişim 0,0060, en büyük ortalama değişim 0,0021.

*3. Kaleci teşhisi (MET1-3, aynı kopyalar, deney ortamında yeniden çalıştırıldı), ortalama spellF1:*

| durum | ilk yazılan | fark | düzeltilmiş | fark |
|---|---|---|---|---|
| olduğu gibi | 0,6360 |  | 0,6845 |  |
| bir kaleci bütün maç yanlış kimlikle | 0,6147 | −0,021 | 0,6615 | −0,023 |
| iki kaleci bütün maç yanlış kimlikle | 0,3346 | −0,301 | 0,3671 | −0,317 |
| iki kaleci maçın %30'unda yanlış kimlikle | 0,6250 | −0,011 | 0,6708 | −0,014 |
| hakem izi, ev sahibi kimliğiyle | 0,6334 | −0,003 | 0,6804 | −0,004 |
| hakem izi, değişen kimlikle | 0,6357 | 0,000 | 0,6827 | −0,002 |

**Ne öğrendik.** "Aynı betik" iki ortamda aynı sonucu vermek zorunda değildir; etiket üreten kod da
çıktı üreten kod kadar ortamdan bağımsız olmalı. Bundan sonra dış etiketle puanlama yapan her kayıt,
çalıştığı Python / pandas / numpy sürümlerini yazar; vekil etiketlerin özeti (SHA-256) düzeltme dosyasındaki
değerle karşılaştırılabilir.

## K004 — Kaleci takım kimliği: teşhis, v2.10 (eşikleri geçti, yayımlanmadı), v2.11 (yeni sürüm), 11 Kasım 2026

**Özet.** Teslim sistemi artık **`possession-v2.11`** (`python -m possession.run211`): v2.9 + özelliklerden
önce çalışan bir kaleci takım denetimi (`possession/keeper2.py`). Teknik basamakların ikincisi v2.9'dur;
dondurulmuş v2.9 dosyalarının hiçbiri değişmedi. Sağlanan maçın hiçbir dosyası okunmadı; sağlanan takip
verisinde böyle bir hata olup olmadığı bilinmiyor ve bakılmadı. Bu girdideki bütün sayılar dış maçlarda,
bizim benzettiğimiz hatalarla ölçülmüştür; yarışma puanı değildir.

**1. Teşhis (ilk çalıştırma 13:04-13:33; yalnız raporlama, `experiments/possession_v2/stress_roles.py`).** DATA.md: "You
get positions and team membership, nothing more". Bir izin takımını izleyici belirler ve kaleci takımından
farklı forma giyer. Bozma modelimiz (`possession.degrade`) yalnız 1-6 sn'lik takım değişimleri içeriyordu.
Soru: kaleci izleri uzun süre yanlış takımın kimliğini taşısaydı dondurulmuş sürüm ne kaybederdi? Metrica
maçları 1-3, birer bozuk kopya (K003 slot ölçümünün kopyaları), dondurulmuş v2.9 mantığı, spellF1
(dosya sırasındaki vekil etiketlere göre yeniden çalıştırma, K005):

| durum | MET1 | MET2 | MET3 | ortalama | fark |
|---|---|---|---|---|---|
| bozulmuş kopya, olduğu gibi | 0,7096 | 0,6272 | 0,7167 | 0,6845 |  |
| ev sahibi kalecisi bütün maç deplasman kimliğiyle | 0,6765 | 0,6048 | 0,7032 | 0,6615 | −0,023 |
| iki kaleci de bütün maç öbür takımın kimliğiyle | 0,3555 | 0,3245 | 0,4214 | 0,3671 | −0,317 |
| iki kaleci, maçın %30'unda (30-300 sn'lik dilimler) öbür kimlikle | 0,7026 | 0,6100 | 0,6999 | 0,6708 | −0,014 |
| oyunu 8-18 m'den izleyen bir hakem izi, ev sahibi kimliğiyle | 0,7027 | 0,6091 | 0,7293 | 0,6804 | −0,004 |
| aynı iz, 20-120 sn'de bir değişen kimlikle | 0,7056 | 0,6282 | 0,7144 | 0,6827 | −0,002 |

*Not (K005):* ilk çalıştırma, Metrica vekil etiketlerinin duran top aralıklarının yaklaşık yarısını
yitirdiği Python 3.10 ortamında yapılmıştı. v2.10 planında (`diagnostic_spell_f1`) duran sayılar onlardır:
ortalama 0,6360; bir kaleci −0,021, iki kaleci −0,301, %30 −0,011, hakem
−0,003 / 0,000. Sonuç aynı; düzeyler farklı. Bu teşhis bir eşik değildi; iki doğrulama da doğru etiketlerle
yapıldı.

İki kaleci birden yanlışken çöküşün nedeni: `features.attack_dirs` her takımın hücum yönünü takımın
ortalama x konumundan çıkarıyor; iki kaleci yanlış kimlik altında bu ortalamayı ters çeviriyor. Dondurulmuş
dosya değiştirilemeyeceği için düzeltme, modellere verilen takip verisinin önüne konan ayrı bir adım oldu.
Hakem izi için bir şey eklenmedi (fark −0,004 ve −0,002).

**2. İlk aday, v2.10 (`possession/keeper.py`).** Kural: oyun öbür yarı sahadayken (bütün oyuncuların
medyan x'i kale çizgisinden en az 50 m) kaleye en yakın izlenen oyuncu kalecidir; böyle iz parçaları ve
onların zaman-yer olarak devamı olan parçalar, o kaleyi savunmayan takımın slotundaysa savunan takıma
aktarılır. Kural ve sabitleri dört DFL eğitim maçında, model çalıştırmadan, kaleci konumlarının kaçının
yanlış kimlik taşıdığı sayılarak geliştirildi; bir model denetimi eğitim maçı J03WOH'de yapıldı (örneklem
içi; iki kaleci yanlış 0,3251 → 0,7328, kimlikler doğru 0,7392 → 0,7392). Plan sonuçlardan önce kaydedildi
(`possession-v210-plan.json`, 13:54); 8 yeni bozuk kopya (J03WN1, J03WR9, MET1, MET2; tohumlar 10100-10131),
izler 46 adsız slota paketli, doğrulama modelleri. Sonuç (`possession-v210-results.json`, 14:36):

| koşul | v2.9 | v2.10 | fark | iyi/aynı/kötü kopya | yanlış kimlikli kaleci konumu, önce → sonra |
|---|---|---|---|---|---|
| kimlikler bozulduğu gibi (kaleciler doğru) | 0,6655 | 0,6655 | 0,0000 | 0/8/0 | %0,0 → %0,0 |
| bir kaleci bütün maç yanlış | 0,6270 | 0,6644 | +0,0374 | 8/0/0 | %50,1 → %1,0 |
| iki kaleci bütün maç yanlış | 0,3271 | 0,6634 | +0,3363 | 8/0/0 | %100,0 → %1,7 |
| iki kaleci maçın %30'unda yanlış | 0,6444 | 0,6644 | +0,0200 | 7/0/1 | %31,4 → %0,6 |

Dört eşik de geçti (G1 fark 0,0000, en kötü kopya 0,0000; G2 0,6634 ≥ 0,6505;
G3 0,6644 ≥ 0,6555 ve fark +0,0374 ≥ +0,008; G4 0,6644 ≥ 0,6555 ve fark +0,0200 ≥ 0).
Kayıtlı karar kuralına göre v2.10 sürüm olacaktı.

**3. Karardan sonra bulunan zayıflık; v2.10 neden yayımlanmadı.** Dondurmadan önce, kimlikler doğruyken
v2.10'un neyi taşıdığına bakıldı (`gk_none.py`, `gk_none_detail.py`; yalnız raporlama). 8 kopyada 80 parça:
77'si bozmanın 1-6 sn'liğine yanlış kimliğe koyduğu kalecilerdi (6.444 kare; doğru düzeltme). 3'ü saha
oyuncusuydu: J03WR9'un son 2,5 dakikasında rakip kaleden 13 m uzakta hareketsiz duran bir forvet (iki
kopyada da: 3.496 ve 1.571 kare; kaleci daha ileride duruyordu) ve MET1'de kalecinin izi kayıpken kaleden
26 m uzakta 15 sn bekleyen bir forvet (366 kare). Bu kopyalarda spellF1 değişmemişti. Ama neden önemli:
"oyun uzaktayken kaleye en yakın izlenen oyuncu" kanıtı, kaleci izlenmiyorsa yanlış kişiyi gösterir. Oyunu
izleyen bir kamera uzak kaleciyi hiç göstermeyebilir (DATA.md: puanlanan karelerde ortalama 20,5 izlenen
nesne; taktik homografi için devre arasında "the camera is not pointed at the pitch"). v2.10 planı bu
durumu kapsamıyordu. Eğitim maçlarında bir kamera penceresi benzetildi (`camera_view.py`: bütün
oyuncuların medyan x'inden belli bir uzaklığın ötesindeki oyuncular izlenmez; kalecinin görüntüde olduğu
kare payı ±50 m'de %80,9 / %86,7 / %89,9 / %84,8, ±42 m'de %62,1 / %65,1 / %71,2 / %67,2, ±35 m'de %40,2 / %40,6 / %46,5 / %45,1). Model çalıştırılmadan sayım
(`gk_far_dev.py`; dört eğitim maçı WOH / WOY / WPY / WQQ, birer bozuk kopya; v2.10 yalnız ilk ikisinde):

| görüş | v2.10: kimlikler doğruyken yanlış takıma aktarılan saha oyuncusu konumu | v2.11: aynısı | v2.11: iki kaleci yanlışken (%100) düzeltme sonrası yanlış kaleci konumu | v2.11: %30 yanlışken sonrası |
|---|---|---|---|---|
| bütün saha | 0 / 0 | 0 / 0 / 0 / 0 | %4,6 / %2,1 / %6,8 / %0,0 | %4,2 / %4,3 / %3,5 / %0,0 |
| ±50 m | 0 / 0 | 0 / 0 / 0 / 0 | %8,5 / %3,1 / %9,0 / %0,9 | %11,9 / %8,2 / %6,9 / %9,1 |
| ±42 m | 1.671 / 4.303 | 0 / 0 / 0 / 388 | %25,9 / %19,5 / %22,1 / %6,5 | %28,1 / %20,7 / %16,5 / %12,2 |
| ±35 m | 4.973 / 8.373 | 0 / 0 / 0 / 0 | %100,0 / %93,9 / %77,9 / %79,2 | %36,2 / %30,7 / %31,1 / %27,2 |

Bu yüzden v2.10 yayımlanmadı. Kayıtlı karar kuralından sapma temkinli yöndedir ve burada, planında
(`possession-v211-plan.json`, "background") ve teknik belgede yazılıdır; v2.10'un planı, sonuçları ve
`keeper.py` dosyası kayıt olarak depoda duruyor.

**4. İkinci aday, v2.11 (`possession/keeper2.py`).** İki değişiklik:
- *Yalıtım:* bir kare ancak parça kaleye ikinci en yakın izlenen oyuncudan en az 8 m daha yakınsa kanıt
  sayılır (eğitim maçlarında gerçek kaleci için bu, ilgili karelerin %96-99'unda doğru; bekleyen bir
  forvet çoğunlukla stoperlerin birkaç metre yakınındadır).
- *Kendi kanıtı yetmez:* öbür takımın kimliğini taşıyan bir parça yalnız iki durumda aktarılır. (a) O
  kalenin o yarıdaki kanıtının en az yarısı ve en az 2.500 karesi öbür kimlik altındaysa (kaleci bütün
  yarı boyunca yanlış etiketli). (b) Parça zaman ve yer olarak bir kaleci parçasının devamıysa (kaleci bir
  süreliğine yanlış etiketli). Eğitim maçlarında kimlikler doğruyken öbür kimlik altındaki kanıt hiçbir
  görüşte kale ve yarı başına 320 kareyi geçmedi; iki kaleci yanlışken bütün sahada ve ±50 m'de en az
  20.242, ±42 m'de en az 6.903, ±35 m'de 597-2.845 kareydi.

Plan, adayın doğrulama ya da ayrılmış maçlardaki hiçbir sonucundan önce kaydedildi (15:03). 8 yeni
kopya (tohumlar 11100-11131), aynı dört doğrulama maçı. Altı eşik: G1-G4 v2.10 planındaki eşiklerin aynısı;
G5 ve G6, kamera penceresi ±42 m ve ±35 m iken kimlikler doğruysa zarar vermeme eşiği (ortalama fark ≥
−0,002, hiçbir kopya −0,005'in altında değil). Sonuç (`possession-v211-results.json`, 16:08; eşikler bir
kez, bütün satırlara uygulandı):

| eşik | koşul | v2.9 | v2.11 | fark | iyi/aynı/kötü | yanlış kimlikli kaleci konumu, önce → sonra | yanlış takıma aktarılan saha oyuncusu konumu (en çok, kopya başına) |
|---|---|---|---|---|---|---|---|
| G1 | kimlikler bozulduğu gibi (kaleciler doğru) | 0,6594 | 0,6596 | +0,0002 | 3/5/0 | %0,0 → %0,0 | 0 |
| G2 | iki kaleci bütün maç yanlış | 0,3354 | 0,6565 | +0,3211 | 8/0/0 | %100,0 → %2,6 | 999 |
| G3 | bir kaleci bütün maç yanlış | 0,6274 | 0,6576 | +0,0302 | 8/0/0 | %50,0 → %1,5 | 567 |
| G4 | iki kaleci maçın %30'unda yanlış | 0,6417 | 0,6591 | +0,0174 | 8/0/0 | %31,8 → %2,1 | 0 |
| G5 | kamera penceresi ±42 m, kimlikler bozulduğu gibi | 0,6492 | 0,6492 | 0,0000 | 1/7/0 | %0,0 → %0,0 | 0 |
| G6 | kamera penceresi ±35 m, kimlikler bozulduğu gibi | 0,6464 | 0,6464 | 0,0000 | 0/8/0 | %0,0 → %0,0 | 0 |
| — | kamera penceresi ±42 m, iki kaleci yanlış (eşik değil) | 0,5570 | 0,6344 | +0,0774 | 8/0/0 | %100,0 → %27,4 | 1.299 |

Altı eşik de geçti. Kayıtlı karar kuralı: v2.11 sürüm olur, v2.9 bir alt basamak olarak kalır, v2.10
yayımlanmaz. Yanında raporlanan (eşik değil): v2.10 aynı kopyalarda ±42 m'de 0,6487 (v2.9'a göre
−0,0004), ±35 m'de 0,6452 (−0,0013; en kötü kopya −0,0044); kopya başına yanlış aktardığı saha
oyuncusu konumu en çok 5.434 ve 14.618.

*Ayrılmış Metrica maçı 3 (tohum 31103), karardan sonra bir kez, eşik değil:*

| koşul | v2.9 | v2.11 | v2.10 | yanlış kimlikli kaleci konumu, önce → sonra | yanlış aktarılan saha oyuncusu konumu |
|---|---|---|---|---|---|
| kimlikler bozulduğu gibi (kaleciler doğru) | 0,6962 | 0,6962 |  | %0,0 → %0,0 | 0 |
| bir kaleci bütün maç yanlış | 0,6856 | 0,6962 |  | %49,9 → %0,4 | 0 |
| iki kaleci bütün maç yanlış | 0,4024 | 0,6962 |  | %100,0 → %0,7 | 0 |
| iki kaleci maçın %30'unda yanlış | 0,6962 | 0,7003 |  | %30,8 → %1,9 | 0 |
| kamera penceresi ±42 m, kimlikler bozulduğu gibi | 0,7080 | 0,7080 | 0,7075 | %0,0 → %0,0 | 0 |
| kamera penceresi ±35 m, kimlikler bozulduğu gibi | 0,6980 | 0,6980 | 0,6980 | %0,0 → %0,0 | 0 |
| kamera penceresi ±42 m, iki kaleci yanlış (eşik değil) | 0,6660 | 0,6797 |  | %100,0 → %67,7 | 0 |

**5. Dondurma ve bağlantılar.**
- `possession-v211-release.json` (16:09): v2.9'un 18 dondurulmuş dosyası aynı özetlerle + `keeper2.py` +
  `run211.py`; iki model paketi aynı. Yedek giriş noktası `possession.run211g` (`possession-v211g-release.json`):
  yayımlanan başlama karesi olmadan.
- `possession-release.json` basamakları: v2.11 → v2.9 → v2.5c → v2.5c yalnız taktik. Yedek yapılandırma:
  v2.11g → v2.9g → v2.5b → v2.5b yalnız taktik. Bir alt basamak yalnız üstteki hata verirse kullanılır,
  bir çıktıya bakılarak değil.
- Son test planı (`possession-final-test-plan.json`) v2.11 için yeniden kaydedildi (16:09); ayrılmış maç
  J03WMX'e hâlâ hiç erişilmedi. Tasarım, kopyalar, tohumlar, benzeticiler ve beklentiler aynı; değişen:
  sınanan sürüm ve araç (giriş noktasını plandan okur, her kopyada denetimin ne taşıdığını yazar). İlk
  kayıt dosyada `registration_history` altında duruyor.
- Zincirin PLATFORM adımı artık yedi sentetik varyantı karşılaştırır: v2.9'un beş varyantı (kayıtlı
  değerler değişmedi) ve kaleci izleri öbür kimlikle yazılmış iki pakette `possession.run211`. Linux'ta
  Python 3.10 ve 3.12 (numpy 1.26.4) ile Python 3.13 (numpy 2.5.3) altında aynı baytlar.
- Ek R'ye bir satır eklendi: "Goalkeeper team correction" (bir şey taşındı / taşınmadı; sayı yok).
- Testler: sabitlenmiş Python 3.10 ortamında 411 test (15 atlandı), yalnız numpy kurulu ortamda 411 (102 atlandı); altı sürüm bildirimi (v2.11, v2.11g, v2.9, v2.9g, v2.5c, v2.5b) doğrulandı.
- Yükleme benzetimi (GitHub dal durumunun bir kopyasında, `GIT-YUKLE-V2.cmd` ile aynı git komutları): birinci
  commit 281 dosya, ikinci commit 9 dosya; aralarında veri türü dosya yok. Bu dalın taze klonunda altı sürüm
  bildirimi doğrulandı ve 411 test geçti (15 atlandı). Bunların hiçbiri Windows'ta henüz çalıştırılmadı.

**6. Tam boy prova (sentetik paketler, K003'teki gibi; bağlantı ve boyut denetimi, doğruluk ölçümü değil).**
Puanlar dosya sırasındaki vekil etiketlere göredir (K005); K003'ün A paketi satırı da yeniden puanlanmıştır
(ilk yazılan 0,7151 / 0,7370).
G1 = paket A, dört kalecinin (Metrica maçı 3 ve 2 parçaları) izleri taktik dosyada öbür takımın kimliğiyle;
G2 = aynı hata yayın dosyasında da.

| çalıştırma | spellF1 / macroF1 (dış etiketlere göre) | denetimin taşıdığı | süre / en yüksek bellek |
|---|---|---|---|
| paket A, v2.9 zinciri (K003) | 0,7631 / 0,8728 | — | 695 sn / 1,54 GB |
| paket A, `run211` | 0,7641 / 0,8728 | 4 parça / 375 kare | 270 sn / 1,53 GB |
| paket A, v2.11 zinciri (testler dahil) | 0,7641 / 0,8728 |  | 962 sn / 1,54 GB |
| paket G1, `run211` | 0,7664 / 0,8727 | 292 parça / 289.702 kare | 233 sn / 1,53 GB |
| paket G1, `run29` (denetimsiz) | 0,4314 / 0,7879 | — | 212 sn / 1,53 GB |
| paket G2, `run211` | 0,7669 / 0,8727 | 292 parça / 289.702 kare | 225 sn / 1,53 GB |
| paket G1, v2.11 zinciri (`--quick`) | 0,7664 / 0,8727 |  | 239 sn / 1,54 GB |
| paket A, yedek yapılandırma zinciri (v2.11g, `--quick`) | 0,7594 / 0,8706 |  | 244 sn / 1,54 GB |

Zincir sonuç satırları: A "TESLIM HAZIR", G1 "TESLIM HAZIR", yedek "TESLIM HAZIR".
Bütün adımlar OK / AYNI / ATLANDI.

**7. Ölçülen / ölçülmeyen.**
- *Ölçülen:* dış maçlarda, bizim benzettiğimiz kaleci kimliği hatalarında ve kamera penceresinde v2.11'in
  v2.9'a göre farkı (yukarıdaki tablolar); kimlikler doğruyken ortalama farkın +0,0002 olduğu.
- *Ölçülmeyen:* sağlanan maçta herhangi bir şey. Sağlanan takip verisinde kaleci kimliği hatası var mı,
  uzak kaleci izleniyor mu, bilinmiyor. Gerçek izleyicinin hataları bu benzetimlerden farklı olabilir.
- *Sınırlar:* uzak kaleci çoğunlukla görüntü dışındaysa (benzetimde ±35 m) yanlış kimlik düzeltilmez
  (yeterli kanıt yok; zarar da verilmez). Bütün maç süren hatalarda kaleciyle birlikte az sayıda saha
  oyuncusu konumu da aktarılabiliyor. Doğrulama maçları bu tasarım için taze değildi (v2.10 çözümlemesi
  aynı maçlarda yapıldı). Denetim yalnız taktik kamerayla doğrulandı; yayın yolu kimlikleri verildiği
  gibi kullanır.
- *Kayıt düzeltmesi yok:* v2.10'un planı ve sonuçları değiştirilmedi; hiçbir eşik gevşetilmedi. v2.11'in
  eşikleri v2.10'unkilerle aynı, artı iki ek eşik.

## K003 — Okuyucu denetimi, girdi öz-denetimi, tam boy prova, slot ve çift izleme ölçümü, yedek sürüm, son test planı, 11 Kasım 2026

> **Düzeltme (K005, 11 Kasım 2026).** Bu girdide dış etiketlere göre yazılan prova puanları ve slot / çift
> izleme ölçümü, duran top aralıklarının yarısını yitirmiş Metrica vekil etiketleriyle hesaplanmıştı. Düzeltilmiş
> sayılar K005 girdisinde ve `possession-label-order-correction.json` dosyasındadır. Aşağıdaki metin ilk hâliyle
> bırakılmıştır; zincirin adımları, süre, bellek ve bayt karşılaştırmaları etkilenmez.

**Neden.** Model tarafı dış doğrulamada bir platoda (son adayların farkı ±0,002). Kalan en büyük
risk, sürümün gerçek dosyalarda *doğru çalışmasıdır*: yarışma dosyalarının biçimi yalnız
belgelerden biliniyor, `(BAR-ATH, 199319)` sabit dalı ve gerçek dosya boyutu hiçbir testte
çalıştırılmamıştı. Bu girdide hiçbir model, eşik ya da parametre seçilmedi; dondurulmuş
dosyaların hiçbiri değişmedi (dört sürüm bildirimi yeniden doğrulandı). Sağlanan maçın hiçbir
dosyası okunmadı; kullanılan veri Metrica örnek maçları 1-3'tür.

**1. Okuyucu denetimi (yalnız kamuya açık kaynaklarla).**
- Organizatör deposu 09:34'te yeniden denetlendi: `f8f2629`'dan sonra commit yok.
- Organizatör ATD'yi kloppy 3.18.0 ile yüklüyor (`requirements-starter.txt`). Dondurulmuş
  `read_epts`, Metrica örnek maçı 3'te kloppy ile kare kare karşılaştırıldı (143.761 kare, 35 slot,
  11 biçim tanımı): eksik gözlem maskeleri aynı, en büyük konum farkı 1,2e-7 (normalize birim),
  takımlar ve kare numaraları aynı.
- `starter/baseline.py` dosyayı elle okur (i. grup = i. `Player` kaydı, ilk `Team` = ev sahibi,
  satır = `frame_id - 1`). Aynı mantıkla yazılmış bağımsız bir okuyucu ile `read_epts`, yarışma
  dosyasına benzetilmiş sentetik bir çiftte aynı sonucu veriyor. Kalıcı test:
  `tests/test_possession_reader_reference.py` (kloppy kuruluysa onunla da karşılaştırır).
- Dondurulmuş çıkarım kodunda Windows / numpy 1.26 için boyuta bağlı int32 taşması adayı arandı;
  bulunmadı (kod okuması; Windows'ta çalıştırma yok).

**2. Girdi öz-denetimi: `possession/inputs_check.py`, zincirde `GIRDI OKUMA` adımı.** 26 denetim;
ekrana yalnız PASS / FAIL / SKIP ve denetimin adı yazılır, değer yazılmaz.
- *DATA.md olguları:* kayıt ve slot sayıları, toplu kare sayıları (toplam ve puanlanan
  karelerde), puanlanan karelerde ortalama izlenen nesne sayısı, yayın topu payı, kullanılabilir
  homografi payı, ilk takımın adı. Sürümün kendi okuyucularının döndürdüğü değerlerle
  karşılaştırılır.
- *Sözdizimi (sürüm okuyucusu kullanılmadan):* her satır üç `:` parçası mı, grup sayısı `Player`
  kaydı sayısına eşit mi, bütün değerler sayı ya da NaN mı, kare numaraları 1'den ardışık mı.
- *İkinci okuma:* iki takip dosyası `starter/baseline.py` mantığıyla satır satır yeniden okunur ve
  sürüm okuyucusuyla kare kare karşılaştırılır (top var mı, topun yeri, takım başına izlenen slot
  sayısı, topa en yakın izlenen oyuncunun takımı). Tutmazsa hangi yönün tutmadığı adın sonuna
  eklenir (`__team_counts` gibi); okuyucu hata verirse hata sınıfı (`__ValueError` gibi).
- FAIL bir model ya da eşik değişikliğine gerekçe değildir; bakılacak yer okuyucudur.
- Zincirin `SURUM` adımı başarısız olursa artık neyin değiştiğini de yazar (dondurulmuş dosyanın ya da
  paketin adı, eksik Python paketi). Bu denetim maç verisi okumadığı için iletisi veri taşıyamaz;
  başka her adımda yalnız hata sınıfı ve kod satırı yazılmaya devam eder.
- Sınır: gerçek dosyada kloppy ile doğrudan karşılaştırma yapılmıyor (kloppy bu deponun
  bağımlılığı değil). Denetimler DATA.md'nin yayımladığı toplu olgulara ve organizatörün başlangıç
  kodunun okuma biçimine dayanır.

**3. Tam boy prova (10:12-11:14).** Sağlanan dosyaların adlarını, kayıt ve slot sayılarını taşıyan
sentetik iki paket kuruldu (`experiments/possession_v2/prova_build.py`): 199.319 taktik kayıt, 46
adsız slot ("Track 1".."Track 46"), Metrica EPTS düzeni; 164.488 kayıtlı yayın akışı, 51 slot,
homografi geçerlilik dosyası; iki kayıt için benzetilmiş saat okumaları. İçerik: Metrica maçı
3'ün iki yarısı, puanlanan pencereleri doldurmak için sonuna maç 2'den parçalar; oyun dışı
bölümler (maç öncesi, devre arası, ikinci yarı başlamadan önceki 2.934 kare, maç sonrası)
uydurma. Takip verisi `possession.degrade` ile bozuldu, az sayıda çift izleme eklendi, izler 46
slota paketlendi. Toplu özellikler DATA.md'deki sayılara getirildi (puanlanan karelerde top
94.214, toplam 113.488; ortalama izlenen nesne 20,5; yayında geçerli homografi %65,8, top %50,5).

| | paket A (bozma eğitim aralığında, doğru yayın) | paket B (oyuncu gürültüsü 0,45 m, yayın kalibrasyon hatası büyük) |
|---|---|---|
| zincir | bütün adımlar OK, `SONUC: TESLIM HAZIR` | bütün adımlar OK, `SONUC: TESLIM HAZIR` |
| süre / en yüksek bellek | 695 sn (testler dahil) / 1,54 GB | 666 sn (testsiz) / 1,55 GB |
| ölçülen gürültü (top / oyuncu), verilen | 0,154 / 0,120 m; 0,15 / 0,12 | 0,286 / 0,450 m; 0,28 / 0,45 |
| gürültü kapısının seçtiği yol | v2.1 | v2.3 |
| yayın hizalama gecikmeleri | 8251-8252 ve 26459-26460 kare (kurulan: 8251, 26459) | aynı |
| doğruluk kapısı (eşik 0,50 m) | 0,222 m, açık | 0,485 m, açık |
| saatli / saatsiz, ikinci üretim | aynı baytlar | aynı baytlar |
| teslim dosyası, dış etiketlerle spellF1 / macroF1 | 0,7151 / 0,7370 | 0,6861 / 0,7278 |
| yalnız taktik kamera (`run25c`), aynı dosyalar | 0,6953 | 0,6641 |
| aynı içerik, çift izleme ve paketleme öncesi, bellekte | 0,6955 | 0,6634 |

- Organizatörün kendi puanlayıcısı (`evaluation/run_evaluation.py`, sentetik tam boy etiket
  dosyasıyla) iki teslim dosyasına da bizim puanlayıcımızla aynı puanı verdi: paket A spellF1
  0,715136, macroF1 0,736991; paket B 0,686076, 0,727793.
- Olumsuz denetim (paket A): takımlar değiştirilince spellF1 0,0045; satırlar 1 saniye kaydırılınca
  0,54; 5 saniye kaydırılınca 0,23; tek kare kaydırılınca 0,7132. Yani bu puan, takım yönü ve kare
  indeksi yanlış olsaydı elde edilemezdi.
- Paketleme (46 slot, çift izler, dosyaya yazıp okuma) puanı değiştirmedi: A'da −0,0002, B'de
  +0,0007. Yayın topu A'da +0,020, B'de +0,022 kazandırdı.
- Girdi öz-denetimi iki pakette de bütün denetimleri geçti (tam boyda 24 sn, 1,55 GB).
- Tek üretim bu 2 çekirdekli ortamda yaklaşık 3,3 dakika, yalnız taktik kamerayla 72 sn sürdü.
- Toplu sonuç dosyası: `possession-rehearsal-results.json`.

**4. Slot kimliği ve çift izleme ölçümü (yalnız raporlama).** DATA.md iki özelliği belgeliyor:
slotlar kimlik değiştirir, izleyici bazen bir oyuncuyu iki kez izler. Eğitim ve doğrulama
bozması ikisini de içermiyordu. Tasarım sonuçtan önce betiğin başına yazıldı
(`experiments/possession_v2/stress_slots.py`): Metrica maçları 1-3, maç başına bir bozuk kopya
(tohum 8101-8103, yeni), dondurulmuş sürüm mantığı, spellF1.

| değişke | MET1 | MET2 | MET3 | ortalama | temele göre |
|---|---|---|---|---|---|
| temel (oyuncu başına bir sütun) | 0,6583 | 0,5846 | 0,6652 | 0,6360 | |
| 46 slot; 1 sn'den kısa kayıpta iz kendi slotuna döner | 0,6583 | 0,5846 | 0,6652 | 0,6360 | 0 |
| 46 slot; iz hiçbir zaman kendi slotuna dönmez | 0,6531 | 0,5846 | 0,6636 | 0,6338 | −0,0022 |
| 46 slot; yeni iz en son boşalan slota girer | 0,6578 | 0,5834 | 0,6659 | 0,6357 | −0,0003 |
| çift izler, izlenen konumların %0,6'sı | 0,6554 | 0,5846 | 0,6681 | 0,6360 | 0 |
| çift izler, %2,9 | 0,6515 | 0,5810 | 0,6683 | 0,6336 | −0,0024 |

Hiçbir değişke model yolunu değiştirmedi. En büyük tek fark −0,0068. Sonuç: bu iki özellik,
benzetildiği biçimde, puanı anlamlı değiştirmiyor; bir düzeltme adımı eklenmedi. Sınır: maç başına
tek kopya; gerçek izleyicinin kimlik değiştirme ve çiftleme biçimi bilinmiyor.

**5. Yedek sürüm `possession-v2.9g` (`python -m possession.run29g`).** v2.9'un, FAQ.md'de
yayımlanan 113.742 başlama karesi kullanılmadan çalışan biçimi: oyun blokları yalnız puanlanan
pencerelerdir, modeller ikinci yarı penceresinin tamamında çalışır. Bildirim
`possession-v29g-release.json`, yapılandırma `possession-release-graded-windows.json` (basamaklar
v2.9g → v2.5b → v2.5b yalnız taktik kamera). Yalnız organizatör "sabit kullanılamaz" derse
kullanılacak; o zamana kadar teslim sistemi v2.9'dur. Provada (paket A) zincir bu yapılandırmayla
da sonuna kadar çalıştı (209 sn). Uydurma başlama öncesi bölümde 2.934 karenin 2.625'i `D`, 309'u
`H`/`A` etiketlendi; puanlanan pencerelerde spellF1 0,7107 (v2.9: 0,7151), oyun karelerinde aynı.
Bu bir ölçüm değildir: başlama öncesinde modellerin gerçek veride ne yapacağı dış veride
ölçülemez (dış takip verileri başlama vuruşuyla başlar).

**6. Organizatöre soru.** 11 Kasım 09:31'de yarışma adresine tek soru gönderildi: FAQ.md'de
yayımlanan ikinci yarı başlama karesini koda sabit yazmak kurallara uygun mu? 11:16 itibarıyla
yanıt yok.

**7. Ayrılmış maçta son test: plan kaydedildi, test ÇALIŞTIRILMADI.** DFL maçı J03WMX 7 Kasım'da
ayrılmıştı. Asistan bu maçın hiçbir dosyasını indirmedi ya da okumadı (bu bulut oturumu kaynağa
erişemiyor); proje kayıtlarına göre ekip bilgisayarında da indirilmedi ve ekibin dış veri
klasörünün 11 Kasım listesinde bu maça ait dosya yok.
`possession-final-test-plan.json` (geçerli kayıt 11:48:54) şunları sonuçtan önce kaydeder: dondurulmuş sürüm
(v2.9, bildirim karması), maçın iki dosyası, dört bozuk kopya (v2 tohum 9101, 9102; oyuncu
gürültülü 9501, 9502), kopya başına dört çalıştırma (yalnız taktik; benzetilmiş iyi / orta / kötü
yayın, akış tohumu 79000, saat tohumu 89000 tabanlı), ölçüt, beklentiler ve karar kuralı: **yok**.
Sonuç ne olursa olsun aynen raporlanır, sürüm bu sonuca göre değiştirilmez. Tohumların daha önce
hiçbir plan, sonuç ya da betikte geçmediği arandı. Araç `tools/possession_final_test.py`
(Windows'ta `SON-TEST.cmd`): kayıtlı indirme ve dönüştürme işlevlerini kullanır
(`sportec_download.ranges`, `sportec_prepare.convert`), kopyaları sağlanan dosyaların düzeninde
yazar (`possession/epts_export.py`) ve sürümün gerçek giriş noktasını ayrı süreçte çalıştırır.
Sonuç dosyası varsa ikinci kez çalışmaz.
- Kod denetimi: araç, geliştirme maçı J03WN1'de bir kopya ve tek rejimle çalıştırıldı (temel
  mantık 0,227; yalnız taktik 0,684; iyi yayın 0,722). Bu maç sürümün eğitim kümesinde olduğu için
  sayılar bir doğruluk ölçümü değildir; yalnız aracın çalıştığını gösterir. Bu ilk denemede planın
  0. kopyasının tohumları (9101, 79000, 89000) kullanıldı; ardından provalara ayrı tohum verildi
  (+100000). Son testin kopyaları J03WMX ile bu tohumlardır ve hiçbiri henüz üretilmedi.
- Süre tahmini: bu ortamda kopya başına yaklaşık 13 dakika, dört kopya için yaklaşık 50 dakika;
  ayrıca indirme ve dönüştürme.
- Plan dosyası 11:30-11:49 arasında, araç son hâlini alırken beş kez yazıldı (araç karması, ifade
  düzeltmeleri, K002 doğrulama satırlarına dayanan beklenti aralıkları). Tasarım (kopyalar,
  tohumlar, rejimler, sistemler, ölçüt, karar kuralı) ilk yazımdan beri aynıdır; bu sürede maça
  hiçbir erişim olmadı. Planı yazan betik: `experiments/possession_v2/register_final_test.py`.

**Testler.** Tam takım Python 3.10 ve sabitlenmiş paketlerle: 399 test, 15 atlandı, hata yok.
Yalnız numpy kurulu ortamda (iş akışı dosyası değişmeden CI'ın göreceği durum): 399 test, 90
atlandı, hata yok.

**Ölçülen ve ölçülmeyen.**
- Ölçülen: sürümün, belgelenen biçimde ve gerçek boyutta yazılmış dosyalarda baştan sona
  çalıştığı; sabit dalın, başlama öncesi `D` yazımının, takım yönünün ve kare indeksinin doğru
  bağlandığı (dış etiketlere ve organizatör puanlayıcısına karşı); süre ve bellek gereksinimi.
- Ölçülmeyen: sağlanan dosyaların kendisi. Prova paketi DATA.md'nin yayımladığı toplu sayılara
  uyar, bilinmeyen ayrıntılara değil (örneğin paket A'da 188 kullanılamaz yayın aralığı var,
  DATA.md 122 diyor). Windows'ta hiçbir şey çalıştırılmadı. Prova puanları yarışma puanı değildir:
  içerik daha önce erişilmiş Metrica maçları, akışlar benzetimdir.
- Değişmeyen: v2.9'un dış doğrulama kanıtı (K002). Prova yeni bir doğruluk kanıtı değil, bağlantı
  ve boyut denetimidir.

## K002 — Kayıt denetimi düzeltmeleri, v2.9 doğrulamasının tamamlanması, teslim zinciri, 11 Kasım 2026

**Neden.** 11 Kasım sabahı yapılan kök neden denetiminde (yalnız okuma) asistanın kendi
kayıtlarında üç yanlış bulundu. Eski girdiler değiştirilmedi; düzeltmeler bu girdidedir.

1. **"16 yeni kopya" yanlıştı (P012, `possession-v29-plan.json`).** v2.9 doğrulamasındaki 16
   kopyanın 8'i (bozma tohumları 4100-4131) v2.6'nın taze doğrulama kopyalarıydı: bu kopyaların
   v2.4 puanları `possession-v26-results.json` ile `possession-v29-results.json` içinde birebir
   aynı. Tohumlar seçilirken önceki planlara bakılmamıştı. Diğer 8 kopya (4500 serisi) gerçekten
   ilk kez kullanılmıştı.
2. **K001 "beş başlık" diyordu.** SUBMISSION.md (satır 64-73) altı başlık ister. Eksik olan
   **eğitim verisi**: kullanılan her etiketli veri kümesi, kaynağı, kimin etiketlediği ve
   miktarı. OVERVIEW.md (satır 201-203) ayrıca eksik ve gürültülü takip verisinin nasıl ele
   alındığını ister.
3. **`DATA_SOURCES.md` DFL verisinin kaynağını "figshare" yazıyordu.** İndirilen kaynak
   HuggingFace aynası `pysport/idsse-data`, commit `a715a38` (`sportec-data-plan.json`).
4. Yöntem dersi: organizatör sayfaları için web özetine güvenildi. Özet bir kez eksik başlık
   listesi verdi, bir kez RULES.md'de bulunmayan bir cümle üretti. Artık organizatör deposunun
   yerel kopyası (`f8f2629`) ve satır numarası kullanılıyor.

**v2.9 doğrulamasının düzeltilmesi.** Plan `possession-v29-amendment-plan.json` (07:37:45, yeni
kopyalarda hiçbir sonuç yokken). Tekrar kullanılmış 8 kopya, hiçbir sistemin puanlanmadığı 8
kopyayla değiştirildi: aynı dört doğrulama maçı, v2.1 bozması, tohum 7100-7131; yayın akışı ve
saat tohumları da yeni. Değerlendirme kümesi bu 8 kopya ile 4500 serisinin 8 kopyasıdır. Dört
eşik değişmedi. "Biri bile kalırsa v2.9 geri çekilir, sürüm v2.5c olur" kuralı önceden yazıldı.
Bir kez çalıştırıldı (`experiments/possession_v2/exp_v29k.py`, `eval_v29k.py`).

| yayın | v2.4 | v2.5b | v2.9 | kapı açık (v2.5b / v2.9) | v2.9 yüksek / eşit / düşük |
|---|---|---|---|---|---|
| iyi | 0,6527 | 0,6857 | 0,6836 | 16 / 16 | 6 / 1 / 9 |
| orta | 0,6527 | 0,6527 | 0,6811 | 0 / 16 | 15 / 0 / 1 |
| kötü | 0,6527 | 0,6527 | 0,6527 | 0 / 0 | 0 / 16 / 0 |

Eşikler: orta ≥ +0,010 (ölçülen +0,0284), iyi ≥ −0,003 (−0,0021), kötü ≥ −0,003 (0), üç rejim
ortalaması ≥ +0,005 (+0,0088). Dördü de geçti. **Karar: v2.9 seçili sürüm olarak kalıyor.**
Sonuç `possession-v29-amendment-results.json`. İlk plan ve ilk sonuç dosyası değişmedi.

Yalnız bilgi için: 8 yeni kopyada tek başına iyi 0,6903 → 0,6876 (−0,0027), orta 0,6625 → 0,6852
(+0,0227), ortalama kazanç +0,0067. İlk 16 kopyalık sonuç: iyi −0,0020, orta +0,0310, ortalama
+0,0097.

Dürüst sınırlar:
- Düzeltme, ilk sonuçlar bilindikten sonra yazıldı. Seçimi yalnız doğrulayabilir ya da geri
  çekebilirdi; bağımsız bir ilk sınama değildir.
- İyi yayında eşik az farkla geçildi (−0,0021; sınır −0,003). Kopya başına fark −0,020 ile
  +0,011 arasında. Üç hesapta da ortalama −0,002 dolayında: yayın zaten doğruysa hizalama küçük
  bir bedel ödetiyor görünüyor. Nedeni araştırılmadı.
- Orta yayında bir kopyada (J03WR9, tohum 7111) kapı açıldı ve puan 0,0064 düştü. Kapının
  açılması her kopyada kazanç demek değil.
- Organizatöre göre tek maçta 0,04'ten küçük spellF1 farkları gürültüdür (EVALUATION.md).
  Yarışma maçında bu büyüklükteki bir fark iki yönde de görünmeyebilir.
- Akışlar benzetim; maçlar daha önce erişilmiş doğrulama maçları. Çalışma sürerken ara satırlar
  ilerleme denetimi için görüldü. Kopyalar, eşikler ve karar kuralı önceden kayıtlıydı; karar
  bütün satırlarla bir kez hesaplandı. Süreç kesintisiz tek parça çalıştı (07:38-08:26).

**Belgeler.** `TECHNICAL_DOCUMENT.md`: eğitim verisi bölümü (4), eksik ve gürültülü takip verisi
paragrafı, düzeltilmiş v2.9 kanıtı ve düzeltme notu, yeniden üretim bölümü (tek komut, elle
adımlar, neyin denetlendiği). `DATA_SOURCES.md`: doğru kaynak ve maç başına etiket sayıları
(856.677 kare: H 254.820, A 212.916, D 388.941; sağlayıcının `BallStatus` / `BallPossession`
bayrakları; ekip hiçbir kareyi elle etiketlemedi). `TECHNICAL_DOCUMENT_V2.md`, `README.md`,
`AGENTS.md`, `CLAUDE.md` ve `docs/SAHIPLIK_V2_TR.md` güncel sürümü ve komutları gösteriyor.

**Yeni araçlar.** Dondurulmuş dosyaların hiçbiri değişmedi; üç sürüm bildirimindeki karmalar
yeniden doğrulandı.
- `tools/possession_deliver.py` ve `TESLIM-HAZIRLA.cmd`: yerel zincirin tamamı tek adımda.
  Programların çıktısı özel bir log dosyasına gider; ekrana yalnız durum sözcükleri yazılır
  (OK, FAIL, AYNI, FARKLI, ATLANDI). Hata olursa yalnız hata sınıfı ve kod satırı yazılır, ileti
  yazılmaz. `possession-release.json` sürümü ve teknik yedek basamakları adlandırır (v2.9 →
  v2.5c → v2.5c yalnız taktik kamera). Alt basamağa yalnız üst basamak hata verirse geçilir;
  çıktıya bakılarak geçilmez. Zincir dosyayı ikinci kez üretir, saatsiz üretimle karşılaştırır,
  GitHub'daki dalın taze kopyasından yeniden üretir ve teknik belgenin kopyasına bir çalışma
  kaydı (Ek R) ekler.
- `possession/public_check.py` ve `possession-final-check-plan.json` (07:40:51): açık 5 dakikada
  yalnız geçti/kaldı denetimi (dosya geçerli mi; spellF1 ≥ 0,20 ve macroF1 ≥ 0,50 mi; takımlar
  yer değiştirince puan artıyor mu). Puan yazmaz ve saklamaz. Kalırsa yalnız eşleme ya da
  indeks hatası aranır; model, eşik ya da sürüm değişmez.
- `tests/test_possession_crossplatform.py`: sentetik bir pakette beş çalıştırmanın (iki model
  yolu, yayınlı/yayınsız, saatli/saatsiz) çıktı karmaları Linux'ta Python 3.10/numpy 1.26.4 ve
  Python 3.13/numpy 2.5.3 altında aynı çıktı ve sabitlendi (Python 3.12/numpy 1.26.4 ile de
  aynı). Windows'ta aynı çıkıp çıkmadığı henüz bilinmiyor; teslim zincirinin PLATFORM satırı
  gösterecek.
- `tests/test_possession_release.py`, `tests/test_possession_public_check.py`,
  `tests/test_possession_deliver.py`. Tam test takımı Python 3.10 altında: 383 test, 14 atlandı.
  GitHub'a gidecek dosya kümesi, uzak dalın ağacı üzerine bindirilip taze bir kopyada da sınandı
  (Python 3.10 ve 3.12, sabitlenmiş paketlerle): aynı sonuç.
- CI ile ilgili iki bulgu. (1) `tests/test_possession_v25.py`, `_v26.py`, `_v27.py` ve
  `_plausibility.py`, scipy/pandas kurulu değilken atlanmak yerine hata veriyordu; yalnız
  `requirements.txt` kuran bir ortamda 6 hata çıkıyordu. Koruma eklendi: o ortamda artık 383
  test, 76 atlandı, hata yok. (2) `.github/workflows/tests.yml` dosyasının güncel hali (pip
  satırında `-r requirements-possession.txt`) kullanıcının bilgisayarına hiç gitmemiş; aygıt
  köprüsü iş akışı dosyalarına yazmayı reddediyor. Bu satır elle eklenene kadar CI sahiplik
  testlerini atlar; yani CI'ın yeşil olması sahiplik hattının Windows'ta sınandığını
  göstermez.
- `experiments/possession_v2/`: deney betiklerinin değiştirilmemiş kopyaları. Plan
  dosyalarındaki `work/...` karmaları bu dosyalara karşılık gelir.
- `GIT-YUKLE-V2.cmd`: güncel dosya listesi, veri türü dosyalara karşı ikinci bir denetim ve
  yalnız çalışma kopyasında duran dış kaynaklı kontrol referansı araçları için ayrı bir commit.
- Doğrulama modelleri (`models_v2.pkl`, `stack_v2.pkl`, `models_v23.pkl`, `stack_v23.pkl`)
  depo dışına, `FootballPrivate\sportec-development-20261107\possession-validation-models`
  klasörüne yedeklendi (yalnız DFL açık verisinden türetilmiş).

**Ölçülen ve ölçülmeyen.** Ölçülen: dış maçların bozulmuş kopyalarında sağlayıcı etiketleriyle
uyum (yukarıdaki tablo), sentetik testlerin geçmesi, Linux'ta iki yorumlayıcıda bayt eşitliği.
Ölçülmeyen: yarışma maçındaki doğruluk; zincirin Windows'ta ve gerçek veride çalışması (bu
oturumda yalnız Linux'ta sentetik paketle denendi); `.cmd` dosyalarının Windows'ta çalışması
(burada çalıştırılamadı).

## P012 — Yayın topunun oyuncular üzerinden hizalanması (v2.9), seçildi, 11 Kasım 2026

Plan `possession-v29-plan.json` (01:05, puanlardan önce). Gerekçe: özellik (v2.7), çözücü ve
etiket alanı (v2.8) denemeleri kazanç vermedi; şimdiye kadar yalnız daha fazla top bilgisi işe
yaradı. v2.5 yayın topunu yalnız zaten doğruysa kullanıyor (ortanca fark en çok 0,50 m).

Yöntem (`possession/register.py`): zaman hizalamasından sonra, iki kameranın da gördüğü aynı
takımdan karşılıklı en yakın oyuncu çiftlerinin (3 m içinde) konum farkı yayın eşlemesinin o
karedeki kalibrasyon hatasını verir. Topa yakın oyuncular daha ağırlıklı alınır, 1 m'den sapan
eşleşmeler atılır, ±0,5 s ortanca alınır ve bu hata yayın topundan çıkarılır; top ±2 kare
yumuşatılır. Tahmin yapılamayan karelerde yayın topu kullanılmaz. Sonra v2.5'in doğruluk kapısı
ve doldurması değişmeden uygulanır. Kapı top konumlarına bakar; hizalama topu hiç kullanmadığı
için bağımsız bir denetim olarak kalır.

Sınama: 16 yeni kopya (tohum 4100 ve 4500 serileri) × 3 yayın kalitesi. Yayın benzetimi
zorlaştırıldı (`work/synth_broadcast3.py`): çekim başına uzamsal eğrilik (oyuncu ile topun hatası
aynı değil) ve oyuncuların gösteremeyeceği yalnız topa ait hata eklendi.

| yayın | v2.4 | v2.5b | v2.9 | kapı açık (v2.5b / v2.9) |
|---|---|---|---|---|
| iyi | 0,6474 | 0,6832 | 0,6812 | 16 / 16 |
| orta | 0,6474 | 0,6474 | 0,6784 | 0 / 16 |
| kötü | 0,6474 | 0,6474 | 0,6474 | 0 / 0 |

Kayıtlı dört eşik de geçti (orta ≥ +0,010: +0,031; iyi ≥ −0,003: −0,002; kötü ≥ −0,003: 0;
üç rejim ortalaması ≥ +0,005: +0,0097). Karar: seçildi. Sürüm `possession-v2.9`,
giriş `python -m possession.run29`, bildirim `possession-v29-release.json`; v2.5c'deki ikinci
yarı başlama vuruşu düzeltmesini de içerir (K001).

Dürüst sınırlar:
- İyi yayında v2.9, 16 kopyanın 13'ünde v2.5b'nin biraz altında (ortalama −0,002), oysa yayın
  topunun gerçek hatası 0,19 m'den 0,10 m'ye düştü. Nedeni araştırılmadı.
- Yayın akışları benzetim; benzetimi ve yöntemi aynı ekip tasarladı. Oyuncu ve topun hatayı
  büyük ölçüde paylaştığı varsayımı benzetimde de var. Gerçek yayında havadaki topun paralaksı
  ve kalabalıkta yanlış oyuncu eşleşmesi farklı davranabilir. Koruma, çalışma anındaki kapıdır.
- Plan öncesinde bir mekanik duman testi yapıldı (MET1, tohum 5/77; yalnız top hatası ve kapı
  durumu, sahiplik puanı yok). Bir süreç bellek sınırında durdu ve kayıtlı satırlardan devam etti.
- Yarışma maçında kapının açılıp açılmayacağı bilinmiyor; değerine bakılmadı.

## K001 — Kural ve açıklama denetimi; ikinci yarı başlama vuruşu düzeltmesi (v2.5c), 11 Kasım 2026

Organizatörün RULES, SUBMISSION, FAQ ve DATA sayfaları 11 Kasım'da yeniden okundu ve depo
bunlara karşı denetlendi.

- **Gözden kaçmış bilgi (FAQ):** "ikinci yarı 110.808. kareden puanlanır ama başlama vuruşu
  113.742'dedir; bu 2.934 kare puanlanır ve hepsi `D`'dir." v2.5b ikinci yarıyı 110.808'den
  oyun olarak işliyordu; modeller ise yalnız başlama vuruşuyla başlayan yarılarla eğitildi.
  `possession/run25c.py` ikinci yarı oyun bloğunu yayımlanan kareden başlatır; önceki kareler
  oyun dışı sayılıp `D` yazılır. Dondurulmuş dosyalar değişmedi; sürüm bildirimi
  `possession-v25c-release.json`, testler `tests/test_possession_v25c.py`.
  Sınır: etkisi dış maçlarda ölçülemez (dış takip verisi başlama vuruşuyla başlıyor). Dayanak
  yalnız organizatörün açıklamasıdır; maç videosundan, doğru etiket dosyasından ya da açık
  pencereden türetilmedi. Bu kare, puanlanan aralıklar gibi yayımlanmış bir maç sabitidir.
- **Teknik belge:** organizatör "en fazla birkaç sayfa" ve beş başlık istiyor (yaklaşım ve
  gerekçe; kullanılan ve bırakılan kaynaklar; serbest top, mücadele ve yeniden başlama
  kuralları; sınırlar; yeniden üretim). `TECHNICAL_DOCUMENT_V2.md` 500 satırdı. Bu başlıkları
  doğrudan karşılayan kısa `TECHNICAL_DOCUMENT.md` yazıldı; uzun belge ek olarak kaldı.
- **Veri ve lisans kaydı:** sahiplik sisteminin kullandığı veri, model ve araçlar
  `DATA_SOURCES.md` içinde toplandı. Metrica örnek verisinin lisans dosyası yok; README
  "sorumlu kullanın, kaynak gösterin" diyor.
- **Depo içeriği:** veri, video, kare düzeyi çıktı yok; yalnız iki model dosyası var.
- **Doğrulanamayanlar:** deponun herkese açık olup olmadığı ve dalın güncelliği bu oturumdan
  görülemiyor (uzak dal 10 Kasım'da hâlâ d38df58'deydi). Önceki süreçteki sağlayıcı tarafı
  silme işlemi doğrulanmış değil (`REMEDIATION.md`). Takım en az 3 kişi olmalı (RULES).

## P011 — Eğitime Metrica etiketli maç eklemek (v2.8), seçilmedi, 11 Kasım 2026

Plan `possession-v28-plan.json` (10 Kasım 21:00, sonuçlardan önce). Düşünce: yarışma
etiketlerini Metrica hazırlıyor; Metrica örnek maçlarının etiket mantığı DFL'den farklı; eğitime
bir Metrica maçı eklemek öbür Metrica maçındaki başarıyı artırabilir.

A aşaması (eski doğrulama kopyaları, tohum 101/102, çözücü sabit):
- Eğitimde görülmeyen Metrica maçı (4 kopya): 0,6158 → 0,6172 (+0,001). Eşik +0,005; geçmedi.
- DFL kopyaları: 0,6466 → 0,6325 (A çeşidi) ve 0,6357 (B çeşidi); 0,011–0,014 kayıp.

Karar: seçilmedi (`possession-v28-results.json`). B ve C aşamaları çalıştırılmadı; 7100 ve
7300/7500 serisi taze kopyalar v2.8 ile puanlanmadı. Yayımlanan modeller değişmedi; Metrica ile
eğitilmiş ağaç yayımlanmıyor.

Yorum ve sınır: tek bir Metrica maçı eklemek az veri; iki Metrica maçının olaylardan türetilen
etiketleri de birbirine, bu modelin gözünden, DFL etiketlerinden daha yakın çıkmadı. Bu, yarışma
etiketlerinin DFL'ye daha yakın olduğunu göstermez; yalnız bu yolun ölçülebilir kazanç
vermediğini gösterir.

## R002 — Gönderim öncesi akla yatkınlık denetimi (doğruluk ölçmez), 10 Kasım 2026

`possession/plausibility.py` üretilen `frame,label` dosyasından yedi toplu istatistik çıkarır
(oyun içi ölü top payı, dakikadaki sahiplik sayısı, ortanca sahiplik süresi, ev sahibinin
sahiplik payı, en uzun sahiplik, en uzun ölü top, oyun süresi) ve her birini geniş bir aralıkla
karşılaştırır. Komut satırı değerleri yazmaz; yalnız PASS/FAIL yazar. Böylece kullanıcı sonucu
paylaşırken yarışma maçına ait sayı paylaşmamış olur. `SAHIPLIK-V25-URET.cmd` bunu
doğrulamadan sonra çalıştırır.

Aralıklar yalnız dış maçlardan belirlendi (4 doğrulama maçı, tahmin ve sağlayıcı etiketleri):
tahminlerde ölü top payı 0,37–0,56, dakikada 2,7–3,9 sahiplik, ortanca 4,8–8,4 s, ev sahibi
payı 0,49–0,63, en uzun sahiplik 44–108 s, en uzun ölü top 127–232 s. Sağlayıcı etiketlerinde
0,28–0,52; 3,8–5,3; 3,1–4,9 s; 0,51–0,62; 60–130 s; 75–206 s. Denetim aralıkları bunlardan
bilerek geniş tutuldu (örneğin ölü top payı 0,15–0,70).

Sınırlar: Bu bir doğruluk ölçümü değildir ve model seçimi için kullanılamaz. FAIL çıktısı
yanlış dosya, bozuk okuma ya da ters takım gibi kaba hataları düşündürür; PASS çıktısı
etiketlerin doğru olduğunu göstermez. Dosya dondurulmuş sürüm listesinde değildir; çıktıyı
değiştirmez. Testler: `tests/test_possession_plausibility.py` (2 sentetik test).

## P010 — Kayıp topu köprüleyen özellikler (v2.7), seçilmedi; çözücü taraması ve kısa araya giriş tanısı, 10 Kasım 2026

Plan sonuçlardan önce kaydedildi (`possession-v27-plan.json`, 19:59). `possession/features3.py`
v2 sütunlarına 48 sütun ekler: top en çok 6 s kaybolduğunda son ve sonraki görülen konum
arasında doğrusal köprü kurulur, takımların bu köprülenmiş konuma uzaklığı ölçülür; ayrıca top
kaybolurken en yakın olan oyuncunun, top yeniden göründüğünde topa uzaklığı (ve tersi)
hesaplanır. Takip verisine hiçbir şey yazılmaz; bunlar yalnız özelliktir.

Sonuç (A aşaması, 8 eski doğrulama kopyası): v2.1 0,6312 → v2.7 0,6332 (+0,002; macroF1
0,8607 → 0,8606). Eşik +0,005 idi; geçmedi. Plan gereği B ve C aşamaları çalıştırılmadı,
7100 serisi taze kopyalar v2.7 ile hiç puanlanmadı. Karar: seçilmedi
(`possession-v27-results.json`).

Ardından yalnız raporlama amaçlı iki tanı yapıldı (seçim için kullanılmadı):
- Çözücü taraması: geçiş maliyeti 1,5–6 ve takım olasılığı sıcaklığı 0,7–2 aralığında 16 eski
  kopyada ortalama 0,633–0,644 arasında kaldı. Karar katmanında kayda değer bir kazanç yok.
- Kısa araya giriş tanısı (J03WN1|1100 ve J03WR9|1110): eşleşmeyen doğru sahipliklerin çoğu
  rakibin yaklaşık 1 saniyelik araya girişi (86 ve 62 tanesi öbür takım olarak etiketlenmiş,
  doğru takıma verilen ortalama olasılık yaklaşık 0,27) ve bunların böldüğü aynı takım
  parçaları (63 ve 31). Model bu anları yüksek güvenle kaçırıyor; bilgi olasılıklarda yok.

Yorum: Yalnız takip verisiyle çalışan sistemde özellik ve çözücü tarafı doygun görünüyor.
Kalan kazanç ya top temasını görüntüden ölçmekten (teslim tarihine yetişmez) ya da etiket
tanımını yarışmanın etiketleyicisine yaklaştırmaktan gelebilir (bkz. v2.8 planı).
Sınır: tanılar iki kopyaya dayanır ve DFL etiketleme biçimine özgü olabilir.

## R001 — Etiket karşılaştırma arayüzü ve kısa sahiplik bulgusu (yalnız raporlama), 10 Kasım 2026

Ekip, doğru etiketle tahminimizi alt alta görmek istedi. Dış doğrulama maçlarının videosu
yok; bu yüzden takip verisinden iki boyutlu bir tekrar hazırlandı. Araç yalnız sahibine
açık bir sayfa olarak yayımlandı ("Sahiplik İnceleme Masası"). Sayfada yalnız DFL J03WN1 ve
J03WR9 var (CC BY 4.0). Metrica örnek maçlarında yeniden paylaşım izni açık olmadığı için
onlar konmadı. Yarışma maçından hiçbir dosya okunmadı.

Her maç için v2.4 taze kopya setinden üç kopya kullanıldı: standart bozulma (tohum
1100/1110), ağır top hatası (1300/1310) ve ağır oyuncu gürültüsü (1500/1510). Kopyalar
`pre24.py` ile aynı tohum ve profillerle yeniden üretildi. Tahminler, gürültü kapısının
seçtiği yolun önbellekteki ikinci aşama olasılıklarından çözüldü. Her kopyanın spellF1 değeri
`possession-v24-results.json` ile karşılaştırıldı; fark 5e-5'ten küçük. Kendi spell
eşleştirmemiz resmi ortalamayı birebir verdi. Üretici betik oturumun çalışma klasöründe
(`work/review/build.py`); önbellekteki olasılıklara bağlı olduğu için depoya konmadı.

Yalnız raporlama amaçlı bulgu (standart kopyalar):
- J03WN1|1100: 500 doğru sahiplik, 365 tahmin. 161 doğru sahiplik hiçbir IoU eşiğinde
  eşleşmedi; bunların ortanca süresi 1,2 s, %68'i 2 s'den kısa. Karşılığı olmayan tahmin
  sayısı yalnız 26. Kare doğruluğu %94,4, spellF1 0,677.
- J03WR9|1110: eşleşmeyen 112 doğru sahiplik (ortanca 1,6 s, %58'i 2 s'den kısa), 41 fazla
  tahmin; spellF1 0,670.
- spellF1 kaybının en büyük kısmı kısa sahipliklerin kaçmasından geliyor (düşük duyarlılık).
  Fazla sahiplik üretmek daha küçük bir sorun.

Sınırlar: Çok kısa DFL sahiplikleri kısmen sağlayıcının etiketleme biçiminden kaynaklanıyor
olabilir; video olmadığı için bu doğrulanamadı. Bu altı kopya ayrıntılı incelendi. Bu yüzden
kısa sahipliklere yönelik bir değişiklik, yeni tohumlu kopyalarda önceden kaydedilen bir
planla seçilmeli ve sınanmalı. Son sınav yine J03WMX olmalı.

## P009 — Öğrenilmiş takım değişimi olasılığıyla değişken geçiş maliyeti (v2.6), seçilmedi, 10 Kasım 2026

Yalnız rapor amaçlı iki ölçüm hatanın yerini gösterdi (`possession-v26-results.json`):
- **Ayrıştırma** (dört doğrulama maçı, tohum 101): temiz tracking 0,748; v2.1 bozulması 0,610;
  aynı bozulma ama top hiç kaybolmuyor 0,700. Kaybın yaklaşık üçte ikisi topun kaybolmasından.
- **Kâhin denemesi** (8 doğrulama kopyası): P(ölü top) yerine sağlayıcı etiketi konunca 0,631 →
  0,647; P(ev sahibi | oyunda) yerine konunca 0,912. Asıl hata oyun içindeki takım kararları.

v2.6 (`possession-v26-plan.json`, 14:09:37'de, sonuçlardan önce): "±0,5 s içinde takım
değişimi olur mu" diye ayrı bir GBDT. 227 birinci aşama özelliği ve 48 ikinci aşama özelliği
kullanıyor; eğitim katlar dışı olasılıklarla yapıldı. Çözücüde geçiş maliyeti
switch_t = max(0, s0 − β·logit(h_t)) (`possession/decode2.py`, `possession/hazard.py`).
Izgarada en iyisi s0=2, β=1: eski 8 kopyada 0,6312 → 0,6351. Kayıtlı doğrulama hiç
kullanılmamış 8 kopyada (tohum 4100+) yapıldı: 0,6518 → 0,6538 (+0,002). Kopyaların yalnız
4'ünde kötüleşme olmadı; DFL'de kazanç, Metrica'da kayıp var. Kapılar (+0,010 ve 8 kopyanın
en az 5'inde kötüleşmeme) geçilmedi → seçilmedi, v2.4 çözücüsü kaldı. Ders: takım değişimini
yeni bir model değil, daha iyi top bilgisi düzeltir. Testler: `tests/test_possession_v26.py`
(3 sentetik test).

## P008 — Saatle çapalanmış yayın eşlemesi (v2.5b), SEÇİLDİ, 10 Kasım 2026

Ekibin önerisi: iki videoda da görünen maç saatiyle kareleri eşlemek. Plan
`possession-v25b-plan.json` (14:03:16; v2.5'in ilk 10 satırı görüldükten sonra yazıldı).
`possession/clocksync.py`, S002'deki OCR çıktısını (`tools/clock_observations.py`) okur. Tutarlı
saat dizilerini eşler; uzatma dakikası gibi iki kez görünen saatleri atlar. Her yarı için ortanca
zaman farkını verir: en az 10 eşleşme, IQR ≤ 1,5 s. Eksen yönü ve takım eşlemesi bu farkta
seçilir; ince ayar ±40 karede yapılır (`possession/fusion.py`). Saat yoksa v2.5'in yörünge
araması kullanılır.

Doğrulama 16 YENİ kopyada (tohum 3100+/3500+) yapıldı. Saat okumaları sentetikti: okunabilirlik
%50-95, hatalı okuma %1-3, uzatma dakikaları ikinci yarıyla çakışıyor.

| Rejim | v2.4 | v2.5 | v2.5b |
|---|---|---|---|
| İyi | 0,635 | 0,672 | 0,672 |
| Orta | 0,635 | 0,641 | 0,641 |
| Kötü | 0,635 | 0,635 | 0,635 |

Başarısız eşleme iki sürümde de 0 oldu. Bu kopyalarda iki eşleme de çalıştı, yani saatin
faydası (P007'deki türden bir başarısızlığı önlemek) burada yeniden görülmedi. Beş kayıtlı
koşulun beşi de sağlandı: iyi ≥ +0,010; orta ≥ −0,005; kötü ≥ −0,002; v2.5'ten en fazla 0,002
kötü olmak; başarısız eşlemede v2.5'ten fazla olmamak. Bu yüzden v2.5b seçildi. Teslim sistemi
saat çapasını kullanıyor; saat dosyası verilmezse yörünge eşlemesine düşüyor.

Sürüm `possession-v25-release.json` ile donduruldu; her çıkarım kaynağının ve iki paketin SHA-256'sı
burada. Tam boyutlu tekrar üretilebilirlik denendi: bozulmuş Metrica maç 3 + sentetik yayın +
sentetik saat. Python 3.10/numpy 1.26 ile 3.13/numpy 2.5 aynı dosyayı verdi; saatli ve saatsiz
eşleme de aynı dosyayı verdi. Bir çalıştırma 3-4 dakika sürdü ve en fazla 4,4 GB kullandı (239
iz yuvası). Sonuçlar: `possession-v25b-results.json`.

## P007 — Yayın topuyla boşluk doldurma, doğruluk kapısıyla (v2.5), SEÇİLDİ, 10 Kasım 2026

Plan `possession-v25-plan.json` (13:48:08, sonuçlardan önce). v4'ün hizalaması aynen
kullanılıyor (`possession/broadcast.py`). Yeni olan doğruluk kapısı (`possession/fusion.py`):
- iki kameranın da topu gördüğü hizalı karelerde ortanca uzaklık 0,50 m'nin altında olmalı,
- en az 120 s örtüşme olmalı,
- yayın karelerinin en az %5'i kabul edilmiş olmalı.

Kapı açıksa yalnız taktik topun eksik olduğu kareler doldurulur; taktik top asla
değiştirilmez. v2.4'ün gürültü kapısı ham taktik veride ölçülür.

Doğrulama 16 yeni taktik kopyada (tohum 2100+/2500+) yapıldı. Sentetik yayın akışları üç
doğruluk rejiminde üretildi:

| Rejim | v2.4 | v2.5 | Kapı açıldı |
|---|---|---|---|
| İyi | 0,651 | 0,675 | 15/16 |
| Orta | 0,651 | 0,655 | 1/16 |
| Kötü | 0,651 | 0,651 | 0/16 |

Üç kayıtlı koşul da sağlandı → v2.5 seçildi. İyi rejimde puanlanan karelerde top görünürlüğü
%53'ten %63'e çıktı. Kopya başına fark −0,004 ile +0,079 arasında. İki yol da kazandı:
v2.1 yolu +0,018, v2.3 yolu +0,031. İyi rejimdeki bir kopyada (J03WN1/2101) top yörüngesi
araması yanlış eksen çevirmesine ve sahte bir zaman farkına kilitlendi; eşleme olmadı,
kazanç kayboldu, zarar olmadı. Bu durum P008'e (saat çapası) yol açtı.

Çalışma notu: iki iş bellek sınırından öldü ve kaldıkları kopyadan devam ettirildi. Sonuçlar
kopya kopya kaydediliyordu; yarıda kalan kopya aynı tohumlarla baştan hesaplandı. Hesap
deterministik olduğu için bu sonucu değiştirmez. Sonuçlar: `possession-v25-results.json`;
`tests/test_possession_v25.py`.

## P006 — Gürültü kapısı: v2.1 ya da v2.3 yolunu ölçülen titreşime göre seçmek (v2.4), SEÇİLDİ, 10 Kasım 2026

v2.3 sonuçları görüldükten sonra tasarlandı (planda açıkça yazıyor). Plan
`possession-v24-plan.json` 2026-11-10T09:55:18+03:00'te, hiçbir v2.4 sonucundan önce kaydedildi.
Kapı (`possession/noise.py`): oyun blokları içinde konumların ikinci farkı
d2 = x[t+1] − 2x[t] + x[t−1]; σ = 1,4826·MAD(d2)/√6. Oyuncularda slot başına ölçülüp ortanca
alınıyor (en az 500 değer). Oyuncu ya da top σ > 0,30 m ise v2.3 yolu çalışıyor (±2 kare
yumuşatma + v2.3 modelleri + çözücü 5/60/60/-0,3), değilse v2.1 birebir. Eşik önceden
sabitlendi: v2.1 eğitim bozulmasının üst sınırı. Kayıttan önce yalnız ölçer denetlendi (etiket
ve puan yok): eklenen 0,1/0,3/0,5 m hata 0,10/0,30/0,50 m ölçüldü. Temiz DFL 0,006 m, Metrica
0,001 m çıktı.

Doğrulama: aynı dört maçın 24 YENİ kopyası, her kopyanın kendi tohumu var (1100+, 1300+, 1500+).
v2.1 0,6032 / v2.4 0,6422 (+0,039). Eski tip kopyalar 0,6542 / 0,6542 (kapı 8/8 v2.1 seçti). Top
hatalı kopyalar 0,5831 / 0,6279, oyuncu hatalı kopyalar 0,5723 / 0,6445 (kapı 16/16 v2.3
seçti). İki kayıtlı koşul da sağlandı → v2.4 seçildi. Yalnız rapor: her yerde v2.3 kullanmak
0,6381 verirdi (eski tipte 0,6419). Sınır: kopyaların hatası ≤ 0,29 m ya da ≥ 0,34 m idi;
0,30 m civarı denenmedi. Kayma ve önceden yumuşatılmış hata kapıya görünmüyor.

Sonra kayıtlı v2.3 tarifiyle son paket 6 DFL maçında eğitildi (`possession-v23-config.json`,
`models/possession-v23.npz`). Giriş noktası `possession/run24.py`; v2.1 paketi değişmedi ve
SHA-256'sı kontrol ediliyor. Ayrılmış test (Metrica maç 3, dondurulmuş paketler, tek sefer,
karar kapısı değil): v2.1 bozulmasında kapı 2/2 v2.1 seçti, sonuç aynı (0,664); v2.1 eski
değerlerini birebir üretti (0,6253 / 0,7021). Top hatalı kopyalarda 0,645 → 0,660, oyuncu hatalı
kopyalarda 0,602 → 0,670; 6 kopyada 0,637 → 0,665. Testler: `tests/test_possession_v24.py`.
Sonuçlar: `possession-v24-results.json`.

Bu oturumdaki diğer işler: disk kotası doldu ve bir hazırlık işi bellek sınırından öldü.
Bozuk önbellek dosyaları silinip yeniden üretildi; sonuçlar etkilenmedi, çünkü her kopya
dosyası okunarak denetlendi.

## P005 — Konum gürültüsüne dayanıklılık: giriş yumuşatma + geniş eğitim gürültüsü (v2.3), seçilmedi, 10 Kasım 2026

Yalnız rapor amaçlı ölçüm: v2.1 tarifinde oyunculara 0,5 m rastgele hata eklenince puan
0,610'dan 0,495'e düşüyor (topa 0,5 m eklenince 0,537). v2.3 (`possession-v23-plan.json`,
sonuçlardan önce kaydedildi): her oyuncu ve top konumu oyun blokları içinde 5 karelik NaN'a
duyarlı hareketli ortalamayla yumuşatılıyor (`possession/smooth.py`; eksik kare eksik kalıyor).
Eğitimde top hatası 0,05-0,6 m ve 0-0,6 m yavaş kayma, oyuncu hatası 0,03-0,6 m oldu. Çözücü
aynı 54 noktalı ızgaradan 24 kopyada seçildi (5/60/60/-0,3).

Doğrulama (aynı dört maç; 8 eski kopya, 8 top hatası genişletilmiş kopya, 8 oyuncu hatası
genişletilmiş kopya): 24 kopyada v2.1 0,6064 / v2.3 0,6207 (+0,014, kapı geçti). Eski kopyalarda
0,6312 / 0,6169 (-0,014; kapı en fazla -0,010 kayba izin veriyordu, geçmedi). Top hatalı
kopyalarda 0,6041 / 0,6178, oyuncu hatalı kopyalarda 0,5840 / 0,6276 (+0,044). Kayıtlı kurala
göre seçilmedi; v2.1 kaldı. Yalnız rapor: v2.1'in çözücüsü de 24 kopyada yeniden seçilince
farkın yaklaşık 0,004'ü çözücüden geliyor. Not: bozma parametreleri yalnız tohuma bağlı; aynı
tohumun dört maçı aynı gürültüyü paylaşıyor, yani 24 kopya altı gürültü ayarı demek.
Sonuçlar: `possession-v23-results.json`; `tests/test_possession_v23.py` 4 sentetik test geçti.

## Kayıt düzeltmesi — ön kayıt dosyalarındaki saatler, 10 Kasım 2026

`possession-v2/v3/v4/v22/v23-plan.json` dosyalarındaki saatleri ajan sistem saatine bakmadan
tahminle yazmıştı. Bu saatler gerçek yazma anından 1-60 dakika sonrayı gösteriyordu (ör. v2.3
planında 08:50 yazıyordu, dosya 08:31:03'te yazılmıştı). Saatler çalışma kopyasının dosya
sistemindeki oluşturma ve son değişiklik zamanlarıyla değiştirildi. Eski değerler her dosyada
`timestamp_correction.original_values` altında duruyor. Dosya zamanları plan → ek → sonuç
sırasını doğruluyor; aralık içindeki kesin saat bilinmiyor. İki açık nokta dosyalara yazıldı:
v3 planındaki birinci ekte, kalibrasyon kod değişikliği (06:23) ilk v3 eğitim günlüğünden
(06:25) önce yapılmış. Ancak ek metninin o anda yazıldığı dosya zamanlarından gösterilemiyor.
v4 planında anılan kâhin üst sınır denemesinin kısmi çıktısı plan yazılmadan önce görülmüş
olabilir. Bundan sonra saatler komutla okunarak yazılıyor.

## P004 — Top konum hatasına duyarlılık ve dayanıklı eğitim (v2.2), seçilmedi, 10 Kasım 2026

Yalnız rapor amaçlı duyarlılık ölçümü (v2.1 tarifinin 4 maçla eğitilmiş doğrulama modelleri,
dört doğrulama maçının 101 kopyası): temel 0,610; ek 0,5 m rastgele top gürültüsü 0,537; 1 m
0,492; yavaş değişen 1 m kayma 0,519; hızlı (havadaki) topun yer izdüşüm hatası 0,611. v2.1
eğitimde yalnız 0,05-0,3 m top gürültüsü görmüştü; gerçek taktik top hatası bilinmiyor.

v2.2 (`possession-v22-plan.json`, sonuçlardan önce kaydedildi): yalnız eğitim bozulması
değişti (top gürültüsü 0,05-0,6 m + 0-0,6 m yavaş değişen kayma; v2.1 profili ve rastgele
çekilişleri birebir korunuyor, önbellekteki v2.1 özellikleri yeniden üretildi). Doğrulama:
eski 8 kopya + aynı maçların genişletilmiş top hatalı 8 yeni kopyası (301/302). Sonuç: 16
kopyada v2.1 0,6177 / v2.2 0,6229 (+0,005; kapı +0,010), eski kopyalarda 0,6312 / 0,6262,
gürültülü kopyalarda 0,6041 / 0,6196 (+0,016). Kayıtlı kurala göre seçilmedi; v2.1 kaldı.
`possession.train` artık `degrade_profile` alanını okuyor (v2.1 yapılandırmasında yok =
eski profil). Sonuçlar: `possession-v22-results.json`.

## P003 — Yayın kamerasından top doldurma (v4), seçilmedi, 10 Kasım 2026

`possession/broadcast.py`: yayın tracking'ini taktik zamana otomatik eşleme ve taktik top
boşluklarını doldurma. Eşleme: eksen yönü/takım eşlemesi, devre başına topun x/y yörüngesinin
maskeli normalize çapraz korelasyonu (FFT), 60 s pencerelerde ±12 kare inceltme (top mesafesi +
aynı takım oyuncu eşleşmesi), kare kabulü ≥3 oyuncu ve medyan ≤2 m (tekrar/yakın çekim elenir).
Birleştirme: yalnız taktik top kayıpsa; 0,5 s içindeki taktik topa göre hız sınırı; genel kapı
(iki kameranın da topu gördüğü karelerin ≥%70'i 2 m içinde). Sabitler sonuçlardan önce
`possession-v4-plan.json` ile kaydedildi. Dış maçlardan sentetik yayın akışı (devre farkı,
kayma, tekrarlar, yakın çekim, kadraj, çekim başına kalibrasyon hatası, gürültü) üretildi.

Sonuç: eşleme doğru (kabul edilen karelerin %98,3'ü doğru, medyan zaman hatası 0 kare), top
görünürlüğü belirgin arttı (ör. %52→%73), fakat spellF1 0,6312→0,6251 düştü: DFL kopyalarında
ortalama -0,037, Metrica kopyalarında +0,025. Neden: sahiplik kararı top-oyuncu mesafesine çok
duyarlı; ikinci kameranın ~0,5-1,5 m hatalı topu sahte değişimler üretiyor. Kötü kalibrasyonlu
akışta kapı birleştirmeyi her kopyada kapattı (v2.1 ile aynı). Kayıtlı kurala göre seçilmedi;
teslim sistemi v2.1. Sağlanan maçın yayın dosyaları okunmadı. Sonuçlar:
`possession-v4-results.json`; `tests/test_possession_v4.py` 4 sentetik test geçti.

## P002 — Smart Tagging kanıtı (v3.0 / v3.1), seçilmedi, 10 Kasım 2026

Amaç: Metrica'nın otomatik Smart Tagging'ini (duran top pencereleri, takım etiketli evreler)
ikinci aşamaya kanıt olarak eklemek. `possession/smarttags.py`: SportsCode okuyucu (takım adı
eşleme + DATA.md'deki belgelenmiş adlar), kare özellikleri (23), çalışma anı güven kapısı
(etiket takımı ile yalnız-tracking birinci aşamanın emin olduğu karelerde uyum; grup başına
eşik 0,60, en az 625 kare; sonuçlardan önce sabitlendi) ve yalnız dış maçlarda kullanılan
etiket benzetimi. Dış maçlarda Metrica etiketi olmadığı için etiketler dış maçın etiketlerinden
üretildi, sayıları DATA.md'de yayımlanan kod sayılarına göre ayarlandı ve zamanlama/takım/N-A/
sahte etiket hataları rastgele bozuldu. Plan: `possession-v3-plan.json` (ekleriyle).

v3.0 (v2.1 birinci aşama + etiketli ikinci aşama): tipik etiketlerde 0,6422 (v2.1 0,6312,
+0,011), doğru etiketlerde 0,6573, etiketsiz 0,6231, gürültülü 0,6253, %30 takım hatası 0,6342,
ters savunma anlamı 0,6433 (kapı ters grubu her kopyada kapattı). Etiketsiz ve gürültülü
koşullar kayıtlı kapıları geçmedi → seçilmedi. v3.1 (sonuçlar görüldükten sonra tasarlandı:
grup kalmazsa birebir v2.1, aksi halde uyuma göre ağırlıklı v3.0/v2.1 karışımı), aynı dört
maçın YENİ bozulmuş kopyalarında: tipik +0,002, doğru +0,019, gürültülü -0,004, takım hatası
-0,002, etiketsiz 0. Tipik koşulda +0,010 kapısını geçmedi → seçilmedi. Teslim sistemi v2.1
kaldı. Sağlanan maçın etiketleri hiç okunmadı. Sonuçlar: `possession-v3-results.json`.
Kod deneysel olarak duruyor; `tests/test_possession_v3.py` 6 sentetik test geçti.

## P001 — Sahiplik v2.1: dış veride seçilmiş H/A/D sistemi, 9-10 Kasım 2026

Yeni `possession/` paketi: yalnız taktik ATD konumlarından özellikler → iki gradyan artırmalı
ağaç modeli (P(D), P(H | top oyunda), takım simetrik) → maç dışarıda bırakmalı olasılıklarla
eğitilmiş ikinci aşama → üç durumlu Viterbi. Eğitim/seçim yalnız Sportec/DFL (CC-BY 4.0) ve
Metrica örnek maçlarında; her kopya `degrade.py` ile otomatik tracking'e benzetildi. Plan
sonuçlardan önce kaydedildi; eklenen adaylar (stacking, v3 özellikleri) sonuçları oluşmadan
plana ek olarak yazıldı. Doğrulama (8 bozulmuş kopya, resmi spellF1, aynı çözücü ızgarası):
v2 0,6218; v2+stacking 0,6312 (seçildi); v3 0,6199; v3+stacking 0,6302; organizatör baseline
mantığı 0,196; S001 0,196. Son paket DFL'nin 6 maçıyla yeniden eğitilip donduruldu
(`models/possession-v2.npz`, SHA-256 `1cd59ba5…`). Ayrılmış test (Metrica 3, iki kopya, tek
sefer): 0,664 (baseline 0,219; S001 0,265). Stres: sert bozulmada 0,584 (baseline 0,170);
1-5 s sahte top izleri -0,025; kopyalanmış oyuncular etkisiz. Bunlar dış maçlarda başka
sağlayıcıların etiketleriyle uyumdur; yarışma puanı değildir. Barcelona maçında hiçbir şey
ölçülmedi; çıktı videoyla karşılaştırılmadı. Okuyucu artık EPTS `DataFormatSpecification`
izliyor; ev sahibi adla da kontrol ediliyor (ikisi de sonuç görülmeden bulundu). Simüle Smart
Tagging deneyi plana göre seçilemeyeceği için çalıştırılmadı. `tests.test_possession_v2`:
21 test geçti (Python 3.10 çıkarım ortamında 8'i scikit-learn olmadığı için atlandı); aynı
çıktı iki numpy sürümünde birebir üretildi.
[Ayrıntılar](SAHIPLIK_V2_TR.md), `TECHNICAL_DOCUMENT_V2.md`, `possession-v2-results.json`.

## C001 — Altı aşamalı görüntü kontrol hattı, 8 Kasım 2026

Temas/kontrol/takım sahipliği ayrımı; bağımsız dış olay referansı sözleşmesi;
görüntü hareket kanıtı; doğrulama ve başlangıç zamanının ayrılması; dış maç
ayrımı/edinimi; kamera-tag bağlantısı ve bileşen kapatma aracı eklendi.
Maç 2/3'ten 500 ardışık kare ve RGB doğrulanmış iki kayıpsız video hazır.
Maç 5 görüntüleri ayrılmış kaldı. Altı sentetik aç/kapat çalıştırması tamam.
295 test: 293 geçti, 2 AV atlandı; ilgili 9 test AV ortamında ayrıca geçti.
Gerçek temas referansları boş; gerçek görüntü sahipliği başarısı veya final
terfi iddiası yok. [Altı adım ve açık doğrulama](ALTI_ADIM_ENTEGRASYON_TR.md).

## S002 — Sahiplik geçiş zamanları ve belirsizlik, 8 Kasım 2026

Yönlü bire bir geçiş eşleştirmesi, 0,2/0,5/1/2 s toleransları ve X boşlukları
için belirsiz zaman aralığı eklendi. Dört dış doğrulama maçında altı değişim
maliyeti karşılaştırıldı. Mevcut adayın 0,5 s sınır F1'i 0,11277; 0,025 s
maliyetle 0,16856'ya çıkarken aralık proxy F1'i 0,48388→0,30809 düştü.
Ortak kabul geçilmedi; model değişmedi ve ayrı kontrol açılmadı. 283 test:
281 geçti, 2 isteğe bağlı AV atlandı. [Yöntem ve sınırlar](SAHIPLIK_SINIRLARI_TR.md).

## V021 — Geometri ve zamansal kanıtı birlikte öğrenme, 8 Kasım 2026

355 eğitim adayıyla öğrenildi. Doğrulamada normal/parçalı doğru eşleşmeler
47→46 / 71→71, eşleşmeyenler 104→55 / 220→75. Sabit kontrolde doğru
eşleşmeler 53 ve 85 korundu; eşleşmeyenler 95→83 / 222→165. Normal
kontroldeki %12,6 azalma gerekli %20'yi geçmedi; final kabul başarısız.
Eşik değiştirilmedi. Ayrı deneysel kanıt alanı 1.200 analiz paketine
eklendi; ham kutular, izler ve sahiplik korunuyor. 277 test: 275 geçti,
2 AV atlandı; ilgili 9 test AV ortamında ayrıca geçti.
[Yöntem, kapsam ve yeni dış maç metadata envanteri](TOP_ZAMANSAL_OGRENME_TR.md).

## V020 — Sınırlı gelecek kareyle tespit doğrulama, 8 Kasım 2026

27 sabit süreklilik adayı karşılaştırıldı. Normal taramada bazı adaylar
47 doğru eşleşmenin tamamını koruyup eşleşmeyenleri 104→37 azalttı;
parçalı taramada kayıplar nedeniyle ortak doğrulama koşulu geçilmedi.
Ayrı maç kontrolü çalıştırılmadı. Tahminler gerçek ölçüm yapılmadı;
bilinmeyen referanslar negatif sayılmadı. `ball-temporal-selection-results-v1.json`.

## V019 — Doğal ölçekte eğitim ve tam kare kontrolü, 8 Kasım 2026

212 eğitim parçasıyla iki epoch tamamlandı. Parça doğrulama mAP@50:95
0,20434; tam karede temel 24 doğru / 54 eşleşmeyen adaya karşı yeni model
0,3 eşikte 18 / 21 verdi. Sekiz eşiğin hiçbiri temel doğru eşleşme sayısını
korumadı (en yüksek 22). Aday reddedildi; ayrı maç kontrolü çalıştırılmadı.
SAHI düşük eşik otomatik NMS geçişi sonuç görülmeden kaynak incelemesinde
bulundu; eğitim korunup sabit ağırlıkla GREEDYNMM/IOS değerlendirmesi yeniden
üretildi. Eski kısmi tahminler kullanılmadı. `ball-patch-results-v1.json`.
267 test: 265 geçti, 2 AV atlandı; AV ortamındaki ilgili 9 test ayrıca geçti.
[Yöntem, kapsam ve sınırlamalar](TOP_PARCA_EGITIMI_TR.md).

## V018 — Dış sahne kapsamı ve parça verisi, 8 Kasım 2026

25 ek kesitten 1.875 seyrek kare edinildi: eğitim maçından 1.050,
doğrulamadan 375, sabit kontrolden 450. Aynı üç kaynak maç kullanıldı;
yeni bağımsız maç iddiası yok. Üye CRC/SHA doğrulandı, tam arşiv hash'i
doğrulanmadı. İlk hatalı sıra numarası görüntü erişiminden önce reddedildi.
Doğal ölçekte 212 eğitim / 960 sabit ızgara doğrulama parçası hazırlandı.
Kontrolün 45 tam karesi eğitim parçası yapılmadı. Bu veri kapsamı sonucudur,
algoritma başarı iddiası değildir. `ball-data-expansion-results-v1.json`;
[yöntem](TOP_PARCA_EGITIMI_TR.md).

## V017 — Sabit modelde güven eşiği kalibrasyonu, 8 Kasım 2026

Sekiz ön kayıtlı eşik yalnız doğrulama maçında karşılaştırıldı. Eşik 0,15
doğru eşleşmeleri korudu, fakat eşleşmeyenler doğrulamada 104→177,
sabit kontrolde 95→150 arttı. Kabul koşulu geçilmedi. Kontrolden sonra
eşik değiştirilmedi, model tekrar eğitilmedi. `ball-confidence-results-v1.json`.

## V016 — COCO top başlığını koruyarak eğitim, 8 Kasım 2026

37 numaralı top logiti yeni dense 0'a tüm başlıklarda aktarıldı; diğer
tensörlerin ve kurulan başlangıç modelinin bire bir korunduğu doğrulandı.
Üç epoch düşük öğrenme hızıyla eğitim yapıldı. Sabit 0,3 eşikte doğrulama
eşleşmesi 47→39, eşleşmeyenler 104→43; ayrı maçta 53→39 ve 95→42.
Doğru eşleşmeler azaldığı için kabul edilmedi. Mevcut model korundu.
`ball-transfer-results-v1.json`; [ayrıntı](TOP_COZUNURLUK_AKTARIM_TR.md).

## V015 — Sabit çözünürlük deneyi ve sınıf sözleşmesi, 8 Kasım 2026

120 dış karede aynı GPU/ağırlık/eşik kullanıldı. 384×384 parçalar,
512×768'e karşı üç kaynak maçta eşleşmeleri 17→25, 12→14, 15→15 yaptı.
Her maçta ≥%20 artış koşulu geçilmedi; süre yaklaşık 60→110 saniye.
Varsayılan dedektör değişmedi. Ayrı düzeltmeyle COCO analiz yolu,
tek sınıflı checkpoint'i model kurmadan reddeder; gerçek dosyalarla kontrol
edildi. [Plan ve yöntem](TOP_COZUNURLUK_AKTARIM_TR.md).

## V014 — Dış top dedektörü eğitim altyapısı, 8 Kasım 2026

Manifest-doğrulanmış 225 eğitim / 150 doğrulama görüntüsüyle yerel Nano
tek epoch eğitimi tamamlandı; ayrı 150 kontrol görüntüsü değerlendirilmedi.
İlk eksik bağımlılık ve ardından Windows konsol kodlama hatası çözüldü;
başarısız kayıtlar saklandı. mAP@50:95=0,0103, mAP@50=0,0382: kullanım
kalitesi kanıtlanmadı, final modele alınmadı. 248/249 omurga tensörü
güncellendi; güvenli yeniden yükleme ve sentetik çıkarım geçti. Yeni sınıf
numaraları eski COCO arayüzüne doğrudan uygulanamaz. Özet:
`ball-detector-feasibility-results-v1.json`. 248 test: 246 geçti, 2 atlandı.

## V013 — Top adayı filtresi ve konum hassasiyeti, 8 Kasım 2026

SoccerNet kaynak maçları 4/6/9 ayrımıyla geometri/güven filtresi öğrenildi.
Sabit aday kontrolünde parçalı tarama eşleşmeyenleri 442→224 azalttı,
85→84 doğru eşleşme korundu; normal tarama 134→128 ile %20 azalma
koşulunu geçemedi. Final modele alınmadı. Betimleyici IoU incelemesi
yer/boyut hatası yanında çok sayıda uzak adayı da gösterdi.
Maçlar daha önce erişilmiş dış veridir; Barcelona kullanılmadı.
[Ayrıntı, özetler ve eğitim veri hattı](TOP_ADAYI_DENEYI_TR.md).

## D004 — Top özellikleri olmadan D ve sağlayıcılar arası kontrol, 7 Kasım 2026

Dört eğitim / iki doğrulama maçında 18 aday karşılaştırıldı. Oyuncu hızları
ve yayılımı dışında özellik kullanılmadı. D F1 0,8781 / 0,8577; bir saniyelik
sınır F1 0,3430 / 0,4195. Ön kayıtlı ortalama sınır koşulu karşılanmadı;
aday final sisteme alınmadı. Sabit adayın iki Metrica kısmi olay proxy'sindeki
D F1 değeri 0,8497 / 0,7888; tam maç veya yeni bağımsız test değildir.
Sağlanan maç kullanılmadı, ayrılmış Sportec testi açılmadı. 236 testten
234 geçti, iki isteğe bağlı AV atlandı. [Ayrıntılar](D_OGRENME_DENEYI_TR.md).
Makine tarafından okunabilir terfi kararı: `dead-ball-promotion-decisions.json`.

## D003 — Öğrenilmiş D ve aktarım riski, 7 Kasım 2026

Dört Sportec eğitim ve iki doğrulama maçında 48 aday karşılaştırıldı.
Temiz doğrulama D F1: 0,9948 / 0,9952. Sayısal kabul geçmiş olsa da aday
final sisteme alınmadı: dört eğitim maçındaki ölçülebilir D top hızlarının
tamamı sıfır. Sağlayıcıya özgü sabit koordinat örüntüsünü öğrenmiş olma riski
var. Başarı yarışma/görüntü başarısı diye sunulmadı. Ayrı oyuncu-temelli
deney ve başka sağlayıcı denetimi gerekiyor. [Ayrıntılar](D_OGRENME_DENEYI_TR.md).
231 test: 229 geçti, 2 isteğe bağlı AV atlandı. Temel ve H/A adayı korundu.

## D002 — Sportec/DFL canlı ve duran oyun hedefleri, 7 Kasım 2026

CC BY 4.0 lisanslı dış kaynak, indirme öncesinde 4 eğitim / 2 doğrulama /
1 ayrılmış son kontrol olarak kaydedildi. İlk eğitim maçı J03WOH hazırlandı:
137.214 kare; 65.269 D karesinin tamamında sonlu top koordinatı mevcut.
71.945 canlı oyun karesi var. BallStatus/BallPossession yalnız ayrı hedef
dosyasında; özelliklere verilmez. Bu kapsam sonucu, D model başarısı değildir.
Yeni D sınıflandırıcısı veya birleşik teslim sürümü seçilmedi.

Araçlar: `tools.sportec_download`, `tools.sportec_prepare`,
`development/state_metrics.py`. Ayrılmış test maçına erişim kapalı.
9 yeni testle toplam 225 test: 223 geçti, 2 isteğe bağlı AV atlandı.
Ayrıntılar ve atıf: [Sportec dış veri](SPORTEC_DIS_VERI_TR.md).

## S001 — Dış maçlarda zamansal sahiplik seçimi, 7 Kasım 2026

Plan: `sequence-selection-plan.json`; sonuç: `sequence-external-results.json`.
SkillCorner'ın kayıtlı 12 eğitim / 4 doğrulama maçı kullanıldı. Önceden
erişilmiş dış veridir. 42 adayın ayarları doğrulama öncesinde sabitlendi.
Seçilen adayın ek dört maçtaki tahminleri hedefler puanlanmadan donduruldu.
Bu dört maç daha önce temel model kontrolünde görüldüğünden yeni test değildir.

| Ölçüm | Eski temel | Yeni aday |
| --- | ---: | ---: |
| Doğrulama: X doldurmalı bölüm proxy F1 | 0,360654 | 0,483879 |
| Doğrulama: H/A makro F1 | 0,681228 | 0,791318 |
| Ek kontrol: X doldurmalı bölüm proxy F1 | 0,350802 | 0,465224 |
| Ek kontrol: H/A makro F1 | 0,639107 | 0,736257 |

Her iki grupta da dört maçın tamamında bölüm proxy iyileşti. Bunlar otomatik
sağlayıcı hedefleriyle uyumdur, insan doğruluğu veya yarışma skoru değildir.
Eski X'i bölümlere ayıran proxy de raporda ayrı tutuldu. D ve görüntü başarısı
bu deneyde ölçülmedi; yeni birleşik teslim sürümü seçilmedi.

Seçilen geometri yarıçapı 3,807335 m, göreli hız ölçeği 3,417601 m/s,
azami kanıtsız bağlantı 5,9 s ve geçiş maliyeti 0,25 s. İlk üçü yalnız eğitim
verisinden, sonuncusu ön kayıtlı adaylar arasından dış doğrulamayla seçildi.
Ek dört maç sonucuyla değiştirilmedi. Kaynak/plan/veri hash'leri özel
`sequence-development-20261107` kaydında. Temel model bytes değişmedi.

11 yeni sentetik test; toplam 216 test, 214 geçti, 2 isteğe bağlı AV atlandı.
Dinamik program kaba kuvvet en iyi sonuçla, takım değişim simetrisi, FPS,
uzun kayıp/devre/kare kopması ve hedef sızıntısı reddiyle doğrulandı.

Öncelikli 3 Kasım kural e-postası yeniden okundu: sağlanan çıktı-video
karşılaştırması yasak. Önceki yerel gösterim yaklaşımı düzeltildi,
8776/8777 sunucuları durduruldu. Sağlanan maç bu deneyde kullanılmadı.
[Güncel süreç ve sonraki aşamalar](OTONOM_GELISTIRME_TR.md).

## V012 — Görüntü karar verir, tracking oyuncuyu etiketler, 7 Kasım 2026

`development/visual_possession.py`, `tools/visual_identity_context.py` ve
`tools/visual_possession_experiment.py` ayrı görüntü temelli sahiplik yolu eklendi.
Plan: `visual-possession-plan.json`; kullanım: `GORUNTU_TEMELLI_SAHIPLIK_TR.md`.
Tracking topu/sağlayıcı sahipliği/eski model çıktısı karar girdisi değildir.
Ölçülmüş görüntü topu ve oyuncu ayaklarının sürekliliğinden kontrol adayı çıkar.
Metadata kimliği karşılıklı izdüşüm yakınlığı ve zamansal onayla bağlanır.
Uygun yayındaki kontrol tercih edilir; uyuşmazlık, tekrar, dar kadraj ve toplu
sıçramada taktik karar korunur. Görünmeyen oyuncular taktikten kalır.

17 yeni test, toplam 195 test: 194 geçti, 1 isteğe bağlı AV atlandı.
8 karelik sentetik taktik koşuda X=4/H=4; uygun yayın görüntüsünde top A
oyuncusuna taşındığında X=4/A=4; eşleme geçersiz olduğunda X=4/H=4 oldu.
Kimlik adaptörü sayısal olmayan ATD top alanıyla da çalıştı; top ayrıştırılmadı.
Önceden görülen dış eğitim kesitlerinin 1.200 çıktı karesi kimlik kanıtı yokken
X kaldı. Bu gerçek sahiplik doğruluğu veya performans artışı değildir.

Özel ön kayıt ve rapor:
`C:/Users/Abra/FootballPrivate/visual-possession-development-20261107`.
Donmuş kaynaklar korundu. Yarışma görüntüsü/tracking'iyle geliştirme yapılmadı;
o maç için yeni tam çıktı üretilmedi. Kimlik/zaman/kalibrasyon ve gerçek görüntü
başarısı dış maçlarda doğrulanmadan yeni teslim sürümü seçilmedi.
İlk kural uçuşta pas sahipliği veya D çözmez; tag destekli görüntü sınırları
sonraki ayrı aşamadır. Eski tracking tabanlı hareket prototipi sessizce yeni
görüntü kararının yerine kullanılmadı.

## V011 — Tracking destekli top adayı, 7 Kasım 2026

Mevcut dedektör ve zamansal takip değiştirilmeden ayrı ilişkilendirme katmanı
eklendi. Sabit sentetik plan: `ball-support-plan.json`; uygulama ve sınırlar:
`TRACKING_DESTEKLI_TOP_TR.md`. Doğrulanmış kaynak/kare/saat/epoch, canlılık,
kalibrasyon ve zemin kanıtı ister; onaylı mevcut ölçümleri karşılaştırır.
Tahmin, hava topu, tekrar, uyuşmazlık ve yakın iki adayda seçim yapmaz.
İkinci kamera ayrı native kontroller ve tam çift eşlemesiyle destek verebilir.
Ortak tracking uyumu bağımsız gerçek kabul edilmez. Sahiplik güncellenmez.

12 yeni birim/entegrasyon testi geçti. Tüm paket: 178 test, 177 geçti,
1 isteğe bağlı AV atlaması. Sekiz önceden görülen dış eğitim kesitinde iki
mod/1.200 çıktı karesi işlendi; önceki paketlerin tüm eski alanları korundu.
Eşzamanlı bağımsız otomatik tracking bulunmadığından destek gerçek kesitlerde
etkinleşmedi; destek açık ve çift kamera yolu sentetik olarak sınandı.
Gerçek doğruluk artışı veya bağımsız test sonucu üretilmedi. Referans etiketler
girdi yapılmadı; yarışma maçı okunmadı; donmuş kaynaklar bütünlük testini geçti.

Özel ön kayıt ve rapor:
`C:/Users/Abra/FootballPrivate/ball-support-development-20261107`.
Seçilen yeni teslim sürümü yok. Gerçek eşzamanlı dış kaynakta açık/kapalı
karşılaştırması bekliyor. Sonraki görüntü+D aşaması: otomatik tag civarında
durma/başlama adaylarını ayrı belirsizlik aralıklarıyla çıkarıp dış D/canlı
oyun hedeflerinde doğrulamak; tüm tag aralığını veya top kaybını D yapmamak.

## V010 — Ayak bağlamı denemesi: kabul edilmedi, 7 Kasım 2026

Kullanıcının ayak/top karışması gözlemine karşı, yalnız otomatik kişi kutuları
ve hareketi kullanan isteğe bağlı `ball_foot_context` prototipi denendi.
Yakınlık tek başına eleme değildir: alt gövdede yüksek örtüşme, uzamış kutu ve
dört bağlı hareket gözlemi gerekir. Önceden iki bağımsız gözlem taşıyan top
izi korunur. Parametreler ve kabul koşulları `ball-foot-context-plan.json`
ile denemeden önce kaydedildi; kaynak maç 4 geliştirme, 6/9 daha önce görülmüş
tekrar doğrulama olarak belirtildi. Dokunulmamış test iddiası yoktur.

Sekiz eğitim kesitinin iki modunda mevcut V009 ile aynı sonuçlar alındı;
katman hiçbir adayı yeterli kanıtla elemedi. Eşleşmeyen kutular azalmadığı için
kabul koşulu geçilmedi, varsayılan akışa veya 8774 galerisine açılmadı. V1
kontrol koşusunun kare çıktısı önceki V009 dosyasıyla byte düzeyinde aynıydı.
Kullanıcı daha sonra ilk gözlemin net olmadığını, aday/tespit/tahmin gösterimini
karıştırmış olabileceğini açıkladı. Ayak hatası düzeltilmiş gibi sunulmadı;
gerekçesiz yeni sınıflandırıcı eğitilmedi. İsteğe bağlı kod yalnız deney olarak
kalır. 166 testlik paket bir isteğe bağlı AV atlamasıyla başarılı.

Kayıt: `C:/Users/Abra/FootballPrivate/foot-context-development-20261107`:
`before-run.json`, `association-audit-v1`, `acceptance.json`, `control-v1`.
Barcelona verisi kullanılmadı, donmuş temel değişmedi. Kaynak/etiket/başarı
ayrımı ve lisans durumu kullanıcıya ayrıca açıklandı.

## V009 — Dış kesitlerde zamansal top adayı takibi, 7 Kasım 2026

`ball-tracking-plan.json` sayısal mühendislik ayarları dış koşudan önce
kaydedildi. Konum/hız öngörüsü, kutu boyutu ve tespit güveniyle çoklu aday
ilişkilendirmesi uygulandı. Çift kutular ilişkilendirmede bastırılır, ham
veride korunur. Üç gözlemle onay, en fazla 0,2 s kısa öngörü; belirsizlik,
kesme/boyut/saat kopması ve sürede kimlik kapanışı vardır. Ölçüm ve tahmin
ayrı alanlardadır; tahmine dedektör ölçümü/kimliği yazılmaz.

Kaynak yalnız önceki SoccerNet eğitim galerisidir: üç görülmüş maçtan sekiz
kesit, iki modda 1.200 çıktı karesi ve önceki kısa örnekte 50 ek çıktı.
Barcelona verisi/görüntüsü kullanılmadı; dedektör ayarları veya donmuş sahiplik
modeli değişmedi. 161 testlik paket bir AV atlamasıyla başarılı; dokuz API
görünümünün takip alanları ve ölçüm/tahmin ayrımı kontrol edildi.

Tahminler dondurulduktan sonra eğitim referanslarıyla betimleyici ilişki
incelemesi yapıldı. SAHI 248/525 referans kutusuyla eşleşen ilişkili ölçüm
üretti, bunların 229'u onaylı izdeydi; 830 ölçüm eşleşmedi. Referans bulunan
216 öngörü gözleminin 27 merkezi referans kutusu içindeydi. Etiket kapsamı
olmayan anlar negatif sayılmadı. Kimlik değişimi sayısı yalnız ardışık
eşleşmiş referanslar arasındadır; düşük kapsamda sıfır olması kusursuzluk
kanıtı değildir. Başarı iddiası/model seçimi yapılmadı. Yanlış aday ve iz
kopmaları sürer; oyundaki top seçimi veya sahiplik girdisi üretilmez.

Kayıt: `C:/Users/Abra/FootballPrivate/temporal-ball-development-20261107`.
Galeri `http://127.0.0.1:8774/`; tahmin pembe kesikli, tespit düz, aday sarıdır.
Rehber: [zamansal top takibi](ZAMANSAL_TOP_TAKIBI_TR.md).
Sağlayıcı temizliği bekleyenleri sürer; bu bir teslim sürümü seçimi değildir.


## V008 — Aynı-kaynak saat ve tracking izdüşümü incelemesi, 7 Kasım 2026

Kullanıcının tracking/video kare saatini kontrol edip saha noktalarını görüntüye
taşıma isteği salt okunur yerel katmanla uygulandı. Kod matematiği/oynatma
kontrolleri yalnız sentetik kaynakta sınandı. Sağlanan maçta video görüntüsü
çözmeden MP4 paket PTS'leri, dosya bağları ve ATD/H kare şeması incelendi.

Taktik 199.319/199.319, yayın 164.487/164.488 video/tracking sayıları ve 25 FPS
ızgarası yapısal olarak uyumludur. Yayındaki son fazla tracking kaydı görüntüye
bağlanmaz. Bu, bağımsız görüntü hizası veya homografi doğruluğu doğrulaması
değildir; kayıtlarda bu alanlar false kalır. Offset arama/ayar/model seçimi yoktur.

`tracking_viewer` aynı karenin ham normalize kişi noktalarını H ile piksele
taşır. `tracking-projection.js` sunulan video karesiyle ATD/H kimliklerini
karşılaştırır; stale/missing/geçersiz veride işaret çizmez. Aspect ratio/DPR
dönüşümü korunur. Top, kutu ilişkisi, oyuncu kimliği ve sahiplik üretilmez.
Gerçek video yalnız kullanıcıya localhost üzerinden açılır, asistanla paylaşılmaz.

151 testlik paket 1 AV atlamasıyla başarılı; iki gerçek kaynağın API kare
sözleşmesi denetlendi. 50 karelik sentetik videoda oynatma ve geri adımda
görüntü/ATD/H aynı kaldı. Donmuş temel hash'i değişmedi; sağlayıcı temizliği
bekleyenleri sürer. Kayıt: `C:/Users/Abra/FootballPrivate/native-projection-review-20261107`.
Rehber: [izdüşüm incelemesi](IZDUSUM_INCELEME_TR.md).


## V007 — Proje görüntü ölçüm girişi ve bağlı inceleme, 7 Kasım 2026

`tools.match_analysis` kayıtlı video/config veya tamamlanmış dedektör koşusunu
`ImageAnalysis` ölçüm sözleşmesine bağlar. Kaynak/zaman, kişi/top adayları,
kutular, piksel konum/hızı ve kaynakla adlandırılmış izler korunur. Rol/takım/
oyuncu kimliği bilinmiyor, bütün top adayları seçilmemiş olarak kalır.
Referans alanları ve kanıtlanmamış rol iddiaları reddedilir; piksel/saha
koordinatları ayrıdır. Bu V1 sahiplik veya hibrit ölçüm kabulü üretmez.

Önceden görülen üç kaynak maçtaki sekiz eğitim kesitinin iki dedektör koşusu
aynı ayarlarla aktarıldı: 16×75 = 1.200 çıktı karesi, 600 farklı kaynak karesi.
Önceki kısa örnek ayrıca 2×25 çıktı verir. Yeni eğitim/ayar/model seçimi yoktur.
`image-integration-plan.json`, özel önce-kayıt ve kaynak/gözlem/çıktı hash'leri
izlenebilirliği sağlar. `vision_review --project-analysis` dokuz seçeneğin
tamamında bu proje çıktılarını okur; yeşil referans paneli modelden ayrıdır.

147 testlik paket bir isteğe bağlı AV atlamasıyla başarılı; JS sözdizimi,
dokuz bağlı API görünümü ve donmuş temel hash'i kontrol edildi. Görüntüden
rol/takım veya sahiplik başarısı ölçülmedi. Geliştirme girdisi yalnız izinli
dış/sentetik veri; sağlayıcı temizliği bekleyenleri korunur.

Özel kayıt: `C:/Users/Abra/FootballPrivate/project-image-integration-20261107`:
`before-integration.json`, `report.json`, `viewer-verification.json` ve
kesit/yöntem bazında `registration.json`, `frames.jsonl`, `summary.json`.
Rehber: [görüntü entegrasyonu](GORUNTU_ENTEGRASYONU_TR.md).


## V006 — Sekiz kesitli görsel inceleme galerisi, 7 Kasım 2026

Kullanıcının daha çok kesiti aynı arayüzde inceleme isteği için
`soccernet-gallery-plan.json` içerik görülmeden kaydedildi. Eğitim arşivinin
sıralı 0,8,16,24,32,40,48,56 indekslerinden SNGS-060/068/076/103/111/154/162/170
seçildi. Başlangıç kareleri 0,75,150,225,300,375,450,525; her kesit 75 kare,
25 FPS, 3 saniye. Metadata kaynak maç kimlikleri 4,6,9: sekiz ayrı maç
iddiası yoktur. Bu maçlar artık dokunulmamış test diye sunulamaz.

Kamuya açık, sabit HF commit'indeki eğitim ZIP'inden seçilmiş üyeler alındı.
Arşivde kareler karışık sırada olduğundan büyük blok önbellek denemesi
durduruldu; küçük HTTP aralıklarıyla paralel edinme tamamlandı. Başlık adı,
sıkıştırma türü, boyut ve ZIP CRC denetlendi; yerel SHA-256'lar kaydedildi.
Doğrulanmış başarılı aralıklar toplamı 193.609.622 byte; bu tam arşiv SHA
doğrulaması veya başarısız istekleri içeren ağ trafiği toplamı değildir.

Mevcut Nano/SAHI/ByteTrack ayarları değişmedi. Her iki yöntem aynı 600 kareyi
ayrı işledi; kaynak JPEG–FFV1 RGB eşitliği, 75'er karelik tahmin sırası ve
PTS, kaynak video bağı, aynı ağırlık/ayarlar, dondurulmuş temel hash'i ve
kutulu MP4'lerin 75'er kare çözülmesi denetlendi. Referans etiketleri
dedektöre verilmedi. Model seçimi veya yeni doğruluk ölçümü yapılmadı.

Oturum kesintisinde son kesitin normal koşusu 67 karede yarım kaldı.
`native-interrupted-20261107` altında ayrı korundu; son kesit yeniden
başlatılıp iki yöntemde de 75/75 tamamlandı. Tamamlanan yedi kesit yeniden
hesaplanmadı. Eski süreç kaydı ve edinme kaynak snapshot'ı ayrı saklandı.

Galeri `http://127.0.0.1:8770/`: sekiz kesit ve önceki bir saniyelik örnekle
dokuz seçenek. Seçici, önceki/sonraki kesit, döngü, peş peşe oynatma, dört
senkron görünüm, yavaşlatma ve yakınlaştırma var. Peş peşe geçiş tarayıcıda
doğrulandı; sekiz kesitin API, ilk/son JPEG ve kare eşleştirmeleri denetlendi.
141 testlik paket 1 isteğe bağlı AV atlamasıyla başarılı; JS sözdizimi de
kontrol edildi. Gerçek video dönüşümlerinin tamamı RGB hash denetiminden geçti.

Özel kayıt: `C:/Users/Abra/FootballPrivate/soccernet-gallery-20261107-v2`.
`acquisition.json`, `range-receipts.json`, `process-registration.json`,
`exposure-register.json`, `gallery.json`, `gallery-verification.json` ve
kesitlerin kaynak/tahmin/önizleme klasörleri. Ham veri Git deposu dışındadır.
Hibrit kabul koşulları ve dondurulmuş sahiplik modeli korunur; sağlanan yarışma
maçı bu geliştirmeye alınmadı. Sağlayıcı temizliği bekleyenleri sürer.


## V005 — SoccerNet profesyonel yayın eğitim örneği, 7 Kasım 2026

SoccerNet GSR 2024 kamuya açık eğitim arşivi, sabit HF commit'i
`3cc710eb6d53a23350a3d2863311c1c0a2e645d7` ile kaydedildi. İlk alfabetik
kesit SNGS-060'ın ilk 25 karesi ve referansı seçildi; görüntü başarı durumuna
göre seçilmedi. Test/valid/challenge içeriği okunmadı; game_id=4 aynı maça
ait kliplerin ileride ayrı doğrulama maçları sayılmasını önlemek için kayıtlı.
Araştırma kullanım koşulları korunur; ham veri/ağırlık yeniden dağıtılmaz.
İlk indirme zaman aşımında eksik kaldı; yeni edinme kaydı tamamlandı.

25 kaynak JPEG kayıpsız RGB video doğrulamasından geçti. Referans v1.3,
25 FPS ve kaynak boyutları eşleşti. Önceki Nano ve SAHI sayısal ayarları
değiştirilmeden iki koşu tamamlandı. Etiket/rol/takım/saha koordinatı girdi
yapılmadı; tahmin hash'leri kutu karşılaştırmasından önce kaydedildi.
IoU ≥0,5 bire bir karşılaştırmada normal yöntem kişi 409/425, top 0/25;
SAHI kişi 416/425, top 19/25 eşleşme verdi. SAHI'de ayrıca 175 kişi ve
11 top tahmini eşleşmedi; normal yöntemde 24 kişi eşleşmedi. Top ölçümü
şema denetimi sonrası keşifseldir; sonuçlar resmî metrik veya genel başarı
oranı değildir. Saha/kimlik/takım/sahiplik doğruluğu değerlendirilmedi.

Yeni model seçilmedi. Donmuş temel kaynaklar ve hibrit kabul koşulları
korundu; `hybrid_ready=false`. Sağlanan yarışma görüntüsü veya public skor
bu geliştirmede kullanılmadı. Sağlayıcı temizliği bekleyenleri sürer.
Ayrıntılar ve takip aşamaları: [SoccerNet planı](SOCCERNET_ASAMALARI_TR.md).


## V004 — Görüntü konumu, iz sürekliliği ve yerel kutulu video, 6 Kasım 2026

Mevcut RF-DETR/SAHI/ByteTrack prototipi doğrudan görüntü ölçümü üretecek
şekilde genişletildi. `vision_measurements.py`, kişi kutusu/ayak noktası ve
top merkezi adaylarını, kamera epoch'una bağlı kişi izlerini, piksel hızını
ve isteğe bağlı aynı-kaynak homografisinde saha metre adayını saklar.
Sahipsiz/çift iz kimliği, kayıp kare, kaybolma, kesme/boyut değişimi ve
kırpılmış ayak noktası bilinmeyen kalır. Kameranın değişmesi tekrar veya
canlılık sınıfı sayılmaz; epoch değişiminde gerçek ByteTrack sıfırlanabilir.

Kişi sınıfı futbolcu/takım değildir. Bütün top adayları korunur; havadaki
topun görüntü merkezi zemin/yükseklik ölçümüne dönüştürülmez. Matematiksel
homografi ve tespit güveni bağımsız kalibrasyon doğrulaması sayılmadı.
`frame_kind=unknown`, `calibration_validated=false`, `hybrid_ready=false`.
Mevcut hibrit güven koşulları ve donmuş H/A/X modeli değiştirilmedi.

Veri: önceden kayıtlı SoccerTrack 117092 eğitim klibinin ilk 125 karesi
mevcut kayıtlı byte-range önbelleğinden, yeni ağ isteği olmadan alındı.
Kayıpsız RGB hash'leri ve önceki ilk 10 kare eşleşmesi doğrulandı. Kaynak
klibin tamamı ve referansın tamamı alınmış/doğrulanmış sayılmaz; Drive
alternatifinin HF sürümüyle aynı içerik olduğu varsayılmadı. Önceden
görülmüş eğitim örneği yeni held-out test değildir.

Sayısal dedektör/dilimleme ayarları önceki prototipten değişmedi. Görüntü
değişimi ayarları sentetik mühendislik değerleridir. Kod ve iki çalışma
ayar hash'i işlemden önce kaydedildi. Native 125 karede 783 kişi gözlemi,
0 top adayı; SAHI ilk 25 karede 1.418 kişi gözlemi ve 3 karede toplam
3 top adayı üretti. Bunlar tekil/doğru kişi sayısı veya oyundaki doğru top
kanıtı değildir. Ayrı saha/rol/takım ve top adayı ilişkilendirmesi gerekir.
Gerçek dış klibe homografi verilmedi; saha koordinatı uydurulmadı.

Yerel CPU koşuları model yükü dahil yaklaşık 79/196 saniyede tamamlandı;
eşzamanlı küçük örnekler olduğundan temsil edici hız veya gerçek zamanlı
başarı iddiası yapılmadı. Kutulu MP4/JPG önizlemeleri kaydedildi, çıktı
kare sayıları çözülerek kontrol edildi. İzlemeyi kolaylaştıran 5 kat
yavaş gösterim yalnız sunum zamanını değiştirir. Görsel etiket yerleşimi
model kutularını veya ölçüm verisini değiştirmeden sadeleştirildi.
Görsel inceleme yalnız izinli dış SoccerTrack örneğinde yapıldı.

**126 test geçti.** Yeni testler piksel/saha aday hızını, kaynak kareyle
matris seçimini, kamera resetini, kayıp/çift izi, kesik ayak noktasını,
top yüksekliği belirsizliğini, kaynak homografisi provenansını, eksik
işlem aralığını ve sağlanan maçın önizlemeye kabul edilmemesini kapsar.
Normal ortam numpy 1.26.4 kaldı; mevcut ayrı görüntü ortamı kullanıldı.
Yeni ağırlık indirilmedi; resmî Nano SHA-256 aynı kaldı. Önceki görüntü
kaynakları ve yeni koşu kaynakları hash/snapshot ile ayrı korundu.

Özel kayıt: `C:/Users/Abra/FootballPrivate/vision-module-development-20261106`.
`sample-manifest.json`, `measurement-freeze.json`, `native-v2`, `sliced-v2`,
`native-preview-v3`, `sliced-preview-v3`, test kaydı ve `stage4-report.json`.
Sağlanan maç görüntüsü/etiketi/public skoru bu geliştirmeye alınmadı;
uzak görüntü çıkarımı veya yeni sağlanan-maç görüntü paylaşımı yapılmadı.
Futbol doğruluğu/parametre seçimi için referans sözleşmesi ve bağımsız
dış doğrulama hâlâ bekliyor. Rehber: [görüntü modülü](GORUNTU_ISLEME_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri tamamlanmış sayılmaz.

## H003 — Taktik öncelikli hibrit ölçüm ve kaynak geçiş koruması, 6 Kasım 2026

Kullanıcı politikası deneysel ölçüm katmanına uygulandı: yeterli ve doğrulanmış
zaman/görünürlük/kalibrasyon/oyuncu uyumu varsa görünür yayın ölçümleri tercih
edilir; geri kalanı taktik kaynaktan korunur. Dar/iki oyunculu kadraj, tekrar,
boş/bilinmeyen görüntü, kaynak çelişkisi ve toplu aşırı hızda yayın kapatılır.
İlişki belirsizliği tekil oyuncuda taktik ölçümü korur. Kısa kayıpta yalnız
taze otomatik ilişki ve mevcut yayın ölçümü kullanılabilir; konum üretilmez.
Top görünürlüğü, hareketi ve zemin dönüşümü ayrı korunur.

`development/hybrid_tracking.py` ve `hybrid_pipeline.py` mevcut hareket
akışına bağlandı. `continuity.py`, kaynak geçişi/kare atlamasını kesen
oyuncu/top çift maskelerini sağlar. Hız, dripling, erişim, temas/pas, takım
hareketi, uzun top ve duran top katmanları bu süreklilikten yararlanır.
Kaynak geçişi temas veya pas diye yorumlanmaz; bilinmeyen görüntü D yapılmaz.
Her oyuncu/top için kaynak, kaynak karesi/yuvası ve karar nedeni saklanır.
Ham girdiler değiştirilmez; oyuncu noktaları ortalanmaz.

Ayarlar: `hybrid-data-plan.json`, yalnız sentetik mühendislik değerleri.
Yeni model/teslim sürümü veya futbol doğruluğu seçilmedi. Donmuş `model.json`
ve sekiz `clean_model` kaynağı korundu; ana numpy 1.26.4 ortamı değişmedi.
Yeni üçüncü taraf kod/model paketi veya servis eklenmedi.

Kontrol: **119 test geçti**. Sentetik durumlar görünür/görünmez alt kümeyi,
permüte yuvaları, iki oyuncu/boş/tekrar/bilinmeyen görünümü, toplu/tekil
sıçramayı, yanlış devre/FPS/eşlemeyi, kalibrasyon kaybını, kısa kimlik bağını,
topun eksik/çelişkili/havada-belirsiz durumunu ve kaynak geçişinde yapay
hız/temas/pas oluşturmamayı kapsar. İnceleme dosyası/API'sinin mevcut
`usable_for_possession=false` işareti nihai kullanım için terfi ettirilmez.

Dış çalışma: sabit Metrica commit'i ve mevcut hazırlanmış dosya hash'leri
doğrulandı. Sample 1 train, Sample 2 validation ayrımı korundu; her maçın
ilk 1.500 karesinde yedi kontrollü senaryo koşuldu. Son koşu 14 koşul/21.000
senaryo karesidir. İki oyuncu, tekrar, geometri çelişkisi, inceleme eşlemesi
ve bilinmeyen görünürlük koşullarında yayın katkısı sıfır kaldı. Pozitif alt
kümede uygun yayın noktaları tercih edildi; toplu sıçrama bölümleri reddedildi.
İlk koşunun kaynakları snapshot ile korundu; yalnız mevcut inceleme JSON/API
biçimini açıkça reddetme uyumluluğu eklendikten sonra ikinci koşu tekrarlandı.
Sayısal ayarlar değiştirilmedi.

İkinci görünüm gerçek bağımsız kamera değildir; aynı dış tracking'in kontrollü
ölçüm/maske değişimidir. Görünürlük/canlılık/zemin bayrakları sentetiktir.
Bu, gerçek çift kamera veya görüntü sınıflandırma doğruluğu ve daha iyi
sahiplik skoru iddiası değildir. Önceden kullanılan dış maçlar yeni held-out
test diye sunulmadı; gerçek kamera doğrulaması hâlâ gerekir.

Kural kontrolü için resmî FAQ erişimi, genel kuralların yanında sağlanan maça
özgü örnek/sınır açıklamaları da döndürdü. Bu tesadüfi erişim özel kayda
yazıldı; içerik özellik, eşik, etiket, eşleme veya değerlendirme girdisi
yapılmadı. Bu geliştirmede sağlanan maçın görüntü/tracking çıktıları okunarak
ayar yapılmadı; yeni görsel paylaşım yapılmadı. Mevcut aday eşlemeler veya
salt sonlu ATD noktaları bağımsız görsel görünürlük yerine kullanılmadı.

Özel kayıt: `C:/Users/Abra/FootballPrivate/hybrid-development-20261106`.
`controlled-v1` ve `controlled-v2` kaynak kayıtları, dış girdilerden türetilen
ölçüm/provenans dizileri ve senaryo özetlerini; `stage3-report.json` birleşik
durumu içerir. Gerçek görünürlük, kadraj/tekrar ve ölçüm güveni girdilerini
üretecek görüntü prosedürü sonraki adımdır. Yarışma maçında yayın düzeltmesi
bu aşamada açılmadı. Rehber: [hibrit politika](HIBRIT_KAYNAK_POLITIKASI_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri değişmedi.

## S002 — Yerel saat OCR'ı, geometri desteği ve çift kamera incelemesi, 6 Kasım 2026

Amaç salt okunur otomatik zaman eşleme prototipidir. Hibrit sahiplik modeli
veya yeni teslim sürümü seçilmedi. `model.json` ve donmuş kaynaklar korundu.

Ayar kaynağı: `sync-review-plan.json`, yalnız sentetik mühendislik değerleri.
Sağlanan videoların ilk kare çözümünden önce OCR/ayrıştırıcı/geometri kodu ve
ayar hash'leri özel kayıtta donduruldu. Daha sonra yalnız video/ATD son kare
sözleşmesi ve ters zaman bağlantılarını reddetme gibi adaptör korumaları
eklenip geometri çalıştırmasından önce ayrıca kaydedildi. OCR, saat/geometri
algoritmaları ve sayısal ayarlar sağlanan sonuçlardan sonra değiştirilmedi.

Ortam: ayrı Python 3.10 CPU ortamında RapidOCR ONNX Runtime 1.4.4,
ONNX Runtime 1.23.2, av 16.0.1. Paket sürümleri `requirements-sync-lock.txt`,
paket içi OCR model SHA-256'ları ve kaynak/lisans bilgileri özel kayıtta.
Ana numpy 1.26.4 ortamı değiştirilmedi. Kareler/kırpmalar yalnız yerel OCR
belleğinde işlendi; görüntü kaydedilmedi veya asistan/uzak servise gönderilmedi.

Kontrol: 107 Python testi geçti. Normal/uzatma saatleri beş yapay görüntüde
okundu. Bilinen 3 saniye farkı ve tekrar aralığı olan iki yapay videoda
eşlenen bağlantıların farkı doğru bulundu, tekrar içi boş bırakıldı.
Sentetik TXT/XML/homografiyle uçtan uca koşucu, farklı takım sırası ve fazla
bir ATD kaydı sınandı. Sentetik geometri örneğinde slot permütasyonu ve
25/20 FPS desteklendi; statik/belirsiz zaman adayı doğrulanmadı.
Tarayıcıda çift oynatma, kare adımı/girişi, aralık seçimi ve boşlukta yayın
duraklatma/gizleme çalıştı. Ekran görüntüsü yalnız sentetik kayıttan alındı.

Sağlanan videolara uygulama: ilk kez yeni otomatik salt okunur saat okuması
yapıldı; önceki etiket/görüntü/türev veya public skorlar okunmadı. Taktikte
1.329 örnekten 1.008, yayında 1.097 örnekten 1.009 güven eşiğini geçen saat
okuması çıktı. Bunlar doğru okuma sayısı veya OCR doğruluğu ölçümü değildir.
846 benzersiz saat adayı incelendi: 494 geometrik destek, 81 belirsiz tepe,
268 yetersiz geometri ve 3 kaynak uyuşmazlığı. Derlenen 817 bağlantı toplam
4.968 saniye/82,8 dakika ve 21 kesintisiz aday aralık içeriyor. 388 bağlantı
geometri destekli, 429 yalnız saat adayı. Bu sayılar kapsam/gözlem bilgisidir;
bağımsız kare doğruluğu veya canlı yayın garantisi değildir. Seyrek örnekler
arasındaki kısa tekrarlar ayrıca doğrulanmalıdır.

Tüm bağlantılarda `usable_for_possession=false`. Oyuncu kimlikleri veya ham
tracking kaynakları birleştirilmedi, top/oyuncu görüntü modeli bu maçta
çalıştırılmadı, sahiplik çıkarımı değiştirilmedi. Kaynak çelişkisi, geçersiz
homografi ve eşleme boşluğu belirsiz kaldı. Eşleme doğrulaması başka maçlarda
tamamlanmadan bu adaylar teslim modelinin birleşim katmanı sayılmaz.

Özel kayıt: `C:/Users/Abra/FootballPrivate/video-sync-development-20261106`.
`stage2-freeze.json`, `alignment-freeze.json`, iki OCR kayıt/çıktı dizini,
`alignment-v1`, sentetik koşular ve kaynak bütünlüğü kayıtları burada.
Güncel izleyici girdisi `C:/Users/Abra/FootballPrivate/video-sync/alignment.json`.
Başlatıcı `ESLESME-IZLE.cmd`; rehber [ESLESTIRME_TR.md](ESLESTIRME_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri bu işlemle tamamlanmış sayılmaz.

## I001 — Yayın dosyaları ve salt okunur izleyici entegrasyonu, 6 Kasım 2026

Resmî Drive yayın klasöründeki TXT, XML ve homografi CSV yeniden indirildi;
SHA-256 değerleri mevcut yerel veri paketiyle birebir eşleşti. Yeni MP4
İndirilenler'den bağlandı, kaynak deposuna taşınmadı. Dosya kimlikleri/hash'leri,
video metadata'sı ve son paket kontrolü özel edinme kaydında tutuldu:
`C:/Users/Abra/FootballPrivate/broadcast-acquisition-20261106`.

Yayın başlatıcısı kendi zaman çizgisindeki ATD/XML/CSV/video ile çalışır;
taktik olayları bu saate bağlamaz. Homografi adaptörü normalize saha → piksel
yönünü, kare numaralarını ve sağlayıcı geçerliliğini korur. Tekil/eksik matris
ve eksik nokta için dönüşüm üretilmez. Ters dönüşüm metre ölçeğini açıkça ister.
Video/tracking sonundaki bir kayıt farkı eşleme sınırıyla ele alındı; ham ATD
silinmedi. Matris geçerliliği tespit/temas doğruluğu olarak değerlendirilmedi.

95 Python testi geçti. Sentetik videoda geçerli/geçersiz matris, piksel konumu,
kare adımı ve video ortak sınırı tarayıcıda kontrol edildi. Gerçek maçın
görüntü kareleri çözülmedi; metadata, dosya bütünlüğü ve yerel servis bağlantısı
kontrol edildi. Bu veri/arayüz entegrasyonudur; yeni model, eşik veya sürüm
seçilmedi. Donmuş `model.json` ve sekiz kaynak dosyası korundu. İki kameranın
otomatik eşlenmesi ve modelde birleştirilmesi henüz tamamlanmadı.

## V001 — Erişim süresi entegrasyonu ve yerel görüntü çalışma kontrolü, 5 Kasım 2026

Dal: `feature/reachability-vision`. Yeni model/teslim seçilmedi. Donmuş H/A/X
çıkarımı, `model.json` ve sekiz kaynak dosyasının hash'leri korundu.

Uygulama: simetrik konum/hız tabanlı erişim süresi, mevcut top hareketi temas
adaylarında mesafe belirsizliğine ek destek olarak bağlandı. Tek başına sahiplik
veya D üretmez; uçuşta yakınlık engelini kaldırmaz. Olay/sahiplik hedefi girdi
olmaz. Kayıp hız, devre ve sıçramalar gözlem bağı üzerinden ele alındı.

Dış veri/split: daha önce kayıtlı Metrica Sample 1 train, Sample 2 validation;
bu çalışmada toplam 286.162 karede uçtan uca kontrol yapıldı. Bütün sayısal
ayarlar sentetik test değerleridir; parametre taraması/seçimi ve doğruluk
değerlendirmesi yapılmadı. Erişim süresi her maçta 5 belirsiz temas adayını
ayırdı. Bu sayı doğrulanmış temas veya sahiplik başarısı değildir. Otomatik
tag/D/LONG BALL katmanları bu veri çalıştırmasında etkin değildi.

Görüntü: ayrı Windows/Python 3.10 CPU ortamı; RF-DETR 1.11.2 Nano, SAHI 0.14.0,
Supervision 0.29.0 ByteTrack. Ana ortam numpy 1.26.4 kaldı. 66 paket sürümü
`requirements-vision-lock.txt` içinde kayıtlı. `pip check` geçti. Resmî Nano
ağırlığının MD5'i yayımlanan varlıkla eşleşti; SHA-256:
`d8d6b9ee57d4d0ed2b1f305163624712a0532cb7bce0c747317984fc5457440d`.
Ek model ağırlığı veya bulut çıkarım servisi kullanılmadan çalışma kontrolü yapıldı.

Önce geometrik yapay videoda native 2, dilimli 1 kare ve yapay kutu dizisinde
iz sürekliliği çalıştı. Sonra CC BY 4.0 SoccerTrack 117092 eğitim klibinin
önceden seçilen ilk 10 karesi HTTP byte aralıklarıyla edinilip kayıpsız RGB
örneğe dönüştürüldü; karelerin RGB SHA-256 değerleri kaynak çözümüyle eşleşti.
Bu gerçek dış örnekte native 10 ve SAHI 2 kare işlendi. Sonuçlar gözlemdir;
takım/sahiplik etiketi veya bağımsız doğruluk skoru değildir.

Veri erişimi: kaynak/maç ayrımı/dosya kimlikleri içerikten önce
`vision-data-plan.json` ve özel ön kayıtla kaydedildi. İlk referans şema
örneğinde 0 tabanlı kare/-1 bayraklar, güncel belgelenen GT sözleşmesiyle
uyuşmadı. Tam referans ve klip indirmesi sırasında sağlayıcı indirme kotası
yanıtı verdi; devam isteği yapılmadı. Başarı değerlendirmesi onaylanmadı.
Olay noktalarından yeniden kurulan yardımcı top izi de bağımsız top gerçeği
veya kendi olaylarına karşı temas değerlendirme girdisi sayılmadı.

Senkronizasyon: otomatik saat gözlemlerinden yalnız aday aralık üreten modül
eklendi; tekrar/donmuş/kopuk saatleri çözülmüş saymaz ve hiçbir saat adayını
sahiplik birleştirmesi için hazır işaretlemez. OCR/geometriyle son eşleme ve
iki kamera birleştirmesi henüz tamamlanmadı. Yayın MP4 yolu bulunamadı;
bilinen yerel pakette yayın ATD/homografi dosyaları mevcut.

Kontrol: **91 test geçti**. Bunlar yön, takım/koordinat simetrisi, 10/25 FPS,
kayıp/sıçrama, uzun top etkileşimi, referans sözleşmesi, zaman damgası,
hash/provenans ve donmuş kaynak bütünlüğünü kapsar. Sağlanan yarışma maçı
görüntüleri/etiketleri veya public skorları seçim için kullanılmadı.

Özel kayıt kökü:
`C:/Users/Abra/FootballPrivate/vision-development-20261105`.
`stage1-report.json` güncel kaynak hash'leri, çalışma kontrolü sonuçları ve
bekleyenleri; `motion-smoke-output-v2` kayıtlı dış tracking çalıştırmasını;
`runtime-smoke-v1`, `real-native-v1`, `real-sliced-v1` görüntü kontrollerini;
`soccertrack-mot-train/sample-manifest.json` kayıpsız örnek edinimini içerir.
Tam plan: [UYGULAMA_PLANI_TR.md](UYGULAMA_PLANI_TR.md).

Sağlayıcı/sohbet temizliğiyle ilgili önceki bekleyen durum değişmedi. Bu kayıt
organizatör şartlarının tümünün tamamlandığı iddiası değildir.

## L001 — LONG BALL aralığında hareket ve yakınlık engeli, 4 Kasım 2026

Kullanıcı isteğiyle otomatik LONG BALL aralıklarında kesintisiz hızlı ve
uzun yer değiştiren top hareketi aranır. Net mesafe, süre ve yol tutarlılığı
ölçülür; eksik noktalar, yön dönüşleri, devre ve sıçramalar diziyi keser.
D/dripling bölgeleri hariç tutulur. Uçuş içindeki salt yakınlık sahipliği
bastırılır; temas/pas gibi ek kanıt ve uç noktalar korunur. Yükseklik iddiası
yoktur. Tag tek başına uzun top veya takım sahipliği hedefi değildir.

Veri/split: yalnız sentetik testler ve sentetik uçtan uca dosyalar.
`tests/test_long_ball.py` sayıları mühendislik örnekleridir. Dış maç ayar
seçimi/başarı değerlendirmesi veya yeni teslim sürümü yoktur. 72 test geçti;
bu bir futbol doğruluk skoru değildir. Yarışma görüntüleri, elle notları
ve public skorları seçim girdisi yapılmadı. Temel sürüm korundu.
Ayrıntılar: `docs/UZUN_TOP_KATMANI_TR.md`.

## D002 — otomatik SET PIECES + ölçülen bekleme/başlangıç, 4 Kasım 2026

Kullanıcı isteğiyle beş yeniden başlama türü için deneysel D katmanı eklendi.
Etiket arama ön bilgisidir; tüm etiket aralığı D kabul edilmez. Ölçülen
bekleme, yakın gözlenen oyuncu, uygun saha bölgesi ve süreklilikle desteklenen
yeniden hareket aranır. D başlangıcı ölçülen bekleme/çıkıştır; kesin düdük
anı iddiası yoktur. Kayıp top veya N/A takım etiketi tek başına D/H/A üretmez.

Veri/split: sentetik mühendislik senaryoları ve sentetik uçtan uca dosyalar.
Dış eğitim/doğrulama ya da parametre seçimi yapılmadı; verilen maçın görüntü,
elle not veya public skorlarından seçim girdisi alınmadı. Ayarlar
`tests/test_set_piece_dead_ball.py` içinde sentetik olarak kayıtlıdır.
63 test geçti. Bağımsız dış maçların eşleşen otomatik tag dosyaları ve
değerlendirilebilir D/canlı oyun hedefleri henüz yoktur; bu eksik tamamlanmadan
yeni teslim sürümü seçilmiş sayılmaz. Temel sürüm değişmedi ve yeni tam maç
çıktısı üretilmedi. Ayrıntılar: `docs/DURAN_TOP_KATMANI_TR.md`.

## V002 — yerel Smart Tagging olay tarayıcısı, 4 Kasım 2026

Kullanıcının tüm otomatik olayları video yanında anlamak için istediği salt
okunur görünüm eklendi. 638 kaynak olay yerel arayüzde korunur. Tekrarlanan
etiket grupları, bilinmeyen alanlar ve N/A takım değerleri değiştirilmez.
Model girdisi, elle doğruluk etiketi, düzeltme veya skor oluşturulmadı.
Görsel karşılaştırma için zaman atlama/aralık oynatma, filtreler, arama ve
aktif fazlar sağlandı. 53 Python testi ve sentetik tarayıcı kontrolleri geçti;
gerçek maç kareleri veya olay payload'ları hosted LLM'ye aktarılmadı.
Model/eşik seçimi yapılmadı; dondurulmuş kaynaklar değişmedi. Bu görünüm
bilimsel doğruluk değerlendirmesi değildir. Ayrıntılar:
`docs/TRACKING_IZLEYICI_TR.md`, `tools/smart_tag_view.py`.

## V001 — salt okunur yerel tracking/video arayüzü, 4 Kasım 2026

Kullanıcının açık isteği üzerine ham tracking mantığını açıklayan yerel
oynatıcı eklendi. Yarışma tactical tracking'i ve İndirilenler'deki tactical
video yalnız kullanıcının bilgisayarındaki arayüze bağlandı. Algoritma veya
eşik seçimi, tahmin üretimi, elle anotasyon veya public skor okuması yapılmadı.
Maç verisi kaynak deposuna alınmadı ve gerçek maç kareleri sohbet/QA görseli
olarak aktarılmadı. Görsel QA sentetik veride yapıldı. Video codec/metadata
erişimi ve sürenin kare sayısı/FPS ile uyumu kontrol edildi. 50 Python testi
geçti; tarayıcıda oynatma, adım, seçim ve dar ekran taşması kontrol edildi.
Bu kullanıcı aracı eğitim/validasyon deneyi veya model başarısı değildir.
Ayrıntılar: `docs/TRACKING_IZLEYICI_TR.md`.

## M003 — ortak takım hareketi değişimi, 4 Kasım 2026

Kullanıcının iki takımın ani hız değişimini top kaybı/kazanımı bağlamı olarak
kullanma önerisi uygulandı. Aynı gözlenen yuvaların önce/sonra ortalamaları,
hız büyüklüğü ve yönlü vektör değişimi ayrı hesaplanır. İki takımda değişim
aranır. Önce/sonra farklı takımlara ait yerel temas/birlikte hareket kanıtı
yoksa top kaybı doğrulanmış sayılmaz; yeni H/A ataması yapılmaz.

Veri/split: yalnız sentetik örnekler; dış maç ayar seçimi veya doğruluk skoru
yoktur. Test ayarları `tests/test_team_transitions.py` içinde kayıtlıdır.
48 test geçti: aynı hızda yön dönüşü, hızlanma, görünür oyuncu kümesi
değişimi, tek takım değişimi, eksik top kanıtı, aynı takım kanıtı,
devre/ölçüm kaybı ve uçtan uca parametre/çıktı kaydı sınandı. Teslim sürümü
seçilmedi; dış gerçek geçişlere göre doğrulama gereklidir. Temel model
korundu. Kaynak: `development/team_transitions.py`.

## M002 — oyuncu/top birlikte hareketi ve takım özetleri, 4 Kasım 2026

Kullanıcının dripling önerisi deney sahiplik algoritmasına eklendi. Kalıcı
yakınlık, aynı yuvada süreklilik ve top/oyuncu hız vektörü uyumu birlikte
aranır. Hızlı dripling kanıtı hızlı top engelini aşabilir. Rakibin birlikte
hareket kanıtı üzerinden pas aralığı yazılmaz. Takım başına ortalama hız
vektörü, ortalama hız büyüklüğü ve katılan yuva sayısı ayrı çıkarılır;
takım özetleri tek başına sahiplik belirlemez.

Veri/split: yalnız sentetik senaryolar; dış maç eğitimi/doğrulaması ve sayısal
ayar seçimi yoktur. Ayarlar `tests/test_player_motion.py` içinde sentetik
olarak kayıtlıdır. 39 test geçti: hızlı dripling, ters yönde eşit hız,
sabit durma, belirsiz yakınlık, devre/kayıp/sıçrama sınırları, eksik takım
kapsamı, eşit takım vektörlerinde farklı sahiplik ve 25 FPS aktarımı sınandı.
Yeni parametre/NPZ çıktıları uçtan uca sentetik test edildi. Futbol doğruluk
skoru veya seçilen teslim sürümü yoktur; dış dripling/sahiplik doğrulaması
henüz yapılmadı. Temel kaynaklar korundu. Ayrıntılar:
`development/player_motion.py`, `docs/HAREKET_VE_TEMAS_TR.md`.

## M001 — hareket/temas/pas uygulaması, 4 Kasım 2026

Kullanıcının hızlı top, yön değişimi ve aynı takım temas zinciri önerisi
ayrı deney katmanında uygulandı. Ayrıntılar: `docs/HAREKET_VE_TEMAS_TR.md`.
Veri: sentetik hareket, ölçüm kaybı, rakip temas, belirsiz yakınlık, ölçüm
sıçraması ve pas dizileri; ayrıca sentetik uçtan uca çalıştırıcı testi.
Dış maçlarda sayısal ayar veya başarı seçimi yapılmadı. Eğitim/doğrulama skoru
yoktur; D001'in dış maç ayrımı ileride kullanılabilir. Sentetik test ayarları
`tests/test_motion_possession.py` içinde kayıtlıdır. Seçilen sürüm: yok.
Gerekçe: dış temas/pas değerlendirmesi henüz yapılmadı. Temel model korunur.
Yarışma tracking değerleri/görüntüleriyle ayar seçilmedi; XML şeması kontrol
edildi. 28 testin tamamı geçti; bu bir futbol doğruluk skoru değildir.

## D001 — dış veri kapsamı, 4 Kasım 2026

Amaç: D katmanından önce saha dışına çıkış, bekleme ve oyuna dönüş için hangi
ölçümlerin ve değerlendirme hedeflerinin mevcut olduğunu belirlemek.

Kaynak: Metrica Sports Sample Data,
`e706dd506b360d69d9d123d5b8026e7294b13996`.
Plan SHA-256: `547ef460d5da98a2739bf35d66cf7fd12971b3dc7f2a91ec30eccd9c2a7af517`.
İki maça ait altı CSV'nin boyutu ve Git blob kimliği doğrulandı; ayrıca yerel
SHA-256 manifesti oluşturuldu. Ham içerik ve kare düzeyindeki çıktılar özel
çalışma dizininde tutuldu.

| Kapsam | Maç 1: eğitim | Maç 2: doğrulama |
| --- | ---: | ---: |
| Kare | 145.006 | 141.156 |
| Top koordinatı bulunan kare | 88.251 | 83.272 |
| Top koordinatı bulunmayan kare | 56.755 | 57.884 |
| BALL OUT olayı | 51 | 49 |
| Eşleştirilen aday duruş aralığı | 39 | 39 |
| Aday duruş aralıklarındaki kare | 16.518 | 13.640 |
| Bu aralıklarda top koordinatı bulunan kare | 0 | 0 |
| Top koordinatı bulunan SET PIECE başlangıcı | 65 / 77 | 71 / 80 |

Ayrım maç bazında ve indirme öncesinde kaydedildi. Önceki erişim geçmişi
doğrulanmadığı için bunlar dokunulmamış test maçları olarak tanımlanmaz.
Doğrulama verisi bu çalışmada yalnız kapsam raporu için okundu; ayar veya
model seçimi yapılmadı.

Aday aralık protokolü: `BALL OUT` son karesini dışarıda bırak, sonraki uygun
`SET PIECE` başlangıcından önce bitir. Aynı devrede olmalı; arada başka çıkış
veya kaydedilmiş canlı oyun varsa reddet. Bilinmeyen kareleri etiketleme.
Bu protokolün olay zamanlarıyla elde ettiği aralıklar tam D gerçeği değildir.
Faul sonrası serbest vuruş, eşleşmeyen aut başlangıçları ve tekrarlar bu
protokolde değerlendirilmez. Çizgiyi geçme anı ve hakem düdüğü ayrıca
doğrulanmış değildir.

Seçilen sınıflandırıcı ayarları: **yok**. Hız/bekleme/mesafe eşiği taranmadı.
Rapordaki çeyrek değerler betimleyici kapsam özetidir; parametre önerisi değildir.

Karar ve gerekçe: **D modeli seçilmedi veya teslim sürümüne eklenmedi.**
İki maçtaki 78 aday duruş aralığının tamamında top koordinatı kayıptır.
Bu aralıklarda topun bekleme geometrisini doğrudan ölçmek mümkün değildir.
Eksikliğin sağlayıcının veri hazırlamasından kaynaklanıyor olması mümkündür;
bu bir çıkarımdır, sağlayıcıdan doğrulanmış bir açıklama değildir. Bu veriyle
yalnız “top yoksa D” öğrenmek, başka sağlayıcıdaki gerçek top kaybını D ile
karıştırabilir. Eksiksiz canlı oyun negatifleri ve bağımsız sınır doğrulaması
olmadan böyle bir sürüm seçilmeyecek.

Ek gözlem: ham ardışık top koordinatlarından hesaplanan en yüksek hızlar
Maç 1'de yaklaşık 1.321 m/s, Maç 2'de 700 m/s'dir. Bunlar fiziksel top hızı
olarak yorumlanamaz; ölçüm süreksizliklerini gösterir. Bu incelemede noktalar
kırpılmadı ve bu değerlere bakılarak güvenilirlik eşiği seçilmedi. Top
güvenilirliği ayrı deneyde değerlendirilecek.

Sonraki veri koşulu: başka maçlarda D/canlı oyun etiketlerini ve olay sınırlarını
bağımsız değerlendirebilen; mümkünse duruş sırasında da top gözlemi veya
izinli eşzamanlı görüntü içeren bir kaynak/protokol. Mevcut aday aralıklar
protokol geliştirme için kullanılabilir; tek başlarına D sürümü seçmeye yetmez.

Temel model SHA-256:
`1efa8f1073c0c204613cdd5ad1882e4525364ada7d982a70bb27387b854ff6cc`.
Dondurulmuş sekiz çıkarım kaynak dosyasının kimlikleri işlem öncesi/sonrası
doğrulandı. Sağlanan yarışma maçı veya public referansı okunmadı. X'ten D'ye
çevrilen kare sayısı: **0**. Yeni model seçilmediği için tam maç yeniden
üretilmedi; eski dondurulmuş çıktı yeni sürüm doğrulaması olarak gösterilmedi.

Doğrulama: 19 test geçti; buna sentetik uçtan uca veri hazırlama/kapsam
incelemesi, devre/kayıp ölçüm sınırları, olay eşleştirmesi, bozuk kaynak
içeriğinin reddi ve dondurulmuş temel kaynakların korunması dahildir. Gerçek
iki dış maçın kapsam aracı da başarıyla tamamlandı. Bunlar D doğruluk skoru
veya yarışma performansı değildir.

Tekrarlanabilir dosyalar:

- Veri planı ve kullanım: `dead-ball-data-plan.json`, `docs/GELISTIRME_TR.md`.
- İndirme kaydı:
  `C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/metrica-coverage-v1/download-manifest.json`.
- Kaynak hash'leri, özellik dağılımları ve ayrıntılı kapsam raporu:
  `C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/audit-v1/report.json`.
- Kare düzeyindeki girdi/özellikler ve ayrı tutulan aday olay aralıkları:
  aynı `audit-v1` dizininin iki maç alt klasörü.

Bu çalışma sağlayıcı/sohbet temizliğinin tamamlandığını veya yarışma
organizatörünün bütün koşullarının karşılandığını iddia etmez.

# Deney kaydı

## K018 — Teslim zinciri ekibin bilgisayarında v2.15 ile baştan sona OK (ilk tam çalıştırma), 15 Kasım 2026

**Ne oldu.** Takım lideri `TESLIM-TEK-TIK.cmd`'yi 11:34'te başlattı. Dosya yerleştirme adımı dokuz dosyanın hepsini paket
klasörüne koydu (iki video Desktop ve Downloads'tan kopyalandı). Yükleme adımı saatlerce bekledi: `git diff --cached --stat`
uzun listeyi sayfalayıcıda açtı ve pencere "(END)" yazısında `q` tuşunu bekledi; takım lideri 16:25'te sordu, `q` ve Enter ile
devam etti. 16:28'de commit `668fc04` (v2.15, K007-K014 kayıtları) GitHub'a gitti; GitHub Actions bu commit'te başarılı
(11 dk 39 sn). Zincir 16:28-17:31 arasında çalıştı (63 dakika).

**Paylaşılabilir durum satırları** (`Desktop\logs\PAYLASILABILIR-durum.txt`; başka hiçbir çıktı okunmadı):

```
[ 1] ORTAM ..................... OK (Windows-10-10.0.19045-SP0, Python 3.10.11, numpy 1.26.4, scipy 1.11.4, pandas 2.1.4)
[ 2] DEPO ...................... commit 668fc04560ed, temiz
[ 3] SURUM ..................... OK (possession-v2.15)
[ 4] TESTLER ................... OK
[ 5] PLATFORM .................. AYNI
[ 6] VERI ...................... OK (taktik VAR, yayin VAR, videolar VAR, smart tagging VAR)
[ 7] GIRDI OKUMA ............... OK
[ 8] URETIM .................... OK (possession-v2.15, saatsiz)
[ 9] BICIM ..................... OK
[10] MAKULLUK .................. OK
[11] ON TESLIM ................. OK (possession-v2.15, saatsiz; onceki teslim dosyasindan FARKLI (eskisi .onceki olarak saklandi))
[12] SAAT OKUMA ................ OK
[13] SAATLI URETIM ............. OK (possession-v2.15, saatli)
[14] MAKULLUK .................. OK
[15] TESLIM .................... OK (possession-v2.15, saatli)
[16] SAATSIZ KARSILASTIRMA ..... AYNI
[17] TEKRAR URETIM ............. AYNI
[18] TEMIZ KLON ................ AYNI (commit 668fc04560ed)
[19] ORGANIZATOR DOGRULAYICI ... OK
[20] ACIK PENCERE .............. OK
[21] BELGE ..................... OK (LittleSickle.md = teknik belge + calisma kaydi)
SONUC: TESLIM HAZIR
```

**Ne anlama geliyor.**
- K013'ün son koşulu (zincir ekibin bilgisayarında OK; `URETIM` ve `TESLIM` satırlarında `possession-v2.15`) sağlandı. Elde
  kurallara uygun, geçerli bir v2.15 teslimi var: `FootballPrivate\teslim\LittleSickle.csv` ve `LittleSickle.md`.
- Windows 10 / Python 3.10.11, dokuz sentetik varyantta Linux'ta kaydedilen baytların aynısını verdi (`PLATFORM AYNI`); dosya
  ikinci çalıştırmada, saat okumaları olmadan ve GitHub'daki dalın temiz klonundan da aynı baytlarla üretildi.
- Girdi denetimi (DATA.md toplamları, 28 denetim), organizatörün doğrulayıcısı ve açık beş dakikadaki geçti/kaldı denetimi
  geçti. Bunlar doğruluk ölçümü değildir; dosyanın geçerli ve boru hattının bozuk olmadığını söyler.
- Bu çalıştırma v2.16'dan önceydi. v2.16 için zincir bir kez daha çalıştırılmalı (K017'nin kalan koşulu); o çalıştırma
  OK bitmezse ya da daha alt bir basamak yazarsa bu v2.15 teslimi geçerli kalır.

**Düzeltme.** `GIT-YUKLE-V2.cmd` artık git'i `--no-pager` ile çağırır ve `TESLIM-TEK-TIK.cmd` içinden başlatıldığında tuş
beklemez (hata olmadıkça). Veri türü dosyaları reddeden koruma değişmedi.

## K017 — possession-v2.16: taktik kameranın kaybettiği oyuncular yayın kamerasından eklenir (kayıtlı doğrulama geçti; sürüm), 15 Kasım 2026

**Ne.** v2.16 = v2.15 + bir adım (`possession/playerfill.py`): yayın dosyaları varsa ve top doğruluk kapısı açıksa (iki kamera
topta 0,50 m içinde anlaşıyor), zaman hizalaması ve oyuncu tabanlı kayıttan sonra **1,5 m çevresinde hiçbir takımdan taktik
oyuncu bulunmayan** yayın oyuncusu, modellerin gördüğü takip verisine eklenir (yayın izinin verdiği takımla, iz başına bir ek
yuvada). Taktik konumlar hiç değiştirilmez. Kaleci takım denetimi eklenmiş oyuncularla birlikte çalışır; top önceki gibi
doldurulur. Yayın dosyası yoksa ya da kapı kapalıysa çıktı v2.15'in çıktısıdır (test: adım kapalıyken `run216`, `run215` ile aynı
baytları yazar). Kullanılan düzeltme, yayın topunu düzelten kare başına kaymanın aynısıdır.

**Neden.** K016: ikinci kameraya öncelik vermek kazandırmadı; kazandıran tek kullanım, birinci kameranın kaybettiği oyuncuları
eklemekti. Otomatik takip, oyuncuları en çok birbirine yakın olduklarında bir iki saniyeliğine kaybeder; yayın kamerası topu
izlediği için çoğu zaman onları görür.

**Plan (sonuçlardan önce).** `possession-v216-plan.json`, kayıt 15:01:19 (ilk doğrulama satırı 15:04:54). Kural ve tek sabiti
(1,5 m) kayıttan önce sabitlendi; doğrulama betiği keşifteki bir satırı birebir yeniden üretti. 16 yeni bozulmuş kopya (4 maç ×
4 tohum, tohumlar 28100...), benzetilmiş ikinci kamera. İki kol aynı kopyayı, akışı, hizalamayı, kaydı, top doldurmayı ve
modelleri paylaşır; yalnız aday kol oyuncu ekler. Kapılar v2.12-v2.15 planlarındaki yedi kapı ve eşiklerdir; adayın sürümden
farklılaştığı koşullara taşındı (ikinci kamera olmadan aday hiçbir şeyi değiştirmez).

**Sonuç (spellF1; `possession-v216-results.json`).**

| koşul | v2.15 | aday | fark | DFL | Metrica | daha iyi / kötü | en kötü kopya | ikinci model olmadan fark |
|---|---|---|---|---|---|---|---|---|
| iyi yayın kamerası, 16 kopya | 0,6864 | 0,6968 | +0,0104 | +0,0098 | +0,0111 | 13 / 3 | -0,0056 | +0,0089 |
| orta kalitede yayın kamerası, 8 kopya | 0,6861 | 0,6934 | +0,0073 | +0,0077 | +0,0069 | 5 / 3 | -0,0026 | +0,0092 |
| oyuncu kaybeden / uyduran yayın kamerası, 8 kopya | 0,6930 | 0,6974 | +0,0044 | +0,0088 | -0,0000 | 6 / 2 | -0,0148 | +0,0039 |
| ekip arkadaşının benzeticisiyle taktik kopya, iyi yayın, 4 kopya | 0,7031 | 0,7035 | +0,0004 | +0,0014 | -0,0006 | 1 / 3 | -0,0047 | +0,0006 |

| kapı | eşik | değer | sonuç |
|---|---|---|---|
| G1 kazanç (iyi yayın, 16 kopya) | ≥ +0,008 | +0,0104 | geçti |
| G2 DFL kopyaları (8) | ≥ +0,008 | +0,0098 | geçti |
| G3 Metrica kopyaları (8) | ≥ −0,002 | +0,0111 | geçti |
| G4 en kötü kopya | ≥ −0,010 | -0,0056 | geçti |
| G5 macroF1 | ≥ −0,003 | +0,0019 | geçti |
| G6 öteki akışlar (orta; oyuncu kaybeden / uyduran) | her biri ≥ 0,000 | +0,0073; +0,0044 | geçti |
| G7 öteki benzetici (4 kopya) | ≥ 0,000 | +0,0004 | geçti (kıl payı) |

"İyi" koşulda eklenen konumlar taktik oyuncu konumlarının ortalama %2,2'si; puanlanan karelerin %30'unda en az bir
eklenmiş oyuncu var. "Orta" koşulda eklenenlerin %68'i, oyuncu kaybeden / uyduran akışta %52'si gerçek bir oyuncunun 1 m
yakınında; kazanç yine de sıfırın üstünde.

**Karar.** Yedi kapının yedisi geçti; kayıtlı kurala göre aday seçildi ve **possession-v2.16** olarak donduruldu
(2026-11-15 17:05; `possession-v216-release.json`; `run216.py`, `run215.py`'den birebir metin değişiklikleriyle türetildi).
Basamak sırası (`possession-release.json`): v2.16 → v2.15 → v2.11k → v2.11g → v2.9g → v2.5b → v2.5b yalnız taktik.

**Entegrasyon denetimleri (kayıtlı teslim koşulları).**
- Python 3.10.20 / numpy 1.26.4 altında çalışıyor.
- Platformlar arası bayt denetimi artık 11 sentetik varyant (ikisi yeni: taktik izleri altışar saniye kaybolan paketlerde
  oyuncu eklenen v2.1 ve v2.3 yolları); 11'i de Python 3.10 / numpy 1.26.4 ile Python 3.13 / numpy 2.5.3 altında aynı bayt.
- Bütün testler: 467 test, Python 3.13 altında 4 atlama, Python 3.10 (sabitlenmiş paketler) altında 15 atlama, hata yok.
- Tam boy zincir provası (K003 sentetik paketi + K011'in uydurma Smart Tagging dosyası, `possession-v216-rehearsal.json`): bütün
  adımlar OK, 1006 sn (v2.15 zinciri 761 sn), en çok 2,20 GB bellek (v2.15: 1,53 GB). Bu sentetik pakette
  67 338 oyuncu konumu eklendi (48 515 karede); teslim dosyası v2.15 zincirinin dosyasından puanlanan karelerin
  %0,7'sinde farklı; paketin etiketlerine göre spellF1 0,7826 (v2.15 zinciri 0,7721). Bağlantı ve boyut denetimidir; doğruluk ölçümü
  değildir, hiçbir seçimde kullanılmadı.
- Ek R'ye "Players added from the broadcast camera" satırı eklendi (yalnız kategori: kullanıldı / eklenecek oyuncu yok /
  kullanılmadı; sayı yok).

**Kalan koşul.** Zincirin ekibin bilgisayarında OK bitmesi; `URETIM` ve `TESLIM` satırlarında `possession-v2.16` yazmalı. Daha
alt bir basamağın adı yazarsa teslim edilen o basamaktır ve belgeler ona göre düzeltilir.

**Sınırlar.**
- İkinci kamera benzetimdir; oyuncuları temiz dış konumlardan gelir. Dört koşulun üçünde penceresi içinde hiç oyuncu
  kaybetmez ve uydurmaz; dördüncüsü uydurulmuş tek bir hata düzenidir (orada kazanç +0,0044, bir kopya -0,0148).
- Sağlanan yayın verisine bakılmadı: ne sıklıkta oyuncu kaybettiği ya da uydurduğu bilinmiyor. Yayın verisinde bir takımın
  altında taşınan ama taktik veride olmayan bir hakem, oyuncu olarak eklenir.
- G7 kıl payı geçti (+0,0004; 4 kopyanın 3'ünde hafif eksi): az oyuncu kaybeden kopyalarda adım neredeyse hiçbir şey
  değiştirmiyor.
- Adım, dört geliştirme kopyasında yedi seçenek arasından seçildi; doğrulama kopyaları yeni, maçlar yeni değil. Aynı gün aynı
  maçlarda incelenen dördüncü fikirdi (K014, K015, K016). Organizatör, tek maçta 0,04'ün altındaki farkların gürültü olduğunu
  söylüyor.
- Bu, v2.15 planındaki "ikinci modelle başka aday kaydedilmez" kaydını değiştirmez: iki kolda da ikinci model aynıdır.

## K016 — İkinci kameraya öncelik vermek işe yaramıyor; işe yarayan, birincinin göremediğini eklemek (keşif; bir aday çıktı), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 12:24'te sordu: yayın kamerası daha yakından ve net görüyor; taktik kamerayla tutarlı olduğu
yerlerde yayın kamerasına öncelik versek, az sayıda oyuncu görse bile o noktada onu temel alsak daha iyi olmaz mı? Ayrıca şu an
maçın ne kadarında hangi kamerayı kullanıyoruz? Bu kayıt geliştirme kopyalarında benzetilmiş ikinci kamerayla yapılan keşiftir;
plan kaydedilmedi. Sağlanan maç açılmadı. Sayılar: `possession-k016-camera-priority.json`; betikler:
`experiments/possession_v2/v218/` (`cam1.py`, `cam2.py`, `cam3.py`).

**Şu an hangi kameradan ne alıyoruz.** Taktik takip verisi her karede temeldir (bütün oyuncular ve top). Yayın takip verisinden
yalnız top alınır; yalnız taktik top eksikse, o kare için kabul edilmiş bir yayın karesi varsa ve iki kamera topta 0,50 m içinde
anlaşıyorsa. Yayın oyuncuları yalnız kalibrasyon hatasını ölçmek için kullanılır. Videoların görüntüsünden yalnız maç saati
okunur. Sağlanan maçtaki oranlar bu kayıtta yoktur (maç verisi ve ondan hesaplanan sayılar ajana verilmez). Benzetilmiş
kopyalarda (yayın "iyi" düzeyde, 8 kopya, puanlanan karelerin payı): taktik top %46, yayından doldurulan %15, iki kamerada da
top yok %40; iki kamera topu birlikte %22 karede görüyor (%20'inde 0,5 m içinde). Kabul edilmiş yayın karesi olan
kareler %64.

**Yöntem.** Dört doğrulama maçı (J03WN1, J03WR9, MET1, MET2), maç başına iki bozulmuş kopya; her kolda v2.15 kararı. İkinci
kamera temiz konumlardan benzetildi (top çevresinde pencere, yakın çekim ve tekrarlar, çekim başına kalibrasyon kayması, gürültü),
üç düzeyde: **keskin** (yayın, taktik kopyadan belirgin biçimde daha hassas: top hatası ortanca 0,03 m, taktikte
0,15 m; oyuncularda 0,04 m ve 0,13 m), **iyi** ve **orta** (v2.5 / v2.9 / v2.15 doğrulamalarındaki düzeyler). Hizalama, kayıt
(registration), kapı ve top doldurma her seçenekte sürümdeki gibidir; yalnız modellerin gördüğü top ya da oyuncular değişir.

**Sonuç: sürüme göre spellF1 farkı** (parantez içinde: daha iyi / daha kötü kopya sayısı).

| | seçenek | keskin yayın | iyi yayın | orta yayın |
|---|---|---|---|---|
| T | ikinci kamera hiç kullanılmaz | -0,0428 (0/8, 8 kopya) | -0,0356 (0/8, 8 kopya) | -0,0383 (0/4, 4 kopya) |
| B1 | iki kamera 0,5 m içinde tutarlıysa top yayından | -0,0007 (5/3, 8 kopya) | +0,0008 (4/4, 8 kopya) | -0,0051 (0/4, 4 kopya) |
| B2 | iki kamera da topu görüyorsa top hep yayından | -0,0016 (1/3, 4 kopya) | -0,0047 (1/3, 4 kopya) | — |
| C | tutarlı yerde iki topun ortalaması | -0,0049 (1/3, 4 kopya) | +0,0002 (2/2, 4 kopya) | — |
| P | tutarlı top ve tutarlı oyuncular yayından | +0,0022 (5/3, 8 kopya) | +0,0002 (6/2, 8 kopya) | -0,0036 (0/4, 4 kopya) |
| F | taktiğin kaybettiği oyuncular yayından eklenir | +0,0057 (3/1, 4 kopya) | +0,0097 (3/1, 4 kopya) | — |
| PF | P ve F birlikte | +0,0047 (3/1, 4 kopya) | +0,0114 (3/1, 4 kopya) | — |

- **Önceliği yayına vermek kazandırmıyor.** Yayın beş kat daha hassas olsa bile fark ±0,002 içinde; yayın daha kabaysa
  −0,004 / −0,005. İki ölçüm yarım metre içinde anlaşıyorsa hangisini seçtiğimiz az şey değiştirir; modelleri sınırlayan,
  eğitildikleri düzeyin altındaki hassasiyet değil.
- **İkinci kameranın değeri, birincinin görmediğini görmesinde.** İkinci kamera hiç kullanılmazsa puan 0,036-0,043 düşüyor
  (8 kopyanın 8'inde). Tutarlı oyuncuların %24'ü (topa 15 m'den yakın olanların %70'u) yayından alınabiliyor, ama almak bir
  şey kazandırmıyor.
- **Taktiğin kaybettiği oyuncuları eklemek (F) kazandırıyor:** keskin yayında +0,0057, iyi yayında +0,0097 (4'er kopya).
  Yayın akışı kendi de oyuncu kaybedip uydursa ve takımları karıştırsa bile (`cam3.py`: her iz zamanın %10'unda yok, dört hayalet
  iz, iki iz daha yanlış takımda; eklenen konumların yalnız %41-67'si gerçek oyuncu) +0,0069 (en kötü kopya -0,0006).
  12 karşılaştırmanın 9'unda daha iyi, en kötüsü -0,0027. Konumları da değiştiren PF belirgin biçimde daha iyi değil ve taktik
  konumlara dokunuyor.

**Karar.** F, önceki planların kapılarıyla aday olarak kaydedildi (`possession-v216-plan.json`, K017). Öteki seçenekler
kullanılmadı.

**Sınırlar.** Karşılaştırma başına 4 (B1 ve P için 8) geliştirme kopyası; 0,005'in altındaki farklar kopyalar arası
dağılımın içindedir. İkinci kamera benzetimdir; sağlanan yayın verisinin nasıl davrandığına bakılmadı. Sayılar bozulmuş dış
kopyalarda başka sağlayıcıların etiketleriyle uyumdur; yarışma puanı değildir.

## K015 — Smart Tagging duran top etiketiyle "kaçırılan duran topu zorla yaz" fikri: ölçüldü, kazanç çok küçük (sürüm değişmedi), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 11:47'de şunu sordu: Smart Tagging bir aralık için duran top diyorsa ve biz o aralıkta hiç duran
top yazmamışsak, orada mutlaka bir duran top vardır; ölü top olasılığının en yüksek olduğu yere bir duran top koyup sonra başını
ve sonunu bulsak puan artar mı? Bu daha önce denenmemişti: v3.0 / v3.1 (P002) etiketleri ikinci aşamaya öğrenilen kanıt olarak
vermişti. Organizatörün belgeleri fikri destekliyor ("every set piece is a restart and every restart ends a dead-ball stretch"),
ama aynı yerde etiketlerin otomatik olduğu, sahte ve eksik etiket içerdiği de yazıyor. Bu kayıt yalnız geliştirme ve raporlamadır:
plan kaydedilmedi, doğrulama yapılmadı, hiçbir şey seçilmedi, teslim sistemi **v2.15** olarak kaldı. Sağlanan maç ve etiket dosyası
açılmadı. Sayılar: `possession-k015-tag-rescue.json`; betikler: `experiments/possession_v2/v217/`.

**Veri.** K014'ün 42 geliştirme kopyası (5 dış maç) ve bunlar için saklanan v2.15 kararı. Dış maçlarda Smart Tagging olmadığı için
duran top etiketleri **benzetimle** üretildi: gerçek yeniden başlama anının çevresinde birkaç saniyelik pencere (v3 planındaki
benzetici), tür başına sayılar DATA.md'de yayımlanan sayılara göre (taç 26, korner 12, kale vuruşu 10, serbest vuruş 5, gol sonrası
başlama 4), ardından zaman kayması ve sahte etiket eklenerek.

**Bu durum ne sıklıkta oluyor?** Kopya başına 85,4 duran top (yeniden başlamayla biten ölü top aralığı) var. Kararımız bunların
%93'ünde en az bir D karesi yazıyor; hiç D yazmadığımız aralık kopya başına 5,9 (DFL maçlarında %2, Metrica maçlarında %10-20).
Kaçırılanlar kısa (ortanca 4,7 sn; bulunanlarda 21,3 sn) ve top bu karelerin yalnız %9'unda görünüyor.
Kaçırılan aralıklarda en yüksek ölü top olasılığının ortancası 0,63: model çoğunda bir şey görüyor ama çözücünün
D'ye giriş-çıkış maliyetini aşamıyor.

| tür | kopya başına | hiç D yazmadığımız | sağlanan dosyada yayımlanan etiket sayısı |
|---|---|---|---|
| taç | 35,5 | %7,4 | 26 |
| serbest vuruş (Metrica maçlarında kale vuruşları da burada) | 33,9 | %9,5 | 5 |
| kale vuruşu | 6,7 | %1,4 | 10 |
| korner | 5,7 | %0,0 | 12 |
| gol sonrası başlama | 3,7 | %0,0 | 4 |

Yayımlanan sayılarla etiketler bir maçtaki yeniden başlamaların yaklaşık yarısını kapsıyor (benzetimde kopya başına 40,5 / 85,7)
ve en çok kaçırdığımız türden (serbest vuruş) yalnız 5 etiket var. "Etiket var, bizde D yok" durumu kopya başına 2,4 kez oluşuyor.

**Tavan (etiketler kusursuz, aralığın gerçek sınırları biliniyor).**

| | bütün yeniden başlamalar etiketli olsaydı | yayımlanan sayılarla |
|---|---|---|
| kaçırılan aralığı D yaz | +0,0091 | +0,0029 (DFL +0,0011, Metrica +0,0045) |
| D'nin bitişini gerçek yeniden başlama anına çek | +0,0014 | +0,0003 (13 kopyada daha kötü) |
| ikisi birlikte | +0,0161 | +0,0040 |

**Denenen kural.** Etiket penceresinin 5 sn öncesinden sonuna kadar kararımızda hiç D yoksa: çözücünün o bölgede D'den geçmesinin
en ucuz olduğu kare bulunur (değiştirilmemiş v2 çözücüsünün ileri-geri puanları); bu maliyet bir sınırın altındaysa (120 log
birimi = bir D parçasının giriş-çıkış maliyeti) çözücü o kare D'ye zorlanarak yeniden çalıştırılır; D parçasının başı ve sonu
böylece modelin olasılıklarından çıkar. spellF1 değişimi (42 kopya ortalaması):

| etiket benzetimi | sınır 120: ortalama | en kötü kopya | kopya başına zorlanan | gerçek bir duran topa denk gelen | sınırsız: ortalama | en kötü kopya |
|---|---|---|---|---|---|---|
| kusursuz etiket (kayma yok) | +0,0011 | -0,0011 | 2,2 | %99 | +0,0015 | +0,0000 |
| bir saniye kadar kayan etiket, %5 sahte | +0,0016 | -0,0031 | 2,9 | %94 | +0,0012 | -0,0080 |
| tipik (±1,5 sn kayma, 0,3-3 sn dağılma, %0-15 sahte) | +0,0010 | -0,0034 | 2,7 | %89 | -0,0003 | -0,0073 |
| gürültülü (yarı sayıda etiket, 1,5 sn gecikme, 3 sn dağılma, %15 sahte) | +0,0005 | -0,0019 | 2,0 | %87 | -0,0012 | -0,0074 |
| tipik, %30 sahte etiket | +0,0008 | -0,0029 | 3,6 | %76 | -0,0045 | -0,0183 |

Sınırın başka değerleri (60-110), arama bölgesinin 3 / 8 sn öncesinden başlaması ya da 2 sn sonrasına uzaması, zorlanan parçanın
en az 1 sn yapılması ve parça ile bir sonraki takım değişimi arasındaki kısa sahipliğin D yazılması bu tabloyu değiştirmedi
(hepsi -0,0001 ile +0,0016 arasında). Etiketin "vuruşu kullanan takım" bilgisinin düzelteceği bir şey yok: bulunan
yeniden başlamalardan sonra yazdığımız ilk takım 651 durumun 9'unda yanlış.

**Sonuç.** Fikir mantıklı ve kural beklendiği gibi çalışıyor, ama kazanılabilecek puan çok küçük: kusursuz kullanımda bile
+0,003, denenen kuralla +0,0005 ile +0,0016 arası; sınır konmazsa sahte etiketler zarar veriyor (-0,0045'e kadar).
Bu, şimdiye kadarki her adaya uygulanan kazanç kapısının (+0,008) onda biri ve organizatörün tek maçta gürültü saydığı farkın
(0,04) çok altında. Gerçek etiketlerin hata düzeni bilinmiyor ve ölçülemez; etiketleyici topun izine dayanıyorsa zaten bizim de
bulduğumuz duran topları etiketliyor olabilir. Bu yüzden aday olarak kaydedilmedi ve sürüm değiştirilmedi.

**Sınırlar.** Geliştirme kopyaları daha önce kullanıldı ve kural seçenekleri bunların üzerinde karşılaştırıldı; bu bir doğrulama
değildir. Etiketler benzetimdir. Sayılar bozulmuş dış kopyalarda başka sağlayıcıların etiketleriyle uyumdur; yarışma puanı değildir.

## K014 — Hata örüntüleri: puanı nerede kaybediyoruz, ortak nedenler ve bunlara dayalı denemeler (sürüm değişmedi), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 03:42'de şunu istedi: sistemin yanlış yaptığı yerleri bul, ortak örüntüyü çıkar, buna göre yeni
yöntemler geliştir ve bunları başka maçlarda dene. Bu kayıt o çalışmadır. Yalnız geliştirme ve raporlamadır: plan kaydedilmedi,
doğrulama yapılmadı, hiçbir şey seçilmedi, teslim sistemi **v2.15** olarak kaldı. Sağlanan maç açılmadı. Sayılar:
`possession-k014-error-patterns.json`; betikler: `experiments/possession_v2/v216/`.

**Veri ve yöntem.** Önceki doğrulamalarda puanlanmış 42 geliştirme kopyası (J03WN1 10, J03WR9 10, Metrica 1 10, Metrica 2 10,
Metrica 3 2; 9'u ekibin ikinci bozma benzeticisiyle). Bu kopyalardaki olasılıkları üreten modeller o maçları eğitimde görmedi.
Organizatörün eşleştirmesi birebir yeniden yazıldı (42 kopyada resmî puanla aynı). Bir sahipliğin "kredisi" = beş IoU eşiğinden
kaçında eşleştiği. spellF1 = 2 × toplam kredi / (gerçek + tahmin edilen sahiplik sayısı) olduğu için, kayıp (1 − spellF1) her
gerçek ve her tahmin edilen sahipliğin (1 − kredi) payına tam olarak bölünür. Böylece "kaybın yüzde kaçı nereden" sorusu kesin
yanıtlanır.

**Genel tablo.** 16.938 gerçek, 12.987 tahmin edilen sahiplik; spellF1 0,673. Kaybın %70'i gerçek
sahiplik tarafında (bulamadıklarımız ve yarım eşleşenler), %30'u tahmin tarafında (fazladan ya da yarım eşleşen tahminler).

| gerçek sahipliğin süresi | gerçeklerin payı | ortalama kredi | kaybın payı | tahminlerin payı | tahminlerin kredisi |
|---|---|---|---|---|---|
| 1 sn altı | %13 | 0,10 | %20 | %4 | 0,45 |
| 1-2 sn | %16 | 0,35 | %18 | %12 | 0,60 |
| 2-4 sn | %21 | 0,58 | %15 | %21 | 0,73 |
| 4-8 sn | %19 | 0,74 | %8 | %23 | 0,78 |
| 8 sn üstü | %31 | 0,84 | %9 | %40 | 0,88 |

| kaybın türü | kaybın payı |
|---|---|
| hiç eşleşmeyen gerçek sahiplik (gerçeklerin %32'si) | %56 |
| — tahmin o sırada öteki takımı gösteriyor | %29 |
| — tahmin aynı takımı gösteriyor ama parça birleşmiş ya da kaymış | %18 |
| — tahmin ölü top diyor | %9 |
| bulunan ama sınırları tutmayan çiftler (iki taraf birlikte) | %29 |
| hiç eşleşmeyen tahmin (tahminlerin %12'si) | %15 |

**Örüntü 1: kısa sahiplikler.** 2 saniyeden kısa sahiplikler gerçeklerin %29'u, kaybın %38'i. Tipik durum: A takımı
oynarken B bir-iki saniyeliğine topu alır, sonra yine A. Sistem bunu tek bir A sahipliği olarak yazar; hem B'nin kısa sahipliği
hem de A'nın iki parçası kaybolur. Bu kısa sahipliklerde iki model ailesinin doğru takıma verdiği ortalama olasılık yalnız
0,25: yani mesele çözücünün yumuşatması değil, modellerin bunu hiç görmemesi.

**Örüntü 2: zamanlama.** Bulunan sahipliklerde kaybın %29'u sınırların yerinden. İki tarafı da en az 2 sn süren
top değişimlerinde (3 sn içinde bulunan / 0,5 sn içinde zamanlanan):

| | top görünüyor | top görünmüyor |
|---|---|---|
| DFL | %89 / %62 | %74 / %26 |
| Metrica | %91 / %74 | %74 / %29 |

Örneklere tek tek bakıldığında ortak neden görülüyor: top yeni takıma doğru yoldayken model topun kimde biteceğini (ilerideki
karelerden) bildiği için olasılığı erkenden çevirir; etiket ise yeni takımın oyuncusu topa değdiği anda değişir. Top görünmüyorken
zamanlama zaten tahmindir.

**Örüntü 3: etiket kaynağına özgü olanlar.** 8 saniyeden uzun gerçek sahipliğin "ölü top" diye tahmin edilmesi neredeyse yalnız
Metrica vekil etiketlerinde görülüyor (kopya başına 14; DFL'de 0,4): olaylardan türettiğimiz etiketler bazı duraklamaları
bilmiyor. Bu bir model hatası değil, etiket kusurudur.

**Örüntüler maçtan maça aynı** (kaybın payları):

| maç | kopya | spellF1 | gerçek / tahmin (kopya başına) | 2 sn altı gerçekler | yarım eşleşen çiftler | eşleşmeyen tahminler |
|---|---|---|---|---|---|---|
| J03WN1 | 10 | 0,641 | 500 / 361 | %41 | %30 | %13 |
| J03WR9 | 10 | 0,697 | 370 / 298 | %37 | %32 | %16 |
| MET1 | 10 | 0,683 | 379 / 298 | %34 | %26 | %18 |
| MET2 | 10 | 0,665 | 364 / 274 | %38 | %27 | %15 |
| MET3 | 2 | 0,729 | 404 / 338 | %36 | %28 | %20 |

**Üst sınırlar (etiketler kopya çekilerek; yöntem değil).** Bulunan her değişimin zamanı kusursuz olsaydı 0,674 → 0,733;
yalnız topun göründüğü yerlerde kusursuz olsaydı 0,704; ölü top kareleri kusursuz olsaydı 0,700. Kalan büyük kısım
bulunamayan kısa sahipliklerdir.

**Örüntülere dayalı denemeler (hepsi modellerin eğitimde görmediği maçlarda).**
1. *Zayıf işaretlerden sahiplik eklemek.* Tahmin edilen bir sahipliğin içinde öteki takımın olasılığının yükseldiği yerler
   ("tümsekler") aday yapıldı. Bu puan düzeyinde eklenen bir sahipliğin kendini ödemesi için kabaca 10 adaydan 4'ünün gerçek
   olması gerekir; tepe olasılığı 0,3-0,4 olanlarda oran %17, 0,5'in üstündekilerde bile %35. Kullanılabilir işaret yok.
2. *Çözücü sabitleri*, topun görünme oranına göre ayrı ayrı: en iyi değişiklik +0,0002. Sabitler zaten en iyi yerde.
3. *Temas kanıtı.* Top bir takımın oyuncusuna 1-1,5 m yakın ve öteki takım uzaktayken o takıma ek puan (12 ayar): en iyisi
   +0,0007, en kötüsü −0,0002. Modeller bu bilgiyi zaten kullanıyor.
4. *Karşılama kuralı.* Top değişimini, yeni takımın oyuncusunun topa ulaştığı ana kaydırmak (24 ayar): en iyisi +0,0007
   (DFL −0,0009), en kötüsü −0,0030. Gürültülü konumlarda "temas anı" yeterince kesin bulunamıyor.
5. *En kısa sahiplik süresi.* Organizatörün kuralı "kontrolsüz tek dokunuş sahiplik değiştirmez" der. Bizim dış etiketlerimizde ise
   saniyenin altında çok sahiplik var. Etiketlerden τ'dan kısa "araya girmeleri" silip aynı kuralı tahmine m ile uyguladık:
   en iyi m her zaman τ'ya eşit çıkıyor (τ = 1,5 sn ise m = 1,5 sn ile 0,723 → 0,755; etiketler olduğu gibiyse
   m = 1,5 sn 0,674 → 0,651). Yani bu, yarışma etiketlerinin kısa dokunuşları sayıp saymadığına dair bir bahistir;
   dış veriyle ölçülemez, yarışma maçının etiketlerine bakarak ayarlamak da yasaktır. Değişiklik yapılmadı.
6. *İki model ailesinin öğrenilmiş birleşimi* (yalnız keşif): dört maçın kopyalarında eğitilen bir sınıflandırıcı beşinci maçta
   denendi, beş kez dönerek. v2.15'e göre ortalama +0,0095 (DFL +0,0081, Metrica +0,0107; 32/42 kopyada iyi), ama en kötü kopya
   −0,0226. Bu, v2.14'ün tablosunun aynısıdır: ortalama kazanç var, tek tek kopyalarda belirgin kayıp var; "hiçbir kopya
   −0,010'dan kötü olmasın" şartını geçmez. Ayrıca v2.15 planı ikinci modelle başka deneme yapılmayacağını yazmıştı. Aday olarak
   kaydedilmedi.

**Sonuç.** (1) En büyük kayıp, modellerin izleme verisinde göremediği kısa sahipliklerdir; bunu düzeltmek yeni bilgi ister (topun
kaybolduğu anlarda görüntüden top bulmak gibi), kural ya da ayar değil. (2) Zamanlama hataları gerçek ama elle yazılan kurallar
modelden daha iyi zamanlamıyor. (3) Denenen yöntemlerin hiçbiri kayıtlı asgari kazanca (+0,008 ve hiçbir kopyada −0,010'dan
kötü olmamak) yaklaşmadı. Organizatörün kendi belgesi de tek maçta 0,04'ün altındaki farkların rastlantı payı içinde kaldığını
söylüyor. Teslim sistemi v2.15 olarak kalır.

**Bağlam notu (seçimde kullanılmadı).** Dış etiketler kendilerine göre 3 / 8 / 25 kare geç kaydırıldığında 0,93-0,96 / 0,84-0,88 /
0,50-0,62 alıyor; organizatör kendi etiketleri için 0,98 / 0,89 / 0,65 yayımlıyor. Bu, yarışma etiketlerinde çok kısa
sahipliklerin bizim dış etiketlerimizdekinden daha az olduğunu düşündürür; öyleyse en büyük hata sınıfımız gerçek puanlamada
buradaki kadar ağır olmayabilir. Bu bir çıkarımdır, ölçüm değildir ve hiçbir ayar buna göre yapılmadı.

**Sınırlar.** Geliştirme kopyalarıdır; aynı maçlar daha önceki bütün seçimlerde kullanıldı. Bozma benzetimi bizimdir. Metrica
etiketleri olaylardan türettiğimiz vekillerdir. Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1.

## K013 — v2.15 adayı: aynı birleşik sistem, ikinci modelin ağırlığı 0,5 yerine 0,2; yedi kapı geçti, teslim sistemi v2.15, 15 Kasım 2026

**Neden üçüncü bir deneme.** v2.14 (K012) 16 yeni kopyanın 15'inde daha iyiydi (ortalama +0,0201) ama bir kopyada
−0,0160 çıktı; "hiçbir kopya −0,010'dan kötü olmasın" kapısı (G4) geçmedi ve aday seçilmedi. O kayıt ve
kapıları değişmedi. Bir denemenin daha hangi koşulda yapılacağı 14 Kasım 23:39'da, o doğrulamanın yalnız üç satırı
bilinirken yazıldı (`experiments/possession_v2/v214/NOTES.md`; o üç satırdan biri, G4'ün geçemeyeceğini zaten gösteren
−0,0160 satırıydı, yani kural v2.14'ün seçilmeyeceği bilinerek yazıldı): yalnız v2.14'ün ortalama kapıları (G1, G2, G3, G5) geçerse; aynı
ağırlık dosyaları, aynı aritmetik havuz, aynı çözücü; yalnız ağın ağırlığı düşürülür; kapılar aynı; kopyalar yeni; **bundan
sonra başka deneme yok**. İkinci modeli eklemek için kayıtlı üçüncü denemedir (v2.13, v2.14, v2.15).

**Ağırlığın seçimi (geliştirme).** v2.14 doğrulamasının 16 taktik ve 4 öteki-benzetici kopyası, kararı kaydedildikten sonra
geliştirme verisi oldu (olasılıkları o andan sonra saklandı); önceki 22 kopyayla birlikte 42 geliştirme kopyası. Kural (23:39):
0,1 / 0,2 / 0,3 ağırlıklarından, herhangi bir geliştirme kopyasında −0,007'den kötü olan elenir (G4'e 0,003 pay); kalanlardan
ortalaması en büyük olan alınır; DFL geliştirme kopyalarındaki ortalaması +0,010'dan küçükse deneme yapılmaz. (Notta DFL kopyaları
için 18 yazılmıştı; doğrusu 20'dir: 16 taktik, 4 öteki benzetici. Koşul 20'sine de, 16 taktik kopyaya da uygulandı.)
42 kopyada aritmetik havuz, v2.11'e göre (ortalama fark | en kötü kopya | iyi olan kopya):

| ağırlık | hepsi (42) | DFL (20) | Metrica (22) | v2.14 doğrulamasının kopyaları (20) | öteki benzetici (9) |
|---|---|---|---|---|---|
| 0,1 | +0,0079 \| −0,0049 \| 37 | +0,0076 \| −0,0013 \| 19 | +0,0082 \| −0,0049 \| 18 | +0,0079 \| −0,0049 \| 16 | +0,0128 \| +0,0024 \| 9 |
| 0,2 | +0,0138 \| −0,0035 \| 38 | +0,0135 \| −0,0026 \| 19 | +0,0141 \| −0,0035 \| 19 | +0,0155 \| −0,0031 \| 19 | +0,0168 \| +0,0075 \| 9 |
| 0,3 | +0,0193 \| −0,0118 \| 41 | +0,0179 \| −0,0118 \| 19 | +0,0206 \| +0,0022 \| 22 | +0,0197 \| +0,0022 \| 20 | +0,0255 \| +0,0119 \| 9 |
| 0,4 | +0,0236 \| −0,0084 \| 41 | +0,0220 \| −0,0084 \| 19 | +0,0250 \| +0,0004 \| 22 | +0,0228 \| +0,0004 \| 20 | +0,0271 \| +0,0087 \| 9 |
| 0,5 | +0,0242 \| −0,0160 \| 39 | +0,0237 \| −0,0069 \| 19 | +0,0247 \| −0,0160 \| 20 | +0,0220 \| −0,0160 \| 18 | +0,0335 \| −0,0056 \| 8 |

0,3 bir eski DFL kopyasında −0,0118 olduğu için elendi; 0,1 ve 0,2 kaldı, ortalaması büyük olan **0,2** seçildi (DFL'in 20
kopyasında +0,0135, 16 taktik kopyasında +0,0125). v2.14'ü düşüren kopyada (Metrica 1, 16120) farklar ağırlığa
göre düzgün değişmiyor: 0,1 −0,0049; 0,2 −0,0031; 0,3 +0,0022; 0,4 +0,0036; 0,5 −0,0160. Yani o −0,016 sistemli bir bozulmadan çok,
çözücünün birkaç sahipliği farklı bölmesinin sonucu; küçük ağırlık bu oynaklığı da küçültüyor.

**Plan.** `possession-v215-plan.json`, 15 Kasım 01:17:34'te kaydedildi; o anda hiçbir havuzun üçüncü tohum dizisindeki bir kopyada
puanı yoktu. Her şey v2.14 doğrulamasıyla aynı (aynı altı ağırlık dosyası, SHA-256 değerleri aynı; `exp_v213.py` değiştirilmeden),
yalnız ağırlık 0,2 ve tohumlar yeni: kopya 19100 + 10·maç + j, yayın 49100 / 49200, saat 59100 / 59200, öteki benzetici 69100 + maç
(hiçbiri eski bir dosyada geçmiyor). Kapılar G1-G7, değişmeden. Plan şunu da yazar: aynı kapılarla üçüncü deneme olduğu için burada
bir geçiş, ilk denemede geçmiş olmaktan daha zayıf bir kanıttır; ve bir kapı geçmezse teslimden önce ikinci modelle başka aday
kaydedilmez.

**Sonuç** (`possession-v215-results.json`, kapılar 02:13'te uygulandı; spellF1, organizatörün ölçütü; yarışma puanı değil):

| koşul | kopya | v2.11 | birleşik | fark | iyi / kötü | en kötü kopya | ağ tek başına | macroF1 farkı |
|---|---|---|---|---|---|---|---|---|
| yalnız taktik kamera, hepsi | 16 | 0,6447 | 0,6559 | +0,0112 | 14 / 0 | +0,0000 | 0,6496 | +0,0032 |
| yalnız taktik kamera, DFL | 8 | 0,6484 | 0,6611 | +0,0126 | 8 / 0 | +0,0034 | 0,6492 | +0,0031 |
| yalnız taktik kamera, Metrica | 8 | 0,6411 | 0,6508 | +0,0097 | 6 / 0 | +0,0000 | 0,6501 | +0,0034 |
| iyi yayınla doldurma | 8 | 0,6858 | 0,6964 | +0,0106 | 7 / 0 | +0,0000 | 0,6848 | +0,0020 |
| orta yayınla doldurma | 8 | 0,6741 | 0,6854 | +0,0114 | 7 / 0 | +0,0000 | 0,6785 | +0,0034 |
| 42 m kamera penceresi (rapor) | 8 | 0,6412 | 0,6530 | +0,0118 | 7 / 0 | +0,0000 | 0,6418 | +0,0032 |
| yazarın benzeticisi (G7) | 4 | 0,6670 | 0,6867 | +0,0197 | 4 / 0 | +0,0186 | 0,6805 | +0,0093 |

Yalnız taktik kamerada kopya kopya farklar: J03WN1 +0,0034, +0,0139, +0,0147, +0,0152; J03WR9 +0,0037, +0,0252, +0,0139, +0,0111; Metrica 1 +0,0222, +0,0022, +0,0122, +0,0000;
Metrica 2 +0,0165, +0,0000, +0,0050, +0,0198.

2 kopya (MET1 19123, MET2 19131) gürültü kapısında v2.3 yoluna düştü; aday o yolda havuzlama yapmadığı için bu kopyalarda çıktı
v2.11'in çıktısıdır ve fark tam 0'dır (ortalamalara 0 olarak girerler).

| kapı | değer | sonuç |
|---|---|---|
| G1 ortalama kazanç ≥ +0,008 | +0,0112 | geçti |
| G2 DFL'de kazanç ≥ +0,008 | +0,0126 | geçti |
| G3 Metrica'da ≥ −0,002 | +0,0097 | geçti |
| G4 en kötü kopya ≥ −0,010 | +0,0000 | geçti |
| G5 macroF1 ≥ −0,003 | +0,0032 | geçti |
| G6 doldurma koşulları ≥ 0 | +0,0106 ve +0,0114 | geçti |
| G7 öteki benzeticinin kopyaları ≥ 0 | +0,0197 | geçti |

**Yanında raporlananlar (yalnız taktik kamera, 16 kopya).** 2 saniyeden kısa sahipliklerin yakalanma oranı: v2.11
0,275, birleşik 0,277, ağ 0,273; 1 saniyeden kısalar: 0,115 /
0,111 / 0,083. Geçiş F1 (12 kare): 0,543 / 0,553 / 0,538. Kopya başına
sahiplik sayısı: etiketlerde 403, v2.11 308, birleşik 304, ağ 313. Birleşik
sistem kopya başına ortalama 1.282 karenin etiketini değiştirdi. Gürültü kapısı: v2.1 yolu 14, v2.3 yolu
2 kopya. Doldurma kapısı iyi yayında 8/8, orta yayında 7/8 kopyada açıldı.

**Karar (2026-11-15 02:13).** Yedi kapının yedisi geçti; kayıtlı kurala göre aday seçildi ve possession-v2.15 olarak
bütünleştirilir. Kapılar bir kez, bütün satırlara uygulandı; başka tohum, ağırlık, havuz ya da çözücü sabiti denenmedi.

**Karardan sonra, bir kez (kapı değil).** Metrica 3, bir yeni kopya (v2.11 → birleşik): yalnız taktik kamera 0,6428 → 0,6650; iyi yayınla doldurma 0,7154 → 0,7316; orta yayınla doldurma 0,6885 → 0,7052; 42 m penceresi 0,6472 → 0,6646; yazarın benzeticisi 0,6972 → 0,7198. PFF maçı (K009; gerçek yayın takibi, top oyun içindeki karelerin 0,41'inde görünüyor; lisansı yayımlanmamış, seçimde kullanılmaz): v2.11 0,6289, birleşik 0,6542, ağ tek başına 0,6391 (macroF1 0,898 / 0,905 / 0,902).

**Yorum (çıkarım, ölçüm değil).**
- Ağırlık 0,2 ile ağ yalnız bizim modelin kararsız olduğu yerlerde söz sahibi olur: bir sınıfın olasılığını en çok 0,2 kaydırabilir.
  Kazanç v2.14'ünkinden küçüktür (+0,0112; v2.14: +0,0201), kopyalar arası oynaklık da.
- Ağ tek başına bu 16 kopyada 0,6496, v2.11 0,6447.
- Üç denemenin üçü de yeni kopyalarda ölçüldü; ama aynı kapılar üç kez denendi. Tek tek kopyalara bakan G4'ü, daha temkinli
  ayarla yeniden denenen bir tasarım daha kolay geçer. Bu yüzden sonuç "birleşik sistem dış kopyalarda ortalamada daha iyi ve bu
  ağırlıkla hiçbir kopyada belirgin kötü değil" diye okunmalı; sağlanan maç için bir ölçüm değildir.

**Sınırlar.** K012'deki sınırların hepsi geçerli (kullanılmış doğrulama maçları; ağırlıkları doğrulayan sürecin eğitmesi; ağın
yalnız ekibin iki benzeticisini görmesi; benzetilmiş bozma, kamera ve yayın; vekil Metrica etiketleri). Ek olarak: ağırlık, v2.14
doğrulamasının kopyaları da kullanılarak seçildi; gürültülü yolda (v2.3) havuzlama yapılmaz ve o yol için hiçbir ölçüm yoktur.
Betikler: `experiments/possession_v2/v215/` (ağırlık dosyaları ve eğitim: `v214/`).

**Bütünleştirme (15 Kasım, karardan sonra).** Kayıtlı karar kuralı, v2.15'in teslimde v2.11k'nın yerini alması için beş
denetim (16 Kasım 23:59'a kadar) ve bir koşul yazar. Durum:
- *Kod ve ağırlıklar.* `possession/tcn/` (commit `167dc7b`'nin çıkarım modüllerinin bayt kopyaları), `possession/pooling.py` (doğrulanan
  dosya), `possession/run215.py` (dondurulmuş `run211.py`'den türetildi: yalnız puanlanan bloklar, havuzlama, başlama vuruşu
  kuralı), `models/possession-tcn-v215.npz` (üç `dfl6_both` üyesi; SHA-256 değerleri plandakilerle aynı). Manifest
  `possession-v215-release.json` (02:33): 29 kaynak dosya, iki ağaç paketi ve ağ ağırlıkları. Havuzlama kapatılınca
  `run215`, `run211k`'nın dosyasını bayt bayt yazar (test eder). Merdiven: v2.15 → v2.11k → v2.11g → v2.9g → v2.5b → v2.5b yalnız
  taktik kamera. Kuralsız yedek (`possession-release-graded-windows.json`) değişmedi; orada ikinci model de yoktur.
- *Python 3.10 / numpy 1.26.4.* Ağ bu ortamda çalışıyor. Dokuz sentetik paketin (ikisi ağla) çıktısı 3.10 / 1.26.4 ve 3.13 / 2.5.3
  altında bayt bayt aynı (`tests/test_possession_crossplatform.py`). Ağın yuvarlanmamış olasılıkları iki ortamda farklı, 4 basamağa
  yuvarlanmışları aynı; başka bir işlemcide farklı çıkması olası değil ama dışlanamaz, zincirin `PLATFORM` adımı bunu
  dosyanın üretildiği bilgisayarda denetler.
- *Testler.* 3.10'da 448 test (15 atlandı), 3.13'te 448 test (4 atlandı); hepsi geçti. `tests/test_possession_final_test.py`
  güncellendi: son test planının teslim edilen ilk basamak için değil, ikinci modelsiz sürüm (v2.11k, ikinci basamak) için kayıtlı
  olduğunu denetler.
- *Tam boy prova* (`possession-v215-rehearsal.json`): K003'ün sentetik paketi ve K011'in uydurma Smart Tagging dosyası, varsayılan
  zincir, Python 3.10. Bütün adımlar OK; 761 sn (v2.11k zinciri 417 sn; ağla bir üretim bu ortamda yaklaşık beş dakika daha uzun sürdü), en çok 1,53 GB. Teslim dosyası
  v2.11k zincirinin dosyasından 889 karede farklı (puanlanan karelerin %0,6'sı), hepsi başlama vuruşlarından sonra.
  O paketin vekil etiketlerine göre spellF1 0,7721 (v2.11k zinciri 0,7641), macroF1 0,8732 (0,8728).
  Bu bir bağlantı ve boyut denetimidir: paket Metrica 2 ve 3'ün bozuk kopyalarıdır, karardan sonra bir kez çalıştırıldı, hiçbir
  seçimde kullanılmadı ve doğruluk iddiası değildir.
- *Belgeler.* `TECHNICAL_DOCUMENT.md` (adım 9, üç deneme, eğitim verisi, sınırlar), `TECHNICAL_DOCUMENT_V2.md` (dördüncü ek),
  `README.md`, `DATA_SOURCES.md`, `AGENTS.md`, Türkçe rehber ve `CLAUDE.md` güncellendi.
- *Son test planı yeniden kaydedilmedi.* `possession-final-test-plan.json` v2.11k için kayıtlı kalır. Ağın tasarımcısı J03WMX'i
  geliştirme sırasında kullandığı için v2.15'in o maçtaki sonucu "taze test" olmazdı; yayımlanan ağırlıklar o maç olmadan eğitildi
  ve sürümü kuran süreç maçı indirmedi. `SON-TEST.cmd` çalıştırılırsa sonuç v2.11k'nın sonucu olarak yazılır.
- **Açık koşul.** Karar kuralının son şartı: teslim zincirinin ekibin bilgisayarında OK bitmesi (`URETIM` ve `TESLIM` satırlarında
  possession-v2.15). Bu kayıt yazılırken zincir orada henüz çalıştırılmadı. Zincir daha alt bir basamağa düşerse teslim edilen o
  basamaktır ve belgelerin ilk satırları buna göre düzeltilir.

## K012 — v2.14 adayı: ikinci model iki benzeticiyle yeniden eğitildi ve bizim çözücümüzle birleştirildi; kayıtlı kapılardan geçmedi, 14-15 Kasım 2026

**Neden ikinci bir deneme.** v2.13 (K010) üç kapıdan geçmedi ve seçilmedi; o kayıt ve kapıları değişmedi. Takım lideri
14 Kasım 18:23'te teslimden önce son bir deneme istedi. Yeni bir aday ancak yeni bir planla ve plan sonuçlardan önce
kaydedilerek ölçülebilir; bu kayıt o denemedir. Sağlanan maçın hiçbir dosyası okunmadı, çalıştırılmadı, puanlanmadı.

**Teşhis (geliştirme; yalnız daha önce puanlanmış kopyalarda).** v2.13 doğrulamasının 20 kopyası (tohum 13100-13133 ve
63100-63103) ile karardan sonra puanlanan iki Metrica 3 kopyası (33103, 63108) artık geliştirme verisidir; teşhis için bir
Metrica 3 kopyası daha üretildi (tohum 7772). Bunların hiçbiri doğrulama değildir. Bulunanlar:
- *Sahte top algılamaları.* Yazarın ağırlıkları (`tcn_dfl6.npz`) tek başına, 7772 kopyasında, bizim benzeticinin bir bileşeni
  kapatılarak (spellF1): hepsi açık 0,686; yanlış takımlı izler kapalı 0,693; konum gürültüsü düşük
  0,684; oyuncu kayıpları kapalı 0,707; **sahte top algılamaları kapalı 0,733**; bozulmamış
  veri 0,742; yazarın kendi benzeticisi 0,727. Onun benzeticisinde sahte algılamalar daha seyrektir ve hep bir
  oyuncunun üstündedir; bizimkinde dört kata kadar sıktır ve yarısı sahada rastgele bir yerdedir. Ağ bunları eğitimde görmemişti.
- *Ezber.* Aynı ağırlıklar bir eğitim maçında (J03WOH, bizim bozmamızla) 0,817 aldı. Eğitim maçları bu yüzden teşhiste kullanılmadı.
- *Çözücü ve ağırlık.* Yazarın ağırlıklarıyla, 22 geliştirme kopyasında, v2.11'e göre ortalama fark: v2.13 kuralı (ağırlık 0,5, her
  değişime tek maliyet) +0,0108 (DFL'de +0,0007, en kötü kopya −0,0295); aynı
  olasılıklar ağırlık 0,2 ile ve bizim çözücümüzden geçirilince +0,0137 (DFL'de +0,0135, en kötü kopya
  −0,0081, 22 kopyanın 21 tanesinde iyi). Tek maliyetli çözücü, bizim çözücünün ölü topa giriş ve çıkış
  maliyetlerini (60) kullanmıyordu.
- *Tek tohum.* v2.13'te DFL satırları tek tohumlu ağırlıklarla, Metrica satırları üç tohumla ölçülmüştü.

**Yeniden eğitim.** PyTorch bu ortama kurulamadı; yazarın eğitim betiği JAX ile yeniden yazıldı
(`experiments/possession_v2/v214/tcn_jax.py`). Mimari, 37 özellik ve NumPy çıkarımı onundur (dal `mtah-possession`, commit
`167dc7b`); çıkarım modülleri bayt bayt kopyadır. Onun betiğinden farklar: Adam momenti sabit 0,9 (PyTorch'un OneCycleLR'ı onu da
değiştirir); başlangıç değerleri ve rastgele akışlar JAX / NumPy'nin; her devre için 12 bozuk kopya ve 6 tur (onunki 6 kopya ve
12 tur; eğitim maçı başına adım sayısı aynı); hazır verimizde top yüksekliği olmadığı için onun benzeticisinin yükseklik terimi
çalışmaz. JAX ağı ile onun NumPy çıkarımı rastgele girdi ve ağırlıklarda karşılaştırıldı: en büyük olasılık farkı 7,9e-7.
- *Veri:* yalnız açık DFL maçları (CC BY 4.0), sağlayıcının kare etiketleri. 12 kopyanın 6'sı onun benzeticisiyle
  (`tcn/degrade.py`), 6'sı bizimkiyle (`possession/degrade.py`, v2 profili) bozuldu; tek numaralı kopyalarda takımlar yer değiştirdi.
- *Modeller (üçer tohum):* `dfl4_both_s0-2`: J03WOH, J03WOY, J03WPY, J03WQQ (bizim doğrulama modellerimizin dört maçı; DFL
  doğrulama satırları için). `dfl6_both_s0-2`: altı maç (Metrica satırları için; seçilirse yayımlanacak ağırlıklar). Bir model
  2 işlemcide 26-40 dakika sürdü.
- *İlk deneme modeli* (J03WN1'siz beş maç, tek tohum): beş J03WN1 geliştirme kopyasında tek başına v2.11'e göre +0,0016
  (yazarın beş maçlık ağırlıkları −0,0326); beş kopyanın beşinde, onun kendi benzeticisinin kopyası dahil, yazarın
  ağırlıklarından iyi.
- *Üçer üyeli yeni ağırlıklar tek başına*, 22 geliştirme kopyasında: v2.11'e göre +0,0089 (DFL −0,0020,
  Metrica +0,0180); yazarın ağırlıkları aynı kopyalarda −0,0266. Tek tek kopyalarda hâlâ oynak
  (en kötü −0,0515).

**Havuzlama kuralının seçimi (geliştirme).** İki modelin üç sınıflı olasılıkları ağırlıklı ortalamayla birleştirilir, sonuç
yeniden P(ölü) ve P(ev | canlı) yapılır ve **değişmemiş v2 çözücüsünden** geçer (`fuse2.py`). Denenen ayarlar: aritmetik ortalama,
ağırlık 0,2-0,6; geometrik ortalama, ağırlık 0,3-0,6. Seçim kuralı 14 Kasım 21:23'te, yeni ağırlıkların DFL satırları görüldükten
sonra ve Metrica satırları henüz yokken yazıldı: (1) herhangi bir geliştirme kopyasında −0,010'dan kötü olan ayar elenir; (2)
kalanlardan ortalaması en büyük olan alınır; (3) ona 0,001'den yakın olanlar eşit sayılır ve en küçük ağırlık kazanır (aynı
ağırlıkta iki havuz varsa ortalaması büyük olan). 22 geliştirme kopyasında (ortalama fark | en kötü kopya | iyi olan kopya):

| ayar | hepsi (22) | DFL (10) | Metrica (12) | yazarın benzeticisi (5) |
|---|---|---|---|---|
| aritmetik 0,2 | +0,0122 \| −0,0035 \| 19 | +0,0115 \| −0,0026 \| 9 | +0,0128 \| −0,0035 \| 10 | +0,0158 \| +0,0075 \| 5 |
| aritmetik 0,3 | +0,0190 \| −0,0118 \| 21 | +0,0162 \| −0,0118 \| 9 | +0,0213 \| +0,0033 \| 12 | +0,0240 \| +0,0119 \| 5 |
| aritmetik 0,4 | +0,0243 \| −0,0084 \| 21 | +0,0204 \| −0,0084 \| 9 | +0,0275 \| +0,0057 \| 12 | +0,0292 \| +0,0089 \| 5 |
| aritmetik 0,5 | +0,0263 \| −0,0069 \| 21 | +0,0222 \| −0,0069 \| 9 | +0,0298 \| +0,0044 \| 12 | +0,0369 \| +0,0192 \| 5 |
| aritmetik 0,6 | +0,0242 \| −0,0176 \| 19 | +0,0204 \| −0,0176 \| 8 | +0,0275 \| −0,0014 \| 11 | +0,0406 \| +0,0109 \| 5 |
| geometrik 0,3 | +0,0203 \| −0,0035 \| 20 | +0,0181 \| −0,0035 \| 9 | +0,0221 \| −0,0019 \| 11 | +0,0266 \| +0,0123 \| 5 |
| geometrik 0,4 | +0,0253 \| −0,0024 \| 20 | +0,0230 \| −0,0024 \| 8 | +0,0272 \| +0,0042 \| 12 | +0,0339 \| +0,0148 \| 5 |
| geometrik 0,5 | +0,0263 \| −0,0069 \| 20 | +0,0233 \| −0,0069 \| 8 | +0,0288 \| +0,0030 \| 12 | +0,0380 \| +0,0157 \| 5 |
| geometrik 0,6 | +0,0248 \| −0,0126 \| 20 | +0,0214 \| −0,0126 \| 8 | +0,0277 \| +0,0035 \| 12 | +0,0399 \| +0,0119 \| 5 |

Kural **aritmetik ortalama, ağırlık 0,5** verdi (ortalama +0,026321; geometrik 0,5 +0,026291 ile aynı
ağırlıkta ve ortalaması daha küçük; geometrik 0,4 +0,025300 ile 0,001'den uzak). Bu, yazarın kendi karışım oranıdır; v2.13'e göre
değişen üç şey ağırlık dosyaları, üye sayısı ve çözücüdür. Çözücü sabitleri (takım değişimi 2-5, ölü topa giriş/çıkış 50-70, ölü
top eğilimi −0,1…−0,5) 10 DFL geliştirme kopyasında denendi: teslim sabitlerinden en çok 0,001 iyi ya da daha kötü; değiştirilmedi.
Gürültülü yol (v2.3; ölçülen gürültü 0,30 m'nin üstünde) için hiçbir ölçüm yapılmadı; aday o yolda havuzlama yapmaz, çıktı
v2.11k'nın çıktısıdır.

**Plan.** `possession-v214-plan.json`, 14 Kasım 23:33:40'ta kaydedildi; o anda adayın, yeni ağırlıkların ya da herhangi bir
havuzun yeni tohumlu bir kopyadaki hiçbir puanı yoktu (kayıttan önce görülenlerin tamamı planın
`seen_on_external_data_before_registration` bölümünde). Tasarım v2.13'ünkiyle aynıdır (`v213/exp_v213.py` değiştirilmeden içe
aktarılır), yalnız:
- yeni tohumlar: kopya 16100 + 10·maç + j, yayın 46100 / 46200, saat 56100 / 56200, yazarın benzeticisi 66100 + maç. Önce
  düşünülen 141xx dizisi eski dosyalardaki rastlantısal sayılarla (kare sayıları) çakıştığı için kayıttan önce değiştirildi;
  kaydedilen tohumların hiçbiri depodaki ya da çalışma alanındaki hiçbir dosyada geçmiyor (betik arar).
- DFL maçlarında ağ tarafı `dfl4_both` (üç üye; bizim doğrulama modelleriyle aynı dört maç), Metrica'da `dfl6_both` (üç üye) ve
  yayımlanan v2 paketleri.
- birleşik kol: `fuse2.pool` (aritmetik, 0,5) + `possession.decode` (yol sabitleri). v2.3 yoluna düşen bir kopyada fark tam 0'dır.
- kapılar: G1-G6, v2.12 ve v2.13'ün kapıları ve eşikleri, değişmeden; G7 eklendi: yazarın benzeticisiyle üretilen 4 kopyada
  ortalama fark ≥ 0 (v2.13'te yalnız rapor ediliyordu).
- v2.12 ve v2.13 planları sürüm değişikliği için son anı 14 Kasım 23:59 olarak yazmıştı. Bu plan, takım liderinin isteğiyle, daha
  geç bir an koyar (16 Kasım 23:59); bedeli, ekibin bilgisayarındaki denetimlere daha az zaman kalmasıdır (planın `limits` bölümü).
- Doğrulama betiği, kayıttan önce, bir geliştirme kopyasında (J03WN1 13100) saklanan olasılıklardan hesaplanan sayıları aynen
  verdi; eğitim maçı J03WOH'ta bağlantı denemesi yapıldı (puan hesaplamaz).
Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1; eğitim için ayrıca jax 0.12.0.1, optax 0.2.9.

**Sonuç** (`possession-v214-results.json`, kapılar 00:33'te uygulandı; spellF1, organizatörün ölçütü; yarışma puanı değil):

| koşul | kopya | v2.11 | birleşik | fark | iyi / kötü | en kötü kopya | ağ tek başına | macroF1 farkı |
|---|---|---|---|---|---|---|---|---|
| yalnız taktik kamera, hepsi | 16 | 0,6475 | 0,6676 | +0,0201 | 15 / 1 | −0,0160 | 0,6518 | +0,0047 |
| yalnız taktik kamera, DFL | 8 | 0,6413 | 0,6605 | +0,0192 | 8 / 0 | +0,0023 | 0,6417 | +0,0078 |
| yalnız taktik kamera, Metrica | 8 | 0,6537 | 0,6748 | +0,0211 | 7 / 1 | −0,0160 | 0,6618 | +0,0017 |
| iyi yayınla doldurma | 8 | 0,6831 | 0,6953 | +0,0122 | 7 / 1 | −0,0109 | 0,6819 | +0,0026 |
| orta yayınla doldurma | 8 | 0,6903 | 0,7102 | +0,0199 | 8 / 0 | +0,0005 | 0,6924 | +0,0035 |
| 42 m kamera penceresi (rapor) | 8 | 0,6404 | 0,6590 | +0,0186 | 8 / 0 | +0,0048 | 0,6396 | +0,0045 |
| yazarın benzeticisi (G7) | 4 | 0,6766 | 0,7058 | +0,0292 | 3 / 1 | −0,0056 | 0,7034 | +0,0168 |

Yalnız taktik kamerada kopya kopya farklar: J03WN1 +0,0102, +0,0262, +0,0288, +0,0300; J03WR9 +0,0158, +0,0023, +0,0264, +0,0139; Metrica 1 −0,0160, +0,0021, +0,0320, +0,0353;
Metrica 2 +0,0328, +0,0428, +0,0190, +0,0208.

| kapı | değer | sonuç |
|---|---|---|
| G1 ortalama kazanç ≥ +0,008 | +0,0201 | geçti |
| G2 DFL'de kazanç ≥ +0,008 | +0,0192 | geçti |
| G3 Metrica'da ≥ −0,002 | +0,0211 | geçti |
| G4 en kötü kopya ≥ −0,010 | −0,0160 | **geçmedi** |
| G5 macroF1 ≥ −0,003 | +0,0047 | geçti |
| G6 doldurma koşulları ≥ 0 | +0,0122 ve +0,0199 | geçti |
| G7 öteki benzeticinin kopyaları ≥ 0 | +0,0292 | geçti |

**Yanında raporlananlar (yalnız taktik kamera, 16 kopya).** 2 saniyeden kısa sahipliklerin yakalanma oranı: v2.11
0,286, birleşik 0,290, ağ 0,280; 1 saniyeden kısalar: 0,111 /
0,128 / 0,102. Geçiş F1 (12 kare): 0,530 / 0,552 / 0,525. Kopya başına
sahiplik sayısı: etiketlerde 403, v2.11 309, birleşik 305, ağ 310. Birleşik
sistem kopya başına ortalama 4.431 karenin etiketini değiştirdi. Gürültü kapısı: v2.1 yolu 16, v2.3 yolu
0 kopya. Doldurma kapısı iyi yayında 8/8, orta yayında 8/8 kopyada açıldı.

**Karar (2026-11-15 00:33).** 1 kapı geçmedi (G4); kayıtlı kurala göre aday teslim sistemine
girmedi, teslim sistemi **v2.11k** olarak kalır. Kapılar bir kez, bütün satırlara uygulandı; başka tohum, ağırlık, havuz ya da çözücü
sabiti denenmedi. İlk iki satır geldiğinde (14 Kasım 23:37) G4'ün geçemeyeceği belliydi; doğrulama yine de planlandığı gibi
tamamlandı.

−0,010'dan kötü kopyalar: MET1 16120 (−0,0160; v2.11 0,6671, ağ tek başına 0,6330, oyun içinde topun göründüğü karelerin payı 0,361).

**Karardan sonra, bir kez (kapı değil).** Metrica 3, bir yeni kopya (v2.11 → birleşik): yalnız taktik kamera 0,6569 → 0,6958; iyi yayınla doldurma 0,6770 → 0,7056; orta yayınla doldurma 0,6915 → 0,7067; 42 m penceresi 0,6625 → 0,6987; yazarın benzeticisi 0,6889 → 0,7032. PFF maçı (K009; gerçek yayın takibi, top oyun içindeki karelerin 0,41'inde görünüyor; lisansı yayımlanmamış, seçimde kullanılmaz): v2.11 0,6289, birleşik 0,6713, ağ tek başına 0,6391 (macroF1 0,898 / 0,910 / 0,902).

**Yorum (çıkarım, ölçüm değil).**
- Ortalama kazanç tutarlı: yalnız taktik kamerada 16 kopyanın 15 tanesi, DFL kopyalarının 8 tanesi iyi; doldurma
  koşullarında, kamera penceresinde ve yazarın benzeticisinin kopyalarında da artı. v2.13'te DFL'de eksi olan fark (−0,0045) burada
  +0,0192. Teşhisin gösterdiği üç değişiklik (iki benzeticiyle eğitim, üç üye, bizim çözücü) birlikte işe yaradı;
  hangisinin ne kadar katkı yaptığı bu doğrulamada ayrı ayrı ölçülmedi.
- Yeni ağırlıklarla ağ tek başına bu 16 kopyada v2.11 düzeyinde (0,6518 / 0,6475); yazarın ağırlıklarıyla v2.13
  doğrulamasında 0,6257 / 0,6598 idi. Tek tek kopyalarda hâlâ oynak.
- Geçmeyen kapı tek kopyadan: MET1, tohum 16120. O kopyada oyun içindeki karelerde topun görünme payı 0,361;
  ağ tek başına 0,633, v2.11 0,667, birleşik 0,651. Aynı kopya iyi yayınla doldurulunca fark +0,0074.
  Geliştirme kopyalarında top görünürlüğü benzer (0,36-0,38) üç kopya vardı ve üçünde de birleşik sistem iyiydi; görünürlük tek
  başına açıklamıyor. Ortalaması +0,02 olan bir farkın 16 kopyadan birinde −0,010'un altına düşmesi şaşırtıcı değil; kapı tam da bunu
  eliyor ve değiştirilmedi.

**Sınırlar.** Doğrulama maçları daha önceki bütün seçimlerde ve bu adayın geliştirilmesinde kullanıldı; yalnız kopyalar yeniydi.
Ağırlıkları doğrulamayı yapan süreç eğitti; eğitim betiğini başka kimse denetlemedi ve yeniden çalıştırma aynı bitleri vermez.
Bozma, slot paketleme, kamera penceresi ve yayın kamerası bizim benzetimimizdir; ağ yalnız ekibin iki benzeticisini gördü. DFL
etiketleri sağlayıcının kare etiketleri, Metrica etiketleri olaylardan türettiğimiz vekil etiketlerdir. Betikler:
`experiments/possession_v2/v214/`.

## K011 — Başlama vuruşu: yayımlanan sabit kare bırakıldı, Smart Tagging kuralı eklendi; teslim sistemi v2.11k, 13 Kasım 2026

**Neden.** 11 Kasım'da organizatöre, FAQ.md'de yayımlanan ikinci yarı başlama karesini (113.742) koda sabit
yazmanın uygun olup olmadığını sorduk; olumsuz yanıt için yedek giriş noktaları hazırdı (v2.9g, v2.11g; K003, K004).
12 Kasım 14:21'de gelen yanıt "evet" ya da "hayır" demedi: 3 Kasım açıklamasını yineledi ve şunu ekledi:
"anything that is not explicitly allowed is not permitted". Yayımlanan bir kareyi sabit yazmak açıkça izin
verilenler arasında değil; Smart Tagging'i girdi olarak kullanmak açıkça izinli. 12 Kasım akşamı kuralı yazan takım
üyesiyle yazışmada şunda anlaşıldı: sabit kare kullanılmaz; Smart Tagging başlama vuruşu etiketi, sentetik testleri
donmadan önce hazırsa kullanılır, değilse yalın v2.11g. Takım lideri bu öneriye itiraz etmedi; 13 Kasım raporunda
kuralsız yedeği (v2.11g) seçme imkânı ayrıca belirtildi.

**Ne.** `possession/kickoff.py` ve giriş noktası `possession.run211k` (manifest `possession-v211k-release.json`,
13 Kasım 12:33). v2.11g'nin çıktısından sonra tek kural: puanlanan bir blokta, bloğun içinde başlayan ilk
"Kick Off (Start)" etiketi (kod SET PIECES, grup Type) bloğun ilk karesinden on dakikadan az sonra başlıyorsa, bloğun
o etiketten önceki kareleri `D` yazılır. Dosya yoksa, okunamıyorsa ya da uygun etiket yoksa çıktı bayt bayt
v2.11g'nin çıktısıdır. Kural, bir takım üyesinin 12 Kasım 19:00'da kendi dalına koyduğu koddan (dal
`mtah-possession`, commit 4b32747, `possession/predict.py`) değiştirilmeden alındı;
`tests/test_possession_kickoff.py` iki uygulamayı 300 rastgele sentetik girdide karşılaştırır. Kodda hiçbir maçın
kare numarası yoktur (test eder).

**Ölçüm.** Yok ve olamaz: dış maçların takip verisi başlama vuruşuyla başlar, Smart Tagging'leri yoktur. Testler
sentetiktir (9 + 2 test): etiketlerin okunması, on dakika sınırı, blok dışındaki etiketler, eksik ya da bozuk
dosya, yeniden yazılan dosyanın biçimi ve `run.json` kaydı; sentetik bir pakette uçtan uca: etiket dosyası yokken
çıktı v2.11g'nin baytlarıdır, etiket varken yalnız etiketten önceki kareler değişir. İki Python ortamında geçti
(3.13 / numpy 2.5.3 ve 3.10 / numpy 1.26.4).

**Zincir.** `possession-release.json` artık v2.11k → v2.11g → v2.9g → v2.5b → v2.5b yalnız taktik kamera sırasını
adlandırır; hiçbir basamak 113.742'yi kullanmaz. `possession-release-graded-windows.json` aynı sıranın kuralsız
hâlidir. Belge ekine (Ek R) "Kick-off rule" satırı eklendi: kategori yazar, sayı ve kare yazmaz. Platform denetimi
değişmedi (kural yalnız etiketleri bir tam sayı kareden önce yeniden yazar; kayan noktalı bir parçası yok). Son test
planı v2.11k için yeniden kaydedildi (13 Kasım 12:48; J03WMX'e sürümü kuran süreçte dokunulmadı; o maçta Smart Tagging
olmadığı ve oyun blokları iki devre olduğu için çıktı v2.11'in çıktısıdır; bir takım üyesinin o maçı ayrı bir model
için kullandığı plana yazıldı). `possession.run211` (sabit kareli v2.11) depoda dondurulmuş duruyor, kullanılmıyor.

**Zincire ve girdi denetimine ekler (13 Kasım öğleden sonra).**
- `tools/possession_deliver.py`: sürümün ilk basamağı Smart Tagging dosyasını okuduğu için (`possession-release.json`
  içinde `"smart_tagging": true`) `VERI` satırı artık dosyanın pakette olup olmadığını da yazar (`smart tagging VAR` /
  `YOK`) ve yoksa uyarır. Dosya yokken çıktı v2.11g'nin çıktısıdır; organizatör dosyayı bütün paketten yeniden
  üreteceği için kural onda uygulanır ve iki dosya farklı çıkabilir. 11 Kasım'daki ilk zincirde satırda
  `videolar YOK` yazıyordu (K006); bu yüzden aynı klasörde Smart Tagging dosyasının bulunduğu varsayılmadı.
- `possession/inputs_check.py`: iki yeni denetim (toplam 28). `tagging_reader_runs`: sürümün başlama vuruşu okuyucusu
  dosyayı okuyabiliyor mu. `tagging_kickoff_start_tags`: bulduğu "Kick Off (Start)" etiketi sayısı DATA.md'nin
  yazdığı 2 mi. Yalnız sayı karşılaştırılır; dosya yoksa SKIP yazar.
- **Önceden yazılan kural (zincir sağlanan dosyalarda v2.11k ile çalıştırılmadan önce, 13 Kasım 13:42):** ekibin
  bilgisayarında bu iki denetimden biri FAIL verirse okuyucu ile DATA.md dosya hakkında anlaşamıyor demektir; o durumda
  kuralın dayanağı doğrulanmamış sayılır ve kuralsız yedek sıra teslim edilir
  (`TESLIM-HAZIRLA.cmd --release-config possession-release-graded-windows.json`). İkisi de PASS ise ya da dosya
  pakete konduktan sonra PASS oluyorsa varsayılan sıra (v2.11k) teslim edilir. Bu seçim bir çıktıya bakılarak yapılmaz.

**Prova (bağlantı ve boyut denetimi; `possession-v211k-rehearsal.json`).** Zincir, yeni varsayılan sürümle, K003'ün
tam boy sentetik A paketinde iki kez çalıştırıldı (Python 3.10 ortamı). Paketin içeriği bozulmuş Metrica örnek
maçlarıdır; ikinci yarı başlama vuruşundan önce uydurma bir bölüm vardır.
- *Uydurma Smart Tagging dosyasıyla* (`experiments/possession_v2/prova_tagging.py`): dosya DATA.md'nin anlattığı
  yapıdadır (638 kayıt, yayımlanan kod ve tür sayıları). İki "Kick Off (Start)" kaydı, paketin iki başlama anını
  içeren 5 saniyelik pencerelerdir; organizatörün `starter/load_smart_tagging.py` dosyası teslim edilen dosya için
  bunu söyler ("The tagging marks a ~5 s window around the restart rather than the instant"; "Both tagged kickoffs
  contain the real one"). Testler dahil bütün
  adımlar OK: `URETIM OK (possession-v2.11k, saatli)`, `PLATFORM AYNI`, `GIRDI OKUMA OK`; 417 s, en çok 1,54 GB.
  Paketin dış etiketlerine göre spellF1 0,7641, macroF1 0,8728. 11 Kasım'daki zincir dosyaları aynı pakette:
  v2.11 0,7641 / 0,8728, v2.11g 0,7594 / 0,8706. v2.11g dosyasından 309 karede ayrılır; hepsi etiketten önce ve
  hepsi `D` oldu. Etiketin başı ile başlama anı arasındaki 60 kareyi modeller de `D` etiketledi. v2.11
  dosyasından tek karede ayrılır.
- *Smart Tagging dosyası olmadan* (son araçla): `VERI OK (taktik VAR, yayin VAR, videolar YOK, smart tagging YOK)`,
  sonuç satırında `UYARILAR VAR (VERI)`; üretilen dosya 11 Kasım'daki v2.11g zincirinin dosyasıyla bayt bayt aynı
  (SHA-256 eşit); Ek R satırı "Smart Tagging file not found: not applied". Bu çalıştırmanın ilk denemesi bulut
  oturumu yeniden başladığı için yarıda kaldı ve boş klasörden yeniden başlatıldı.
- Etiket dosyasını biz uydurduk: bu prova sağlanan maçtaki doğruluğu ya da oradaki etiketlerin yerini göstermez.

**Sınırlar.** Etiket otomatiktir. Organizatörün `starter/load_smart_tagging.py` dosyasına göre etiketli her başlama
vuruşu, gerçek anı içeren yaklaşık 5 saniyelik bir penceredir; öyleyse kural yalnız başlama vuruşundan önceki
kareleri `D` yazar ve pencerenin içindeki son anları modellere bırakır. Bir etiket gerçek başlama vuruşundan sonra
başlasaydı oyunun ilk anları `D` olurdu. Uygun etiket yoksa modeller karar verir; başlama öncesindeki davranışları
dış veride ölçülmedi (tam boy provada uydurma bir başlama öncesi bölümde 2.934 karenin 2.625'i `D` idi; K003).
Etiketin kullanılıp kullanılmadığı yalnız ekipte kalan belge kopyasının Ek R bölümünde yazar.

## K010 — v2.13 adayı: olasılıkları bir takım üyesinin TCN modeliyle birleştirmek; kayıtlı kapılardan geçmedi, 12-13 Kasım 2026

**Fikir.** Takım üyemiz Hüseyin Umut Işık ayrı bir model geliştirdi (dal `mtah-possession`, commit `167dc7b`): kare başına 37
takım-simetrik özellik üzerinde 12,5 Hz'de çalışan genişlemeli zamansal evrişim ağı (TCN); çıkarım NumPy ile, üç çıktı (takım 0,
takım 1, ölü top). Önerisi iki modeli birleştirmekti (`fuse.py`): bizim ikinci aşama olasılıklarımız ile TCN olasılıklarının
ortalaması alınır (ağırlık 0,5) ve tek bir Viterbi geçişiyle çözülür (her durum değişimi için maliyet 6); bizim çözücümüz
kullanılmaz. Kendi geliştirme ölçümünde 24 bozuk Metrica kopyasında bizim sistem 0,702, TCN 0,714, birleşim 0,731-0,734 çıkmıştı.

**Bu sayılar neden karar için yetmedi.** Karışım ağırlığı ve geçiş maliyeti puanlanan kopyalarda denenmişti; etiketler
`metrica_labels.py` ile değil kendi betiğiyle üretilmişti (K005); bizim taraf v2.11 değil v2.4 yoluydu; TCN ağırlıkları sonradan
yeniden eğitildi; ölçüm yalnız Metrica'daydı. Yazar da aynı görüşteydi ve kendi dalına bir doğrulama taslağı koydu
(`docs/POSSESSION_TCN_VALIDATION_PLAN.md`): karışım sabit (0,5 / 6), yeni tohumlar, v2.12'nin kapıları; kapılar geçmezse
birleşim kullanılmaz. Bizim kayıtlı planımız bu taslağı tohumlar, dosya özetleri ve eşiklerle kesinleştirir.

**Plan.** `possession-v213-plan.json`, 13 Kasım 12:12'de kaydedildi. O anda birleşimin ya da depoya konan TCN ağırlıklarının
hiçbir dış maçtaki puanı bizde yoktu (yazarın bildirdiğine göre onda da yoktu); kayıttan önce görülenler planın
`seen_on_external_data_before_registration` bölümünde. Tasarım:
- 16 yeni bozuk kopya (4 doğrulama maçı × 4; tohum 13100 + 10·maç + j; önceki hiçbir planda yok), 46 anonim slota paketlenmiş,
  gürültü kapısı ve kaleci denetimi teslim sistemindeki gibi.
- Koşullar: yalnız taktik kamera (16 kopya; G1-G5), benzetilmiş iyi ve orta yayınla top doldurma (8'er kopya; G6), 42 m kamera
  penceresi (8; yalnız rapor), TCN yazarının benzeticisiyle üretilmiş kopyalar (4; yalnız rapor).
- DFL maçlarında (J03WN1, J03WR9): bizim taraf her doğrulamadaki dört maçlık doğrulama modelleri, TCN tarafı o maç çıkarılarak
  beş maçla eğitilmiş ağırlıklar. Metrica 1-2'de: yayımlanacak çift (altı DFL maçlı paketlerimiz + `tcn_dfl6.npz`).
- TCN'in girdisi bizim modellerin gördüğü takip verisi (paketlenmiş, kaleci düzeltmeli, kapı açıksa doldurulmuş top).
- Kapılar (yuvarlanmamış değerlerle, bir kez): G1 ortalama fark ≥ +0,008; G2 DFL ≥ +0,008; G3 Metrica ≥ −0,002; G4 hiçbir
  kopya −0,010'dan kötü değil; G5 macroF1 ≥ −0,003; G6 iki doldurma koşulunda ≥ 0.
- Betikler ve TCN modüllerinin commit'teki baytlarla kopyaları: `experiments/possession_v2/v213/` (SHA-256 değerleri planda).
  Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5.

**Sonuç** (`possession-v213-results.json`; spellF1, organizatörün ölçütü; yarışma puanı değil):

| koşul | kopya | v2.11 | birleşim | fark | iyi / kötü | en kötü kopya | TCN tek başına | macroF1 farkı |
|---|---|---|---|---|---|---|---|---|
| yalnız taktik kamera, hepsi | 16 | 0,6598 | 0,6661 | +0,0063 | 9 / 7 | −0,0295 | 0,6257 | +0,0013 |
| yalnız taktik kamera, DFL | 8 | 0,6640 | 0,6594 | −0,0045 | 3 / 5 | −0,0295 | 0,6219 | +0,0007 |
| yalnız taktik kamera, Metrica | 8 | 0,6556 | 0,6728 | +0,0172 | 6 / 2 | −0,0100 | 0,6295 | +0,0018 |
| iyi yayınla doldurma | 8 | 0,6959 | 0,7066 | +0,0107 | 6 / 2 | −0,0070 | 0,6680 | +0,0028 |
| — bunun DFL kopyaları | 4 | 0,6877 | 0,6973 | +0,0096 | 3 / 1 | −0,0070 | 0,6642 | +0,0050 |
| — bunun Metrica kopyaları | 4 | 0,7040 | 0,7159 | +0,0118 | 3 / 1 | −0,0056 | 0,6719 | +0,0006 |
| orta yayınla doldurma | 8 | 0,6906 | 0,7050 | +0,0143 | 6 / 2 | −0,0122 | 0,6630 | +0,0031 |
| — bunun DFL kopyaları | 4 | 0,6835 | 0,7025 | +0,0190 | 3 / 1 | −0,0114 | 0,6643 | +0,0069 |
| — bunun Metrica kopyaları | 4 | 0,6977 | 0,7074 | +0,0097 | 3 / 1 | −0,0122 | 0,6617 | −0,0007 |
| 42 m kamera penceresi (rapor) | 8 | 0,6506 | 0,6608 | +0,0101 | 4 / 4 | −0,0143 | 0,6151 | +0,0022 |
| TCN yazarının benzeticisi (rapor) | 4 | 0,6685 | 0,6962 | +0,0277 | 3 / 1 | −0,0071 | 0,6805 | +0,0077 |

Yalnız taktik kamerada kopya kopya farklar: J03WN1 +0,0284, +0,0267, −0,0295, −0,0181; J03WR9 −0,0113, −0,0119, −0,0279,
+0,0072; Metrica 1 −0,0022, +0,0182, −0,0100, +0,0040; Metrica 2 +0,0263, +0,0317, +0,0254, +0,0441.

| kapı | değer | sonuç |
|---|---|---|
| G1 ortalama kazanç ≥ +0,008 | +0,0063 | **geçmedi** |
| G2 DFL'de kazanç ≥ +0,008 | −0,0045 | **geçmedi** |
| G3 Metrica'da ≥ −0,002 | +0,0172 | geçti |
| G4 en kötü kopya ≥ −0,010 | −0,0295 | **geçmedi** |
| G5 macroF1 ≥ −0,003 | +0,0013 | geçti |
| G6 doldurma koşulları ≥ 0 | +0,0107 ve +0,0143 | geçti |

**Karar (13 Kasım 13:58).** 3 kapı geçmedi (G1, G2, G4); kayıtlı kurala göre birleşim teslim sistemine girmedi. Kapılar
bir kez uygulandı; başka tohum, ağırlık, karışım oranı ya da geçiş maliyeti denenmedi. Teslim sistemi bizim modelimizle kalıyor
(başlama vuruşu kuralı ayrı kayıt: K011).

**Yanında raporlananlar (yalnız taktik kamera, 16 kopya).** 2 saniyeden kısa sahipliklerin yakalanma oranı: v2.11 0,288,
birleşim 0,281, TCN 0,296; 1 saniyeden kısalar: 0,122 / 0,104 / 0,121. Geçiş F1 (12 kare): 0,562 / 0,561 / 0,518.
Kopya başına sahiplik sayısı: etiketlerde 403, v2.11 308, birleşim 310, TCN 344. Birleşim kopya başına ortalama 5.096
karenin etiketini değiştirdi. Bütün kopyalarda gürültü kapısı v2.1 yolunu seçti; doldurma kapısı iyi yayında 8/8, orta
yayında 8/8 kopyada açıldı.

**Yorum (çıkarım, ölçüm değil).**
- Birleşim ortalamada biraz iyi (+0,0063), ama kaynağa göre ayrışıyor. Metrica kopyalarında +0,0172: Metrica 2'nin dört
  kopyasının dördünde kazanç var, Metrica 1'de fark sıfırın iki yanında. DFL kopyalarında −0,0045: sekiz kopyanın beşi
  kötü, üçü −0,018 ile −0,030 arasında. Kayıtlı kurallar iki kaynakta da kazanç ve hiçbir kopyada belirgin kayıp istiyordu.
- TCN tek başına bizim 16 kopyamızın hiçbirinde v2.11'i geçmedi (0,6257 / 0,6598). Yazarın benzeticisiyle üretilen 4
  kopyanın 3'ünde geçti (0,6805 / 0,6685) ve birleşim orada +0,0277 kazandırdı. O kopyalarda ölçülen konum gürültüsü daha
  düşük (top 0,02-0,10 m, oyuncular 0,05-0,07 m; bizim kopyalarda top 0,07-0,30 m, oyuncular 0,04-0,30 m). TCN, eğitildiği
  benzeticinin kopyalarında belirgin daha güçlü; v2.11 iki benzeticide de benzer puan alıyor (0,6685 / 0,6598). Hangi
  benzeticinin sağlanan takip verisine daha çok benzediği bilinmiyor ve buna bakılamaz. Bizim 16 kopyanın içinde farkın
  ölçülen gürültüyle ilişkisi zayıf (r = +0,31) ve ters yönde; "gürültü azsa birleşim iyidir" sonucu bu veriden çıkmaz.
- Yayınla doldurma koşullarında ve 42 m pencerede birleşim ortalamada iyi (+0,0107, +0,0143, +0,0101), ama orada da tek
  kopyada −0,0122 ve −0,0143 var.
- Birleşim bizim çözücümüzü (ölü top eğilimi, oyuna giriş ve çıkış maliyetleri) tek maliyetli bir çözücüyle değiştiriyor.
  Kazancın ve kaybın ne kadarının ikinci modelden, ne kadarının çözücü değişikliğinden geldiği ayrıştırılmadı.
- Tek bir maç teslim edeceğimiz için kopyadan kopyaya ±0,03 oynayan bir değişikliği almamak G4'ün amacıydı. Sonuç "iki
  model birleştirilemez" demek değildir; başka bir birleştirme kuralı yeni bir kayıtlı planla denenebilir. Bu teslimden
  önce yapılmayacak: zaman yok ve kapılar sonradan gevşetilmez.

**Karardan sonra, bir kez (kapı değil).**
- Ayrılmış Metrica maçı 3 (yeni bir kopya, tohum 33103; bu maç TCN ailesi için dokunulmamış değil): yalnız taktik kamera
  0,7141 → 0,7126 (−0,0015; TCN tek başına 0,6321); iyi yayınla 0,7479 → 0,7325 (−0,0154; TCN 0,6615); orta yayınla
  0,7297 → 0,7470 (+0,0173; TCN 0,6526); 42 m pencere 0,7016 → 0,6982 (−0,0034; TCN 0,6142); yazarın benzeticisiyle
  0,7219 → 0,7482 (+0,0262; TCN 0,7166).
- K009'daki PFF maçı (3839, yayın takibi, bozma eklenmedi; karşılaştırma PFF olaylarından kurduğumuz vekille; lisansı
  yayımlanmamış veri, seçimde kullanılmaz): v2.11 0,629, birleşim 0,632, TCN tek başına
  0,619 (macroF1 0,898 / 0,905 / 0,901).

**Kesinti.** Doğrulamanın son parçası (Metrica 2) çalışırken bulut oturumu yeniden başladı; o parçanın hiçbir satırı
kaydedilmemişti. Aynı betik, aynı tohumlarla, değiştirilmeden yeniden başlatıldı (`exp_v213.py 3`); önceki üç parçanın
satırları olduğu gibi kullanıldı.

**Sınırlar.**
- Doğrulama maçları iki model için de taze değil: v2.x'in bütün seçimlerinde ve TCN tarifinin geliştirilmesinde kullanıldılar;
  yeni olan yalnız kopyalar. Birleşim için dokunulmamış bir test maçı yok (J03WMX TCN'in geliştirilmesinde kullanıldı).
- DFL satırlarında bizim taraf dört maçla, TCN tarafı beş maçla ve üç yerine tek tohumla eğitilmiş; Metrica satırlarında ikisi
  de altı maçla. Bu bir eşitsizliktir ve hangi yöne çalıştığı ölçülmedi.
- Bozma, slot paketleme, kamera penceresi ve yayın akışı bizim benzetimimiz; TCN kendi yazarının benzeticisiyle eğitildi.
- DFL etiketleri sağlayıcının bayrakları, Metrica etiketleri olaylardan türettiğimiz vekiller.
- Bu, önerilen tek bir birleştirme kuralının ölçümüdür; "iki model birleştirilemez" demek değildir.

## K009 — Dış maçta izleme: PFF FC Dünya Kupası 2022, İspanya–Almanya (yalnız inceleme), 12 Kasım 2026

**Ne.** Kullanıcının isteğiyle teslim sistemi bir dış maçta izlendi. Yalnız inceleme ve rapor: hiçbir seçim,
ayar ya da eğitim yapılmadı. possession-v2.11'in karar adımları, ikinci kamera olmadan (`run211`'in yayın
dosyası yokken izlediği yol), PFF FC'nin 2022 Dünya Kupası açık veri setindeki 3839 numaralı maçta çalıştırıldı
ve PFF'in olay kayıtlarından bizim kurduğumuz bir vekil etiketle karşılaştırıldı. `check_release()` aynı kopyada
geçti. Betikler, dosya özetleri ve SHA-256 değerleri: `experiments/possession_v2/pff_viewer/README.md`.

**Veri ve lisans.** PFF FC blogundaki formla (yalnız ad ve e-posta) 12 Kasım 2026'da alındı; form bir Google
Drive klasörüne yönlendiriyor. Lisans metni yayımlanmamış. Bu yüzden veri, kare düzeyi çıktılar ve izleyici
HTML'i depoda değil (klasördeki `.gitignore` bu adları dışarıda tutuyor), paylaşılmıyor; model ya da parametre
seçiminde kullanılmadı, lisans netleşmeden kullanılmayacak. Maç videosu veri setinde yok; izleyici, maçın yayın
tekrarıyla maç saati üzerinden yan yana izlenmek için yapıldı. Sağlanan maça dokunulmadı.

**Dönüşüm.** 29,97 fps PFF yayın takibi 25 fps'e çevrildi. Oyuncular PFF'in düzeltilmiş konumları (görülen ya da
ekran dışı tahmin); top yalnız PFF'in "görünür" dediği karelerde. Oyun karelerinde topun görünme payı %41,2,
ortalama 22,0 oyuncu. Yol v2.1 (top gürültüsü 0,002 m); kaleci denetimi hiçbir parçayı taşımadı.

**Vekil (gerçek cevap değil).** Topla oynama olayından sonra o oyuncunun takımı; OUT/END'den yeniden başlamaya
kadar ölü top; OUT izlemeyen serbest vuruş ve hakem atışından önce, önceki olaydan 0,5 s sonrasından başlayarak
ölü; devreler dışında ölü. PFF'in olay zamanları ve tanımları organizatörün etiketleriyle aynı değil.

**Sonuç (organizatörün puan kodu; vekile göre uyum).** spellF1 0,629; macroF1 0,898; oyun karelerinde aynı
etiket %90,6; canlı/ölü F1 0,943; ikisi de canlıyken takım doğruluğu 0,943; geçiş F1 12 kare içinde 0,419,
25 kare içinde 0,535 (kesinlik 0,649, yakalama 0,455).

**Döküm (`analyse_pff.py`).**
- Aynı etiket: top görünürken %96,1, görünmezken %86,7.
- En büyük ayrışma, vekil "oyunda" derken bizim "ölü" dememiz: oyun karelerinin %5,4'ü. Vekilin "oyunda" dediği
  karelerde top görünürken %1,1, görünmezken %28,4 oranında "ölü" diyoruz. Takım ters (ikisi de canlı) %3,0;
  biz canlı, vekil ölü %1,0.
- 2 s'den uzun ölü top dönemleri: vekilde 97, bunların 92'si bizde de çoğunlukla ölü; bizde 85, bunların 79'u
  vekilde de. Başlangıç farkı (biz eksi vekil) medyan -0,02 s (çeyrekler -1,05 / +0,12); bitiş farkı medyan
  +1,82 s (çeyrekler +0,23 / +4,38): oyunun yeniden başladığını geç görüyoruz.
- Sahiplik sayısı bizde 236, vekilde 360 (ev sahibi dönemlerinin medyan süresi 9,8 s / 5,3 s). Eşleştirme bire
  bir olduğu için yalnız bu sayı farkı spellF1'i bu vekilde 0,79 civarında sınırlar.
- 2 s'den uzun 92 uyuşmazlık parçası, uyuşmazlık karelerinin %73,9'unu tutuyor; en uzun 15 parçanın 12'sinde top
  karelerin en çok %6'sında görünüyor.

**Yorum (çıkarım, ölçüm değil).** Yayın takibinde top, yakın çekim ve tekrar anlarında uzun süre görünmüyor;
modelimiz uzun top boşluğunu ölü top lehine okuyor gibi görünüyor. Kısa sahipliklerin birleşmesi K007'deki DFL
teşhisiyle aynı yönde. Yeniden başlamayı geç görme K007'de ayrı bir kalem olarak raporlanmadı; DFL'de ölçülmeden
bir değişiklik gerekçesi değildir. Yarışma verisi taktik kameradan, başka bir sağlayıcıdan ve başka bir top
görünürlüğüyle geliyor: bu sayılar yarışmadaki başarıyı göstermez ve DFL/Metrica doğrulama sayılarıyla doğrudan
karşılaştırılamaz.

**Geriye kalan.** Hiçbir sürüm değişmedi. Betikler depo konumundan `python -I` ile çalıştırıldığında
`3839_summary.json`, `3839_analysis.json`, iki `.npz` ve izleyici bit bit aynı çıktı. İzleyici kullanıcının
bilgisayarında (İndirilenler altında); depoda yok. Ortam: Python 3.13.18, numpy 2.5.3.

## K008 — v2.12 adayı: topa dokunma ve kontrol değişimi sütunları; kayıtlı kapılardan geçmedi, 12 Kasım 2026 gecesi

**Ne denendi.** K007'nin bulduğu kayıp (2 saniyeden kısa sahipliklerin çoğu kaçırılıyor) için çekirdek modellere
36 yeni sütun eklendi (`possession/touch.py`). Her karede, topun görünür olduğu önceki ve sonraki 0,28 saniyeye
birer doğru oturtuluyor; iki doğrunun hız farkı ölçüm gürültüsüne bölünüyor; fark büyükse "dokunma" sayılıyor ve
2 m içindeki en yakın oyuncunun takımına yazılıyor. Top 0,6 saniyeye kadar kaybolduğunda dokunma, gelen ve giden
doğruların buluştuğu yerde çıkarılıyor; hiçbir yere top konumu yazılmıyor. Sütunlar: her takımın son dokunmasından
beri geçen süre, son dokunmanın kimde olduğu, son 1 saniyedeki dokunmalar, topun en yakın oyuncuyla birlikte
hareket edip etmediği, o oyuncunun üzerindeki baskı. Yalnız v2.1 yolu (gürültü 0,30 m altı) değişecekti; dokunma
sütunları yayın kamerası doldurmasından önceki taktik top üzerinden hesaplanacaktı.

**Geliştirme (yalnız 4 DFL eğitim maçı, maç dışarıda bırakmalı).** İkinci aşamayla spellF1 0,669 → 0,690; 20
kopyanın 19'unda iyileşme, en kötü kopya -0,0011; yeni bozma tohumlarında +0,016; 2 s altı sahiplik yakalama
0,322 → 0,380. Tasarım ajanı geliştirdi; bunlar geliştirme sayıları, test değil (`possession-v212-development.json`).

**Bağımsız denetim (iki tur, kod yazmamış ayrı bir ajan).** `touch.py`'de etiket sızıntısı, takım değişimi
simetrisi ya da belirlenimcilik hatası bulunmadı; Python 3.10/numpy 1.26 ile 3.13/numpy 2.5 arasında bit bit aynı.
Önbellekteki dokunma dizilerinin bir kısmı, dosyanın son düzenlemesinden önce başlayan bir süreçte üretilmişti
(M1); 40 dizinin ve 4 satır dosyasının hepsi kayıtlı dosyayla yeniden hesaplandı, bit bit aynı çıktı
(`verify_caches.json`). İkinci tur bir engelleyici buldu (B1): kapı betiği 4 basamağa yuvarlanmış değerlerle karar
veriyordu (-0,00004 "≥ 0" kapısından geçebilirdi); kayıttan önce düzeltildi, kapılar yuvarlanmamış değerlere
uygulandı. Plan metnindeki üç abartılı ifade de kayıttan önce düzeltildi (özet planın içinde).

**Ön kayıt.** `possession-v212-plan.json`, 12 Kasım 02:16:05; aynı dakika kullanıcının bilgisayarına kopyalandı
(dosya saati 02:16:15). Doğrulama: 4 doğrulama maçının 16 yeni bozulmuş kopyası (tohum 12100-12133; 46 anonim
yuva; gürültü kapısı; kaleci düzeltmesi), 8'inde iki yayın kamerası simülasyonu ve 42 m kamera penceresi. Altı
kapı, karar kuralı ve tohum taraması planda.

**Sonuç (kapılar bir kez, bütün satırlara uygulandı; `possession-v212-results.json`).**

| koşul | v2.11 → v2.12 spellF1 farkı (ortalama) | DFL (8 / 4 kopya) | Metrica (8 / 4 kopya) |
|---|---|---|---|
| taktik kamera, 16 kopya | +0,0024 (10 iyi, 6 kötü) | +0,0125 (8'i de iyi) | -0,0077 (2 iyi, 6 kötü) |
| yayın simülasyonu, iyi | -0,0025 | +0,0149 | -0,0199 |
| yayın simülasyonu, orta | -0,0062 | +0,0073 | -0,0197 |
| 42 m kamera penceresi (rapor) | -0,0005 | +0,0045 | -0,0055 |

Kapılar: G1 kazanç ≥ +0,008 **geçmedi** (+0,0024); G2 DFL kazancı ≥ +0,008 geçti (+0,0125); G3 Metrica zararsızlık
≥ -0,002 **geçmedi** (-0,0077); G4 hiçbir kopya -0,010 altında değil **geçmedi** (en kötü -0,0191, MET2); G5 macroF1
geçti (+0,0011); G6 yayın doldurmasıyla zararsızlık **geçmedi** (-0,0025 / -0,0062). **Karar: v2.12 kullanılmıyor,
possession-v2.11 teslim sistemi olarak kalıyor.** Kapılar gevşetilmedi, başka tohum ya da ayarla yeniden
çalıştırılmadı.

**Rapor (karar sonrası, kapı değil).** Ayrılmış Metrica maçı 3'ün bir yeni kopyası (tohum 32103): taktik +0,018
(0,703 → 0,721), yayın iyi -0,002, orta +0,010, 42 m pencere +0,049. 2 s altı sahiplik yakalama: DFL 0,316 →
0,347; Metrica 1-2'de 0,244 → 0,231, yayın doldurmasıyla 0,268 → 0,199.

**Yorum (çıkarım, ölçüm değil).** Dokunma kanıtı DFL'nin kare başına sahiplik bayrağını her koşulda ve her kopyada
daha iyi izliyor. Metrica maç 1-2'de (başka izleme sağlayıcısı; etiketleri olaylardan bizim türettiğimiz vekiller;
bozulmuş kopyalarda top oyun karelerinin %35-50'sinde görünür, DFL'de %61-79) tahminleri vekil etiketlerden
uzaklaştırdı; maç 3'ün tek kopyasında tersi oldu. Bunun etiket tanımından mı, izleme sağlayıcısından mı, şanstan mı
geldiği bu verilerle ayrılamıyor. Organizatörün etiketi düzeltilmiş izlemenin sahiplik bayrağından türetildiği için
DFL sonucu tanım olarak daha yakın görünebilir; ama kapılar sağlam olmayı da ölçmek için önceden yazıldı ve karar
onlara göre verildi.

**Geriye kalan.** `possession/touch.py` ve `tests/test_possession_touch.py` yayımlanmamış aday kaydı olarak duruyor
(v2.10'un `keeper.py`'si gibi). Hazırlanan giriş noktası, boru hattı, eğitim betiği ve testleri hiçbir zaman
çalıştırılmadı ve yayımlanmadı; `experiments/possession_v2/v212/integration_not_released/` altına taşındı. Sağlanan
maça dokunulmadı. Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1.

## K007 — Teşhis: takım kararlarındaki kayıp nerede?, 11 Kasım 2026 gecesi

**Ne.** Yalnız rapor amaçlı; hiçbir seçim yapılmadı. Daha önce kullanılmış 8 doğrulama kopyası (J03WN1, J03WR9,
MET1, MET2 x bozma tohumu 101/102), v2.1 çekirdeğinin önbellekteki olasılıkları (v2.11'in çekirdek modelleri
aynı) ve dondurulmuş çözücü. Sağlayıcı etiketleri yalnız hataları sınıflamak ve "kâhin" üst sınırlarını ölçmek
için kullanıldı. Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5 (K005 kuralı; Metrica etiketleri dosya
sırasıyla). Kayıt: `possession-k007-diagnosis.json`; betikler `experiments/possession_v2/err_spells.py`,
`err_short.py`.

**Bulgular.**
- spellF1 0,631. Bütün tahmin geçişlerini 5-25 kare ileri ya da geri kaydırmak puanı her iki yönde düşürüyor:
  sistematik bir gecikme yok.
- 3.226 gerçek sahiplikten 1.428'i beş IoU eşiğinin hepsinde, 650'si yalnız bir kısmında eşleşti; 1.148'i hiç
  eşleşmedi. 2 saniyeden kısa 926 sahipliğin 686'sı (%74) kaçırılıyor; 1 saniyenin altında 410'un 356'sı.
  Kaçırılan sahipliklerin %60'ı 2 saniyeden kısa.
- Tahmin edilen 2.436 sahiplikten 358'i hiçbir gerçek sahiplikle eşleşmiyor.
- Kâhin üst sınırları (etiket kullanır, ulaşılabilir değil, yalnız büyüklük): kaçırılan 2 s altı sahiplikler
  eklense 0,788; yakalanan sahipliklerin sınırları kusursuz olsa 0,896; 2 s altı fazladan sahiplikler silinse 0,651.
- Sınır sapmalarının medyanı 0-2 kare, ortalama mutlak sapma 20-42 kare. En uzun kuyruk, rakibe geçişte
  sahipliğin geç bitmesi (çeyrek üstü +18 kare, ortalama 42 kare). Yanlış takım karelerinin %66'sı gerçek bir
  değişikliğin 1 saniye yakınında.
- Olasılıklar da kısa sahiplikleri çoğunlukla görmüyor: kaçırılan 2 s altı sahipliklerin %38'inde ortalama takım
  olasılığı 0,5'in üstünde; uzun sahipliklerin içindeki eşit uzunluktaki pencerelerde bu oran %7,5. 0,8 eşiğinde
  %16'ya %3,7.
- Bozulmuş girdide top, kaçırılan 2 s altı sahipliklerde zamanın %56'sında görünüyor; yakalanan kısa
  sahipliklerde %83'ünde. Topun kaybolması kaçırmaların bir kısmını açıklıyor, ama kaçırılan kısa sahipliklerin
  yaklaşık yarısında top zamanın en az yarısında görünür durumda (`err_ballvis.py`).

**Yorum.** Kaybın büyük kısmı kısa sahipliklerden ve rakibe geçişlerin geç yakalanmasından geliyor. Çözücü ayarı
ya da sonradan sahiplik eklemek tek başına yetmez, çünkü olasılıklardaki sinyal zayıf; bu anları gösteren yeni
kanıt gerekir (topa dokunma ve kontrol değişimi). Bir sonraki adayın gerekçesi budur; aday ön kayıtla ve taze
kopyalarla seçilecek.

## K006 — İlk teslim zinciri ve GitHub testleri, 11 Kasım 2026 akşamı

**Teslim zinciri (kullanıcının bilgisayarı, Windows 10, Python 3.10.11, commit `0810fec`).** Paylaşılan durum
satırları: ORTAM, SURUM, TESTLER, GIRDI OKUMA, BICIM, MAKULLUK, ORGANIZATOR DOGRULAYICI, ACIK PENCERE (geçti/kaldı)
OK; PLATFORM AYNI (yedi sentetik varyant Windows'ta da aynı bayt); TEKRAR URETIM ve TEMIZ KLON AYNI; URETIM
`possession-v2.11, saatsiz`; SAAT ATLANDI (videolar zincirin beklediği yerde değil). Sonuç: teslim dosyası hazır,
uyarı yalnız SAAT. Doğruluk ölçümü değildir; sağlanan maça dair başka hiçbir bilgi paylaşılmadı.

**GitHub Actions #11 (aynı commit, Ubuntu/3.12 ve Windows/3.10, sahiplik paketleri ilk kez kurulu).** 411 testten
biri iki makinede de kaldı: `test_possession_deliver` içinde yapay hatalı giriş noktasının hata sınıfı
`ValueError` yerine `hata` okundu. Neden: alt programın `print` çıktısı dosyaya yazılırken tamponlanıyor ve
traceback'ten sonra diske düşüyordu; `error_class` son satırı istisna satırı sanıyordu. Bulut oturumunda
`PYTHONUNBUFFERED=1` tanımlı olduğu için görünmemişti (değişken kaldırılınca burada da tekrarlandı). Etki yalnız
hata durumunda ekrana yazılan sınıf adıdır; üretilen dosyayı, sürümü ya da bu akşamki zinciri etkilemez.
Düzeltme `tools/possession_deliver.py`: alt programlar `PYTHONUNBUFFERED=1` ile çalışır ve istisna satırı son
çerçeveden sonraki ilk girintisiz satırdan okunur; teste tamponlu çıktı durumu eklendi. Dondurulmuş dosya
değişmedi.

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

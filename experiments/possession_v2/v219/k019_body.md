## K019 — Teslim zinciri ekibin bilgisayarında v2.16 ile OK; çıkan dosya v2.15 dosyasıyla aynı baytlar; form gönderildi, 15-16 Kasım 2026

**Ne oldu.**
- *Form (15 Kasım, yaklaşık 18:45).* Takım lideri organizatörün gönderim formunu K018 çalıştırmasının dosyalarıyla gönderdi:
  takım adı LittleSickle, `LittleSickle.csv`, bu dalın adresi, `LittleSickle.md` (v2.15 belgesi). Formu yalnız takım lideri
  doldurur; bu süreç forma dokunmadı ve tahmin dosyasını okumadı. Form bağlantısı yalnız katılımcılara gönderildiği için depoya
  yazılmadı. Form aynı bağlantıdan yeniden gönderilebiliyor; organizatörün SUBMISSION.md dosyasına göre son tarihten önceki son
  yanıt puanlanır.
- *v2.16 zinciri (16 Kasım).* Takım lideri `TESLIM-TEK-TIK.cmd`'yi 00:13'te yeniden başlattı (yeni sürümde tuş beklemedi).
  Commit `1c31412` (v2.16, K015-K018 kayıtları) GitHub'a gitti; GitHub Actions bu commit'te başarılı (17 dk 41 sn; Ubuntu
  3.12 ve Windows 3.10). Zincir 00:13-01:04 arasında çalıştı (51 dakika; saat okuması önceki çalıştırmadan alındı).

**Paylaşılabilir durum satırları** (`Desktop\logs\PAYLASILABILIR-durum.txt`; başka hiçbir çıktı okunmadı):

```
[ 1] ORTAM ..................... OK (Windows-10-10.0.19045-SP0, Python 3.10.11, numpy 1.26.4, scipy 1.11.4, pandas 2.1.4)
[ 2] DEPO ...................... commit 1c3141279e45, temiz
[ 3] SURUM ..................... OK (possession-v2.16)
[ 4] TESTLER ................... OK
[ 5] PLATFORM .................. AYNI
[ 6] VERI ...................... OK (taktik VAR, yayin VAR, videolar VAR, smart tagging VAR)
[ 7] GIRDI OKUMA ............... OK
[ 8] URETIM .................... OK (possession-v2.16, saatli)
[ 9] BICIM ..................... OK
[10] MAKULLUK .................. OK
[11] TESLIM .................... OK (possession-v2.16, saatli; onceki teslim dosyasi ile AYNI)
[12] SAAT ...................... VAR (onceki okuma kullanildi)
[13] SAATSIZ KARSILASTIRMA ..... AYNI
[14] TEKRAR URETIM ............. AYNI
[15] TEMIZ KLON ................ AYNI (commit 1c3141279e45)
[16] ORGANIZATOR DOGRULAYICI ... OK
[17] ACIK PENCERE .............. OK
[18] BELGE ..................... OK (LittleSickle.md = teknik belge + calisma kaydi)
SONUC: TESLIM HAZIR
```

**Ne anlama geliyor.**
- K017'nin son koşulu sağlandı: zincir ekibin bilgisayarında OK bitti, `URETIM` ve `TESLIM` satırlarında `possession-v2.16`
  yazıyor. On bir sentetik varyant (ikisi oyuncu eklemeli) Windows'ta Linux'ta kaydedilen baytları verdi; dosya ikinci
  çalıştırmada, saat okumaları olmadan ve dalın temiz klonundan da aynı baytlarla üretildi.
- **`onceki teslim dosyasi ile AYNI`:** v2.16'nın bu maçta ürettiği dosya, bir gün önce v2.15'in ürettiği ve forma yüklenen
  dosyayla bayt bayt aynıdır. v2.16'nın eklediği adım bu maçta hiçbir etiketi değiştirmedi. Neden: ya iki kameranın topta
  anlaşmasını ölçen doğruluk kapısı kapalı kaldı, ya da kapı açıkken eklenecek oyuncu bulunmadı (ya da eklenenler kararı
  değiştirmedi). Hangisi olduğu teslim belgesinin Ek R'sinde ("Broadcast camera" ve "Players added from the broadcast
  camera" satırları) yazılıdır; bu süreç o eki okumaz.
- K017'deki +0,0104, benzetilmiş ikinci kamerayla dış maç kopyalarında ölçülmüştü; bu maç için bir kazanç iddiası değildi. Bu
  satır, o kazancın bu maçta gerçekleşmediğini gösterir: puanlanacak dosya v2.15'in dosyasıdır.
- Bu bir özet (hash) karşılaştırmasıdır: yalnız sağlanan veriyle yapılan otomatik bir denetim. Doğruluk ölçümü değildir ve
  hiçbir seçimde kullanılmadı (v2.16 dış veride, bu çalıştırmadan önce seçilmişti; iki çıktı zaten aynıdır).
- Formdaki sahiplik dosyası bu yüzden değişmedi. Yeni `LittleSickle.md` v2.16'yı anlatır; takım liderine 16 Kasım sabahı
  formu yeni belgeyle bir kez daha göndermesi söylendi. Bunun yapıldığı, bu kayıt yazılırken teyit edilmemişti.

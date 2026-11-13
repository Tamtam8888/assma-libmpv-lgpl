# libmpv LGPL uyum değerlendirmesi (yayın b10)

**Durum:** teknik değerlendirme. Hukuki onay değildir.
**Tarih:** 13.11.2026.
**Hazırlayan:** Claude.
**İstek:** ChatGPT incelemesi, 13.11.

**Değerlendirilen dağıtım:** `libmpv-lgpl-v0.42.0-dev-gfe753a782-fe753a782-x64-b10`.
- Zip SHA-256: `a4d3b13d…6fdb`
- `libmpv-2.dll` SHA-256: `34b7bd89…6257`

Değerlendirme, dağıtılan dosyaların kendisi üzerinden yapıldı: zip, ekler ve kaynak arşivleri GitHub'dan indirilip açıldı.

## 0. Sonuç (kısa)

- **Teknik olarak kanıtlı karşılananlar:**
  - DLL'de GPL kod yok (bağlayıcı haritası ile).
  - LGPL/MPL bileşenlerin hepsinin kaynağı yayınla aynı yerde.
  - Lisans metinleri zip'te.
  - Kullanıcı DLL'i değiştirebiliyor.
- **Eksikler (düzeltilebilir):** 6 madde (bkz. 3).
  - Derlemeyi yöneten betikler kaynak arşivinde değil.
  - mingw-w64 / winpthreads lisans metinleri yok.
  - Üst düzey bildirim dosyası yok.
  - FreeType teşekkür cümlesi yok.
  - ASSMA tarafında kaynak sunumu ve About bildirimi eksik.
- **Hukuki belirsizlikler (karar hukukçunun):** 5 madde (bkz. 4). En önemlileri:
  - LGPL-2.1-only lisanslı libssh dosyaları ile LGPL-3 FFmpeg aynı DLL'de.
  - ASSMA'nın kendi kullanım koşulları henüz yok.
  - Codec patentleri.
- **Bu yayın için "LGPL'ye uygundur" onayı verilmiyor.**

## 1. Dağıtılan şey

| Parça | İçerik |
|---|---|
| `…-b10.zip` (58 MB) | `libmpv-2.dll`, `libmpv.dll.a`, `include/mpv`, `LICENSE.LGPL` (mpv, LGPL-2.1), `MANIFEST.json`, `INVENTORY.md`, `BUILDINFO.txt`, `SOURCES.txt`, `IMAGE-SOURCES.tsv`, `licences/` (4,3 MB, 130'dan fazla bileşenin lisans dosyaları), 2 libbluray `.jar` |
| `mpv-and-ffmpeg-sources.tar.xz` (129 MB) | mpv, FFmpeg ve tarifin klonladığı kütüphaneler (LuaJIT, libsixel, libarchive, uchardet, subrandr, windows-rs, winmd, mujs, cppwinrt), derlenen sürümleriyle |
| `image-library-sources.tar` (22 MB) | Derleme ortamından gelip DLL'e giren 15 LGPL/MPL kütüphanenin kaynağı |
| `SHA256SUMS.txt` | Yukarıdakilerin ve DLL'in özetleri |

**DLL'in içinde ne var? (kanıt yöntemi)**
- Bağlayıcı haritasının (`-Wl,-Map`) "Archive member included" bölümüne göre DLL'e 151 kütüphaneden 9.370 nesne girdi.
- Bunlardan 149'u lisans tablosunda sınıflandırıldı.
- GPL, nonfree ya da bilinmeyen lisanslı bir kütüphaneden alınan nesne sayısı 0.
- Bağlama satırında olup DLL'e hiç nesne vermeyen GPL kütüphaneler: `lcms2_fast_float` ve `lcms2_threaded` (GPL-3). Haritaya göre ikisinden de 0 nesne alındı.

**DLL'e giren copyleft bileşenler**

| Lisans | Bileşenler |
|---|---|
| LGPL | FFmpeg (7 kütüphane), libiconv, FriBidi, GMP, libudfread, aribb24, libbluray, LAME, libssh, soxr, TwoLAME, libplacebo, GME, Chromaprint |
| MPL | SRT, ZeroMQ, subrandr, uchardet |

Geri kalanı izin veren (permissive) lisanslı ya da Windows sistem kütüphanesi.

## 2. Yükümlülükler ve kanıtlar

Durum işaretleri: ✅ karşılanıyor (kanıtlı) · ⚠️ kısmen / eksik · ❓ hukuki belirsizlik.

| # | Yükümlülük | Dayanak | Durum | Kanıt / not |
|---|---|---|---|---|
| Y1 | GPL kod içermemek (kapalı program bağlayacak) | GPL-2/3 | ✅ | `MANIFEST.json` › `linked_libraries`: GPL sınıfında `members_in_dll` > 0 olan yok. FFmpeg `CONFIG_GPL 0`, `CONFIG_NONFREE 0`; mpv `gpl=false` (BUILDINFO). |
| Y2 | Lisans metinlerini ikili dosyayla birlikte vermek | LGPL-2.1 §1, §6; LGPL-3 §4(b) (LGPL-3 + GPL-3 metni) | ✅ | `LICENSE.LGPL` (2.1); `licences/recipe/ffmpeg/` içinde COPYING.LGPLv2.1, COPYING.LGPLv3, COPYING.GPLv2, COPYING.GPLv3. |
| Y3 | Hangi lisansın neye uygulandığını açıkça bildirmek | LGPL-2.1 §6 ("prominent notice"); LGPL-3 §4(a) | ⚠️ | Zip'te üst düzey bir NOTICE yok. DLL'in bütününün hangi koşullarla dağıtıldığı (pratikte LGPL-3.0-or-later, çünkü FFmpeg `--enable-version3`) hiçbir yerde tek cümleyle yazmıyor. INVENTORY.md bileşen bazında söylüyor. |
| Y4 | Telif ve lisans bildirimlerini korumak (BSD, MIT, ISC, Zlib, Apache…) | Her lisansın kendi koşulu | ⚠️ | `licences/image/` 71 aşama, `licences/recipe/` 11 kaynak, `licences/rust/` 51 paket (57 Rust paketinin hepsi metinli ya da subrandr'ın kendi MPL'i). **Eksik:** winpthreads (MIT/BSD, DLL'de 9 nesne) ve mingw-w64 CRT (`mingwex` 80, `mingw32` 8 nesne). GCC çalışma kütüphaneleri (`gcc`, `stdc++`, `gomp`) GCC Runtime Library Exception kapsamında; dağıtım için bildirim şartı yok. |
| Y5 | Apache-2.0 NOTICE dosyalarını aktarmak | Apache-2.0 §4(d) | ⚠️ | opencore-amr NOTICE var. Diğer Apache bileşenleri (Vulkan loader, shaderc, SPIRV-Cross, OpenCL, OpenSSL 3) için toplayıcı en fazla 3 klasör derinliğinde arıyor. NOTICE dosyaları olmadıkları ayrıca doğrulanmadı. |
| Y6 | FreeType teşekkür cümlesi ("Portions of this software are copyright © The FreeType Project") | FTL §3 | ⚠️ | FreeType DLL'de (32 nesne). Cümle ne zip'te ne ASSMA belgelerinde. |
| Y7 | Karşılık gelen kaynak kodu: kütüphanelerin kaynağı | LGPL-2.1 §6(a); LGPL-3 §4(d)(0) + GPL-3 §6 | ✅ | 24 copyleft bileşenin 24'ü kapsandı. mpv, FFmpeg, uchardet ve subrandr `mpv-and-ffmpeg-sources.tar.xz` içinde; diğer 15'i `image-library-sources.tar` içinde. |
| Y8 | Karşılık gelen kaynak: derlemeyi yöneten betikler | LGPL-2.1 §0 ("scripts used to control compilation and installation"); GPL-3 §1 | ⚠️ | mpv'nin `ci/build-mingw64-full.sh` betiği kaynak arşivinde. `git-pin-shim`, `pins.lock`, workflow ve FFmpeg-Builds `scripts.d` (c9fe5114) **arşivde yok**. Hepsi herkese açık depolarda ama yayının içinde değil. |
| Y9 | Kaynağın gerçekten bu ikiliye karşılık gelmesi | Y7/Y8'in özü | ⚠️ | mpv, FFmpeg ve tarifin klonları: commit'ler derleme sırasında okundu, kanıt güçlü. Derleme ortamındaki kütüphaneler: commit'ler ortamın içinden okunamadı; FFmpeg-Builds sürümü dolaylı yoldan çıkarıldı (bkz. B4). |
| Y10 | Kaynağa erişim yolu ve süresi | LGPL-2.1 §6(c)/(d); GPL-3 §6(d) | ⚠️ | GitHub yayınında ikiliyle aynı sayfada; "aynı yerden eşdeğer erişim" sağlanıyor, yayın durdukça. ASSMA saha paketi DLL'i kendi zip'ine koyarsa dağıtıcı ASSMA olur. O zaman kaynak ya pakete girmeli ya da yazılı teklif verilmeli. Bu henüz yapılmadı. |
| Y11 | Kullanıcının kütüphaneyi değiştirip yerine koyabilmesi | LGPL-2.1 §6(b); LGPL-3 §4(d)(1) | ✅ | ASSMA libmpv'yi çalışırken ayrı bir DLL olarak yüklüyor (ctypes; mpv kodu ASSMA'da yok). Tools > Locate mpv library ile başka bir DLL seçilebiliyor (`licences.py`, libmpv kaydı). Arayüzü uyumlu değiştirilmiş bir DLL ile çalışır. |
| Y12 | DLL içindeki statik LGPL kütüphanelerin değiştirilebilmesi | LGPL-2.1 §6; LGPL-3 §4 | ✅ / ⚠️ | DLL'in bütünü LGPL; tüm kaynak ve tarif açık, kullanıcı DLL'i yeniden derleyebilir. İşlevsel yeniden derleme mümkün; bit bit aynı değil (b6, b9, b10 aynı boy, farklı özet). Y8 eksikliği bu hakkı zorlaştırıyor. |
| Y13 | Birleşik eserin (ASSMA) koşullarının değiştirmeye ve hata ayıklama amaçlı tersine mühendisliğe izin vermesi | LGPL-2.1 §6 ilk paragraf; LGPL-3 §4 | ❓ | ASSMA'nın henüz bir kullanım/lisans sözleşmesi yok. ASSMA dışarı verilmeden önce bu koşulu içeren metin gerekir. |
| Y14 | LGPL-3 "Installation Information" | LGPL-3 §4(e) → GPL-3 §6 "User Product" | ✅ (değerlendirme) | Tüketici cihazına gömülü değil, genel Windows yazılımı; madde uygulanmıyor gibi görünüyor. Hukuki teyit edilmedi. |
| Y15 | MPL dosyalarının kaynağının sunulması ve nasıl alınacağının bildirilmesi | MPL-2.0 §3.2 | ✅ | SRT ve ZeroMQ `image-library-sources.tar` içinde; subrandr ve uchardet mpv kaynak arşivinde; `SOURCES.txt` yerini söylüyor. |
| Y16 | Bileşen lisanslarının birbiriyle uyumu | LGPL-2.1 / LGPL-3 | ❓ | Bkz. B1 (libssh). |
| Y17 | Patent koşulları dağıtımı engellememeli | LGPL-2.1 §7; LGPL-3 §11–12 | ❓ | Bkz. B3. |

## 3. Düzeltilebilir eksikler (teknik, Claude yapabilir)

1. **Y8:** `tools/`, `pins.lock`, workflow ve FFmpeg-Builds `scripts.d` (+ `util/`, `images/base` yardımcıları) kaynak arşivine eklensin.
2. **Y4:** winpthreads ve mingw-w64 lisans metinleri eklensin. Kaynak: mingw-w64 deposundaki COPYING dosyaları, araç zincirinin kullandığı sürüm.
3. **Y3:** Zip'in köküne `NOTICE.md` eklensin. İçeriği:
   - DLL'in bütününün lisansı;
   - kaynakların nerede olduğu;
   - kullanıcının hakları (değiştirme, yeniden derleme);
   - bileşen listesine yönlendirme.
4. **Y5:** NOTICE araması bütün kaynak ağacında yapılsın; bulunanlar raporlansın.
5. **Y6:** FreeType cümlesi `NOTICE.md`'ye ve ASSMA'nın `THIRD_PARTY_NOTICES.md`'sine girsin.
6. **Y10 + ASSMA:** ASSMA tarafında yapılacaklar:
   - About > Licences'taki libmpv kaydı bu yayını (ad, SHA-256, kaynak yeri) göstersin.
   - Saha paketi DLL'i taşıyorsa kaynak arşivlerini de taşısın ya da yazılı teklif koysun.

## 4. Hukuki belirsizlikler (karar hukukçunun; varsayımla onay yok)

**B1 · libssh lisans karışıklığı**
- libssh'nin 25 dosyası "LGPL, **version 2.1**" diyor; "or any later version" ifadesi yok. Örnekler: `src/curve25519.c`, `src/mlkem.c`, `src/sntrup761.c`, `src/pki_context.c`.
- FFmpeg `--enable-version3` ile LGPL-3.0-or-later; aribb24'ün COPYING dosyası da LGPL-3.
- LGPL-2.1-only ile LGPL-3 kodun **aynı statik DLL'de** birleşmesinin uyumlu olup olmadığı bir hukuk sorusu.
- **Teknik çıkış yolu:** ASSMA'nın SFTP/SSH ile dosya açma ihtiyacı yok. FFmpeg libssh olmadan derlenirse soru ortadan kalkar. Ancak bu, mpv'nin resmi tarifinden sapmak demek (bkz. 5).

**B2 · ASSMA'nın kullanım koşulları (Y13)**
- LGPL-2.1 §6, birleşik eserin koşullarının değiştirmeye ve hata ayıklama amaçlı tersine mühendisliğe izin vermesini istiyor.
- ASSMA kapalı kaynak ve satılabilir bir ürün olacak; sözleşme metni bu şartla çelişmemeli.

**B3 · Patentler**
- DLL'de çok sayıda codec var: H.264, HEVC, VVC, AV1, AAC, MP3, AMR ve diğerleri. Bunlara ASSMA'nın hiç ihtiyacı olmayan kodlayıcılar (encoder) da dahil: OpenH264, Kvazaar (HEVC), VVenC, SVT-AV1, LAME, TwoLAME, opencore-amr.
- Patent lisansı LGPL'nin konusu değil. Ama LGPL-2.1 §7 / LGPL-3 §11–12'ye göre bir patent yükümlülüğü telifsiz yeniden dağıtımı engelliyorsa dağıtım yapılamaz.
- AV1 için AOMedia telifsiz patent lisansı var (`licences/image/50-aom/PATENTS`). Diğerleri için değerlendirme yapılmadı.

**B4 · Derleme ortamının kaynağa karşılığı**
- Ortamın hangi FFmpeg-Builds sürümünden üretildiği içinde yazmıyor.
- Dolaylı kanıt:
  - oluşturulma tarihi 1970 (FFmpeg-Builds tekrarlanabilir derlemeye 7 Kasım'da geçti);
  - `scripts.d` 4 Kasım'dan beri yalnızca zvbi'de değişti (zvbi bu ortamda yok);
  - ortam günlük derleniyor.
- Kütüphanelerin sürümleri `pkg-config` ile okundu ve kaydedildi; arşivdeki kaynak sürümleriyle **tek tek karşılaştırılmadı**. Bu karşılaştırma eklenebilir; belirsizliği teknik olarak daraltır ama hukuken kapatmaz.

**B5 · Dağıtıcı kim?**
- Yayın şu an kullanıcının kişisel GitHub hesabında (Tamtam8888).
- DLL ASSMA ile kurum içinde mi kullanılacak, kurum dışına mı verilecek, satılacak mı? Yükümlülüklerin kime düştüğü buna göre değişir. Kurum içi kullanım çoğu yorumda "dağıtım" sayılmaz, ama bu da hukuki bir yorum.

Ek bir not, hukuki belirsizlik değil: bu depoda (assma-libmpv-lgpl) bir LICENSE dosyası yok. Betiklerin (Y8) alıcı tarafından kullanılabilmesi için deponun bir lisansı olması iyi olur (örneğin MIT). Bu bir ürün kararı.

## 5. Tarihe sapma seçeneği (B1 ve B3 için)

mpv'nin resmi tarifi ASSMA'nın ihtiyacından çok daha geniş bir FFmpeg derliyor: kodlayıcılar, ağ protokolleri, SSH, ZeroMQ, Blu-ray. Daraltılmış bir derleme şunları kapatabilir:
- libssh ile B1'i;
- kodlayıcılarla B3'ün büyük kısmını;
- 2 `.jar` dosyasını ve birkaç MPL bileşenini.

Bedeli: "değiştirilmemiş resmi tarif" kanıtı yerine "resmi tarif + belgelenmiş değişiklik listesi" kanıtı olur, ve regresyon testleri yeniden gerekir.

## Kanıtların yeri

Hepsi yayının içinde:
- `MANIFEST.json`: `linked_libraries`, `members_in_dll`, `image_library_sources`, `cloned_sources`, `ffmpeg.configuration`.
- `INVENTORY.md`.
- `licences/`.
- Bu depo: `tools/inventory.py` (kapı mantığı), `licences.tsv` (sınıflandırma).
- Derleme günlükleri: GitHub Actions, run 43344465801.

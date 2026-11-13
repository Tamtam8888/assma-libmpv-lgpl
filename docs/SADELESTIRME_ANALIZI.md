# libmpv: libssh, kaynak paketi, encoder ve protokol sadeleştirmesi - analiz ve öneri

**Durum:** analiz ve öneri. Hiçbir derleme yapılandırması değiştirilmedi; b10 yayını olduğu gibi duruyor.
**Tarih:** 13.11.2026.
**Hazırlayan:** Claude.
**Dayandığı belgeler:** `LGPL_UYUM_DEGERLENDIRMESI.md` ve b10'un kendi dosyaları.
- `MANIFEST.json`;
- `ffmpeg/config.h` ve `ffmpeg/config_components.h` (`mpv-and-ffmpeg-sources.tar.xz` içinden);
- `image-library-sources.tar`;
- FFmpeg-Builds `c9fe5114`;
- mpv `fe753a78` `ci/build-mingw64-full.sh`.

Her bulgu iki sınıftan birinde:
- **[T]** Teknik olarak doğrulandı: dosya, satır ya da sayı gösterilebilir.
- **[H]** Hukukçu değerlendirmesi gerekir: burada hüküm verilmiyor.

---

## 1. libssh'yi kaldırmanın teknik etkisi

### 1.1 Yapılandırma zinciri [T]
1. FFmpeg-Builds imajı, her kütüphane aşamasının `ffbuild_configure` çıktısını `FF_CONFIGURE` ortam değişkenine yazar. libssh için bu `scripts.d/50-libssh.sh` → `--enable-libssh`.
2. mpv'nin tarifi FFmpeg'i bu değişkenle yapılandırır:
   ```
   ./configure … $FFBUILD_TARGET_FLAGS $FF_CONFIGURE … --disable-{librav1e,librsvg,openal}
   ```
   (`ci/build-mingw64-full.sh`, satır 36–43)
3. Sonuç: b10'un `config.h` dosyasında `CONFIG_LIBSSH 1`, `config_components.h` dosyasında `CONFIG_LIBSSH_PROTOCOL 1`.
4. mpv'nin kendisi libssh kullanmıyor: mpv `meson.build` ve tarifin meson seçeneklerinde libssh yok.

### 1.2 Bağımlılık zinciri [T]
- `libssh.pc` → `Requires.private: libssl libcrypto zlib`. libssh, şifreleme için OpenSSL'in libcrypto'sunu kullanır.
- b10 DLL'inde (bağlayıcı haritası): `ssh` 65 nesne, `crypto` 875 nesne, `ssl` 81 nesne.
- **OpenSSL libssh kaldırılınca gitmez.** curl de OpenSSL ile derlenmiş (`50-libcurl.sh`: `CURL_USE_OPENSSL=ON`), ve curl'ü iki yer kullanıyor:
  - FFmpeg'in `libcurl` protokolü;
  - mpv'nin kendi `-Dlibcurl=enabled` seçeneği (`stream/stream_curl.c`).
  libcrypto'dan alınan nesne sayısı azalabilir; kesin sayı ancak derlemeyle görülür.
- libssh'ye bağlı başka bir bileşen yok. FFmpeg-Builds'te yalnızca `50-libssh.sh` ve son aşama `zz-final.sh` onu anıyor.

### 1.3 İşlev kaybı [T]
- Kaybolan tek işlev FFmpeg'in `sftp://` protokolü (`CONFIG_LIBSSH_PROTOCOL`). Bununla SSH sunucusundaki bir dosya doğrudan açılabiliyordu.
- ASSMA bunu kullanmıyor:
  - Dosyalar yerel diskten açılıyor; ağ klasörü kuralı gereği ağdan da açılmıyor.
  - mpv'ye URL verilmiyor; `ytdl=no`.
  - ASSMA'nın mpv kodunda (`mpv_core.py`, `mpv_view.py`, `mpv_audio.py`, `mpv_native.py`) `sftp`, `http` ya da URL kullanımı yok.

### 1.4 Uygulama yolları (henüz uygulanmadı)

| Yol | Nasıl | Resmi tarif | Not |
|---|---|---|---|
| **A** (önerilen) | Workflow, tarifi çalıştırmadan önce `FF_CONFIGURE` değişkenindeki `--enable-libssh` yerine `--disable-libssh` koyar | **değişmeden kalır** (kontrol adımı sürer) | Değişen tek şey bir ortam değişkeni; MANIFEST'e "girdi değişikliği" olarak yazılır |
| B | Tarife `--disable-libssh` eklemek | değişir | Kanıt zinciri "resmi tarif + yama" olur |
| C | libssh'siz başka bir imaj | - | FFmpeg-Builds'te böyle bir varyant yok |

### 1.5 Kanıt: b10 ile karşılaştırma (her biri otomatik üretilebilir) [T]
- `config.h`: `CONFIG_LIBSSH 0`; `config_components.h`: `CONFIG_LIBSSH_PROTOCOL 0`.
- `MANIFEST.json`:
  - `ssh` bağlama satırında yok ya da 0 nesne;
  - LGPL-2.1-only dosyaların hiçbiri DLL'de değil;
  - `crypto` nesne sayısının b10'dan farkı yazılır.
- `image-library-sources.tar`: `50-libssh` artık yok.

### 1.6 Hukuki boyut
- [T] libssh kaldırılırsa, DLL'de "yalnızca LGPL-2.1" başlıklı dosya kalmaz. Değerlendirme belgesindeki B1 sorusu bu derleme için konusuz kalır.
- [H] Kalan bileşenlerin (LGPL-2.1-or-later ve LGPL-3.0-or-later) birlikte dağıtılmasının uygunluğu yine hukukçunun onayıyla kesinleşir.

---

## 2. Kaynak paketindeki eksikler ve doğrulanabilir kaynak paketi

### 2.1 b10'da olmayanlar [T]

| # | Eksik | Neden gerekli | Kanıt |
|---|---|---|---|
| K1 | FFmpeg-Builds `scripts.d` (kullanılan 71 aşama), `patches/` (aom: 1, aribb24: 3 yama), `util/` (`dl_functions.sh`, `vars.sh`), `images/base` (`git-mini-clone`, `retry-tool`, `run_stage`), `variants/` (win64-lgpl) | Kütüphaneler bu betiklerle derlenir; birçoğunda kaynak, derleme sırasında değiştirilir | DLL'e giren aşamalardan 14'ü, derleme adımında kaynağa `sed` ya da yama uyguluyor (fribidi, openssl, libudfread, vmaf, zstd, aom, aribb24, libbluray, libwebp, onevpl, soxr, twolame, zimg, libva). **Somut örnek:** aribb24'ün `configure.ac` dosyası 1.0.3 diyor, DLL'deki pkg-config sürümü 1.0.4. Fark `50-libaribb24.sh` içindeki `sed -i 's/1.0.3/1.0.4/'` ve 3 yamadan geliyor. Betikler olmadan kaynak ile ikili eşleştirilemez. |
| K2 | İki depolu aşamaların ikinci deposu | Kaynağın bir parçası arşivde yok | libiconv (+gnulib), OpenCL (+ICD Loader), Vulkan loader, libpsl, ffnvcodec: `collect_image_sources.sh` yalnızca `SCRIPT_REPO`/`SCRIPT_COMMIT`'i kaydediyor |
| K3 | Bu depo (`assma-libmpv-lgpl`) o commit'teki hâliyle: workflow, `git-pin-shim`, `pins.lock`, `inventory.py`, `licences.tsv` | Derlemeyi yöneten betikler | Herkese açık ama yayının içinde değil |
| K4 | mpv kaynak arşivinin temizliği | "Tercih edilen kaynak biçimi" ve doğrulanabilirlik | `mpv-and-ffmpeg-sources.tar.xz` içinde derleme ürünleri var: ffmpeg/ altında 2.694, libarchive 132, uchardet 55, libsixel 21, LuaJIT 11 nesne ya da kütüphane dosyası. Açılınca 709 MB. Commit'le birebir karşılaştırılamıyor. |
| K5 | cppwinrt kaynak paketinin özeti | Tarif `wget` ile sürüm etiketinden indiriyor, özet kontrolü yok | `cppwinrt-2.0.250303.1` |
| K6 | İmajdan gelen kütüphanelerin kaynağı, indirildiği hâliyle | Şu anki arşiv, FFmpeg-Builds'in indirme adımından **sonraki** hâli (bazılarında `autoreconf` çalışmış) | `50-libmp3lame` indirme adımında `autoreconf` var |
| K7 | Araç zinciri (mingw-w64 CRT, winpthreads) lisans metinleri | Bildirim (Y4) | DLL'de `mingwex` 80, `mingw32` 8, `pthread` 9 nesne |

### 2.2 Önerilen kaynak paketi
- **Biçim:** her bileşen için ayrı, saf kaynak arşivi. Git kaynaklarında `git archive <commit>` kullanılır; bu, aynı commit için her zaman aynı içeriği verir.
- **Paketin içeriği:**
  - mpv ve tarifin klonladığı her depo (`pins.lock`'taki commit'ler);
  - mujs wrap arşivi (meson'un SHA-256 doğruladığı orijinal dosya) ve cppwinrt arşivi (SHA-256 ile);
  - FFmpeg-Builds `c9fe5114`: `scripts.d`, `patches`, `util`, `images/base`, `variants`, `generate.sh`;
  - imajdaki her LGPL/MPL kütüphanenin saf kaynağı, ikinci depolar dahil. İstenirse izin veren lisanslılar da eklenebilir: boyut artar, yükümlülük değil;
  - bu deponun derleme commit'indeki `git archive` çıktısı.
- **`SOURCE-MANIFEST.json`:** her parça için
  - depo adresi;
  - commit;
  - git ağaç kimliği (tree id);
  - arşiv dosyasının SHA-256 özeti;
  - pkg-config sürümü;
  - kaynak dosyadaki sürüm metni;
  - fark varsa açıklaması ve ilgili betik satırı (aribb24 örneği gibi).
- **`verify_sources.sh` (alıcının çalıştıracağı doğrulama betiği):**
  1. Arşiv özetlerini kontrol eder.
  2. İsteğe bağlı olarak her depoyu ilgili commit'te yeniden indirip `git archive` çıktısını karşılaştırır. Bu, kaynağın gerçekten o commit olduğunu kanıtlar.
  3. Sürüm metinlerini pkg-config sürümleriyle karşılaştırır.
- **Sınır [T]:** FFmpeg-Builds sürümünün (`c9fe5114`) imajı gerçekten ürettiği yine dolaylı kanıta dayanıyor. 3. adımdaki sürüm karşılaştırması bu kanıtı güçlendirir ama doğrudan kanıt değildir.

---

## 3. NOTICE.md taslağı
Ayrı dosya: `docs/NOTICE_TASLAK.md`.
- Yaklaşık 80 bileşen satırı, b10 verisinden üretildi. Yalnızca DLL'e nesne veren bileşenler var. Her satırda:
  - bileşen ve kütüphane adları;
  - sürüm;
  - **kendi lisansı**;
  - zip içindeki lisans metni;
  - kaynağın yeri ve commit'i.
- DLL'in tamamına tek bir lisans atanmıyor.
- Ayrıca şunlar var:
  - FreeType teşekkür cümlesi;
  - GCC çalışma kütüphanesi istisnası;
  - Apache NOTICE notu;
  - patent uyarısı (yalnızca bilgi; hüküm içermiyor);
  - taslağın bilinen eksikleri (K2, K7).

---

## 4. Patent açısından gereksiz encoder ve protokoller

### 4.1 ASSMA'nın libmpv'den gerçekten kullandığı şeyler [T]
- **Çözme (decode):** yerel dosyalardaki video ve ses.
  - Konteynerler: MXF, MOV/MP4, MKV, MPEG-TS, AVI, WAV ve diğerleri.
  - Donanımla çözme: `hwdec=auto-safe` (d3d11va ve diğerleri).
- **Görüntü:** mpv'nin `vo=gpu` (ya da `libmpv` render) çıkışı. libplacebo, shaderc, SPIRV-Cross ve Vulkan bu yüzden mpv tarafında gerekli.
- **Ses filtreleri (lavfi):** `volume`, `alimiter`, `amix`, `amerge`, `asplit`, `channelsplit`, `join`, `pan`, `asetpts`, `anull`, `null` (`mpv_audio.py`). Hepsi FFmpeg'in kendi filtreleri.
- **Kapalı olanlar:** mpv altyazısı (`sub-auto=no`, `sid=no`), ekran görüntüsü (ASSMA'nın mpv kodunda `screenshot` yok), `ytdl`, mpv betikleri.
- **Ses çözücüleri:** FFmpeg'in kendi kod çözücüleri. b10'da hepsi var:
  - **Video:** h264, hevc, vvc, mpeg2video, prores, dnxhd, cfhd, ffv1, v210, jpeg2000, vp8, vp9, av1 (yalnızca donanım; yazılımla çözmeyi dav1d yapar), apv, hap.
  - **Ses:** aac, ac3, eac3, dca, truehd, s302m, dolby_e, mp2, mp3, pcm.

### 4.2 Gereksiz bileşenler ve kaldırma etkisi [T]

**a) Harici encoder kütüphaneleri.** ASSMA hiçbir şey kodlamıyor.

| Kütüphane | FFmpeg'de verdiği | Patentle ilgisi | Lisans etkisi | Kaldırınca kaybolan |
|---|---|---|---|---|
| OpenH264 | H.264 encoder (+ decoder) | H.264 | BSD | Hiç; H.264'ü FFmpeg'in kendi çözücüsü açıyor |
| Kvazaar | HEVC encoder | HEVC | BSD | Hiç |
| VVenC | VVC encoder | VVC | BSD | Hiç; VVC'yi kendi çözücüsü açıyor |
| SVT-AV1 | AV1 encoder | AV1 (AOMedia telifsiz lisansı) | BSD | Hiç |
| libaom | AV1 encoder + decoder | AV1 | BSD | Hiç; dav1d çözüyor |
| LAME | MP3 encoder | MP3 | **LGPL çıkar** | Hiç |
| TwoLAME | MP2 encoder | MP2 | **LGPL çıkar** | Hiç |
| libtheora, libvorbis, libopus, libvpx, libwebp, libjxl, OpenJPEG, liboapv, opencore-amr | Encoder (+ bazılarında decoder) | Çoğu telifsiz kodek | BSD / Apache | **libjxl:** JPEG XL resim çözme (FFmpeg'in kendi çözücüsü yok). Diğerlerinin kendi çözücüsü var: vp8, vp9, opus, vorbis, theora, amrnb, amrwb, webp, jpeg2000, apv. |

**b) FFmpeg'in kendi ve donanım encoder'ları.** b10'da 229 encoder açık. Bunların 34'ü donanım encoder'ı (NVENC, AMF, QSV, Media Foundation, VAAPI, Vulkan, D3D12): h264_*, hevc_*, av1_*, aac_mf ve diğerleri. Patentli kodekler ayrıca yazılımla da kodlanabiliyor (aac, ac3, eac3, mpeg2video, mpeg4).
- **Öneri:** `--disable-encoders`. İstenirse yalnızca patent açısından nötr `png` ve `mjpeg` açık bırakılır; bunlar mpv ekran görüntüsü içindir ve ASSMA şu an kullanmıyor.
- **Kaybolan:** mpv'nin kodlama modu (`--o`) ve ekran görüntüsü. ASSMA ikisini de kullanmıyor.

**c) Ağ protokolleri ve ağ kütüphaneleri.** Açık olanlar:
- http/https/tls;
- rtmp*, rtp, srtp, udp, tcp, ftp, gopher, icecast, mms, prompeg, ipfs;
- libcurl, librist, libsrt, libssh, libzmq.

Öneriler:
- `--disable-network` ya da `--disable-protocols` ile yalnızca şunları bırakmak: `file`, `pipe`, `fd`, `data`, `subfile`, `cache`, `async`, `concat`, `concatf`.
- `--disable-lib{curl,rist,srt,ssh,zmq} --disable-gmp`. GMP yalnızca RTMPE şifrelemesi için.
- **Lisans etkisi:** SRT ve ZeroMQ (MPL) ile libssh ve GMP (LGPL) çıkar.

**d) ASSMA'nın kullanmadığı diğer FFmpeg özellikleri.**

| Kütüphane | İşlev | Lisans | Not |
|---|---|---|---|
| GME, libopenmpt | Oyun müziği ve tracker dosyası çözme | LGPL / BSD | - |
| Chromaprint | Ses parmak izi muxer'ı | LGPL | - |
| aribb24, libaribcaption | Japon ARIB yayın altyazısı | LGPL / MIT | ASSMA mpv altyazısını kullanmıyor |
| soxr | Alternatif yeniden örnekleyici | LGPL | mpv varsayılan olarak swresample kullanıyor |
| VMAF | Kalite ölçüm filtresi | BSD | - |
| lilv/serd/sord/sratom/zix | LV2 eklenti filtresi | ISC | - |
| ZeroMQ | Uzaktan filtre kontrolü | MPL | - |
| LCEVCdec, uavs3d | LCEVC katmanı, AVS3 çözme | BSD | Yayıncılıkta nadir; kalsın / çıksın kararı |

**Korunması gerekenler:**
- `libxml2`: IMF ve DASH için. IMF yayın arşivinde gerçekten karşılaşılabilecek bir biçim.
- `zimg`, `libplacebo`, `lcms2`.
- `fontconfig`, `freetype`, `harfbuzz`, `fribidi`, `libass`: mpv'nin OSD'si için. ASSMA mpv OSD'sini kullanmıyor, ama bunlar mpv'nin zorunlu bağımlılıkları.
- Donanımla çözme API'leri.
- `snappy`: HAP çözücüsü için.

### 4.3 Sınır: tarifi değiştirmeden ne yapılabilir? [T]

| Profil | Ne değişir | Tarif | DLL'den çıkan copyleft bileşenler |
|---|---|---|---|
| **S1** | yalnızca libssh (`FF_CONFIGURE`) | değişmez | libssh |
| **S2** | FFmpeg tarafı: a + b + c + d (`FF_CONFIGURE` + ek `--disable-…`) | değişmez | libssh, LAME, TwoLAME, GME, Chromaprint, aribb24, soxr, GMP (LGPL) + SRT, ZeroMQ (MPL) |
| **S3** | S2 + mpv tarafı: `-Dlibcurl`, `-Dlibbluray`, `-Dsdl2-*`, `-Dvapoursynth`, `-Djavascript`, `-Dlua` kapalı | **değişir** | + libbluray, libudfread (LGPL); curl, OpenSSL, nghttp*, SDL çıkar |

- **S2'den sonra DLL'de kalan copyleft bileşenler:** FFmpeg, libiconv, FriBidi, libplacebo, libbluray, libudfread (LGPL); subrandr, uchardet (MPL).
- **S2'de bile curl ve OpenSSL kalır.** Tarif mpv'yi `-Dlibcurl=enabled` ile derliyor. libbluray da `-Dlibbluray=enabled` yüzünden kalır.

### 4.4 Hukuki boyut
- [T] S2'de gereksiz encoder'ların, donanım encoder'larının ve ağ protokollerinin kodu DLL'de olmaz. Bu, bağlayıcı haritası ve `config_components.h` ile gösterilebilir.
- [H] **Kod çözücüler kalmak zorunda:** H.264, HEVC, VVC, AAC, AC-3, E-AC-3, DTS, TrueHD, Dolby E ve diğerleri. Patent sorusunun asıl ağırlığı burada olabilir. Hangi patentin geçerli olduğu, Windows'un ya da GPU sürücüsünün lisanslı çözücüsünün durumu ne kadar değiştirdiği ve kurum içi kullanımla satışın farkı hukuki konular.
- Sadeleştirme patent riskini **azaltır**, ortadan kaldırdığı **söylenemez**.

---

## 5. Karşılaştırmalı kanıt ve regresyon test planı

### 5.1 Her derlemede otomatik üretilecek karşılaştırma (b10 → yeni) [T]
1. **`COMPARE.md`:**
   - FFmpeg yapılandırma satırı farkı;
   - `config.h` ve `config_components.h` farkı: açılan/kapanan encoder, decoder, protokol, demuxer ve filtre listeleri;
   - bağlanan kütüphanelerin ve `members_in_dll` sayılarının farkı;
   - DLL'den çıkan copyleft bileşenler;
   - DLL boyutu.
2. **Değişmemesi gerekenlerin kontrolü** (fark çıkarsa derleme kırmızı olur):
   - 4.1'deki çözücü listesi;
   - ASSMA'nın kullandığı ses filtreleri;
   - donanımla çözme API'leri (d3d11va, dxva2, nvdec, vulkan, qsv);
   - mpv'nin istemci API sürümü (`include/mpv/client.h`, `MPV_CLIENT_API_VERSION`).

### 5.2 Otomatik çözme testi (CI, Wine altında, yeni)
- **Test dosyaları:** GitHub runner'ında Ubuntu'nun ffmpeg'iyle her derlemede yeniden üretilir; dağıtılmaz. Her biri kısa:
  - H.264, HEVC, MPEG-2, ProRes, DNxHD, VP9, AV1, VVC;
  - AAC, AC-3, E-AC-3, MP2, MP3, PCM 24 bit;
  - MXF, MOV, MP4, MKV, TS, WAV konteynerleri.
- **Test:** her dosya hem b10'un hem yeni derlemenin `mpv.com --no-config --vo=null --ao=null` komutuyla oynatılır. Karşılaştırılanlar:
  - çıkış kodu;
  - seçilen çözücü (`-v` günlüğü);
  - çözülen kare ve örnek sayısı.
- **ASSMA'nın ses filtresi testi:** ASSMA'nın `lavfi-complex` ve `af` dizgilerinin (`mpv_audio.py` üretir) birebir aynısı, sesli bir test dosyası üzerinde çalıştırılır.
- **Sınır:** Wine gerçek Windows değildir; donanımla çözme ve GPU çıkışı orada test edilemez.

### 5.3 ASSMA saha testi (senin, Windows'ta)
Toplu test listesindeki 59. madde genişletilir ve her yeni DLL için uygulanır:
1. Oynat/duraklat ve 2 dk kesintisiz oynatma. Performance Log'da düşen kare 0, `hwdec-current` d3d11va.
2. Seek: timeline'a tıklama, cue'ya çift tık, Home/End.
3. Ok tuşlarını basılı tutma ve J/K/L hızları.
4. Ayrı pencere ve tam ekran viewer, oynarken.
5. A+B(+C) şerit sesi, offset, L/R/Mute; Lane audio sync ölçümünün b10 ile aynı olması.
6. Oynarken Bypass aç/kapa.
7. Close Video / Open Video, 5 kez üst üste.
8. Kurumda en sık kullanılan biçimlerden birer dosya: MXF (XDCAM, AVC-Intra), ProRes MOV, MP4 H.264, TS (yayın kaydı), WAV 24 bit. Her biri açılıyor mu, sesi geliyor mu?
9. Help > Third-Party Licences: mpv satırı yeni derlemeyi gösteriyor mu?

### 5.4 Değişiklik bazında beklenen kanıt

| Değişiklik | Beklenen otomatik kanıt | Ek test |
|---|---|---|
| S1 (libssh) | `CONFIG_LIBSSH 0`; `ssh` DLL'de yok; 5.2'de tüm çözme sonuçları b10 ile aynı | 5.3'ün 1. ve 8. maddeleri |
| S2 (FFmpeg sadeleştirme) | Encoder sayısı 229 → 0 (ya da 2); ağ protokolleri yok; 10 copyleft bileşen çıkmış; çözücü, filtre ve donanım API listeleri değişmemiş | 5.3'ün tamamı |
| S3 (mpv tarafı) | `MANIFEST.json` `mpv_build_options` farkı; curl, OpenSSL, libbluray ve SDL DLL'de yok | 5.3'ün tamamı + tarif değişikliğinin yaması `MANIFEST.json`'a yazılır |
| Kaynak paketi (K1–K7) | `verify_sources.sh` temiz geçer; sürüm uyuşmazlıklarının hepsi açıklamalı | - |

---

## 6. Önerilen sıra ve karar gerektirenler

**Öneri:**
1. Önce kaynak paketi (K1–K7) ve NOTICE.md. Bunlar DLL'i değiştirmez; b10'un kendisi için de üretilebilir. b10'un dosyalarına dokunulmaz; ek bir "b10 kaynak paketi" yayını yapılır.
2. Sonra **S2**: tarif değişmeden en büyük kazanç; 10 copyleft bileşen çıkar.
3. **S3** ayrı bir karar: resmi tarif kanıtından vazgeçmeyi gerektirir.

**Onay bekleyen kararlar:**
- [Ürün] S1 mi, S2 mi, S3 mü?
- [Ürün] LCEVC, AVS3 ve JPEG XL çıksın mı?
- [Ürün] Bu depo için bir lisans (ör. MIT).
- [H] Bkz. `LGPL_UYUM_DEGERLENDIRMESI.md` B1–B5. S1/S2 seçilirse B1 bu derleme için konusuz kalır; B2–B5 aynen duruyor.

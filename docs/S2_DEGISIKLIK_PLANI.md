# S2: FFmpeg tarafını sadeleştirme - değişiklik planı ve regresyon kontrolleri

**Durum (21.11.2026): uygulandı.** Yayın `libmpv-lgpl-v0.42.0-dev-gfe753a782-fe753a782-x64-s2-b16` (ilk yeşil koşu);
uygulama notları ve sonuçlar §9'da. Plan metni aşağıda olduğu gibi duruyor.
**Referans:** b10 (`libmpv-lgpl-v0.42.0-dev-gfe753a782-fe753a782-x64-b10`), değişmeden korunuyor.
**Kararlar (13.11):**
- S2 seçildi.
- Çözücüler (decoder), ASSMA'nın ses filtreleri ve donanımla çözme korunacak.
- mpv'nin tarifi değişmeyecek.
- LCEVC, AVS3 ve JPEG XL korunacak.

Her öğe iki sınıftan birinde:
- **[T]** Derlemede ya da b10 verisinde otomatik doğrulanır.
- **[H]** Hukukçu değerlendirmesi gerekir; bu plan hüküm vermez.

## 1. Değişikliğin yeri: tarif değil, tarifin girdisi
- mpv'nin tarifi FFmpeg'i `./configure … $FF_CONFIGURE … --disable-{librav1e,librsvg,openal}` ile yapılandırıyor.
- `FF_CONFIGURE` değişkeni derleme ortamı imajından geliyor.
- Workflow, tarifi çalıştırmadan hemen önce bu değişkeni `tools/ff_profile.py` ile dönüştürecek:
  - kaldırılacak bileşenlerin `--enable-X` seçenekleri silinir;
  - sonuna `--disable-X` seçenekleri eklenir.
  FFmpeg'de sonra gelen seçenek önce geleni geçersiz kılar; çift güvence budur.
- Tarifin değişmediği kontrolü (`git diff ci/`) aynen sürer.
- MANIFEST'e yazılacaklar:
  - imajın orijinal `FF_CONFIGURE` değeri;
  - S2 değeri;
  - aradaki fark;
  - profil adı ve `ff_profile.py`'nin SHA-256 özeti.

## 2. Çıkarılacaklar

| Grup | `configure` seçeneği | DLL'den çıkan | Lisans etkisi | Neden güvenli |
|---|---|---|---|---|
| Bütün encoder'lar (yazılım + donanım) | `--disable-encoders` | b10'da 229 encoder; 34'ü donanım (NVENC, AMF, QSV, MF, VAAPI, Vulkan, D3D12) | - | ASSMA hiçbir şey kodlamıyor. mpv'nin kodlama modu (`--o`) ve ekran görüntüsü kullanılmıyor (`mpv_*.py`). |
| Yalnızca encoder olan kütüphaneler | `--disable-lib{mp3lame,twolame,kvazaar,vvenc,svtav1,openh264,theora,webp,openjpeg,oapv}` | 10 kütüphane | LAME, TwoLAME (LGPL) çıkar | Bunların FFmpeg'de çözücüsü yok, ya da FFmpeg'in kendi çözücüsü kullanılıyor (h264, theora, webp, jpeg2000, apv) [T] |
| Kendi çözücüsü olan çift işlevli kütüphaneler | `--disable-lib{aom,opencore-amrnb,opencore-amrwb}` | libaom, opencore-amr | - | AV1'i dav1d, AMR'yi FFmpeg'in `amrnb`/`amrwb` çözücüleri çözüyor [T] |
| Ağ | `--disable-network --disable-lib{curl,ssh,srt,rist,zmq} --disable-gmp --disable-schannel` | Bütün ağ protokolleri | libssh, GMP (LGPL); SRT, ZeroMQ (MPL) çıkar | ASSMA yerel dosya açıyor; ağ klasörü kuralı var; `ytdl=no` |
| Kullanılmayan özellikler | `--disable-lib{gme,openmpt,soxr,vmaf,aribb24,aribcaption} --disable-chromaprint --disable-lv2` | Oyun/tracker müziği, ses parmak izi, soxr, VMAF, ARIB altyazı, LV2 eklentileri | GME, Chromaprint, aribb24, soxr (LGPL) çıkar | ASSMA'nın mpv yolunda hiçbiri kullanılmıyor; mpv altyazısı kapalı (`sid=no`) |

**Korunanlar** [T]:
- **Çözme ve resim:** dav1d, libjxl, LCEVCdec, uavs3d, libvpx, libopus, libvorbis (+ogg), snappy (HAP için).
- **Görüntü ve renk:** libplacebo, zimg, lcms2.
- **Metin ve OSD:** libass, fontconfig, freetype, harfbuzz, fribidi.
- **Biçimler ve dosya:** libxml2 (IMF/DASH), libbluray, iconv, zlib, lzma.
- **Donanım:** Vulkan, OpenCL, AMF, ffnvcodec/CUDA, libvpl, D3D11VA, D3D12VA, DXVA2, VAAPI(win32).
- **Diğer:** SDL2, VapourSynth.

**mpv tarafında değişmeyecek olanlar** (tarif değişmiyor): mpv curl'ü (+OpenSSL, nghttp*), libbluray'i (+libudfread) ve SDL2'yi kendisi bağlıyor. Bunlar DLL'de kalır.

**Beklenen sonuç:**
- DLL'den çıkan copyleft bileşenler, toplam 10:
  - LGPL: libssh, LAME, TwoLAME, GME, Chromaprint, aribb24, soxr, GMP;
  - MPL: SRT, ZeroMQ.
- Kalan copyleft bileşenler:
  - LGPL: FFmpeg, libiconv, FriBidi, libplacebo, libbluray, libudfread;
  - MPL: subrandr, uchardet.

## 3. Otomatik kontroller (yeni derlemede; biri kırmızıysa yayın çıkmaz)

**K-S1 · Korunması gerekenler.** `config_components.h` b10 ile karşılaştırılır.
- **Çözücüler:** b10'daki bütün çözücüler kalmalı. Yalnızca şu harici kütüphane çözücülerinin gitmesi beklenir:
  - `libaom_av1`, `libopenh264`, `libopencore_amrnb`, `libopencore_amrwb`;
  - `libaribb24`, `libaribcaption`.
  
  Bunların her birinin FFmpeg'de kendi karşılığı ya da kullanılmama gerekçesi var: `av1` (dav1d), `h264`, `amrnb`, `amrwb`; ARIB için `sid=no`.
- **Filtreler:** ASSMA'nın kullandıkları kalmalı: `volume`, `alimiter`, `amix`, `amerge`, `asplit`, `channelsplit`, `join`, `pan`, `asetpts`, `anull`, `null`. Ayrıca lavfi'nin kendiliğinden eklediği `aresample`, `aformat`, `format`, `scale`.
- **Donanımla çözme:** b10'daki bütün hwaccel'ler kalmalı (`*_d3d11va`, `*_d3d11va2`, `*_d3d12va`, `*_dxva2`, `*_nvdec`, `*_vulkan`, `*_vaapi`).
- **Demuxer'lar:** b10'dakilerden yalnızca ağa özgü olanlar (rtsp, sdp, …) ve kaldırılan kütüphanelerinkiler (`libgme`, `libopenmpt`) gidebilir. `mxf`, `mov`, `matroska`, `mpegts`, `imf`, `wav`, `w64`, `avi`, `gxf`, `lxf`, `mpegps` kalmalı.

**K-S2 · Çıkması gerekenler.**
- Encoder sayısı 0 olmalı.
- `file` dışında ağ protokolü kalmamalı.
- Bağlayıcı haritasında 10 bileşenden 0 nesne alınmış olmalı.

**K-S3 · Lisans kapısı.** Mevcut kapı aynen çalışır: GPL, nonfree ya da bilinmeyen lisanslı nesne 0.

**K-S4 · `COMPARE.md`.** b10 ile yeni derleme arasındaki farklar:
- yapılandırma satırı;
- bileşen listeleri;
- bağlanan kütüphaneler ve nesne sayıları;
- DLL boyutu;
- mpv istemci API sürümü (değişmemeli).

**K-S5 · Kaynak paketi.** Yeni derleme için de `source-package` iş akışı çalışır, kontrollerin hepsi geçmeli.

## 4. Otomatik çözme testi (CI, Wine; b10 ve yeni derleme aynı dosyalarla)
- **Test dosyaları:** runner'da Ubuntu'nun ffmpeg'iyle her seferinde yeniden üretilir, yayına girmez. Her biri 3 saniyelik:
  - H.264 (High), HEVC (Main10), MPEG-2 (XDCAM benzeri, MXF), ProRes 422 (MOV), DNxHD (MXF), VP9 ve AV1 (MKV), VVC (çıkarılabiliyorsa);
  - AAC, AC-3, E-AC-3, MP2, MP3, PCM 24 bit (WAV ve MXF), 8 kanal PCM;
  - MPEG-TS içinde H.264 + AC-3.
- **Komut:**
  ```
  mpv.com --no-config --vo=null --ao=null --untimed --frames=… -v
  ```
- **Karşılaştırma:** çıkış kodu, seçilen çözücü adı, çözülen kare ve örnek sayısı.
- **Ses filtresi testi:** ASSMA'nın `mpv_audio.py` ile ürettiği `af` ve `lavfi-complex` dizgileri, 8 kanallı test dosyasında aynen çalıştırılır. İki derlemenin çıkış sesinin özeti karşılaştırılır (`--ao=pcm`).
- **Beklenen:** bütün satırlar b10 ile aynı. Tek fark beklenen yer AV1: b10'da da dav1d seçildiğinden fark çıkmamalı.
- **Sınır [T]:** Wine gerçek Windows değil; donanımla çözme, GPU çıkışı ve zamanlama orada test edilemez. Bunlar saha testinde.

## 5. Saha testi (Windows'ta; b10 ile yan yana)
Toplu test listesinin 59. maddesi bu derleme için şöyle genişler. Her adım önce b10, sonra yeni DLL ile yapılır.
1. 2 dk kesintisiz oynatma. Performance Log'da düşen kare 0 ve `hwdec-current` aynı.
2. Seek, ok tuşlarını basılı tutma, J/K/L.
3. Ayrı pencere ve tam ekran viewer.
4. A+B+C şerit sesi, offset, L/R/Mute; Lane audio sync değeri b10 ile aynı (±1 ms).
5. Oynarken Bypass aç/kapa; Close/Open Video 5 kez.
6. Kurumun gerçek biçimleri: XDCAM MXF, AVC-Intra MXF, ProRes MOV, H.264 MP4, TS kaydı, 24 bit WAV. Görüntü, ses ve süre b10 ile aynı mı?
7. Help > Third-Party Licences: yeni derleme görünüyor mu?

## 6. Uygulama sırası (onaydan sonra)
1. `tools/ff_profile.py`, workflow girdisi `profile` (varsayılan `none`, yani b10 ile aynı), `inventory.py`'ye K-S1…K-S4.
2. Önce **profilsiz** bir deneme derlemesi. K-S4'ün b10'a karşı "fark yok" demesi gerekir. Bu, karşılaştırma aracının kendisini doğrular.
3. S2 derlemesi, çözme testi, kaynak paketi.
4. Sonuçlar sana; saha testi; onaylanırsa ASSMA'nın saha paketi yeni DLL'e geçer.

## 7. Hukuki boyut (hüküm yok)
- [T] S2'den sonra DLL'de "yalnızca LGPL-2.1" başlıklı dosya kalmaz (libssh çıkar). Encoder ve ağ protokolü kodu da kalmaz.
- [H] Çözücüler kalıyor: H.264, HEVC, VVC, AAC, AC-3, E-AC-3, DTS, TrueHD, Dolby E ve diğerleri. Bunların patent durumu bu planın kapsamı dışında. Sadeleştirme patent riskini azaltır, ortadan kaldırdığı söylenemez.
- [H] Kalan LGPL-2.1-or-later ve LGPL-3.0-or-later bileşenlerin birlikte dağıtılması, ASSMA'nın kullanım koşulları (LGPL-2.1 §6) ve dağıtıcının kim olduğu: `LGPL_UYUM_DEGERLENDIRMESI.md` B2–B5 aynen duruyor.

## 8. Not (19.11.2026, C# dönemi — K210, K238)
- §2'deki "mpv altyazısı kapalı (`sid=no`)" gerekçesi C#'ta değişti: K210 gereği görünen track'ler tek bir ASS olarak
  mpv'ye verilir, yani mpv'nin altyazı çizicisi (libass) **kullanılıyor**. Sonuç değişmez: libass, fontconfig, FreeType,
  HarfBuzz, FriBidi zaten korunanlar listesinde; çıkarılan ARIB (aribb24 / aribcaption) ASSMA'da kullanılmıyor.
- C#'ın ses grafiği (K238): `amerge`, `asplit`, `pan`, `volume`, `amix`, `join` — hepsi K-S1'de korunanlar listesinde.
  §4'teki ses filtresi testine Python'un `mpv_audio.py` dizgileriyle birlikte K238 grafiği de eklenir
  (assma reposu `prototype/K205_Bench/Bench/Runner.cs`, `AudioGraph`).
- K205 prototipi `screenshot-raw` kullanıyor: ham piksel döndürür, kodlayıcı (encoder) gerektirmez → S2 ile çalışır.
  Dosyaya ekran görüntüsü (PNG / JPEG) ise S2'den sonra mpv ile alınamaz; gerekirse ASSMA kendisi yazar.

## 9. Uygulama (21.11.2026)

**Araçlar** (hepsi bu depoda, `README.md` özetliyor):
- `tools/ff_profile.py`: §1'deki dönüşüm. `s2` profilinin tanımı, korunması gerekenlerin listesi (`KEEP`; profil
  bunlardan birine dokunursa araç çalışmaz) ve beklenen kayıp listeleri (çözücü, filtre, demuxer) bu dosyada.
- `tools/ff_components.py`: K-S1 / K-S2. §6 adım 2'deki "profilsiz deneme derlemesi" yerine her derlemede yapılan daha
  güçlü bir denetim: FFmpeg aynı commit'in temiz bir kopyasından, imajın orijinal `FF_CONFIGURE`'u ile **yalnız
  yapılandırılır** (derlenmez) ve bu yapılandırma satırının b10'unkiyle harfi harfine aynı olması şarttır. Böylece
  karşılaştırma her seferinde b10'un FFmpeg yapılandırmasına karşı yapılır.
- Ayrıca profilsiz tam derleme de bir kez yapıldı (koşu 12, `profile=none`): denetleyici kendini denetledi; 11 bileşen
  listesinin hepsinde "derleme = taban" çıktı ve taban satırı b10 ile aynıydı. Çözme testinde b10 ile 23 / 23 aynı.
- `tools/inventory.py`: K-S2 bağlayıcı düzeyi (10 bileşenden alınan nesne sayısı).
- `tools/decode_probe.c` + `tools/decode_test.py` + `tools/make_test_media.sh`: §4. mpv.com yerine küçük bir C programı
  kullanıldı, çünkü b10'un mpv.com'u yayında yok; program DLL'i ASSMA gibi çalışırken yüklüyor, yani aynı program
  iki DLL'le çalışabiliyorsa DLL'in değiştirilebildiği (LGPL) de gösterilmiş oluyor.
- `tools/compare_builds.py`: K-S4 `COMPARE.md`.

**Planda olmayan ama çıkan iki durum:**
1. **b10'un araç zinciri imajı silinmiş.** FFmpeg-Builds eski imajları günler içinde siliyor. b11 koşusu imajı
   bulamadığı için başlamadı. Çözüm, kalıcı: imaj kendi kayıt defterimize **aynı özetle** kopyalanıyor
   (`mirror-toolchain.yml`; `ghcr.io/tamtam8888/assma-libmpv-toolchain`) ve derlemeler yalnız bu kopyadan yapılıyor.
   b10'un imajı geri getirilemez. Bu yüzden b10 aynı ortamda yeniden derlenemez; kaynakları (b10-sources) tam.
   Yeni imaj: FFmpeg-Builds `7f2a6b10` (18.11; `c9fe5114`'ten sonra kütüphane sürümleri güncellenmiş).
   FFmpeg, mpv ve tarifin klonladıkları `pins.lock` ile aynı kaldı. İmaj değişikliğinin etkisi ayrıca ölçüldü: koşu 12
   (yeni imaj, profilsiz) b10 ile aynı yapılandırma satırını ve aynı çözme sonuçlarını verdi.
2. **İlk koşuda beklenti listelerim eksikti; denetim bunu yakaladı** (koşu 13, kırmızı):
   - kaldırılan kütüphanelerin filtreleri gitti: `azmq`, `zmq` (ZeroMQ), `libvmaf`, `lv2`;
   - iki yerel protokol listemde yoktu: `bluray` (yerel disk / klasör), `windows_handle` (açık dosya tanıtıcısı).

   Hepsi gerekçesiyle listelere eklendi. ASSMA'nın filtreleri ayrı bir zorunlu listeyle denetleniyor; hepsi yerinde.
   Çözme testinde de iki test hatası çıktı: bir filtre dizgisinin yazımı yanlıştı (b10'da da çalışmıyordu), ve
   `estimated-frame-number` aynı b10 ile iki koşuda 75 ve 76 verdi (bir tahmin, sayaç değil) → ±1 tolerans. Ses
   örneklerinin özeti, çözücü adları ve ses biçimi birebir aynı olmak zorunda.

**Sonuç (koşu 15 ve 16; ayrıntı yayındaki `PROFILE-CHECKS.md`, `COMPARE.md`, `DECODE-TEST.md`):**
- Çözücüler: 536 / 542. Gidenler yalnız beklenen 6 dış kütüphane çözücüsü: `libaom_av1`, `libopenh264`,
  `libopencore_amrnb`, `libopencore_amrwb`, `libaribb24`, `libaribcaption`.
- Filtreler: 530 / 534 (giden 4'ü yukarıda). Donanım çözücüleri 70 / 70.
- Demuxer'lar: 363 / 369. Gidenler `rtp`, `rtsp`, `sap`, `sdp`, `libgme`, `libopenmpt`.
- Kodlayıcılar: 229 → 0. Protokoller: 47 → 16, hepsi yerel.
- 10 copyleft bileşenden DLL'e giren nesne: 0.
- DLL'de kalan copyleft bileşenler:
  - LGPL: FFmpeg (7 kütüphane), libiconv, FriBidi, libplacebo, libbluray, libudfread;
  - MPL: subrandr, uchardet.
- DLL: 129,5 MB → 86,3 MB. mpv istemci API'si 2.6, değişmedi.
- Çözme testi: 24 durumun hepsi b10 ile aynı. Bunlar 21 dosya ve 3 ses grafiği; ASSMA'nın K238 grafiği (amerge 8+2 →
  20 volume@ → amix) dahil, ses örneklerinin SHA-256'sı birebir.
- K-S5: `…-s2-b16-sources` yayınlandı (REPORT: 102 kontrol geçti, 0 hata, 9 not).
- ASSMA'nın Windows CI'ı (gerçek Windows, s2-b16 DLL): 105 / 105 test geçti. mpv testlerinin hepsi koştu: seek, kare adımı,
  basılı tutma, cue'ya atlama ve altyazı görünürlüğü SE ile birebir, önizleme, osd.
- Kalan: §5 saha testi (kullanıcı; ASSMA 0.0.4, b10'lu 0.0.3 ile yan yana).

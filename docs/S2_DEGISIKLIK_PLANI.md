# S2: FFmpeg tarafını sadeleştirme - değişiklik planı ve regresyon kontrolleri

**Durum:** plan; onay bekliyor. Bu plan uygulanmadı, yeni DLL derlenmedi.
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

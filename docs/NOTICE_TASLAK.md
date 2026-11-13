# NOTICE.md - TASLAK (b10 verisiyle; yayına henüz konmadı)

> Bu dosya, ileride zip'in köküne konacak `NOTICE.md`'nin taslağıdır. Tablo `MANIFEST.json`'dan (b10) üretildi:
> yalnızca **DLL'e gerçekten nesne veren** bileşenler (bağlayıcı haritası) listelenir. DLL'in tamamına tek bir lisans
> atanmaz; her bileşen kendi lisansıyla gösterilir. Köşeli parantezli yerler sonraki derlemede doldurulacak.

---

# libmpv-2.dll - üçüncü taraf bileşenler ve lisansları

Bu paket, mpv'nin (https://mpv.io) LGPL yapılandırmasıyla (`-Dgpl=false`) derlenmiş bir libmpv kitaplığıdır.
`libmpv-2.dll`, aşağıdaki bileşenlerden statik olarak bağlanmış nesneler içerir. Her bileşen **kendi lisansına**
tabidir; lisans metinleri `licences/` klasöründe, bileşenin kaynağındaki dosya adlarıyla durur.

## Haklarınız
- `libmpv-2.dll`'i değiştirilmiş ya da başka bir derlemeyle değiştirebilirsiniz. Bu DLL'i kullanan programlar onu
  ayrı bir dosya olarak, çalışırken yükler.
- Bu derlemenin tam kaynağı ve derleme betikleri bu yayınla birlikte verilir: `[kaynak paketi adı]`. İçeriği ve
  doğrulama yöntemi: `SOURCES.txt` ve `SOURCE-MANIFEST.json`.
- LGPL ve MPL bileşenlerin kaynağı, bu yayın yayımda kaldığı sürece aynı sayfadan indirilebilir.
  [Yayın kaldırılırsa sunulacak alternatif erişim / yazılı teklif: hukuki karar bekliyor.]

## Bileşenler (DLL'in içinde olanlar)

Sıra: LGPL, MPL, izin veren (permissive) lisanslar, derleyici çalışma kütüphaneleri.

| Bileşen | Sürüm | Lisans | Zip içindeki lisans metni | Kaynak ve sürüm kimliği |
|---|---|---|---|---|
| aribb24 (aribb24) | 1.0.4 | LGPL-3.0-or-later | licences/image/50-libaribb24/ | image-library-sources › https://github.com/nkoriyama/aribb24.git · 5e9be272f96e |
| Chromaprint (chromaprint) | 1.6.2 | LGPL-2.1-or-later | licences/image/50-chromaprint/ | image-library-sources › https://github.com/acoustid/chromaprint.git · 3b38c100022b |
| FFmpeg (avcodec, avdevice, avfilter, avformat, avutil, swresample, swscale) | 63.28.100 | LGPL-3.0-or-later (FFmpeg, --enable-version3) | licences/recipe/ffmpeg/ | mpv-and-ffmpeg-sources › ffmpeg/ · commit 4b0fad0c61a9 |
| Game Music Emu (gme) | 0.6.6 | LGPL-2.1-or-later | licences/image/50-gme/ | image-library-sources › https://github.com/libgme/game-music-emu.git · f68963b1de06 |
| GMP (gmp) | 6.3.0 | LGPL-3.0-or-later OR GPL-2.0-or-later | licences/image/25-gmp/ | image-library-sources › https://github.com/BtbN/gmplib.git · 5c3e9a9d52b6 |
| GNU FriBidi (fribidi) | 1.0.17 | LGPL-2.1-or-later | licences/image/25-fribidi/ | image-library-sources › https://github.com/fribidi/fribidi.git · d2f3e1f4946e |
| GNU libiconv (iconv) | — | LGPL-2.1-or-later | licences/image/20-libiconv/ | image-library-sources › https://git.savannah.gnu.org/git/libiconv.git · b5a1735e02bf |
| LAME (mp3lame) | — | LGPL-2.0-or-later | licences/image/50-libmp3lame/ | image-library-sources › https://svn.code.sf.net/p/lame/svn/trunk/lame · 7113 |
| libbluray (bluray) | 1.5.1 | LGPL-2.1-or-later | licences/image/50-libbluray/ | image-library-sources › https://code.videolan.org/videolan/libbluray.git · f33a738fd7bb |
| libplacebo (placebo) | 7.387.0 | LGPL-2.1-or-later | licences/image/50-libplacebo/ | image-library-sources › https://code.videolan.org/videolan/libplacebo.git · 275f7dea2792 |
| libssh (ssh) | 0.12.0 | LGPL-2.1-only | licences/image/50-libssh/ | image-library-sources › https://gitlab.com/libssh/libssh-mirror.git · 9de02f3d01ba |
| libudfread (udfread) | 1.2.0 | LGPL-2.1-or-later | licences/image/45-libudfread/ | image-library-sources › https://code.videolan.org/videolan/libudfread.git · b0bc6957e7e0 |
| SoX Resampler (soxr) | 0.1.3 | LGPL-2.1-or-later | licences/image/50-soxr/ | image-library-sources › https://git.code.sf.net/p/soxr/code · 945b592b7047 |
| TwoLAME (twolame) | — | LGPL-2.1-or-later | licences/image/50-twolame/ | image-library-sources › https://github.com/njh/twolame.git · 6fced852d4d5 |
| SRT (srt) | 1.5.7 | MPL-2.0 | licences/image/50-srt/ | image-library-sources › https://github.com/Haivision/srt.git · 9f2390232a82 |
| subrandr (subrandr) | 1.4.0 | MPL-2.0 | licences/recipe/subrandr/ | mpv-and-ffmpeg-sources › subrandr/ · commit c5474ada85b1 |
| uchardet (uchardet) | — | MPL-1.1 OR GPL-2.0-or-later OR LGPL-2.1-or-later | licences/recipe/uchardet/ | mpv-and-ffmpeg-sources › uchardet/ · commit ae6302a01608 |
| ZeroMQ (zmq) | 4.3.6 | MPL-2.0 | licences/image/50-libzmq/ | image-library-sources › https://github.com/zeromq/libzmq.git · 46493370217a |
| Brotli (brotlicommon, brotlidec, brotlienc) | 1.2.0 | MIT | licences/image/45-brotli/ | https://github.com/google/brotli.git · 2e2bcf17ae71 |
| curl (curl) | 8.23.1-DEV | curl (MIT style) | licences/image/50-libcurl_50-libcurl/ | https://github.com/curl/curl.git · bc677a8f16a5 |
| dav1d (dav1d) | 1.5.4 | BSD-2-Clause | licences/image/50-dav1d/ | https://code.videolan.org/videolan/dav1d.git · b8b2d726b4b7 |
| Fontconfig (fontconfig) | 2.18.3 | HPND-like (MIT style) | licences/image/45-fonts_35-fontconfig/ | https://gitlab.freedesktop.org/fontconfig/fontconfig.git · b25ffeabd15b |
| FreeType (freetype) | — | FTL OR GPL-2.0-or-later | licences/image/45-fonts_50-freetype/ | https://gitlab.freedesktop.org/freetype/freetype.git · 4ba7c3d82ab8 |
| HarfBuzz (harfbuzz) | 15.0.0 | MIT | licences/image/45-fonts_45-harfbuzz/ | https://github.com/harfbuzz/harfbuzz.git · 75d8ac5d2313 |
| Highway (libjxl submodule) (hwy) | 1.2.0 | Apache-2.0 OR BSD-3-Clause | licences/image/50-libjxl_50-libjxl/ | https://github.com/libjxl/libjxl.git · e47d2a2b5bb4 |
| Khronos OpenCL ICD loader (OpenCL) | — | Apache-2.0 | licences/image/45-opencl/ | https://github.com/KhronosGroup/OpenCL-Headers.git · 82f60316cc14 |
| Kvazaar (kvazaar) | 2.3.2 | BSD-3-Clause | licences/image/50-kvazaar/ | https://github.com/ultravideo/kvazaar.git · 1f11f9ae33ef |
| LCEVCdec (lcevc_dec_api, lcevc_dec_common, lcevc_dec_enhancement, lcevc_dec_pipeline, lcevc_dec_pipeline_cpu, lcevc_dec_pixel_processing) | 4.3.0 | BSD-3-Clause-Clear | licences/image/50-lcevcdec/ | https://github.com/v-novaltd/LCEVCdec.git · 741fb7c869cf |
| libaom (aom) | — | BSD-2-Clause + AOMedia patent licence | licences/image/50-aom/ | https://aomedia.googlesource.com/aom · 9ace39e02a34 |
| libarchive (archive) | 3.9.0 | BSD-2-Clause | licences/recipe/libarchive/ | mpv-and-ffmpeg-sources › libarchive/ · commit 4a5944b726d2 |
| libaribcaption (aribcaption) | 1.1.2 | MIT | licences/image/50-libaribcaption/ | https://github.com/xqq/libaribcaption.git · 37dde0f32652 |
| libass (ass) | 0.17.5 | ISC | licences/image/50-libass/ | https://github.com/libass/libass.git · f61db567e659 |
| libjxl (jxl, jxl_cms, jxl_threads) | 0.13.0 | BSD-3-Clause | licences/image/50-libjxl_50-libjxl/ | https://github.com/libjxl/libjxl.git · e47d2a2b5bb4 |
| libopenmpt (openmpt) | 0.9.0-pre.13+r25817 | BSD-3-Clause | licences/image/50-openmpt/ | https://github.com/OpenMPT/openmpt.git · 3ee3c8000b45 |
| libpng (png18) | 1.8.0.git | libpng-2.0 | licences/image/25-libpng/ | https://github.com/glennrp/libpng.git · 0b0876829d77 |
| libpsl (psl) | 0.23.3 | MIT | licences/image/50-libcurl_40-libpsl/ | https://github.com/rockdaboot/libpsl.git · 620d51d13351 |
| librist (rist) | 0.2.20 | BSD-2-Clause | licences/image/50-librist_50-librist/ | https://code.videolan.org/rist/librist.git · 47ad5513d1aa |
| libsamplerate (samplerate) | — | BSD-2-Clause | licences/image/45-libsamplerate/ | https://github.com/libsndfile/libsamplerate.git · 0844c208f683 |
| libsixel (sixel) | 1.8.7-r2 | MIT | licences/recipe/libsixel/ | mpv-and-ffmpeg-sources › libsixel/ · commit 3c9fd6a294b2 |
| libunibreak (unibreak) | 8.0 | Zlib | licences/image/45-libunibreak/ | https://github.com/adah1972/libunibreak.git · f8172fe771ef |
| libva (va, va_win32) | 1.25.0 | MIT | licences/image/50-vaapi_50-libva/ | https://github.com/intel/libva.git · f052e984e0c8 |
| libvpx (vpx) | 1.17.0 | BSD-3-Clause | licences/image/50-libvpx/ | https://chromium.googlesource.com/webm/libvpx · 900b2a52b69e |
| libwebp (sharpyuv, webp, webpmux) | 1.6.0 | BSD-3-Clause | licences/image/50-libwebp/ | https://chromium.googlesource.com/webm/libwebp · 1844042d1ca7 |
| libxml2 (xml2) | — | MIT | licences/image/25-libxml2/ | https://github.com/GNOME/libxml2.git · c79c9612fcc7 |
| lilv (lilv-0) | 0.28.1 | ISC | licences/image/50-lilv_99-lilv/ | https://github.com/lv2/lilv.git · 4b8f30055fa5 |
| Little CMS (lcms2) | 2.20 | MIT | licences/image/45-lcms2/ | https://github.com/mm2/Little-CMS.git · 1112313b3784 |
| LuaJIT (luajit-5.1) | — | MIT | licences/recipe/LuaJIT/ | mpv-and-ffmpeg-sources › LuaJIT/ · commit 63c8f1a9b479 |
| MuJS (mujs) | — | ISC | licences/recipe/mujs-1.3.8/ | mpv-and-ffmpeg-sources › subprojects/mujs-1.3.8 (meson wrap, SHA-256 doğrulamalı) |
| Netflix VMAF (vmaf) | 3.2.0 | BSD-2-Clause-Patent | licences/image/45-vmaf/ | https://github.com/Netflix/vmaf.git · f712fa7564fe |
| nghttp2 (nghttp2) | 1.70.90 | MIT | licences/image/50-libcurl_40-nghttp2/ | https://github.com/nghttp2/nghttp2.git · 3baf9561e09f |
| nghttp3 (nghttp3) | 1.18.90 | MIT | licences/image/50-libcurl_40-nghttp3/ | https://github.com/ngtcp2/nghttp3.git · ac11a456eb9d |
| ngtcp2 (ngtcp2, ngtcp2_crypto_ossl) | 1.25.90 | MIT | licences/image/50-libcurl_40-ngtcp2/ | https://github.com/ngtcp2/ngtcp2.git · 20da63db12a3 |
| oneVPL / libvpl (vpl) | 2.17 | MIT | licences/image/50-onevpl/ | https://github.com/intel/libvpl.git · 674d015bcb29 |
| OpenAPV (oapv) | — | BSD-3-Clause | licences/image/50-openapv/ | https://github.com/AcademySoftwareFoundation/openapv.git · b4ff69856b4c |
| opencore-amr (opencore-amrnb, opencore-amrwb) | 0.1.6 | Apache-2.0 | licences/image/50-opencore-amr/ | https://git.code.sf.net/p/opencore-amr/code · 7dba8c322384 |
| OpenH264 (source build, no Cisco binary) (openh264) | 2.7.0 | BSD-2-Clause | licences/image/50-openh264/ | https://github.com/cisco/openh264.git · 1bca62311e44 |
| OpenJPEG (openjp2) | 2.5.4 | BSD-2-Clause | licences/image/50-openjpeg/ | https://github.com/uclouvain/openjpeg.git · 8314119b067c |
| OpenSSL 3 (crypto, ssl) | 3.6.5 | Apache-2.0 | licences/image/25-openssl/ | https://github.com/openssl/openssl.git · openssl-3.6. |
| Opus (opus) | unknown | BSD-3-Clause | licences/image/50-libopus/ | https://github.com/xiph/opus.git · a8b2545eec71 |
| SDL 2 (SDL2) | — | Zlib | licences/image/50-sdl/ | https://github.com/libsdl-org/SDL.git · 8acf7cfc0f88 |
| serd (serd-0) | 0.32.11 | ISC | licences/image/50-lilv_96-serd/ | https://github.com/drobilla/serd.git · b621b0bc790d |
| shaderc (shaderc_combined) | — | Apache-2.0 (glslang parts BSD-3 / MIT; generated parser GPL-3 with Bison exception) | licences/image/47-vulkan_50-shaderc/ | https://github.com/google/shaderc.git · 2737994b5521 |
| Snappy (snappy) | — | BSD-3-Clause | licences/image/50-snappy/ | https://github.com/google/snappy.git · 946606459314 |
| sord (sord-0) | 0.16.22 | ISC | licences/image/50-lilv_97-sord/ | https://github.com/drobilla/sord.git · 4b5232bb91e7 |
| SPIRV-Cross (spirv-cross-c, spirv-cross-core, spirv-cross-glsl, spirv-cross-hlsl, spirv-cross-msl, spirv-cross-reflect) | — | Apache-2.0 | licences/image/47-vulkan_55-spirv-cross/ | https://github.com/KhronosGroup/SPIRV-Cross.git · 300681bbcb83 |
| SVT-AV1 (SvtAv1Enc) | — | BSD-3-Clause-Clear + AOMedia patent licence | licences/image/50-svtav1/ | https://github.com/AOMediaCodec/SVT-AV1.git · ad11d76a6c9c |
| uavs3d (uavs3d) | 1.2.89 | BSD-3-Clause | licences/image/50-uavs3d/ | https://github.com/uavs3/uavs3d.git · 0e20d2c29185 |
| Vulkan loader (vulkan-1) | — | Apache-2.0 | licences/image/47-vulkan_45-vulkan-loader/ | https://github.com/BtbN/Vulkan-Shim-Loader.git · 65b3936528cd |
| VVenC (vvenc) | 1.15.0-dev | BSD-3-Clause-Clear | licences/image/50-vvenc/ | https://github.com/fraunhoferhhi/vvenc.git · 0e7508b811bb |
| Xiph libogg (ogg) | 1.3.6 | BSD-3-Clause | licences/image/25-libogg/ | https://github.com/xiph/ogg.git · 06a5e0262cdc |
| Xiph libvorbis (vorbis, vorbisenc, vorbisfile) | — | BSD-3-Clause | licences/image/45-libvorbis/ | https://github.com/xiph/vorbis.git · 1b75110b5a27 |
| Xiph Theora (theoraenc) | — | BSD-3-Clause | licences/image/50-libtheora/ | https://github.com/xiph/theora.git · 28fd5ec77f0a |
| XZ Utils (lzma) | 5.8.4 | 0BSD | licences/image/25-xz/ | https://github.com/tukaani-project/xz.git · 299eb5c3f597 |
| zimg (zimg) | 3.0.6 | WTFPL | licences/image/50-zimg/ | https://github.com/sekrit-twc/zimg.git · 67e0603271c0 |
| zix (zix-0) | 0.8.3 | ISC | licences/image/50-lilv_96-zix/ | https://github.com/drobilla/zix.git · 17d632393f5a |
| zlib (z) | — | Zlib | licences/image/20-zlib/ | https://github.com/madler/zlib.git · 9d314c341b2c |
| Zstandard (zstd) | 1.6.0 | BSD-3-Clause OR GPL-2.0-only | licences/image/45-zstd/ | https://github.com/facebook/zstd.git · 49cf51799ea0 |
| GCC libgomp (OpenMP runtime) (gomp) | — | GPL-3.0-or-later WITH GCC-exception-3.1 | gerekmez (GCC Runtime Library Exception) | araç zinciri (derleme ortamı imajı) |
| GCC runtime library (gcc, stdc++) | — | GPL-3.0-or-later WITH GCC-exception-3.1 | gerekmez (GCC Runtime Library Exception) | araç zinciri (derleme ortamı imajı) |
| mingw-w64 winpthreads (pthread) | — | MIT AND BSD-3-Clause | — (eklenecek) | araç zinciri (derleme ortamı imajı) |
| mingw-w64 C çalışma kütüphanesi (mingw32, mingwex) | [araç zinciri sürümü] | mingw-w64 lisansları (büyük kısmı kamu malı, ZPL-2.1 ve MIT/BSD tarzı dosyalar) | [eklenecek: licences/toolchain/mingw-w64/] | araç zinciri (derleme ortamı imajı) |
| Windows sistem kitaplıkları (kernel32, user32, …: yalnızca içe aktarma kayıtları) | — | mingw-w64 içe aktarma kitaplıkları | — | Windows'un kendi DLL'leri; pakette değil |

## Özel bildirimler
- **FreeType:** Portions of this software are copyright © [yıl] The FreeType Project (www.freetype.org).
  All rights reserved. (FTL §3 gereği)
- **GCC çalışma kütüphaneleri** (libgcc, libstdc++, libgomp): GPL-3.0 + GCC Runtime Library Exception 3.1.
  İstisna, bu nesnelerin GCC ile derlenmiş bir programa katılmasına lisans koşulu getirmez.
- **Apache-2.0 bileşenleri:** NOTICE dosyaları `licences/` içinde, ait oldukları bileşenin klasöründedir
  [tam tarama sonucu eklenecek].
- **Patentler:** Bu bileşenlerin bir kısmı patentli teknolojileri (ör. video ve ses kodekleri) uygular. Telif
  lisansları patent hakkı vermez. AV1 bileşenleri (libaom, SVT-AV1, dav1d) AOMedia'nın telifsiz patent lisansıyla
  gelir (`licences/image/50-aom/PATENTS`). Diğerleri için bu paket hiçbir patent beyanı yapmaz.

## Bağlama satırında olup DLL'e girmeyenler (bilgi)
`lcms2_fast_float`, `lcms2_threaded` (GPL-3.0): bağlayıcı bunlardan hiçbir nesne almadı (`MANIFEST.json`,
`members_in_dll` = 0).

## Bu tablonun bilinen eksikleri (taslak notu, yayında olmayacak)
- İki depolu derleme aşamalarında yalnızca ilk depo kaydedildi: libiconv (+gnulib), OpenCL (+ICD Loader),
  Vulkan loader, libpsl, ffnvcodec. OpenCL satırındaki "OpenCL-Headers" bu yüzden eksik.
- "Sürüm" sütunu pkg-config'ten gelir; bazı bileşenler sürüm yazmaz (—). Kaynak kimliği her zaman commit'tir.
- winpthreads ve mingw-w64 metinleri derleme ortamından ya da mingw-w64 deposundan (aynı sürüm) eklenecek.

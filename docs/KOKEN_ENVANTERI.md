# Depo dosyalarının köken ve lisans envanteri (MIT öncesi)

**Tarih:** 13.11.2026.
**Amaç:** MIT lisansı yalnızca bize ait dosyalara uygulansın; üçüncü taraf içerik varsa kendi lisansıyla kalsın.

**Yöntem:**
- Depodaki her dosya (`git ls-files`) tek tek incelendi.
- Commit geçmişine bakıldı: 17 commit; 1'i kullanıcının GitHub'da açtığı ilk README, 16'sı Claude'un bu oturumlarda yazdığı.
- Dosyaların içinde başka bir projeden kopyalanmış kod ya da metin arandı.

| Dosya | Köken | Üçüncü taraf içerik | MIT kapsamı |
|---|---|---|---|
| `.github/workflows/build-libmpv-lgpl.yml` | Bu depoda yazıldı | Yok. mpv'nin betiğini **çağırır**, içine kopyalamaz. GitHub Actions'ı commit SHA'sıyla **anar**, kodlarını içermez. | Evet |
| `.github/workflows/image-info.yml` | Bu depoda yazıldı | Yok | Evet |
| `.github/workflows/source-package.yml` | Bu depoda yazıldı | Yok | Evet |
| `tools/git-pin-shim` | Bu depoda yazıldı | Yok | Evet |
| `tools/inventory.py` | Bu depoda yazıldı | Yok | Evet |
| `tools/collect_image_sources.sh` | Bu depoda yazıldı | Yok. FFmpeg-Builds'in `git-mini-clone` ve `retry-tool` betiklerini **çalışırken** onların deposundan kopyalar. Bu dosyalar depoda tutulmuyor. | Evet |
| `tools/make_source_package.py`, `tools/make_notice.py`, `tools/verify_sources.py` | Bu depoda yazıldı | Yok. FFmpeg-Builds yardımcılarını çalışırken kullanır, depoda tutmaz. | Evet |
| `licences.tsv` | Bu depoda yazıldı | Yalnızca olgular: kütüphane adları, SPDX lisans adları, proje adları. Lisans metni yok. | Evet (tablo düzeni) |
| `pins.lock` | Bu depoda yazıldı | Yalnızca olgular: depo adresleri ve commit kimlikleri | Evet |
| `README.md` | İlk satır kullanıcının (GitHub'ın ilk commit'i), gerisi bu depoda yazıldı | Yok | Evet |
| `docs/LGPL_UYUM_DEGERLENDIRMESI.md`, `docs/SADELESTIRME_ANALIZI.md`, `docs/KOKEN_ENVANTERI.md` | Bu depoda yazıldı | Lisans maddelerine **atıf** (madde numaraları); metin kopyası yok | Evet |
| `docs/NOTICE_TASLAK.md` | Bu depoda yazıldı | FreeType'ın zorunlu teşekkür cümlesi (FTL §3'ün istediği metin) | Evet, bu cümle hariç: o, FreeType lisansının istediği bir bildirim olarak kalır |
| `tools/__pycache__/inventory.cpython-313.pyc` | Yanlışlıkla eklenmiş derleme çıktısı | - | Depodan çıkarıldı; `.gitignore` eklendi |

**Sonuç [T]:** Depoda üçüncü taraf kaynak kodu ya da lisans metni yok. Tek istisna, NOTICE taslağındaki FreeType cümlesi; o da bir bildirim olarak kendi lisansına bağlı kalır.

Derlemenin kullandığı ve depoda **olmayan** üçüncü taraf parçalar kendi lisanslarıyla kalır; MIT onları kapsamaz:
- mpv, FFmpeg, FFmpeg-Builds betikleri;
- GitHub Actions;
- derleme ortamı imajı ve kütüphaneler.

## MIT'den önce gereken karar
- **[Ürün kararı] Telif sahibi satırına kim yazılacak?** (`Copyright (c) 2026 …`) Seçenekler:
  - senin adın;
  - kurum;
  - "ASSMA contributors" gibi bir ad.
- **[H] Kodu Claude yazdı, sen yönettin.** Yapay zekâ ile üretilen kodun telif durumu birçok ülkede henüz netleşmemiş bir hukuk konusu.
- **[H] İş ilişkisi.** ASSMA çalışmasının işvereninle ilişkisi (iş sözleşmesi, kurum kaynakları), telif sahibini etkileyebilir.

MIT bu belirsizliklerle çelişmez: kimin sahibi olduğu sorusunu çözmez, yalnızca sahibin verdiği izni tanımlar.

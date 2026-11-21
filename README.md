# assma-libmpv-lgpl

An LGPL build of **libmpv** (Windows x64) for ASSMA, with its sources, how it was made and its licence terms
documented. This repository contains no ASSMA code.

## How it is made
- **Recipe:** mpv's own official CI script `ci/build-mingw64-full.sh` (job `mingw64-full`, variant `lgpl`).
  The script is not edited; the workflow checks this (`git diff` of `ci/` against the mpv commit).
- **Toolchain:** the FFmpeg-Builds container image `win64-lgpl`, pinned by digest, used from **our own copy**
  (`ghcr.io/tamtam8888/assma-libmpv-toolchain`, same digest; workflow *Mirror toolchain image*). FFmpeg-Builds deletes
  its old images within days; the copy is kept for good, so every build can be repeated in the same environment.
- **FFmpeg profile** (input `profile`, default `s2`; `docs/S2_DEGISIKLIK_PLANI.md`): the recipe is still not edited.
  `tools/ff_profile.py` turns its input `FF_CONFIGURE` (a variable of the image) into the profile's value: no encoders,
  no network, no encoder-only or unused external libraries. Decoders, ASSMA's audio filters and hardware decoding stay.

## Everything is fixed to an exact version
| What | Where it is fixed |
|---|---|
| mpv | workflow input `mpv_ref` (commit) |
| toolchain image and the ~70 libraries inside it | input `image` (digest) and `ffbuilds_ref` (the FFmpeg-Builds revision whose `scripts.d` fixes each library to a commit) |
| FFmpeg, LuaJIT, libsixel, libarchive, subrandr, windows-rs (cloned by the recipe) | `pins.lock`, applied by `tools/git-pin-shim` (lets the recipe clone, then checks out the listed commit) |
| uchardet, cppwinrt | tag / version in the recipe; commit recorded in the manifest |
| mujs (meson wrap) | wrap file with SHA-256 of the source archive, recorded in the manifest |
| GitHub Actions | commit SHA (the version tag is in a comment) |

## Licence: proven from what is inside the DLL
`tools/inventory.py` reads the link line of `libmpv-2.dll` (meson's `build.ninja`) and checks every library on it
against `licences.tsv`. A GPL, nonfree or unknown library stops the release. Libraries that are only present in the
image (for example FFTW, used by the GPL-only rubberband) are listed but do not matter unless linked.
The Rust crates inside subrandr are checked from `cargo metadata` the same way.
The build also still checks the switches: mpv `gpl=false`, FFmpeg `CONFIG_GPL 0` and `CONFIG_NONFREE 0`.

## Checks of a profiled build (any red check stops the release)
- `tools/ff_components.py` (K-S1, K-S2): FFmpeg is configured once more from a clean worktree of the same commit with
  the image's `FF_CONFIGURE` (configure only). That configure line must equal the reference release's (b10) character
  for character. Then: every decoder, filter, hwaccel and demuxer of the reference stays, except listed external-library
  ones, each with its reason; 0 encoders; only local protocols. With profile `none` the build must equal the baseline in
  every list (the checker checks itself). Result: `PROFILE-CHECKS.md`, `PROFILE.json`.
- `tools/inventory.py` (K-S2, link level): the linker took 0 objects from each copyleft component the profile removes.
- `tools/decode_test.py` (Wine): one small program (`tools/decode_probe.c`, loads `libmpv-2.dll` at run time like
  ASSMA) decodes the same freshly made test files with the reference DLL and the new DLL: chosen decoders, frame count,
  audio format and the SHA-256 of the decoded samples (also through ASSMA's audio graph K238) must be identical.
  `DECODE-TEST.md`. Workflow *Decode compare* runs the same test between any two releases.
- `tools/compare_builds.py` (K-S4): `COMPARE.md` - configure line, component counts, linked libraries and object
  counts, DLL size, mpv client API (must not change), copyleft components (a profile may only remove).

## A release contains
- `libmpv-…zip`: `libmpv-2.dll`, import library, headers, `LICENSE.LGPL`,
  `MANIFEST.json` (SHA-256 of every file; mpv, FFmpeg, image, FFmpeg-Builds and workflow identity; every cloned
  source with its commit; FFmpeg's configure line; mpv's build options; meson dependencies with versions; every
  linked library with origin, version and licence; Rust crates; gate result),
  `INVENTORY.md` (the same for people), `BUILDINFO.txt`, `SOURCES.txt`, `IMAGE-SOURCES.tsv`,
  `licences/` (licence texts of every component), and for a profiled build `PROFILE-CHECKS.md`, `PROFILE.json`,
  `DECODE-TEST.md`, `DECODE-TEST.json`, `COMPARE.md`.
- `mpv-and-ffmpeg-sources.tar.xz`: mpv, FFmpeg and every library the recipe cloned, at the built commits.
- `image-library-sources.tar`: the sources of every LGPL / MPL library that came from the image.
- `SHA256SUMS.txt`.

Run: Actions → *Build LGPL libmpv* → *Run workflow*. `Image information` prints what the toolchain image says
about itself (environment, layer history, creation time).

Complete, verifiable sources of a release: workflow *Source package for a build* publishes `<release>-sources`
(every part fetched again at the recorded commits, the scripts that controlled the build, `NOTICE.md`,
`SOURCE-MANIFEST.json`, `verify_sources.py`, `REPORT.md`). A build is ready for ASSMA only when its `-sources`
release exists.

## Moving to newer versions
1. New toolchain image: run *Mirror toolchain image* (source tag or digest + the FFmpeg-Builds revision), then use the
   printed pin as the `image` input / default. Never build from an image that is not in our copy.
2. Change `mpv_ref`, `ffbuilds_ref` or a line of `pins.lock` as needed, run the workflow, read the gate in
   `INVENTORY.md` and the profile checks, run *Source package for a build*, then test the DLL in ASSMA before it
   replaces the one in use.

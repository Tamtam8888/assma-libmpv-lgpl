# assma-libmpv-lgpl

An LGPL build of **libmpv** (Windows x64) for ASSMA, with its sources, how it was made and its licence terms
documented. This repository contains no ASSMA code.

## How it is made
- **Recipe:** mpv's own official CI script `ci/build-mingw64-full.sh` (job `mingw64-full`, variant `lgpl`).
  The script is not edited; the workflow checks this (`git diff` of `ci/` against the mpv commit).
- **Toolchain:** the FFmpeg-Builds container image `win64-lgpl`, pinned by digest.

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

## A release contains
- `libmpv-…zip`: `libmpv-2.dll`, import library, headers, `LICENSE.LGPL`,
  `MANIFEST.json` (SHA-256 of every file; mpv, FFmpeg, image, FFmpeg-Builds and workflow identity; every cloned
  source with its commit; FFmpeg's configure line; mpv's build options; meson dependencies with versions; every
  linked library with origin, version and licence; Rust crates; gate result),
  `INVENTORY.md` (the same for people), `BUILDINFO.txt`, `SOURCES.txt`, `IMAGE-SOURCES.tsv`,
  `licences/` (licence texts of every component).
- `mpv-and-ffmpeg-sources.tar.xz`: mpv, FFmpeg and every library the recipe cloned, at the built commits.
- `image-library-sources.tar`: the sources of every LGPL / MPL library that came from the image.
- `SHA256SUMS.txt`.

Run: Actions → *Build LGPL libmpv* → *Run workflow*. `Image information` prints what the toolchain image says
about itself (environment, layer history, creation time).

## Moving to newer versions
Change `mpv_ref`, the image digest / `ffbuilds_ref` or a line of `pins.lock`, run the workflow, read the gate in
`INVENTORY.md`, then test the DLL in ASSMA before it replaces the one in use.

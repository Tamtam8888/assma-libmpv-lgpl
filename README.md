# assma-libmpv-lgpl

An LGPL build of **libmpv** (Windows x64) for ASSMA.

- **Recipe:** mpv's own official CI script `ci/build-mingw64-full.sh` (job `mingw64-full`, variant `lgpl`), unchanged.
- **Toolchain:** the FFmpeg-Builds container image `win64-lgpl`.
- **Checked:** the build fails unless mpv's `gpl` option is `false` and FFmpeg is neither GPL nor nonfree.
- **Result:** a release with `libmpv-2.dll`, `LICENSE.LGPL`, `BUILDINFO.txt` (exact commits, toolchain, Actions run),
  `SOURCES.txt` and the source archive.

Run: Actions → *Build LGPL libmpv* → *Run workflow*.

This repository contains no ASSMA code.

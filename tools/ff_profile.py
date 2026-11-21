#!/usr/bin/env python3
"""FFmpeg configure profile for the LGPL libmpv build (docs/S2_DEGISIKLIK_PLANI.md).

mpv's recipe (ci/build-mingw64-full.sh) is NOT edited. It configures FFmpeg with `$FF_CONFIGURE`, a variable of the
FFmpeg-Builds toolchain image. This tool turns the image's value into the value of a profile, and the workflow
exports the result before it runs the recipe:

    FF_CONFIGURE="$(python3 tools/ff_profile.py s2 --from="$FF_CONFIGURE")"

How a profile works (two safeguards, both needed):
1. every `--enable-X` of a removed component is deleted from the image's value;
2. `--disable-X` is appended for each of them. In FFmpeg's configure the later option wins, so even an `--enable-X`
   that this tool did not see (for example one added by the recipe itself) is switched off again.

`--report FILE` writes what was changed (image value, profile value, removed / added options, the profile's own
definition and this file's SHA-256) as JSON; inventory.py copies it into MANIFEST.json.

Profiles:
- none: the image's value unchanged (= b10).
- s2:   no encoders, no network, no encoder-only / unused external libraries. Decoders, ASSMA's audio filters and
        hardware decoding stay. Why each group goes: S2_DEGISIKLIK_PLANI.md §2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path

# group -> configure options to switch off. Order is kept in the output so the configure line is readable.
S2 = {
    'encoders (ASSMA encodes nothing; screenshot-raw needs no encoder)': [
        '--disable-encoders',
    ],
    'encoder-only libraries (FFmpeg decodes these formats itself)': [
        '--disable-libmp3lame', '--disable-libtwolame', '--disable-libkvazaar', '--disable-libvvenc',
        '--disable-libsvtav1', '--disable-libopenh264', '--disable-libtheora', '--disable-libwebp',
        '--disable-libopenjpeg', '--disable-liboapv',
    ],
    'dual-use libraries whose formats FFmpeg decodes itself (AV1: dav1d; AMR: amrnb / amrwb)': [
        '--disable-libaom', '--disable-libopencore-amrnb', '--disable-libopencore-amrwb',
    ],
    'network (ASSMA opens local files only)': [
        '--disable-network', '--disable-libcurl', '--disable-libssh', '--disable-libsrt', '--disable-librist',
        '--disable-libzmq', '--disable-gmp', '--disable-schannel',
    ],
    'features ASSMA does not use': [
        '--disable-libgme', '--disable-libopenmpt', '--disable-libsoxr', '--disable-libvmaf',
        '--disable-libaribb24', '--disable-libaribcaption', '--disable-chromaprint', '--disable-lv2',
    ],
}

PROFILES = {'none': {}, 's2': S2}

# K-S2 (link level): the copyleft components the profile removes. inventory.py stops the release if the linker took
# even one object from any of them (stems as on the link line: -lssh -> ssh).
MUST_NOT_LINK = {
    'none': [],
    's2': ['ssh', 'mp3lame', 'twolame', 'gme', 'chromaprint', 'aribb24', 'soxr', 'gmp', 'srt', 'zmq'],
}

# K-S1: external-library decoders that may disappear, each with the reason it does not matter.
EXPECTED_GONE_DECODERS = {
    'none': {},
    's2': {
        'libaom_av1': 'AV1 is decoded by dav1d (libdav1d) / FFmpeg av1',
        'libopenh264': 'H.264 is decoded by FFmpeg h264',
        'libopencore_amrnb': 'FFmpeg amrnb',
        'libopencore_amrwb': 'FFmpeg amrwb',
        'libaribb24': 'ARIB captions are not used by ASSMA (subtitles come from ASSMA itself, K210)',
        'libaribcaption': 'ARIB captions are not used by ASSMA (K210)',
        'libgme': 'game music, not a broadcast format',
        'libopenmpt': 'tracker music, not a broadcast format',
    },
}

# K-S1: filters that may disappear: only the filters of removed libraries (ZeroMQ control, VMAF metric, LV2 plugin
# host). ASSMA's filters are checked separately (ff_components.py REQUIRED_FILTERS).
EXPECTED_GONE_FILTERS = {
    'none': set(),
    's2': {'azmq', 'zmq', 'libvmaf', 'lv2'},
}

# K-S1: demuxers that may disappear (network-only, or of a removed library).
EXPECTED_GONE_DEMUXERS = {
    'none': set(),
    's2': {'rtp', 'rtsp', 'sap', 'sdp', 'libgme', 'libopenmpt'},
}

# Components that must NOT be switched off by any profile (S2 plan §2, "Korunanlar"). A profile that touches one of
# them is a mistake in this file; the tool refuses to run.
KEEP = {
    'libdav1d', 'libjxl', 'liblcevc-dec', 'libuavs3d', 'libvpx', 'libopus', 'libvorbis', 'libsnappy',
    'libplacebo', 'libzimg', 'lcms2', 'libass', 'fontconfig', 'libfreetype', 'libharfbuzz', 'libfribidi',
    'libxml2', 'libbluray', 'iconv', 'zlib', 'lzma', 'vulkan', 'opencl', 'amf', 'ffnvcodec', 'cuda-llvm', 'libvpl',
    'd3d11va', 'd3d12va', 'dxva2', 'vaapi', 'sdl2', 'vapoursynth', 'decoders', 'filters', 'demuxers', 'hwaccels',
}


def name_of(option: str) -> str:
    for prefix in ('--enable-', '--disable-'):
        if option.startswith(prefix):
            return option[len(prefix):].split('=', 1)[0]
    return ''


def apply(profile: str, image_value: str) -> dict:
    groups = PROFILES[profile]
    disables = [o for opts in groups.values() for o in opts]
    names = {name_of(o) for o in disables}
    clash = sorted(names & KEEP)
    if clash:
        raise SystemExit(f'ff_profile: profile {profile} would switch off protected components: {clash}')
    tokens = shlex.split(image_value)
    kept, removed = [], []
    for tok in tokens:
        if tok.startswith('--enable-') and name_of(tok) in names:
            removed.append(tok)
        else:
            kept.append(tok)
    # 'none' must give the image's value byte for byte (b10 equivalence); others are rebuilt from tokens
    value = image_value if not groups else ' '.join(shlex.quote(t) for t in kept + disables)
    return {
        'profile': profile,
        'image_value': image_value,
        'value': value,
        'removed_options': removed,
        'added_options': disables,
        'groups': groups,
        'must_not_link': MUST_NOT_LINK[profile],
        'expected_gone_decoders': EXPECTED_GONE_DECODERS[profile],
        'expected_gone_demuxers': sorted(EXPECTED_GONE_DEMUXERS[profile]),
        'expected_gone_filters': sorted(EXPECTED_GONE_FILTERS[profile]),
        'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('profile', choices=sorted(PROFILES))
    ap.add_argument('--from', dest='image_value', required=True, help="the image's FF_CONFIGURE")
    ap.add_argument('--report', help='write the change as JSON to this file')
    args = ap.parse_args()
    result = apply(args.profile, args.image_value)
    if args.report:
        Path(args.report).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['value'])
    return 0


if __name__ == '__main__':
    sys.exit(main())

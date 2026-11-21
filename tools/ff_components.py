#!/usr/bin/env python3
"""Checks K-S1 / K-S2 of a profiled FFmpeg (docs/S2_DEGISIKLIK_PLANI.md §3), run in the build container after the
recipe, from the mpv source folder:

    python3 tools/ff_components.py --ffmpeg ffmpeg --report /tmp/ff_profile.json \
        --reference-manifest ref/MANIFEST.json --out artifact-libmpv

What it does:
1. Reads the components of the FFmpeg that was really built (ffmpeg/config_components.h).
2. Makes the BASELINE: FFmpeg configured once more, out of tree, from a clean worktree of the same commit, with the
   build's own configure line in which the profile's FF_CONFIGURE is put back to the image's value. Only configure
   runs (about two minutes), nothing is compiled. This is "the same build without the profile".
3. Proves the baseline is real: its configure line must be identical, character for character, to the configure
   line recorded in the reference release (b10's MANIFEST.json). So the baseline is b10's FFmpeg configuration, and
   the comparison below is "new build vs b10" for every component list.
4. Compares and decides:
   K-S1 (must stay): every baseline decoder except the expected external-library ones (each with a reason); ASSMA's
        filters; every hwaccel; every demuxer except network-only ones and those of removed libraries.
   K-S2 (must go, profile s2): 0 encoders; only local protocols (no tcp / udp / tls / http / ... at all).
   Profile none: the build must equal the baseline in every list (this checks the checker).
Writes PROFILE.json and PROFILE-CHECKS.md into --out; exit status 1 if a check failed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

KINDS = ['DECODER', 'ENCODER', 'HWACCEL', 'PARSER', 'BSF', 'DEMUXER', 'MUXER', 'PROTOCOL', 'FILTER', 'INDEV',
         'OUTDEV']

# ASSMA's audio graph (K238, Python mpv_audio.py) and what lavfi inserts on its own.
REQUIRED_FILTERS = ['volume', 'alimiter', 'amix', 'amerge', 'asplit', 'channelsplit', 'join', 'pan', 'asetpts',
                    'anull', 'null', 'aresample', 'aformat', 'format', 'scale']
REQUIRED_DEMUXERS = ['mxf', 'mov', 'matroska', 'mpegts', 'imf', 'wav', 'w64', 'avi', 'gxf', 'lxf', 'mpegps', 'mp3',
                     'aac', 'ac3', 'eac3', 'flac', 'ogg', 'image2', 'concat', 'hls', 'dash', 'srt', 'webvtt', 'ass']
# Protocols that cannot reach a network by themselves. prompeg is an output-only FEC protocol that opens "udp://"
# through FFmpeg's URL layer; without the udp protocol it cannot send anything (it is in b10 too).
LOCAL_PROTOCOLS = {'async', 'cache', 'concat', 'concatf', 'crypto', 'data', 'fd', 'file', 'md5', 'pipe', 'prompeg',
                   'shared', 'subfile', 'tee', 'android_content'}
NETWORK_PROTOCOLS = {'tcp', 'udp', 'udplite', 'unix', 'tls', 'http', 'https', 'httpproxy', 'ftp', 'gopher', 'gophers',
                     'hls', 'icecast', 'mmsh', 'mmst', 'rtmp', 'rtmps', 'rtmpe', 'rtmpt', 'rtmpte', 'rtmpts', 'rtp',
                     'srtp', 'sctp', 'ipfs_gateway', 'ipns_gateway', 'librtmp', 'libsmbclient', 'libssh', 'libsrt',
                     'librist', 'libzmq', 'dtls', 'whip', 'ffrtmpcrypt', 'ffrtmphttp'}


def components(config_components_h: Path) -> dict:
    text = config_components_h.read_text(errors='replace')
    out = {k: [] for k in KINDS}
    for name, kind in re.findall(r'^#define CONFIG_([A-Z0-9_]+)_(' + '|'.join(KINDS) + r') 1$', text, re.MULTILINE):
        out[kind].append(name.lower())
    return {k: sorted(v) for k, v in out.items()}


def configuration(config_h: Path) -> str:
    m = re.search(r'^#define FFMPEG_CONFIGURATION "(.*)"$', config_h.read_text(errors='replace'), re.MULTILINE)
    if not m:
        raise SystemExit(f'ff_components: no FFMPEG_CONFIGURATION in {config_h}')
    return re.sub(r'\\(["\\])', r'\1', m.group(1))


def replace_sublist(seq: list, old: list, new: list) -> list:
    if not old:
        return list(seq)
    for i in range(len(seq) - len(old) + 1):
        if seq[i:i + len(old)] == old:
            return seq[:i] + new + seq[i + len(old):]
    raise SystemExit('ff_components: the profile value was not found in the build\'s configure line')


def baseline(ffmpeg: Path, report: dict, work: Path) -> tuple[str, dict, list]:
    args = shlex.split(configuration(ffmpeg / 'config.h'))
    args = replace_sublist(args, shlex.split(report['value']), shlex.split(report['image_value']))
    if work.exists():
        shutil.rmtree(work)
    src, bld = work / 'src', work / 'build'
    subprocess.run(['git', '-C', str(ffmpeg), 'worktree', 'add', '-q', '--detach', str(src.resolve()), 'HEAD'],
                   check=True)
    bld.mkdir(parents=True)
    try:
        r = subprocess.run([str((src / 'configure').resolve())] + args, cwd=bld, capture_output=True, text=True)
        if r.returncode != 0:
            print((bld / 'ffbuild' / 'config.log').read_text(errors='replace')[-4000:] if
                  (bld / 'ffbuild' / 'config.log').exists() else r.stdout[-4000:], file=sys.stderr)
            raise SystemExit('ff_components: baseline configure failed')
        return configuration(bld / 'config.h'), components(bld / 'config_components.h'), args
    finally:
        subprocess.run(['git', '-C', str(ffmpeg), 'worktree', 'remove', '--force', str(src.resolve())])


def checks(build: dict, base: dict, report: dict, base_conf: str, ref_conf: str | None) -> list:
    res = []

    def add(gate: str, ok: bool, text: str, items=None):
        res.append({'gate': gate, 'result': 'pass' if ok else 'fail', 'text': text, 'items': sorted(items or [])})

    if ref_conf is None:
        add('baseline', False, 'no reference configure line given; the baseline cannot be proven equal to b10')
    else:
        add('baseline', base_conf == ref_conf,
            'baseline configure line is identical to the reference release (b10)' if base_conf == ref_conf
            else 'baseline configure line differs from the reference release', [] if base_conf == ref_conf
            else [f'baseline: {base_conf}', f'reference: {ref_conf}'])

    def gone(kind):
        return set(base[kind]) - set(build[kind])

    def added(kind):
        return set(build[kind]) - set(base[kind])

    if report['profile'] == 'none':
        for kind in KINDS:
            diff = {f'-{x}' for x in gone(kind)} | {f'+{x}' for x in added(kind)}
            add('self-test', not diff, f'{kind.lower()}s: build equals baseline ({len(build[kind])})', diff)
        return res

    exp_dec = set(report['expected_gone_decoders'])
    unexpected = gone('DECODER') - exp_dec
    add('K-S1', not unexpected, f"decoders: {len(build['DECODER'])} kept of {len(base['DECODER'])}; "
        f"gone only the expected external ones ({', '.join(sorted(gone('DECODER') & exp_dec)) or 'none'})"
        if not unexpected else 'decoders: unexpected decoders are gone', unexpected)
    add('K-S1', not added('DECODER'), 'decoders: none added' if not added('DECODER') else 'decoders added (?)',
        added('DECODER'))
    missing = [f for f in REQUIRED_FILTERS if f not in build['FILTER']]
    add('K-S1', not missing, f"ASSMA filters present ({', '.join(REQUIRED_FILTERS)})", missing)
    add('K-S1', not gone('FILTER'), f"filters: {len(build['FILTER'])}, none lost against b10", gone('FILTER'))
    add('K-S1', not gone('HWACCEL') and not added('HWACCEL'),
        f"hwaccels identical to b10 ({len(build['HWACCEL'])})", gone('HWACCEL') | added('HWACCEL'))
    unexpected = gone('DEMUXER') - set(report['expected_gone_demuxers'])
    add('K-S1', not unexpected, f"demuxers: {len(build['DEMUXER'])} of {len(base['DEMUXER'])}; gone only "
        f"network / removed-library ones ({', '.join(sorted(gone('DEMUXER'))) or 'none'})"
        if not unexpected else 'demuxers: unexpected demuxers are gone', unexpected)
    missing = [d for d in REQUIRED_DEMUXERS if d not in build['DEMUXER']]
    add('K-S1', not missing, 'broadcast / file demuxers present (' + ', '.join(REQUIRED_DEMUXERS) + ')', missing)
    for kind in ('PARSER', 'BSF'):
        add('K-S1', not gone(kind), f'{kind.lower()}s: none lost ({len(build[kind])})', gone(kind))

    if '--disable-encoders' in report['added_options']:
        add('K-S2', not build['ENCODER'], f"encoders: {len(build['ENCODER'])} (b10: {len(base['ENCODER'])})",
            build['ENCODER'])
    if '--disable-network' in report['added_options']:
        bad = set(build['PROTOCOL']) - LOCAL_PROTOCOLS
        net = set(build['PROTOCOL']) & NETWORK_PROTOCOLS
        add('K-S2', not bad and not net, f"protocols: only local ones ({', '.join(build['PROTOCOL'])}); "
            f"b10 had {len(base['PROTOCOL'])}", bad | net)
    return res


def markdown(p: dict) -> str:
    L = [f"# FFmpeg profile `{p['profile']['profile']}` - checks K-S1 / K-S2", '',
         f"Result: **{p['result']}**", '',
         f"- Image FF_CONFIGURE: `{p['profile']['image_value']}`",
         f"- Removed from it: {', '.join(f'`{o}`' for o in p['profile']['removed_options']) or '-'}",
         f"- Appended: {', '.join(f'`{o}`' for o in p['profile']['added_options']) or '-'}",
         f"- tools/ff_profile.py SHA-256 `{p['profile']['tool_sha256']}`", '',
         '| gate | result | check | items |', '|---|---|---|---|']
    for c in p['checks']:
        items = ', '.join(c['items'][:40]) + (f" … (+{len(c['items']) - 40})" if len(c['items']) > 40 else '')
        L.append(f"| {c['gate']} | {c['result'].upper()} | {c['text']} | {items} |")
    L += ['', '## Component counts', '', '| kind | b10 (baseline) | this build |', '|---|---|---|']
    for k in KINDS:
        L.append(f"| {k.lower()} | {p['counts']['baseline'][k]} | {p['counts']['build'][k]} |")
    L += ['', 'Removed / added lists per kind: PROFILE.json › `difference`.', '']
    return '\n'.join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--ffmpeg', default='ffmpeg')
    ap.add_argument('--report', required=True, help='JSON written by ff_profile.py --report')
    ap.add_argument('--reference-manifest', help="the reference release's MANIFEST.json (b10)")
    ap.add_argument('--work', default='/tmp/ff-baseline')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    report = json.loads(Path(a.report).read_text())
    ffmpeg = Path(a.ffmpeg)
    build = components(ffmpeg / 'config_components.h')
    base_conf, base, base_args = baseline(ffmpeg, report, Path(a.work))
    ref_conf = None
    if a.reference_manifest:
        ref = json.loads(Path(a.reference_manifest).read_text())
        ref_conf = ref['ffmpeg']['configuration']
    res = checks(build, base, report, base_conf, ref_conf)
    out = {
        'profile': report,
        'build_configuration': configuration(ffmpeg / 'config.h'),
        'baseline_configuration': base_conf,
        'reference_release': (json.loads(Path(a.reference_manifest).read_text())['name']
                              if a.reference_manifest else None),
        'counts': {'build': {k: len(v) for k, v in build.items()}, 'baseline': {k: len(v) for k, v in base.items()}},
        'difference': {k.lower(): {'gone': sorted(set(base[k]) - set(build[k])),
                                   'added': sorted(set(build[k]) - set(base[k]))} for k in KINDS},
        'components': build,
        'checks': res,
        'result': 'fail' if any(c['result'] == 'fail' for c in res) else 'pass',
    }
    o = Path(a.out)
    (o / 'PROFILE.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    (o / 'PROFILE-CHECKS.md').write_text(markdown(out), encoding='utf-8')
    print(markdown(out))
    return 0 if out['result'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())

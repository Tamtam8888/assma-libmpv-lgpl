#!/usr/bin/env python3
"""Decode regression test: the reference DLL (b10) and the new DLL decode the same files with the same program.

    decode_test.py --probe decode_probe.exe --media media/ --ref b10/libmpv-2.dll --new new/libmpv-2.dll --out OUT

For every test file (media/MADE.txt) and every audio graph case, decode_probe.exe runs under Wine once with each
DLL (each DLL sits in its own folder next to its own copy of the probe). Compared: everything the probe prints
(decoders chosen, last frame number, audio format, end reason) and, for audio, the SHA-256 of the decoded samples.
Expected: identical lines. Writes DECODE-TEST.md / DECODE-TEST.json into OUT; exit status 1 on any difference or if
the new DLL fails where the reference works.

Limits (S2 plan §4): Wine is not Windows - hardware decoding, GPU output and timing are tested in the field test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO_ONLY = ('.m4a', '.ac3', '.eac3', '.mp2', '.mp3', '.flac', '.ogg', '.wav')

# ASSMA's audio graph K238 (assma repo, decision log): the inputs are merged with lavfi-complex (amerge), then one
# lavfi graph gives every input channel its own volume@ filter for L and for R and mixes everything with amix
# (normalize off) to stereo.
def k238_af(channels: int) -> str:
    parts, labels = [f'asplit={channels * 2}' + ''.join(f'[s{i}]' for i in range(channels * 2))], []
    for k in range(channels):
        for side, idx in (('L', 2 * k), ('R', 2 * k + 1)):
            route = f'c0=c{k}|c1=0*c{k}' if side == 'L' else f'c0=0*c{k}|c1=c{k}'
            parts.append(f'[s{idx}]pan=stereo|{route},volume@{side}{k}={0.25 + 0.05 * k:.2f}[m{idx}]')
            labels.append(f'[m{idx}]')
    parts.append(''.join(labels) + f'amix=inputs={channels * 2}:normalize=0')
    return 'lavfi=[' + ';'.join(parts) + ']'


GRAPHS = [
    # (case name, file, af, lavfi-complex)
    ('k238 amerge 8+2 -> 20 volume@ -> amix', 'two_tracks.mkv', k238_af(10),
     '[aid1][aid2]amerge=inputs=2[ao];[vid1]null[vo]'),
    ('pan + alimiter + volume (8 ch)', 'pcm8ch.wav',
     'lavfi=[pan=stereo|c0=0.5*c0+0.5*c2|c1=0.5*c1+0.5*c3,alimiter=limit=0.7,volume=0.8,asetpts=PTS-STARTPTS]', ''),
    ('channelsplit + join (8 ch)', 'pcm8ch.wav',
     'lavfi=[channelsplit=channel_layout=7.1:channels=FL+FR[l][r];[l][r]join=inputs=2:channel_layout=stereo]', ''),
]


def run_probe(folder: Path, args: list) -> dict:
    cmd = ['wine', str(folder / 'decode_probe.exe')] + args
    try:
        r = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, timeout=300,
                           env={**os.environ, 'WINEDEBUG': '-all'})
        text = r.stdout
    except subprocess.TimeoutExpired:
        text, r = 'end=wine-timeout\n', None
    facts = {}
    for line in text.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            facts[k.strip()] = v.strip()
    facts['exit'] = str(r.returncode if r else 'timeout')
    return facts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', required=True)
    ap.add_argument('--media', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--new', required=True)
    ap.add_argument('--ref-name', default='reference')
    ap.add_argument('--new-name', default='new')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    media = Path(a.media).resolve()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path('/tmp/decode-test')
    shutil.rmtree(work, ignore_errors=True)
    folders = {}
    for side, dll in (('ref', a.ref), ('new', a.new)):
        f = work / side
        f.mkdir(parents=True)
        shutil.copy2(dll, f / 'libmpv-2.dll')
        shutil.copy2(a.probe, f / 'decode_probe.exe')
        (f / 'media').symlink_to(media)
        folders[side] = f

    files = [x for x in (media / 'MADE.txt').read_text().split('\n') if x]
    cases = []
    for name in files:
        pcm = name.endswith(AUDIO_ONLY)
        cases.append((f'decode {name}', name, '', '', pcm))
    for case, name, af, lavfi in GRAPHS:
        if name in files:
            cases.append((case, name, af, lavfi, True))

    rows, failed = [], False
    for case, name, af, lavfi, pcm in cases:
        res = {}
        for side, f in folders.items():
            args = [f'media\\{name}', af, lavfi, 'out.wav' if pcm else '']
            (f / 'out.wav').unlink(missing_ok=True)
            facts = run_probe(f, args)
            if pcm:
                w = f / 'out.wav'
                facts['pcm_sha256'] = hashlib.sha256(w.read_bytes()).hexdigest()[:16] if w.exists() else 'no output'
                facts['pcm_bytes'] = str(w.stat().st_size) if w.exists() else '0'
            res[side] = facts
        ref, new = res['ref'], res['new']
        keys = sorted(set(ref) | set(new))
        diff = {k: (ref.get(k), new.get(k)) for k in keys if ref.get(k) != new.get(k)}
        ref_ok = ref.get('end') == 'eof' and 'error' not in ref
        new_ok = new.get('end') == 'eof' and 'error' not in new
        if not ref_ok:
            # the reference must decode every test file; otherwise the test itself is broken and proves nothing
            status = 'REFERENCE FAILS'
            failed = True
        elif diff or not new_ok:
            status = 'DIFFERENT'
            failed = True
        else:
            status = 'same'
        rows.append({'case': case, 'status': status, 'reference': ref, 'new': new, 'difference': diff})
        print(f'{status:16} {case}', flush=True)

    skipped = (media / 'SKIPPED.txt').read_text().strip() if (media / 'SKIPPED.txt').exists() else ''
    L = [f'# Decode test: {a.new_name} vs {a.ref_name} (Wine, same probe, same files)', '',
         f"Result: **{'fail' if failed else 'pass'}** - {sum(r['status'] == 'same' for r in rows)} of {len(rows)} "
         'cases identical', '',
         '| case | result | video decoder | frames | audio decoder | audio out | samples (SHA-256) |',
         '|---|---|---|---|---|---|---|']
    for r in rows:
        n = r['new']
        L.append(f"| {r['case']} | {r['status']} | {n.get('current-tracks/video/decoder-desc', '')} | "
                 f"{n.get('estimated-frame-number', '')} | {n.get('current-tracks/audio/decoder-desc', '')} | "
                 f"{n.get('audio-out-params/channel-count', '')} ch | {n.get('pcm_sha256', '-')} |")
        for k, (x, y) in r['difference'].items():
            L.append(f"|  | `{k}` | {a.ref_name}: {x} | | {a.new_name}: {y} | | |")
    L += ['', f'Test files not made by the runner\'s ffmpeg: {skipped or "none"}', '',
          'Wine is not Windows: hardware decoding, GPU output and timing are covered by the field test.', '']
    (out / 'DECODE-TEST.md').write_text('\n'.join(L), encoding='utf-8')
    (out / 'DECODE-TEST.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    print('\n'.join(L))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""K-S4: COMPARE.md - what changed between the reference release (b10) and a new build.

    compare_builds.py --ref ref_folder --new new_folder [--decode DECODE-TEST.md] > COMPARE.md

Both folders are unpacked release zips (MANIFEST.json, include/mpv/client.h, libmpv-2.dll; the new one also
PROFILE.json). Exit status 1 if the mpv client API changed, or if a copyleft component is inside the new DLL that
was not inside the reference DLL (a profile may only remove).
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path


def api_version(folder: Path) -> str:
    text = (folder / 'include' / 'mpv' / 'client.h').read_text(errors='replace')
    m = re.search(r'#define MPV_CLIENT_API_VERSION MPV_MAKE_VERSION\((\d+),\s*(\d+)\)', text)
    return f'{m.group(1)}.{m.group(2)}' if m else '?'


def dll_bytes(m: dict) -> int:
    return next((f['bytes'] for f in m['files'] if f['file'] == 'libmpv-2.dll'), 0)


def in_dll(m: dict) -> dict:
    return {x['stem']: x for x in m['linked_libraries'] if x.get('in_dll') or not x['file'].endswith('.a')}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True)
    ap.add_argument('--new', required=True)
    ap.add_argument('--decode', help='DECODE-TEST.md of the decode job (its result line is quoted)')
    a = ap.parse_args()
    ref_dir, new_dir = Path(a.ref), Path(a.new)
    ref = json.loads((ref_dir / 'MANIFEST.json').read_text())
    new = json.loads((new_dir / 'MANIFEST.json').read_text())
    prof_file = new_dir / 'PROFILE.json'
    prof = json.loads(prof_file.read_text()) if prof_file.exists() else None
    problems = []

    L = [f"# {new['name']} compared with {ref['name']}", '']
    api_r, api_n = api_version(ref_dir), api_version(new_dir)
    if api_r != api_n:
        problems.append(f'mpv client API changed: {api_r} -> {api_n}')
    copyleft_r = {s for s, x in in_dll(ref).items() if x['class'] in ('lgpl', 'mpl')}
    copyleft_n = {s for s, x in in_dll(new).items() if x['class'] in ('lgpl', 'mpl')}
    if copyleft_n - copyleft_r:
        problems.append(f'new copyleft components inside the DLL: {sorted(copyleft_n - copyleft_r)}')
    L += [f"Result: **{'fail' if problems else 'pass'}**", '']
    L += [f'- PROBLEM: {p}' for p in problems]
    L += ['## Summary', '',
          '| | ' + ref['name'] + ' | ' + new['name'] + ' |', '|---|---|---|',
          f"| mpv commit | `{ref['mpv']['commit'][:12]}` | `{new['mpv']['commit'][:12]}` |",
          f"| FFmpeg commit | `{ref['ffmpeg']['commit'][:12]}` | `{new['ffmpeg']['commit'][:12]}` |",
          f"| toolchain image | `{ref['toolchain_image']['reference'][-16:]}` | `{new['toolchain_image']['reference'][-16:]}` |",
          f"| mpv client API | {api_r} | {api_n} |",
          f"| FFmpeg profile | none | {(new.get('ffmpeg_profile') or {}).get('profile', 'none')} |",
          f"| libmpv-2.dll bytes | {dll_bytes(ref):,} | {dll_bytes(new):,} ({dll_bytes(new) - dll_bytes(ref):+,}) |",
          f"| libraries inside the DLL | {len(in_dll(ref))} | {len(in_dll(new))} |",
          f"| objects inside the DLL | {sum(x['members_in_dll'] for x in ref['linked_libraries']):,} | "
          f"{sum(x['members_in_dll'] for x in new['linked_libraries']):,} |",
          f"| copyleft components inside the DLL | {len(copyleft_r)} | {len(copyleft_n)} |",
          f"| licence gate | {ref['gate']['result']} | {new['gate']['result']} |", '']
    if a.decode and Path(a.decode).exists():
        line = next((x for x in Path(a.decode).read_text().splitlines() if x.startswith('Result:')), '')
        L += [f'Decode test (DECODE-TEST.md): {line[len("Result:"):].strip()}', '']

    L += ['## FFmpeg configure line', '']
    tr, tn = shlex.split(ref['ffmpeg']['configuration']), shlex.split(new['ffmpeg']['configuration'])
    L.append('- only in ' + ref['name'] + ': ' + (' '.join(f'`{t}`' for t in tr if t not in tn) or '-'))
    L.append('- only in ' + new['name'] + ': ' + (' '.join(f'`{t}`' for t in tn if t not in tr) or '-'))
    L.append('')

    if prof:
        L += ['## FFmpeg components (baseline = ' + str(prof.get('reference_release')) + ' configure line, checked '
              'identical)', '', '| kind | ' + ref['name'] + ' | new | gone | added |', '|---|---|---|---|---|']
        for kind, d in prof['difference'].items():
            k = kind.upper()
            gone = ', '.join(d['gone']) if len(d['gone']) <= 12 else f"{len(d['gone'])} (PROFILE.json)"
            L.append(f"| {kind} | {prof['counts']['baseline'][k]} | {prof['counts']['build'][k]} | {gone or '-'} | "
                     f"{', '.join(d['added']) or '-'} |")
        L.append('')

    L += ['## Copyleft components inside the DLL', '',
          f"- {ref['name']}: {', '.join(sorted(copyleft_r))}",
          f"- {new['name']}: {', '.join(sorted(copyleft_n))}",
          f"- removed: {', '.join(sorted(copyleft_r - copyleft_n)) or '-'}", '',
          '## Linked libraries: objects inside the DLL', '',
          '| library | licence | ' + ref['name'] + ' | new | change |', '|---|---|---|---|---|']
    r_libs = {x['stem']: x for x in ref['linked_libraries']}
    n_libs = {x['stem']: x for x in new['linked_libraries']}
    for stem in sorted(set(r_libs) | set(n_libs)):
        r, n = r_libs.get(stem), n_libs.get(stem)
        rc = r['members_in_dll'] if r else '-'
        nc = n['members_in_dll'] if n else '-'
        if r is None:
            change = 'new on the link line'
        elif n is None:
            change = 'gone from the link line'
        elif rc and not nc:
            change = 'no longer in the DLL'
        elif rc != nc:
            change = 'changed'
        else:
            continue
        lic = (n or r)['licence']
        L.append(f'| {stem} | {lic} | {rc} | {nc} | {change} |')
    L += ['', 'Libraries with the same number of objects in both builds are not listed.', '']
    print('\n'.join(L))
    if problems:
        print('\nCOMPARE PROBLEMS:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""NOTICE.md for a libmpv build: one row per component that is really inside libmpv-2.dll (linker map), each with
its own licence, licence text location and exact source. No single licence is claimed for the DLL as a whole.

    python3 tools/make_notice.py <build MANIFEST.json> <SOURCE-MANIFEST.json> <source release name> > NOTICE.md
"""
from __future__ import annotations

import json
import sys

ORDER = {'lgpl': 0, 'mpl': 1, 'permissive': 2, 'runtime': 3}


def main() -> None:
    m = json.load(open(sys.argv[1], encoding='utf-8'))
    sm = json.load(open(sys.argv[2], encoding='utf-8'))
    release = sys.argv[3]
    image = {e['component']: e for e in sm['image']}
    recipe = {e['component']: e for e in sm['recipe']}
    tool = {e['component']: e for e in sm.get('toolchain', [])}
    rows = {}
    for lib in m['linked_libraries']:
        if not lib.get('in_dll') or lib['class'] == 'system':
            continue
        r = rows.setdefault(lib['project'], {'libs': set(), 'licence': lib['licence'], 'class': lib['class'],
                                             'source': lib.get('source', ''), 'version': ''})
        r['libs'].add(lib['stem'])
        if lib.get('pkgconfig') and not r['version']:
            name, _, ver = lib['pkgconfig'].rpartition(' ')
            if lib['stem'] in name or name.replace('lib', '') in lib['stem']:
                r['version'] = ver
    out = [f"# libmpv-2.dll - third-party components and their licences", '',
           f"Build: `{m['name']}` · libmpv-2.dll SHA-256 `{sm['dll_sha256']}`", '',
           "This is an LGPL build of libmpv (mpv built with `-Dgpl=false`; https://mpv.io). `libmpv-2.dll` contains "
           "objects statically linked from the components below. **Each component is under its own licence**; the "
           "licence texts are in the `licences/` folder of the source release, under the component's own file names.",
           '', '## Your rights', '',
           "- You may replace `libmpv-2.dll` with a modified or different build. Programs that use it load it as a "
           "separate file at run time.",
           f"- The complete source of this build, including the scripts that control its compilation, is published "
           f"in the release `{release}`: `SOURCE-MANIFEST.json` lists every part with its commit and SHA-256, and "
           f"`verify_sources.py` checks that each archive holds exactly that commit.",
           "- [Availability period and written offer for the case that the release is removed: legal decision "
           "pending.]", '',
           '## Components inside the DLL', '',
           'Order: LGPL, MPL, permissive licences, compiler runtime.', '',
           '| Component (libraries) | Version | Licence | Source: repository @ commit |', '|---|---|---|---|']
    for name, r in sorted(rows.items(), key=lambda kv: (ORDER.get(kv[1]['class'], 9), kv[0].lower())):
        s = r['source']
        if s.startswith('mpv:'):
            key = s[4:]
            e = recipe.get(key) or next((v for k, v in recipe.items() if key == 'subprojects' and k.startswith('mujs')), None)
            src = f"{e['url']} @ `{e.get('commit', e.get('sha256', ''))[:12]}`" if e else '?'
        elif s == 'toolchain':
            t = tool.get('gcc') if 'GCC' in name else tool.get('mingw-w64')
            src = f"{t['url']} @ {t['ref'].split('/')[-1]}" if t else 'toolchain'
        else:
            e = image.get(s)
            src = '<br>'.join(f"{x['remote']} @ `{x['commit'][:12]}`" + ('' if x['path'] == '.' else f" ({x['path']})")
                              for x in (e['repositories'] if e else [])) or (
                  '<br>'.join(f"{v['url']} r{v['revision']}" for v in e['svn']) if e else '?')
        out.append(f"| {name} ({', '.join(sorted(r['libs']))}) | {r['version'] or '-'} | {r['licence']} | {src} |")
    mingw = tool.get('mingw-w64')
    out.append(f"| mingw-w64 C runtime (mingw32, mingwex) | {mingw['ref'].split('/')[-1] if mingw else '?'} | "
               f"mingw-w64 runtime licences (mostly public domain; some files ZPL-2.1 or MIT / BSD style) | "
               f"{mingw['url'] + ' @ ' + mingw['ref'].split('/')[-1] if mingw else '?'} |")
    ft = image.get('45-fonts/50-freetype')
    year = (ft['repositories'][0].get('commit_date') or '')[:4] if ft else ''
    notices = [f"{e['component']}: {f}" for e in sm['image'] for f in e.get('licence_and_notice_files', [])
               if f.split('/')[-1].upper().startswith('NOTICE')]
    out += ['', 'Windows system libraries (kernel32, user32, ...) appear only as import records; they are not part '
                'of this package.', '', '## Special notices', '',
            f"- **FreeType:** Portions of this software are copyright © {year or '[year]'} The FreeType Project "
            "(www.freetype.org). All rights reserved.",
            "- **GCC runtime** (libgcc, libstdc++, libgomp): GPL-3.0 with the GCC Runtime Library Exception 3.1, "
            "which places no licence conditions on a program that includes these objects through GCC compilation "
            "(texts: `toolchain/gcc/`).",
            "- **Apache-2.0 NOTICE files** found in the sources (all depths), copied to `licences/`: "
            + ('; '.join(notices) if notices else 'none found') + '.',
            "- **Patents:** some components implement patented technology (for example video and audio codecs). "
            "Copyright licences do not grant patent rights. The AV1 components (libaom, SVT-AV1, dav1d) come with "
            "the Alliance for Open Media royalty-free patent licence (`licences/image/50-aom/PATENTS`). This package "
            "makes no other patent statement.", '',
            '## On the link line but not inside the DLL (information)', '']
    for lib in m['linked_libraries']:
        if not lib.get('in_dll') and lib['class'] in ('gpl', 'nonfree', 'unknown'):
            out.append(f"- `{lib['stem']}` ({lib['licence']}): the linker took no object from it "
                       f"(MANIFEST.json, members_in_dll = 0).")
    print('\n'.join(out))


if __name__ == '__main__':
    main()

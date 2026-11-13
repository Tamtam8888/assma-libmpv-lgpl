#!/usr/bin/env python3
"""Dependency and licence inventory of the libmpv build, and the release gate.

Run inside the build container from the mpv source folder, after ci/build-mingw64-full.sh:

    python3 tools/inventory.py --out artifact-libmpv [--strict]

What it records (MANIFEST.json, machine-readable; INVENTORY.md, the same for people):
- the delivered files with their SHA-256,
- mpv / recipe / toolchain image / workflow identity,
- every repository the recipe cloned, at which commit, and whether pins.lock fixed it,
- FFmpeg's exact configure line and licence switches,
- mpv's build options and the dependencies meson found (with versions),
- every library on the link line of libmpv-2.dll, where it came from, its version (pkg-config) and its licence,
- the Rust crates inside subrandr, with their licences.

The gate (why it exists: ChatGPT review 13.11 - the licence must be proven from what is really inside the DLL,
not only from build switches): every library actually linked into libmpv-2.dll must have a known licence that a
closed program may use (classes lgpl / mpl / permissive / runtime / system). A GPL, nonfree or unknown library stops
the release. Libraries that are only present in the toolchain image (for example FFTW, used by the GPL-only
rubberband) do not matter unless they are linked; they are listed separately for information.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ALLOWED = {'lgpl', 'mpl', 'permissive', 'runtime', 'system'}
REPO = Path(os.environ.get('ASSMA_REPO_DIR', Path(__file__).resolve().parent.parent))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def run(*cmd, cwd=None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
    except subprocess.CalledProcessError as e:
        return f'ERROR: {e}: {(e.stderr or "").strip()[-800:]}'
    except OSError as e:
        return f'ERROR: {e}'


def load_table() -> dict:
    table = {}
    for line in (REPO / 'licences.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        stem, licence, klass, project, source = (line.split('\t') + ['', '', '', ''])[:5]
        table[stem] = {'licence': licence, 'class': klass, 'project': project, 'source': source}
    return table


def pkgconfig_index(prefix: str) -> tuple[dict, list]:
    """stem -> (package, version) from the .pc files of the image, and the list of all packages."""
    by_stem, packages = {}, []
    for pc in sorted(glob.glob(os.path.join(prefix, 'lib', 'pkgconfig', '*.pc'))):
        text = Path(pc).read_text(encoding='utf-8', errors='replace')
        fields = dict(re.findall(r'^([A-Za-z.]+):\s*(.*)$', text, flags=re.MULTILINE))
        name = Path(pc).stem
        version = fields.get('Version', '')
        packages.append({'package': name, 'version': version, 'description': fields.get('Description', '')})
        for stem in re.findall(r'(?:^|\s)-l(\S+)', fields.get('Libs', '')):
            by_stem.setdefault(stem, (name, version))
    return by_stem, packages


def link_line(build_dir: Path) -> list:
    """Tokens of the command that linked libmpv-2.dll, exactly as ninja ran it (`ninja -t commands`).
    If the command passes its arguments in a response file (@file.rsp), that file is read too."""
    out = subprocess.run(['ninja', '-C', str(build_dir), '-t', 'commands', 'libmpv-2.dll'],
                         check=True, capture_output=True, text=True).stdout.strip().splitlines()
    if not out:
        raise SystemExit('inventory: ninja gave no command for libmpv-2.dll')
    command = out[-1]
    print('inventory: link command of libmpv-2.dll (first 600 characters):', command[:600])
    tokens = []
    for tok in shlex.split(command):
        if tok.startswith('@') and (build_dir / tok[1:]).is_file():
            tokens += shlex.split((build_dir / tok[1:]).read_text(errors='replace'))
        else:
            tokens.append(tok)
    return tokens


def compiler_dirs() -> list:
    cc = os.environ.get('CC', 'gcc')
    out = run(cc, '-print-search-dirs')
    for line in out.splitlines():
        if line.startswith('libraries:'):
            return [d for d in line.split('=', 1)[-1].split(':') if d]
    return []


def stem_of(filename: str) -> str:
    name = os.path.basename(filename)
    for suffix in ('.dll.a', '.a', '.lib'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name[3:] if name.startswith('lib') else name


def linked_libraries(build_dir: Path, prefix: str) -> list:
    tokens = link_line(build_dir)
    toolchain = [os.path.realpath(d) for d in compiler_dirs()]
    search = [t[2:] for t in tokens if t.startswith('-L')] + [os.path.join(prefix, 'lib')] + toolchain
    found, seen = [], set()
    for tok in tokens:
        for part in tok.split(','):                     # -Wl,... may carry nothing useful; plain tokens matter
            path = None
            if part.startswith('-l:'):
                name = part[3:]
                path = next((os.path.join(d, name) for d in search if os.path.isfile(os.path.join(d, name))), None)
                stem = stem_of(name)
            elif part.startswith('-l'):
                stem = part[2:]
                for d in search:
                    for cand in (f'lib{stem}.a', f'lib{stem}.dll.a', f'{stem}.lib', f'lib{stem}.lib'):
                        if os.path.isfile(os.path.join(d, cand)):
                            path = os.path.join(d, cand)
                            break
                    if path:
                        break
            elif part.endswith(('.a', '.lib')) and not part.startswith('-'):
                stem = stem_of(part)
                path = part if os.path.isabs(part) else str(build_dir / part)
            else:
                continue
            if stem in seen:
                continue
            seen.add(stem)
            real = os.path.realpath(path) if path else ''
            if not real:
                origin = 'not found'
            elif real.startswith(os.path.realpath(prefix)):
                origin = 'image library'
            elif real.startswith(os.path.realpath(build_dir)):
                origin = 'built here'
            elif any(real.startswith(d.rstrip('/') + '/') for d in toolchain):
                origin = 'toolchain'
            else:
                origin = 'other'
            found.append({'stem': stem, 'file': real, 'origin': origin})
    return found


def rust_crates(manifest: Path) -> tuple[list, str]:
    if not manifest.is_file():
        return [], 'subrandr/Cargo.toml not found'
    base = ['cargo', 'metadata', '--format-version', '1', '--locked',
            '--filter-platform', os.environ.get('FFBUILD_RUST_TARGET', 'x86_64-pc-windows-gnu'),
            '--manifest-path', str(manifest)]
    out = run(*base, '--offline')
    if out.startswith('ERROR'):                      # index not cached: same lock file, read online
        print('inventory: cargo metadata offline failed, trying online:', out)
        out = run(*base)
    if out.startswith('ERROR'):
        return [], out
    data = json.loads(out)
    by_id = {p['id']: p for p in data['packages']}
    nodes = {n['id']: n for n in data['resolve']['nodes']}
    root = data['resolve']['root'] or data['workspace_members'][0]
    keep, todo = set(), [root]
    while todo:                                           # normal (non-dev, non-build) dependencies only
        node = todo.pop()
        if node in keep:
            continue
        keep.add(node)
        for dep in nodes[node]['deps']:
            if any(k.get('kind') is None for k in dep.get('dep_kinds', [])):
                todo.append(dep['pkg'])
    crates = [{'name': by_id[i]['name'], 'version': by_id[i]['version'], 'licence': by_id[i].get('license') or '',
               'source': by_id[i].get('source') or 'local'} for i in sorted(keep)]
    return crates, ''


LICENCE_NAMES = re.compile(r'^(LICEN[CS]E|COPYING|COPYRIGHT|NOTICE|PATENTS|UNLICENSE)', re.IGNORECASE)


def copy_licence_files(src: Path, dest: Path, depth: int = 2) -> int:
    """Licence files of one source tree (top level and a little below) -> dest. Returns how many."""
    import shutil
    count = 0
    if not src.is_dir():
        return 0
    for path in sorted(src.rglob('*')):
        rel = path.relative_to(src)
        if (path.is_file() and LICENCE_NAMES.match(path.name) and len(rel.parts) <= depth + 1
                and '.git' not in rel.parts and 'build' not in rel.parts[:1]):
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            count += 1
    return count


def collect_licences(out: Path, clones: list, crates: list) -> list:
    """Licence texts of everything built by the recipe itself (the image libraries are collected by
    tools/collect_image_sources.sh in a separate job). Returns problems (a source without a licence file)."""
    problems = []
    base = out / 'licences'
    trees = {'mpv': Path('.')}
    trees.update({Path(c['folder']).name: Path(c['folder']) for c in clones})
    trees.update({p.name: p for p in Path('subprojects').glob('*') if p.is_dir() and p.name != 'packagecache'})
    trees.update({p.name: p for p in Path('.').glob('cppwinrt-*') if p.is_dir()})
    for name, tree in sorted(trees.items()):
        depth = 0 if name == 'mpv' else 2
        if copy_licence_files(tree, base / 'recipe' / name, depth) == 0:
            problems.append(f'no licence file found in {tree}')
    cargo_src = Path(os.environ.get('CARGO_HOME', os.path.expanduser('~/.cargo'))) / 'registry' / 'src'
    for c in crates:
        if c['source'] == 'local':
            continue
        dirs = list(cargo_src.glob(f"*/{c['name']}-{c['version']}"))
        if not dirs or copy_licence_files(dirs[0], base / 'rust' / f"{c['name']}-{c['version']}", 0) == 0:
            c['licence_text'] = 'not shipped by the crate (licence named in Cargo.toml only)'
        else:
            c['licence_text'] = 'included'
    for candidate in ('/opt/ct-ng/share/licenses', '/opt/ct-ng/share/doc'):
        if Path(candidate).is_dir():
            copy_licence_files(Path(candidate), base / 'toolchain', 3)
    return problems


def spdx_class(expr: str) -> str:
    """Rust crate licence expression -> class. 'A OR B': the most permissive alternative counts."""
    if not expr:
        return 'unknown'
    best = 'unknown'
    order = ['unknown', 'nonfree', 'gpl', 'lgpl', 'mpl', 'permissive']
    for alt in re.split(r'\s+OR\s+|/', expr):
        a = alt.upper()
        if re.search(r'(?<![L])GPL|AGPL', a):
            c = 'gpl'
        elif 'LGPL' in a:
            c = 'lgpl'
        elif 'MPL' in a:
            c = 'mpl'
        elif re.search(r'MIT|APACHE|BSD|ISC|ZLIB|UNICODE|UNLICENSE|0BSD|CC0|BSL|WTFPL', a):
            c = 'permissive'
        else:
            c = 'unknown'
        if order.index(c) > order.index(best):
            best = c
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--strict', action='store_true', help='stop on a GPL / nonfree / unknown linked library')
    args = ap.parse_args()
    out = Path(args.out)
    prefix = os.environ['FFBUILD_PREFIX']
    build = Path('build')
    table = load_table()
    problems = []

    # delivered files
    files = [{'file': str(p.relative_to(out)).replace(os.sep, '/'), 'bytes': p.stat().st_size, 'sha256': sha256(p)}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ('MANIFEST.json', 'INVENTORY.md')
             and 'licences' not in p.relative_to(out).parts]

    # sources
    clones = []
    log = os.environ.get('PIN_LOG', '')
    if log and os.path.isfile(log):
        for line in Path(log).read_text().splitlines():
            url, folder, commit, pinned = line.split('\t')
            clones.append({'url': url, 'folder': folder, 'commit': commit, 'pinned_by_pins_lock': pinned == 'yes'})
    wraps = {Path(w).name: Path(w).read_text() for w in sorted(glob.glob('subprojects/*.wrap'))}
    cppwinrt = sorted(Path('.').glob('cppwinrt-*'))
    script = Path('ci/build-mingw64-full.sh')
    recipe_changed = run('git', 'status', '--porcelain', '--', 'ci')

    # FFmpeg
    config_h = Path('ffmpeg/config.h').read_text(errors='replace')
    configuration = re.search(r'#define FFMPEG_CONFIGURATION "(.*)"', config_h)
    switches = dict(re.findall(r'#define CONFIG_(GPL|NONFREE|VERSION3|GPLV3|LGPLV3) (\d)', config_h))
    ff_ext = sorted(set(re.findall(r'--enable-(lib[\w-]+)', configuration.group(1) if configuration else '')))
    if switches.get('GPL') != '0' or switches.get('NONFREE') != '0':
        problems.append(f'FFmpeg licence switches: {switches}')

    # mpv
    options = json.loads((build / 'meson-info' / 'intro-buildoptions.json').read_text())
    mpv_options = {o['name']: o['value'] for o in options if o.get('section') == 'user' or o['name'] == 'gpl'}
    if mpv_options.get('gpl') is not False:
        problems.append(f"mpv gpl option is {mpv_options.get('gpl')!r}")
    deps = json.loads((build / 'meson-info' / 'intro-dependencies.json').read_text())
    mpv_deps = sorted({(d['name'], d.get('version') or '') for d in deps})

    # linked libraries + licences
    by_stem, packages = pkgconfig_index(prefix)
    libs = linked_libraries(build, prefix)
    for lib in libs:
        entry = table.get(lib['stem'])
        if entry is None and lib['origin'] == 'toolchain':
            entry = {'licence': 'mingw-w64 import library / CRT (public domain, ZPL)', 'class': 'system',
                     'project': 'mingw-w64', 'source': 'toolchain'}
        entry = entry or {'licence': '?', 'class': 'unknown', 'project': '?', 'source': '?'}
        lib.update(entry)
        pkg = by_stem.get(lib['stem'])
        lib['pkgconfig'] = f'{pkg[0]} {pkg[1]}' if pkg else ''
        if lib['class'] not in ALLOWED:
            problems.append(f"linked library {lib['stem']} ({lib['file'] or 'not found'}): "
                            f"{lib['licence']} [{lib['class']}]")

    if len(libs) < 10 or not any(x['stem'] == 'avcodec' for x in libs):
        problems.append(f'link line not understood: only {len(libs)} libraries found (expected FFmpeg and more)')

    crates, crate_error = rust_crates(Path('subrandr/Cargo.toml'))
    for c in crates:
        c['class'] = spdx_class(c['licence'])
        if c['class'] not in ALLOWED:
            problems.append(f"Rust crate {c['name']} {c['version']}: {c['licence'] or 'no licence field'}")
    if crate_error:
        problems.append(f'Rust crate list: {crate_error}')
    problems += collect_licences(out, clones, crates)

    image_only = sorted(p['package'] for p in packages
                        if not any(lib['pkgconfig'].startswith(p['package'] + ' ') for lib in libs))

    manifest = {
        'name': os.environ.get('NAME', ''),
        'files': files,
        'mpv': {'repository': 'https://github.com/mpv-player/mpv', 'commit': run('git', 'rev-parse', 'HEAD'),
                'version': os.environ.get('VERSION', ''), 'gpl_option': mpv_options.get('gpl')},
        'recipe': {'script': str(script), 'sha256': sha256(script), 'unchanged': recipe_changed == '',
                   'pin_method': 'tools/git-pin-shim + pins.lock (the script itself is not edited)'},
        'toolchain_image': {'reference': os.environ.get('IMAGE', ''), 'variant': os.environ.get('VARIANT', ''),
                            'ffmpeg_builds_revision': os.environ.get('FFBUILDS_REVISION', '')},
        'workflow': {'repository': os.environ.get('GITHUB_REPOSITORY', ''), 'commit': os.environ.get('GITHUB_SHA', ''),
                     'run': f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}"
                            f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                     'pins_lock_sha256': sha256(REPO / 'pins.lock'), 'licences_tsv_sha256': sha256(REPO / 'licences.tsv')},
        'cloned_sources': clones,
        'meson_wraps': wraps,
        'cppwinrt': [p.name for p in cppwinrt],
        'ffmpeg': {'commit': run('git', '-C', 'ffmpeg', 'rev-parse', 'HEAD'), 'licence_switches': switches,
                   'configuration': configuration.group(1) if configuration else '', 'external_libraries': ff_ext},
        'mpv_build_options': mpv_options,
        'mpv_dependencies': [{'name': n, 'version': v} for n, v in mpv_deps],
        'linked_libraries': libs,
        'rust_crates_in_subrandr': crates,
        'image_packages_not_linked': image_only,
        'image_packages': packages,
        'gate': {'strict': args.strict, 'result': 'fail' if problems else 'pass', 'problems': problems},
    }
    (out / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (out / 'INVENTORY.md').write_text(markdown(manifest), encoding='utf-8')
    print(markdown(manifest))
    if problems:
        print('\nGATE PROBLEMS:\n- ' + '\n- '.join(problems), file=sys.stderr)
        if args.strict:
            return 1
    return 0


def markdown(m: dict) -> str:
    L = [f"# {m['name'] or 'libmpv'} - dependency and licence inventory", '',
         f"Gate: **{m['gate']['result']}** (strict: {m['gate']['strict']})", '']
    for p in m['gate']['problems']:
        L.append(f'- PROBLEM: {p}')
    L += ['', '## Files', '', '| file | bytes | SHA-256 |', '|---|---|---|']
    L += [f"| {f['file']} | {f['bytes']} | `{f['sha256']}` |" for f in m['files']]
    L += ['', '## Identity', '',
          f"- mpv {m['mpv']['version']} commit `{m['mpv']['commit']}` (gpl option: {m['mpv']['gpl_option']})",
          f"- Recipe {m['recipe']['script']} sha256 `{m['recipe']['sha256']}`, unchanged: {m['recipe']['unchanged']}",
          f"- Toolchain image `{m['toolchain_image']['reference']}` (variant {m['toolchain_image']['variant']}, "
          f"FFmpeg-Builds revision {m['toolchain_image']['ffmpeg_builds_revision'] or 'not given'})",
          f"- FFmpeg commit `{m['ffmpeg']['commit']}`, switches {m['ffmpeg']['licence_switches']}",
          f"- Workflow {m['workflow']['repository']} commit `{m['workflow']['commit']}`, run {m['workflow']['run']}",
          '', '## Cloned sources', '', '| repository | commit | fixed by pins.lock |', '|---|---|---|']
    L += [f"| {c['url']} | `{c['commit']}` | {'yes' if c['pinned_by_pins_lock'] else 'no'} |"
          for c in m['cloned_sources']]
    L += ['', f"Meson wraps: {', '.join(m['meson_wraps']) or '-'}; cppwinrt: {', '.join(m['cppwinrt']) or '-'}",
          '', '## Libraries linked into libmpv-2.dll', '',
          '| library | licence | class | project | pkg-config | origin |', '|---|---|---|---|---|---|']
    L += [f"| {x['stem']} | {x['licence']} | {x['class']} | {x['project']} | {x['pkgconfig']} | {x['origin']} |"
          for x in m['linked_libraries']]
    L += ['', '## Rust crates inside subrandr', '', '| crate | version | licence | class |', '|---|---|---|---|']
    L += [f"| {c['name']} | {c['version']} | {c['licence']} | {c['class']} |" for c in m['rust_crates_in_subrandr']]
    L += ['', '## mpv dependencies found by meson', '']
    L += [f"- {d['name']} {d['version']}" for d in m['mpv_dependencies']]
    L += ['', '## FFmpeg external libraries', '', ', '.join(m['ffmpeg']['external_libraries']), '',
          '## Image packages not on the link line (present in the toolchain image only)', '',
          ', '.join(m['image_packages_not_linked']), '']
    return '\n'.join(L)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Complete, verifiable source package for an existing libmpv build (first use: b10).

The build itself is not touched. Everything is taken from that build's MANIFEST.json (commits, image, FFmpeg-Builds
revision, the libraries that are really inside the DLL) and fetched again at exactly those versions.

Run inside the build's own (pinned) toolchain image, from any folder:
    python3 tools/make_source_package.py --manifest MANIFEST.json --ffb ffb --repo assma --out out

Output (out/):
  recipe/            mpv and every repository the recipe cloned, at the built commits (clean `git archive`-like
                     trees, no build products), mujs wrap files (hash-checked), cppwinrt archive
  image/             every FFmpeg-Builds stage whose library is inside the DLL, fetched with FFmpeg-Builds' own
                     download commands (all repositories of the stage, including second repositories and submodules)
  scripts/           FFmpeg-Builds at the image revision (scripts.d, patches, util, images, variants, ...) and this
                     repository at the commit that made the build
  rust/              cargo vendor of subrandr's dependencies (Cargo.lock of the built commit)
  toolchain/         licence texts of the mingw-w64 runtime / winpthreads and the GCC runtime exception
  licences/          licence and NOTICE files of every component (all NOTICE files, at any depth)
  lists/             for every git repository: `git ls-files -s` (mode, blob id, path) - lets anyone check, file by file,
                     that the archived source is that commit (verify_sources.py)
  SOURCE-MANIFEST.json, REPORT.md (every automatic check with its result), NOTICE.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

LICENCE_RE = re.compile(r'^(LICEN[CS]E|COPYING|COPYRIGHT|UNLICENSE|PATENTS)', re.I)
NOTICE_RE = re.compile(r'^NOTICE', re.I)
checks: list = []          # (ok: bool|None, text)  None = information / gap


def check(ok, text):
    checks.append((ok, text))
    print(('PASS ' if ok else 'FAIL ' if ok is False else 'NOTE ') + text, flush=True)


def sh(*cmd, cwd=None, check_=True, capture=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    if check_ and r.returncode != 0:
        raise RuntimeError(f'{" ".join(map(str, cmd))} failed ({r.returncode}): {r.stderr[-2000:] if capture else ""}')
    return (r.stdout or '').strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)
    return sha256(dest)


def git_repos(root: Path) -> list:
    """Every git work tree under root (the root itself, nested clones, submodules)."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        if '.git' in dirnames or '.git' in filenames:
            found.append(Path(dirpath))
        if '.git' in dirnames:
            dirnames.remove('.git')
    return sorted(found)


def describe_repo(work: Path, base: Path, lists: Path, label: str) -> dict:
    """Commit, remote, tracked-file list (written to lists/) and what the download step changed or added."""
    rel = work.relative_to(base).as_posix() if work != base else '.'
    head = sh('git', '-C', str(work), 'rev-parse', 'HEAD')
    date = sh('git', '-C', str(work), 'log', '-1', '--format=%cI', check_=False)
    remote = sh('git', '-C', str(work), 'config', '--get', 'remote.origin.url', check_=False)
    sparse = sh('git', '-C', str(work), 'config', '--get', 'core.sparseCheckout', check_=False) == 'true'
    entries = sh('git', '-C', str(work), 'ls-files', '-s').splitlines()
    if sparse:          # only what the sparse checkout really holds
        entries = [e for e in entries if e.startswith('160000') or (work / e.split('\t', 1)[1]).exists()]
    listing = '\n'.join(entries) + '\n'
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', f'{label}__{rel}')
    (lists / f'{name}.lsfiles').write_text(listing, encoding='utf-8')
    status = sh('git', '-C', str(work), 'status', '--porcelain', '--ignored', '--untracked-files=all').splitlines()
    nested = {p.relative_to(work).as_posix() for p in git_repos(work) if p != work}
    changed = [s[3:] for s in status if s[:2].strip() and not s.startswith(('??', '!!'))]
    added = [s[3:] for s in status if s.startswith(('??', '!!'))
             and not any(s[3:].rstrip('/') == n or s[3:].startswith(n + '/') for n in nested)]
    return {'path': rel, 'remote': remote, 'commit': head, 'commit_date': date, 'sparse': sparse,
            'tracked_files': sum(1 for e in entries if not e.startswith('160000')),
            'lsfiles': f'lists/{name}.lsfiles', 'lsfiles_sha256': hashlib.sha256(listing.encode()).hexdigest(),
            'changed_by_download_step': changed, 'added_by_download_step': added}


def pack(src: Path, dest: Path) -> dict:
    """tar.xz of a source tree without VCS folders; returns name, size and SHA-256."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(f"tar -C '{src}' --exclude=.git --exclude=.svn --sort=name --owner=0 --group=0 --numeric-owner "
                   f"--mtime=@0 -cf - . | xz -T0 -6 > '{dest}'", shell=True, check=True)
    return {'archive': dest.as_posix(), 'bytes': dest.stat().st_size, 'sha256': sha256(dest)}


def copy_licences(src: Path, dest: Path, depth: int = 3) -> list:
    copied = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '.svn')]
        rel = Path(dirpath).relative_to(src)
        for f in filenames:
            is_notice = bool(NOTICE_RE.match(f))
            if is_notice or (LICENCE_RE.match(f) and len(rel.parts) <= depth):
                target = dest / rel / f
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(dirpath) / f, target, follow_symlinks=True)
                copied.append((rel / f).as_posix())
    return copied


def fetch_commit(url: str, commit: str, dest: Path, sparse: str | None = None, recursive: bool = True):
    dest.mkdir(parents=True)
    sh('git', 'init', '-q', str(dest))
    sh('git', '-C', str(dest), 'remote', 'add', 'origin', url)
    if sparse:
        sh('git', '-C', str(dest), 'sparse-checkout', 'set', sparse)
        sh('git', '-C', str(dest), 'fetch', '-q', '--depth=1', '--filter=blob:none', 'origin', commit)
    else:
        sh('git', '-C', str(dest), 'fetch', '-q', '--depth=1', 'origin', commit)
    sh('git', '-C', str(dest), '-c', 'advice.detachedHead=false', 'checkout', '-q', 'FETCH_HEAD')
    if recursive and (dest / '.gitmodules').is_file():
        sh('git', '-C', str(dest), 'submodule', 'update', '-q', '--init', '--recursive', '--depth=1')


# ------------------------------------------------------------------------------------------------------------------
def recipe_sources(m: dict, out: Path, work: Path) -> list:
    entries = []
    clones = [{'name': 'mpv', 'url': m['mpv']['repository'], 'commit': m['mpv']['commit'], 'recursive': True}]
    for c in m['cloned_sources']:
        name = os.path.basename(c['folder'])
        clones.append({'name': name, 'url': c['url'], 'commit': c['commit'],
                       'sparse': 'crates/libs/bindgen/default' if name == 'windows-rs' else None,
                       'recursive': name != 'windows-rs'})
    for c in clones:
        dest = work / 'recipe' / c['name']
        fetch_commit(c['url'], c['commit'], dest, c.get('sparse'), c['recursive'])
        repos = [describe_repo(r, dest, out / 'lists', f"recipe_{c['name']}") for r in git_repos(dest)]
        ok = repos[0]['commit'] == c['commit']
        check(ok, f"recipe {c['name']}: archived tree is commit {c['commit'][:12]} (as in b10 MANIFEST)")
        lic = copy_licences(dest, out / 'licences' / 'recipe' / c['name'], 0 if c['name'] == 'mpv' else 3)
        if not lic:
            check(False, f"recipe {c['name']}: no licence file found")
        arch = pack(dest, out / 'recipe' / f"{c['name']}-{c['commit'][:12]}.tar.xz")
        entries.append({'component': c['name'], 'kind': 'git', 'url': c['url'], 'commit': c['commit'],
                        'sparse': c.get('sparse'), 'repositories': repos, **arch,
                        'note': 'sparse checkout, as used by the recipe' if c.get('sparse') else ''})

    # mujs (meson wrap): the wrap file in b10's MANIFEST names the files and their SHA-256
    wrap = m['meson_wraps'].get('mujs.wrap', '')
    fields = dict(re.findall(r'^(\w+)\s*=\s*(.+)$', wrap, flags=re.M))
    for kind in ('source', 'patch'):
        url, name, want = fields.get(f'{kind}_url'), fields.get(f'{kind}_filename'), fields.get(f'{kind}_hash')
        if not url:
            continue
        dest = out / 'recipe' / 'mujs-wrap' / name
        try:
            got = download(url, dest)
        except Exception:
            got = download(fields.get(f'{kind}_fallback_url', url), dest)
        check(got == want, f'mujs wrap {kind} {name}: SHA-256 equals the wrap file of b10 ({want[:12]})')
        entries.append({'component': f'mujs ({kind})', 'kind': 'meson-wrap', 'url': url, 'archive': dest.as_posix(),
                        'bytes': dest.stat().st_size, 'sha256': got, 'expected_sha256': want})
    (out / 'recipe' / 'mujs-wrap' / 'mujs.wrap').write_text(wrap, encoding='utf-8')

    # cppwinrt: the recipe downloads it by version with wget, without a checksum
    for name in m.get('cppwinrt', []):
        version = name.split('-', 1)[1]
        url = f'https://github.com/microsoft/cppwinrt/archive/{version}.tar.gz'
        dest = out / 'recipe' / f'{name}.tar.gz'
        got = download(url, dest)
        check(None, f'cppwinrt {version}: archive SHA-256 {got[:12]} recorded now (b10 did not record one; '
                    f'GitHub release archives are generated and not guaranteed byte-stable)')
        entries.append({'component': name, 'kind': 'tarball', 'url': url, 'archive': dest.as_posix(),
                        'bytes': dest.stat().st_size, 'sha256': got})
    return entries


VERSION_FILES = re.compile(r'^(configure\.ac|configure\.in|meson\.build|CMakeLists\.txt|.*\.pc\.in|version.*|VERSION.*|'
                           r'NEWS.*|ChangeLog.*|.*version.*\.h|Cargo\.toml|package\.json)$', re.I)


def version_in_source(root: Path, version: str) -> str:
    """First build / version file (depth <= 3) that contains the pkg-config version string, or ''."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '.svn', 'test', 'tests')]
        if len(Path(dirpath).relative_to(root).parts) > 3:
            dirnames.clear()
            continue
        for f in filenames:
            if VERSION_FILES.match(f):
                try:
                    if version in (Path(dirpath) / f).read_text(errors='ignore')[:200000]:
                        return (Path(dirpath) / f).relative_to(root).as_posix()
                except OSError:
                    pass
    return ''


def image_sources(m: dict, ffb: Path, out: Path, work: Path) -> list:
    tools = work / 'ffb-tools'
    tools.mkdir(parents=True, exist_ok=True)
    for f, n in (('git-mini-clone.sh', 'git-mini-clone'), ('retry-tool.sh', 'retry-tool')):
        shutil.copy(ffb / 'images' / 'base' / f, tools / n)
        (tools / n).chmod(0o755)
    env = dict(os.environ, PATH=f'{tools}:{os.environ["PATH"]}', TARGET='win64', VARIANT='lgpl')
    rank = {'lgpl': 3, 'mpl': 2}
    stages = {}
    for lib in m['linked_libraries']:
        stage = lib.get('source', '')
        if lib.get('in_dll') and stage[:1].isdigit():
            s = stages.setdefault(stage, {'libraries': [], 'class': 'permissive', 'versions': set()})
            s['libraries'].append(lib['stem'])
            if lib.get('pkgconfig'):
                name, _, ver = lib['pkgconfig'].rpartition(' ')
                if ver and (lib['stem'] in name or name.replace('lib', '') in lib['stem']):
                    s['versions'].add((name, ver))
            if rank.get(lib['class'], 0) > rank.get(s['class'], 0):
                s['class'] = lib['class']
    entries = []
    for stage, info in sorted(stages.items()):
        script = ffb / 'scripts.d' / f'{stage}.sh'
        dl = subprocess.run(['bash', '-c', f"source util/dl_functions.sh; source '{script}'; ffbuild_dockerdl"],
                            cwd=ffb, env=env, capture_output=True, text=True, check=True).stdout
        dest = work / 'image' / stage.replace('/', '_')
        dest.mkdir(parents=True)
        r = subprocess.run(['bash', '-c', 'set -e\n' + dl], cwd=dest, env=env, capture_output=True, text=True)
        if r.returncode:
            check(False, f'image {stage}: download failed: {r.stderr[-400:]}')
            continue
        meta = subprocess.run(['bash', '-c', f"source '{script}'; set | grep -E '^SCRIPT_(REPO|COMMIT|REV|TAG|URL|SHA)[0-9]*='"],
                              cwd=ffb, capture_output=True, text=True).stdout
        declared = dict(re.findall(r"^(SCRIPT_\w+)=['\"]?([^'\"\n]*)", meta, flags=re.M))
        repos = [describe_repo(rp, dest, out / 'lists', f'image_{stage}') for rp in git_repos(dest)]
        svn = []
        for dirpath, dirnames, _ in os.walk(dest):
            if '.svn' in dirnames:
                svn.append({'path': Path(dirpath).relative_to(dest).as_posix() or '.',
                            'url': sh('svn', 'info', '--show-item', 'url', dirpath, check_=False),
                            'revision': sh('svn', 'info', '--show-item', 'revision', dirpath, check_=False),
                            'added_or_changed_by_download_step':
                                sh('svn', 'status', '--no-ignore', dirpath, check_=False).splitlines()})
                dirnames.clear()
        # every declared commit must be the HEAD of one of the fetched repositories (tags resolved by git)
        for key, value in declared.items():
            if key.startswith('SCRIPT_COMMIT'):
                hit = any(rp['commit'] == value for rp in repos) or any(
                    sh('git', '-C', str(dest / rp['path']), 'rev-parse', f'{value}^{{commit}}', check_=False) == rp['commit']
                    for rp in repos)
                check(hit, f'image {stage}: {key} {value[:16]} is the fetched commit')
            if key.startswith('SCRIPT_REV'):
                check(any(s['revision'] == value for s in svn), f'image {stage}: svn revision {value} fetched')
        vchecks = []
        for name, ver in sorted(info['versions']):
            where = version_in_source(dest, ver)
            vchecks.append({'pkgconfig': name, 'version': ver, 'found_in': where})
            check(True if where else None,
                  f'image {stage}: pkg-config {name} {ver} ' + (f'found in {where}' if where else
                  'not found as text in the build files (version set at build time? see download/build commands)'))
        lic = copy_licences(dest, out / 'licences' / 'image' / stage.replace('/', '_'))
        if not any(LICENCE_RE.match(Path(x).name) for x in lic):
            check(False, f'image {stage}: no licence file found')
        arch = pack(dest, out / 'image' / f"{stage.replace('/', '_')}.tar.xz")
        entries.append({'component': stage, 'kind': 'ffmpeg-builds-stage', 'libraries_in_dll': info['libraries'],
                        'class': info['class'], 'declared': declared, 'download_commands': dl.strip(),
                        'repositories': repos, 'svn': svn, 'licence_and_notice_files': lic,
                        'version_checks': vchecks, **arch})
        shutil.rmtree(dest)
    return entries


def script_sources(m: dict, ffb: Path, repo: Path, out: Path) -> list:
    entries = []
    rev = m['toolchain_image']['ffmpeg_builds_revision']
    for name, path, commit in (('ffmpeg-builds', ffb, rev),
                               ('assma-libmpv-lgpl', repo, m['workflow']['commit'])):
        head = sh('git', '-C', str(path), 'rev-parse', 'HEAD')
        check(head == commit, f'scripts {name}: checkout is {commit[:12]}')
        dest = out / 'scripts' / f'{name}-{commit[:12]}.tar.xz'
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(f"git -C '{path}' archive --format=tar {commit} | xz -T0 -6 > '{dest}'", shell=True, check=True)
        listing = sh('git', '-C', str(path), 'ls-files', '-s') + '\n'
        (out / 'lists' / f'scripts__{name}.lsfiles').write_text(listing)
        entries.append({'component': name, 'kind': 'git', 'url': sh('git', '-C', str(path), 'config', '--get',
                                                                       'remote.origin.url', check_=False),
                        'commit': commit, 'archive': dest.as_posix(), 'bytes': dest.stat().st_size,
                        'sha256': sha256(dest), 'lsfiles': f'lists/scripts__{name}.lsfiles',
                        'lsfiles_sha256': hashlib.sha256(listing.encode()).hexdigest()})
    return entries


def rust_sources(out: Path, work: Path) -> list:
    sub = work / 'recipe' / 'subrandr'
    lock = sub / 'Cargo.lock'
    vendor = work / 'rust-vendor'
    r = subprocess.run(['cargo', 'vendor', '--locked', '--versioned-dirs', '--manifest-path', str(sub / 'Cargo.toml'),
                        str(vendor)], capture_output=True, text=True)
    if r.returncode:
        check(False, f'rust: cargo vendor failed: {r.stderr[-400:]}')
        return []
    check(True, f'rust: cargo vendor --locked with subrandr Cargo.lock (sha256 {sha256(lock)[:12]})')
    copy_licences(vendor, out / 'licences' / 'rust', 1)
    arch = pack(vendor, out / 'rust' / 'subrandr-vendored-crates.tar.xz')
    crates = sorted(p.name for p in vendor.iterdir() if p.is_dir())
    return [{'component': 'subrandr Rust dependencies', 'kind': 'cargo-vendor', 'cargo_lock_sha256': sha256(lock),
             'crates': crates, **arch}]


def toolchain_licences(out: Path, work: Path) -> list:
    entries = []
    cc = os.environ.get('CC', 'x86_64-w64-mingw32-gcc')
    gcc_version = sh(cc, '-dumpfullversion', check_=False) or sh(cc, '-dumpversion', check_=False)
    header = sh(cc, '-print-sysroot', check_=False)
    mac = next(Path(header or '/').rglob('_mingw_mac.h'), None)
    mingw_version = ''
    if mac:
        t = mac.read_text(errors='replace')
        parts = [re.search(rf'#define __MINGW64_VERSION_{k}\s+(\d+)', t) for k in ('MAJOR', 'MINOR', 'BUGFIX')]
        if all(parts):
            mingw_version = '.'.join(p.group(1) for p in parts)
        rev = re.search(r'#define __MINGW64_VERSION_STATE\s+"(\w+)"', t)
        if rev:
            mingw_version += f' ({rev.group(1)})'
    check(bool(mingw_version), f'toolchain: mingw-w64 headers say version {mingw_version or "?"}; GCC {gcc_version}')
    jobs = []
    if mingw_version:
        v = mingw_version.split(' ')[0]
        tag = f'v{v}'
        jobs.append(('mingw-w64', 'https://github.com/mingw-w64/mingw-w64.git', f'refs/tags/{tag}',
                     ['COPYING', 'DISCLAIMER', 'DISCLAIMER.PD', 'COPYING.MinGW-w64', 'COPYING.MinGW-w64-runtime',
                      'mingw-w64-crt', 'mingw-w64-libraries/winpthreads', 'mingw-w64-headers']))
    if gcc_version:
        jobs.append(('gcc', 'https://github.com/gcc-mirror/gcc.git', f'refs/tags/releases/gcc-{gcc_version}',
                     ['COPYING.RUNTIME', 'COPYING3', 'COPYING3.LIB', 'COPYING.LIB', 'COPYING']))
    for name, url, ref, paths in jobs:
        dest = work / 'toolchain' / name
        dest.mkdir(parents=True)
        sh('git', 'init', '-q', str(dest))
        sh('git', '-C', str(dest), 'remote', 'add', 'origin', url)
        r = subprocess.run(['git', '-C', str(dest), 'fetch', '-q', '--depth=1', '--filter=blob:none', 'origin', ref],
                           capture_output=True, text=True)
        if r.returncode:
            check(False, f'toolchain {name}: {ref} not found ({r.stderr.strip()[-200:]}) - licence texts missing')
            continue
        commit = sh('git', '-C', str(dest), 'rev-parse', 'FETCH_HEAD')
        files = [p for p in sh('git', '-C', str(dest), 'ls-tree', '-r', '--name-only', 'FETCH_HEAD').splitlines()
                 if any(p == x or p.startswith(x + '/') for x in paths) and LICENCE_RE.match(Path(p).name)
                 or p in paths]
        target = out / 'toolchain' / name
        for p in files:
            data = subprocess.run(['git', '-C', str(dest), 'show', f'FETCH_HEAD:{p}'], capture_output=True).stdout
            (target / p).parent.mkdir(parents=True, exist_ok=True)
            (target / p).write_bytes(data)
        check(bool(files), f'toolchain {name}: {len(files)} licence files from {ref} ({commit[:12]})')
        entries.append({'component': name, 'kind': 'licence-texts', 'url': url, 'ref': ref, 'commit': commit,
                        'files': files})
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--ffb', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--work', default='/tmp/srcwork')
    a = ap.parse_args()
    manifest_path = Path(a.manifest).resolve()
    m = json.loads(manifest_path.read_text())
    out, work, ffb, repo = Path(a.out).resolve(), Path(a.work).resolve(), Path(a.ffb).resolve(), Path(a.repo).resolve()
    for p in (out / 'lists', work):
        p.mkdir(parents=True, exist_ok=True)
    os.chdir(out)                      # every path written to the manifest is relative to the package folder
    out = Path('.')
    sm = {'for_build': m['name'], 'for_build_manifest_sha256': sha256(manifest_path),
          'dll_sha256': next((f['sha256'] for f in m['files'] if f['file'] == 'libmpv-2.dll'), ''),
          'made_by': {'repository': os.environ.get('GITHUB_REPOSITORY', ''), 'commit': os.environ.get('GITHUB_SHA', ''),
                      'run': f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}"
                             f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                      'image': os.environ.get('IMAGE', '')}}
    sm['scripts'] = script_sources(m, ffb, repo, out)
    sm['recipe'] = recipe_sources(m, out, work)
    sm['image'] = image_sources(m, ffb, out, work)
    sm['rust'] = rust_sources(out, work)
    sm['toolchain'] = toolchain_licences(out, work)
    covered = {e['component'] for e in sm['image']}
    for lib in m['linked_libraries']:
        if lib.get('in_dll') and lib['class'] in ('lgpl', 'mpl'):
            src = lib.get('source', '')
            ok = src in covered or (src.startswith('mpv:') and any(
                e['component'] == src[4:] or (src == 'mpv:subprojects' and e['component'].startswith('mujs'))
                for e in sm['recipe']))
            check(ok, f"copyleft {lib['stem']} ({lib['class']}, {src}): source in this package")
    changed = [(e['component'], r['path'], len(r['changed_by_download_step']), len(r['added_by_download_step']))
               for e in sm['image'] for r in e['repositories']
               if r['changed_by_download_step'] or r['added_by_download_step']]
    for comp, path, n_changed, n_added in changed:
        check(None, f'image {comp} ({path}): download step changed {n_changed} and added {n_added} files '
                    f'(listed in SOURCE-MANIFEST; e.g. autoreconf / autogen output)')
    sm['checks'] = [{'result': 'pass' if ok else 'fail' if ok is False else 'note', 'text': t} for ok, t in checks]
    (out / 'SOURCE-MANIFEST.json').write_text(json.dumps(sm, indent=2, ensure_ascii=False) + '\n')
    fails = sum(1 for ok, _ in checks if ok is False)
    report = [f"# Source package for {m['name']} - automatic checks", '',
              f"Pass: {sum(1 for ok, _ in checks if ok)} · Fail: {fails} · Notes: {sum(1 for ok, _ in checks if ok is None)}",
              '']
    report += [f"- {'PASS' if ok else 'FAIL' if ok is False else 'NOTE'} {t}" for ok, t in checks]
    (out / 'REPORT.md').write_text('\n'.join(report) + '\n')
    print(f'{fails} failed checks')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

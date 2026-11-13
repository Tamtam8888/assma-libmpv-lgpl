#!/usr/bin/env python3
"""Check a libmpv source package (made by make_source_package.py). Needs Python 3.8+; --deep also needs git.

    python verify_sources.py <folder with SOURCE-MANIFEST.json and the archives> [--deep]

1. Every archive has the SHA-256 written in SOURCE-MANIFEST.json.
2. Every git repository inside the archives holds, file by file, exactly the content of its commit: each tracked
   file's git blob id (computed here from the archived file) equals the one in lists/*.lsfiles, and each list file
   has the SHA-256 written in the manifest.
3. --deep: each list file equals `git ls-files -s` of that commit fetched again from its public repository, so the
   lists themselves are not taken on trust.
Files that a download step added or changed (for example autoreconf output) are named in the manifest and are not
part of the comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def blob_id(path: Path) -> str:
    data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def check_tree(root: Path, listing: str, changed: set) -> list:
    problems = []
    for line in listing.splitlines():
        meta, _, rel = line.partition('\t')
        mode, blob, _stage = meta.split()
        if mode == '160000' or rel in changed:
            continue
        p = root / rel
        if not (p.exists() or p.is_symlink()):
            problems.append(f'missing {rel}')
        elif blob_id(p) != blob:
            problems.append(f'differs {rel}')
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--deep', action='store_true')
    a = ap.parse_args()
    base = Path(a.folder)
    sm = json.loads((base / 'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
    failures = 0
    for group in ('scripts', 'recipe', 'image', 'rust'):
        for e in sm.get(group, []):
            if 'archive' not in e:
                continue
            arch = base / e['archive']
            ok = arch.is_file() and sha256(arch) == e['sha256']
            print(('ok    ' if ok else 'FAIL  ') + f"{group}: {e['archive']} SHA-256")
            failures += not ok
            repos = e.get('repositories') or ([{'path': '.', 'commit': e['commit'], 'remote': e['url'],
                                                'lsfiles': e['lsfiles'], 'lsfiles_sha256': e['lsfiles_sha256'],
                                                'changed_by_download_step': []}] if e.get('lsfiles') else [])
            if not ok or not repos:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                with tarfile.open(arch) as t:
                    t.extractall(tmp, filter='tar') if sys.version_info >= (3, 12) else t.extractall(tmp)
                for r in repos:
                    listing = (base / r['lsfiles']).read_text(encoding='utf-8')
                    if hashlib.sha256(listing.encode()).hexdigest() != r['lsfiles_sha256']:
                        print(f"FAIL  {group}: {r['lsfiles']} does not match the manifest")
                        failures += 1
                        continue
                    problems = check_tree(Path(tmp) / r['path'], listing, set(r.get('changed_by_download_step', [])))
                    print(('ok    ' if not problems else 'FAIL  ') +
                          f"{group}: {e.get('component')} {r['path']} = commit {r['commit'][:12]}"
                          + (f" ({len(problems)} problems, first: {problems[:3]})" if problems else ''))
                    failures += bool(problems)
                    if a.deep and r.get('remote'):
                        with tempfile.TemporaryDirectory() as g:
                            run = lambda *c: subprocess.run(['git', '-C', g, *c], capture_output=True, text=True)
                            run('init', '-q'); run('remote', 'add', 'origin', r['remote'])
                            f = run('fetch', '-q', '--depth=1', '--filter=blob:none', 'origin', r['commit'])
                            run('read-tree', 'FETCH_HEAD')
                            remote_list = run('ls-files', '-s').stdout
                            own = set(listing.splitlines())
                            same = f.returncode == 0 and own <= set(remote_list.splitlines())
                            print(('ok    ' if same else 'FAIL  ') +
                                  f"deep: {r['remote']} {r['commit'][:12]} lists the same files")
                            failures += not same
    print(f'\n{failures} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

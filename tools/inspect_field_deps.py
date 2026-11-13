"""Read-only inspection of the third-party binaries the ASSMA field package carries (run on a Windows runner).
Prints, per wheel / archive: every DLL and .pyd, FFmpeg DLLs with their embedded configuration and licence strings,
Qt multimedia plugins and what they import, licence files shipped. Nothing is installed into ASSMA."""
import glob, os, re, sys, zipfile
import pefile

root = sys.argv[1]
def strings_with(path, needles):
    data = open(path, 'rb').read()
    out = set()
    for m in re.finditer(rb'[\x20-\x7e]{12,}', data):
        s = m.group().decode('ascii', 'replace')
        if any(n in s for n in needles):
            out.add(s[:600])
    return sorted(out)

for archive in sorted(glob.glob(os.path.join(root, '*.whl')) + glob.glob(os.path.join(root, '*.zip'))):
    name = os.path.basename(archive)
    dest = os.path.join(root, 'x', name)
    zipfile.ZipFile(archive).extractall(dest)
    print(f'\n######## {name} ({os.path.getsize(archive)} bytes)')
    bins = [p for p in glob.glob(dest + '/**/*', recursive=True) if p.lower().endswith(('.dll', '.pyd', '.exe'))]
    print(f'binaries: {len(bins)}')
    for p in sorted(bins):
        rel = os.path.relpath(p, dest)
        line = f'  BIN {rel} {os.path.getsize(p)}'
        low = os.path.basename(p).lower()
        if re.match(r'(avcodec|avformat|avutil|swresample|swscale|avfilter|avdevice|postproc)', low) or 'ffmpeg' in low or 'mpv' in low:
            line += '  <== FFmpeg/mpv'
        print(line)
        if re.match(r'(avcodec|avformat|avutil|swresample|swscale|avfilter|avdevice)', low) or 'ffmpegmediaplugin' in low:
            for s in strings_with(p, ['--prefix', '--enable-', 'LGPL', 'GPL version', 'FFmpeg version', 'license']):
                print(f'    STR {s}')
        if 'multimedia' in rel.lower() or 'ffmpeg' in low:
            try:
                pe = pefile.PE(p, fast_load=True)
                pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
                imps = [e.dll.decode() for e in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])]
                print(f'    IMPORTS {", ".join(imps)}')
            except Exception as e:
                print(f'    IMPORTS ? {e}')
    lic = [os.path.relpath(p, dest) for p in glob.glob(dest + '/**/*', recursive=True)
           if re.search(r'(LICEN[CS]E|COPYING|NOTICE|THIRD|ThirdParty|licenses)', os.path.basename(p), re.I)]
    for meta in glob.glob(dest + '/*.dist-info/METADATA'):
        for line in open(meta, encoding='utf-8', errors='replace'):
            if line.startswith(('License', 'Classifier: License')):
                print(f'  META {line.strip()[:300]}')
    for p in glob.glob(dest + '/**/*', recursive=True):
        b = os.path.basename(p)
        if os.path.isfile(p) and re.match(r'(LICEN[CS]E|COPYING)', b, re.I) and ('dist-info' in p or os.path.dirname(p).count(os.sep) <= dest.count(os.sep) + 1):
            text = open(p, encoding='utf-8', errors='replace').read()
            heads = [l.strip() for l in text.splitlines() if l.strip()][:3]
            marks = [k for k in ('OpenSSL', 'libffi', 'SQLite', 'bzip2', 'xz', 'Expat', 'zlib', 'Tcl', 'mpdecimal', 'GNU LESSER', 'GNU GENERAL', 'Version 3', 'version 2.1') if k in text]
            print(f'  LICHEAD {os.path.relpath(p, dest)} :: {" | ".join(heads)[:250]} :: mentions {marks}')
    print(f'licence files: {len(lic)}')
    for l in sorted(lic)[:80]:
        print(f'  LIC {l}')

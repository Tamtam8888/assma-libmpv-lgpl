#!/usr/bin/env bash
# Sources and licence texts of the libraries that came from the FFmpeg-Builds toolchain image.
#
# Why: libmpv-2.dll is a static build, so libraries from the image (libbluray, fribidi, libiconv, ...) are inside
# the DLL. LGPL / MPL require their exact source to be offered with the binary; BSD / MIT / Apache require their
# licence text to travel with it. The image does not keep sources, but FFmpeg-Builds fixes every library to one
# commit in scripts.d (SCRIPT_REPO / SCRIPT_COMMIT). This script downloads each linked library exactly the way
# FFmpeg-Builds itself does (its own ffbuild_dockerdl commands and helper tools), then
#   - copies the licence files of every linked library to licences/<stage>/
#   - archives the full source of every LGPL / MPL library to sources/<stage>.tar.xz
#   - writes image-sources.tsv (stage, repository, commit, class) for the manifest.
#
# Usage: collect_image_sources.sh <FFmpeg-Builds checkout> <MANIFEST.json> <out dir>
set -euo pipefail
FFB="$(realpath "$1")"; MANIFEST="$(realpath "$2")"; OUT="$(realpath -m "$3")"
mkdir -p "$OUT/licences" "$OUT/sources" "$OUT/bin"
cp "$FFB/images/base/git-mini-clone.sh" "$OUT/bin/git-mini-clone"
cp "$FFB/images/base/retry-tool.sh" "$OUT/bin/retry-tool"
chmod +x "$OUT/bin/"*
export PATH="$OUT/bin:$PATH"

# stage <tab> class, one line per FFmpeg-Builds stage that has a linked library
python3 - "$MANIFEST" > "$OUT/stages.tsv" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
rank = {'permissive': 0, 'runtime': 0, 'system': 0, 'mpl': 1, 'lgpl': 2}
stages = {}
for lib in m['linked_libraries']:
    stage = lib.get('source', '-')
    if stage and stage[0].isdigit():
        c = lib['class']
        if stage not in stages or rank.get(c, 3) > rank.get(stages[stage], 3):
            stages[stage] = c
for s, c in sorted(stages.items()):
    print(f'{s}\t{c}')
PY
cat "$OUT/stages.tsv"

printf 'stage\trepository\tcommit\tclass\tsource archived\n' > "$OUT/image-sources.tsv"
while IFS=$'\t' read -r stage class; do
    script="$FFB/scripts.d/$stage.sh"
    [ -f "$script" ] || { echo "missing stage script $script" >&2; exit 1; }
    work="$(mktemp -d)"
    # the download commands, exactly as FFmpeg-Builds generates them
    dl="$(cd "$FFB" && TARGET=win64 VARIANT=lgpl bash -c "source util/dl_functions.sh; source '$script'; ffbuild_dockerdl")"
    meta="$(cd "$FFB" && bash -c "source '$script'; echo \"\${SCRIPT_REPO:-}\"; echo \"\${SCRIPT_COMMIT:-\${SCRIPT_REV:-\${SCRIPT_TAG:-}}}\"")"
    repo="$(sed -n 1p <<<"$meta")"; commit="$(sed -n 2p <<<"$meta")"
    echo "== $stage ($class): $repo @ $commit"
    (cd "$work" && eval "set -e; $dl") > "$OUT/dl-$(tr / _ <<<"$stage").log" 2>&1 \
        || { echo "download failed for $stage"; tail -20 "$OUT/dl-$(tr / _ <<<"$stage").log"; exit 1; }
    name="$(tr / _ <<<"$stage")"
    mkdir -p "$OUT/licences/$name"
    find "$work" -maxdepth 3 -type f \( -iname 'LICEN[CS]E*' -o -iname 'COPYING*' -o -iname 'COPYRIGHT*' \
        -o -iname 'NOTICE*' -o -iname 'PATENTS*' \) -not -path '*/.git/*' -print0 |
        while IFS= read -r -d '' f; do
            rel="${f#"$work"/}"; mkdir -p "$OUT/licences/$name/$(dirname "$rel")"; cp "$f" "$OUT/licences/$name/$rel"
        done
    [ -n "$(ls -A "$OUT/licences/$name")" ] || { echo "no licence file found for $stage" >&2; exit 1; }
    archived=no
    if [ "$class" = lgpl ] || [ "$class" = mpl ]; then
        tar -C "$work" --exclude=.git --exclude=.svn -cJf "$OUT/sources/$name.tar.xz" .
        archived=yes
    fi
    printf '%s\t%s\t%s\t%s\t%s\n' "$stage" "$repo" "$commit" "$class" "$archived" >> "$OUT/image-sources.tsv"
    rm -rf "$work"
done < "$OUT/stages.tsv"
rm -rf "$OUT/bin"
cat "$OUT/image-sources.tsv"

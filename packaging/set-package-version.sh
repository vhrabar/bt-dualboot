#!/usr/bin/env bash

# Render the packaging files for a version, so the distro packaging never has
# to be edited by hand:

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

version="${1:-}"
if [ -z "$version" ]; then
    version="$(python3 -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("'"$root"'/pyproject.toml").read_text())["project"]["version"])')"
fi
case "$version" in
    [0-9]*) ;;
    *) echo "::error::version must start with a digit, got '$version'" >&2; exit 1 ;;
esac

changelog="$root/packaging/debian/changelog"
spec="$root/packaging/copr/bt-dualboot-sync.spec"
pkgbuild="$root/packaging/aur/PKGBUILD"
srcinfo="$root/packaging/aur/.SRCINFO"
manpage="$root/packaging/bt-dualboot.1"
changelog_md="$root/CHANGELOG.md"

msg="${CHANGELOG_MSG:-New upstream release ${version}.}"
name="${DEBFULLNAME:-Vedran Hrabar}"
mail="${DEBEMAIL:-vedran.hrabar@outlook.com}"

# Render the CHANGELOG.md section for $1 in style $2 (deb|rpm).
render_changelog() {
    local want=$1 style=$2 out
    [ -f "$changelog_md" ] || return 1
    out="$(awk -v want="$want" -v style="$style" '
        # Version token out of a "## [1.2.3] - date" / "## 1.2.3" heading.
        function hdrver(s,   i) {
            sub(/^##[ \t]+/, "", s)
            if (substr(s, 1, 1) == "[") {
                s = substr(s, 2)
                i = index(s, "]")
                if (i > 0) s = substr(s, 1, i - 1)
            } else {
                i = index(s, " ")
                if (i > 0) s = substr(s, 1, i - 1)
            }
            return s
        }
        # Greedy wrap so generated entries stay inside 76 columns.
        function wrap(prefix, cont, text,   words, n, i, line, started) {
            n = split(text, words, /[ \t]+/)
            started = 0
            for (i = 1; i <= n; i++) {
                if (!started)                                    { line = prefix words[i]; started = 1 }
                else if (length(line) + 1 + length(words[i]) <= 76) { line = line " " words[i] }
                else                                             { print line; line = cont words[i] }
            }
            if (started) print line
        }
        function flush(   text) {
            if (buf == "") return
            if (style == "deb") {
                if (group != "") {
                    # trailing colon: lintian flags a bullet of five characters
                    # or fewer as too terse unless it ends in one
                    if (group != shown) { print "  * " group ":"; shown = group }
                    wrap("    - ", "      ", buf)
                } else {
                    wrap("  * ", "    ", buf)
                }
            } else {
                text = (group != "") ? group ": " buf : buf
                wrap("- ", "  ", text)
            }
            buf = ""
        }
        /^## /   { flush(); insec = (hdrver($0) == want); group = ""; shown = ""; next }
        !insec   { next }
        /^### /  { flush(); group = $0; sub(/^###[ \t]+/, "", group); next }
        /^[ \t]*$/                { flush(); next }
        /^[ \t]*[-*][ \t]+/       { flush(); buf = $0; sub(/^[ \t]*[-*][ \t]+/, "", buf); next }
        # Link reference definitions - "[0.1.0]: https://..." - sit at the end
        # of the file, inside the last section. They are markup, not content.
        /^\[[^][]+\]:[ \t]/     { flush(); next }
        # Anything else continues the current bullet, or starts a bare one.
        {
            line = $0; sub(/^[ \t]+/, "", line)
            buf = (buf == "") ? line : buf " " line
        }
        END { flush() }
    ' "$changelog_md")"
    [ -n "$out" ] || return 1
    printf '%s\n' "$out"
}

# Date for $version, taken from its "## [X.Y.Z] - YYYY-MM-DD" heading so the
# generated entries are identical in CI, on COPR and locally. Nothing is
# committed back, so a clock-derived date would make every build differ.
entry_date() {
    local want=$1 fmt=$2 d
    d="$(awk -v want="$want" '
        $0 ~ "^##[ \t]+\\[?" want "\\]?([ \t]|$)" {
            if (match($0, /[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/))
                print substr($0, RSTART, RLENGTH)
            exit
        }' "$changelog_md")"
    if [ -z "$d" ]; then
        echo "::warning::CHANGELOG.md [$want] has no date; using today's, so this build is not reproducible." >&2
        d="$(date -u +%F)"
    fi
    LC_ALL=C date -u -d "$d 00:00:00" "+$fmt"
}

# Every released version heading in CHANGELOG.md, in file order (newest first).
list_versions() {
    awk '
        /^## / {
            s = $0
            sub(/^##[ \t]+/, "", s)
            if (substr(s, 1, 1) == "[") {
                s = substr(s, 2)
                i = index(s, "]")
                if (i > 0) s = substr(s, 1, i - 1)
            } else {
                i = index(s, " ")
                if (i > 0) s = substr(s, 1, i - 1)
            }
            if (s ~ /^[0-9]/) print s
        }' "$changelog_md"
}

# The release workflow promotes [Unreleased] before tagging, so a released tree
# has a [$version] section. Before that - a local dry run - fall back to
# [Unreleased] so the rendered entry still shows the real notes.
section="$version"
if ! render_changelog "$version" deb >/dev/null 2>&1; then
    if render_changelog Unreleased deb >/dev/null 2>&1; then
        echo "::warning::CHANGELOG.md has no [$version] section yet; rendering [Unreleased]"
        section="Unreleased"
    fi
fi

if deb_body="$(render_changelog "$section" deb)" \
   && rpm_body="$(render_changelog "$section" rpm)"; then
    echo "CHANGELOG.md: using the [$section] section"
else
    echo "::warning::CHANGELOG.md has no [$version] section and no [Unreleased] content; falling back to '$msg'"
    deb_body="  * ${msg}"
    rpm_body="- ${msg}"
fi

# --- debian ---------------------------------------------------------------
#
# debian/changelog is not kept in git: it is rendered in full, one entry per
# released CHANGELOG.md section, so the packaged changelog always matches the
# project's and no entry is ever written by hand.

deb_entry() {
    local v=$1 body=$2
    printf 'bt-dualboot-sync (%s-1) unstable; urgency=medium\n\n' "$v"
    printf '%s\n\n' "$body"
    printf ' -- %s <%s>  %s\n' "$name" "$mail" \
        "$(entry_date "$v" '%a, %d %b %Y %H:%M:%S +0000')"
}

tmp="$(mktemp)"
entries=0

# Before the release workflow promotes [Unreleased] there is no [$version]
# section, so lead with one rendered from [Unreleased].
if [ "$section" = "Unreleased" ]; then
    deb_entry "$version" "$deb_body" > "$tmp"
    entries=1
fi

while read -r v; do
    [ -n "$v" ] || continue
    body="$(render_changelog "$v" deb)" || continue
    [ "$entries" -gt 0 ] && printf '\n' >> "$tmp"
    deb_entry "$v" "$body" >> "$tmp"
    entries=$((entries + 1))
done <<EOF
$(list_versions)
EOF

if [ "$entries" -eq 0 ]; then
    deb_entry "$version" "$deb_body" > "$tmp"
    entries=1
fi

mkdir -p "$(dirname "$changelog")"
mv "$tmp" "$changelog"
chmod 0644 "$changelog"   # mktemp makes 0600, and mv carries it over
echo "debian/changelog: rendered $entries entr$([ "$entries" -eq 1 ] && echo y || echo ies), newest $version"

# The override only applies while the changelog has a single entry; keeping it
# afterwards would trade initial-upload-closes-no-bugs for unused-override.
overrides="$root/packaging/debian/bt-dualboot-sync.lintian-overrides"
if [ "$entries" -eq 1 ]; then
    cat > "$overrides" <<'OVERRIDES'
# Uploaded to a Launchpad PPA rather than to the Debian archive, so there is no
# ITP bug for this first upload to close. Generated by set-package-version.sh,
# which removes it once the changelog has more than one entry.
bt-dualboot-sync: initial-upload-closes-no-bugs
OVERRIDES
    echo "debian/*.lintian-overrides: written (single-entry changelog)"
else
    rm -f "$overrides"
    echo "debian/*.lintian-overrides: removed (changelog has $entries entries)"
fi

# --- rpm ------------------------------------------------------------------
#
# Everything below %changelog is rewritten from CHANGELOG.md, the same way
# debian/changelog is, so the spec in git holds packaging logic only and never
# a hand-written entry. Rewriting rather than prepending keeps this idempotent.

sed -i -E "s/^(%\{!\?pkg_version:%global pkg_version )[^}]*(\})/\1${version}\2/" "$spec"
grep -q "pkg_version ${version}}" "$spec" \
    || { echo "::error::failed to set pkg_version in $spec" >&2; exit 1; }

rpm_entry() {
    local v=$1 body=$2
    printf '* %s %s <%s> - %s-1\n' \
        "$(entry_date "$v" '%a %b %d %Y')" "$name" "$mail" "$v"
    printf '%s\n' "$body"
}

tmp="$(mktemp)"
# the spec up to and including the %changelog marker
awk '/^%changelog$/ { print; exit } { print }' "$spec" > "$tmp"
grep -q '^%changelog$' "$tmp" || printf '\n%%changelog\n' >> "$tmp"

rpm_entries=0
if [ "$section" = "Unreleased" ]; then
    rpm_entry "$version" "$rpm_body" >> "$tmp"
    rpm_entries=1
fi

while read -r v; do
    [ -n "$v" ] || continue
    body="$(render_changelog "$v" rpm)" || continue
    [ "$rpm_entries" -gt 0 ] && printf '\n' >> "$tmp"
    rpm_entry "$v" "$body" >> "$tmp"
    rpm_entries=$((rpm_entries + 1))
done <<EOF
$(list_versions)
EOF

if [ "$rpm_entries" -eq 0 ]; then
    rpm_entry "$version" "$rpm_body" >> "$tmp"
    rpm_entries=1
fi

mv "$tmp" "$spec"
chmod 0644 "$spec"   # mktemp makes 0600, and mv carries it over
echo "rpm spec: pkg_version -> $version, %changelog rendered ($rpm_entries)"

# --- arch -----------------------------------------------------------------

sed -i -E "s/^pkgver=.*/pkgver=${version}/" "$pkgbuild"
sed -i -E "s/^pkgrel=.*/pkgrel=1/" "$pkgbuild"
sed -i -E "s/^([[:space:]]*pkgver = ).*/\1${version}/" "$srcinfo"
sed -i -E "s/^([[:space:]]*pkgrel = ).*/\11/" "$srcinfo"
sed -i -E "s#^([[:space:]]*source = ).*#\1bt-dualboot-sync-${version}.tar.gz::https://github.com/vhrabar/bt-dualboot/archive/v${version}.tar.gz#" "$srcinfo"

if [ -n "${SRC_SHA256:-}" ]; then
    sed -i -E "0,/^sha256sums=\('[^']*'/s//sha256sums=('${SRC_SHA256}'/" "$pkgbuild"
    grep -q "sha256sums=('${SRC_SHA256}'" "$pkgbuild" \
        || { echo "::error::failed to set sha256sums[0] in $pkgbuild" >&2; exit 1; }
    sed -i -E "s/^([[:space:]]*sha256sums = ).*/\1${SRC_SHA256}/" "$srcinfo"
    echo "PKGBUILD/.SRCINFO: pkgver -> $version, sha256sums[0] -> $SRC_SHA256"
else
    echo "PKGBUILD/.SRCINFO: pkgver -> $version (sha256sums left untouched)"
fi

# --- man page -------------------------------------------------------------

sed -i -E "s/^(\.TH BT\\\\-DUALBOOT 1 )\"[^\"]*\"( \")[^\"]*(\".*)/\1\"$(entry_date "$version" '%Y-%m-%d' | sed 's/-/\\\\-/g')\"\2bt\\\\-dualboot\\\\-sync ${version}\3/" "$manpage"
echo "man page: .TH -> ${version}"

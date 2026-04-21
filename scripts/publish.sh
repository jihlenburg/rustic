#!/usr/bin/env bash
# Publish rust-tutorial.html to a static-hosting directory.
#
# Fetches the tutorial from GitHub, atomically writes it as index.html in the
# target directory, and (optionally) vendors the Prism + Google Fonts assets so
# the page no longer reaches out to third-party CDNs at runtime.
#
# Usage:
#   ./publish.sh                                 # writes ./public/index.html from main
#   ./publish.sh /var/www/rust-tutorial          # custom target directory
#   ./publish.sh --ref v1.2.3 /var/www/...       # pin to a tag/branch/commit
#   ./publish.sh --vendor-prism /var/www/...     # also mirror Prism assets locally
#   ./publish.sh --vendor-fonts /var/www/...     # also mirror Fraunces woff2 locally
#   ./publish.sh --all /var/www/...              # vendor everything (recommended for prod)
#
# Safe to run from cron — atomic swap, idempotent, exits non-zero on failure.

set -euo pipefail

REPO="jihlenburg/rustic"
FILE="rust-tutorial.html"
REF="main"
TARGET="./public"
VENDOR_PRISM=0
VENDOR_FONTS=0
WRITE_HEADERS=1
UA="Mozilla/5.0 (publish.sh; +https://github.com/${REPO})"

die()  { printf 'publish.sh: error: %s\n' "$*" >&2; exit 1; }
note() { printf 'publish.sh: %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref)            REF="${2:?--ref needs a value}"; shift 2 ;;
    --vendor-prism)   VENDOR_PRISM=1; shift ;;
    --vendor-fonts)   VENDOR_FONTS=1; shift ;;
    --all)            VENDOR_PRISM=1; VENDOR_FONTS=1; shift ;;
    --no-headers)     WRITE_HEADERS=0; shift ;;
    -h|--help)        sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --)               shift; TARGET="${1:-$TARGET}"; shift || true ;;
    -*)               die "unknown flag: $1" ;;
    *)                TARGET="$1"; shift ;;
  esac
done

command -v curl >/dev/null 2>&1 || die "curl is required"

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"
note "target directory: $TARGET"
note "source: github.com/${REPO}@${REF}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

RAW_URL="https://raw.githubusercontent.com/${REPO}/${REF}/${FILE}"
TMP_HTML="$TMPDIR/index.html"

note "fetching $FILE …"
curl --fail --silent --show-error --location \
     --retry 3 --retry-delay 2 --max-time 60 \
     --user-agent "$UA" \
     --output "$TMP_HTML" "$RAW_URL" \
  || die "download failed: $RAW_URL"

# Sanity checks: a half-truncated or 404'd HTML must not be published.
SIZE=$(wc -c < "$TMP_HTML" | tr -d ' ')
[[ "$SIZE" -gt 500000 ]] || die "downloaded file suspiciously small (${SIZE} bytes)"
grep -q '<title>' "$TMP_HTML" || die "no <title> tag — not the expected HTML"
grep -q 'rust-tutorial\|fedit-tut-' "$TMP_HTML" \
  || die "missing tutorial sentinel — wrong file?"
note "downloaded ${SIZE} bytes, sanity checks passed"

# ─── optional: vendor Prism CSS + JS ─────────────────────────────────────────
if [[ "$VENDOR_PRISM" -eq 1 ]]; then
  note "vendoring Prism assets …"
  PRISM_DIR="$TMPDIR/vendor/prism"
  mkdir -p "$PRISM_DIR"
  PRISM_BASE="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0"
  PRISM_FILES=(
    "themes/prism-tomorrow.min.css"
    "prism.min.js"
    "components/prism-rust.min.js"
    "components/prism-toml.min.js"
    "components/prism-json.min.js"
    "components/prism-javascript.min.js"
    "components/prism-bash.min.js"
    "components/prism-diff.min.js"
  )
  for f in "${PRISM_FILES[@]}"; do
    out="$PRISM_DIR/$(basename "$f")"
    curl --fail --silent --show-error --location --retry 3 --max-time 30 \
         --user-agent "$UA" --output "$out" "$PRISM_BASE/$f" \
      || die "Prism fetch failed: $f"
  done

  # Rewrite all cdnjs Prism URLs to local vendor paths.
  python3 - "$TMP_HTML" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
src = p.read_text()
base = re.escape("https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/")
# /themes/foo.min.css → vendor/prism/foo.min.css
# /prism.min.js       → vendor/prism/prism.min.js
# /components/foo.min.js → vendor/prism/foo.min.js
src = re.sub(base + r"(?:themes|components)/([^\"' ]+)", r"vendor/prism/\1", src)
src = re.sub(base + r"(prism\.min\.js)", r"vendor/prism/\1", src)
p.write_text(src)
PY
  mkdir -p "$TARGET/vendor/prism"
  cp -f "$PRISM_DIR"/* "$TARGET/vendor/prism/"
  note "→ $TARGET/vendor/prism/ (${#PRISM_FILES[@]} files)"
fi

# ─── optional: vendor Fraunces (Google Fonts) ────────────────────────────────
if [[ "$VENDOR_FONTS" -eq 1 ]]; then
  note "vendoring Fraunces font from Google Fonts …"
  FONT_DIR="$TMPDIR/vendor/fonts"
  mkdir -p "$FONT_DIR"

  # Pull the exact CSS URL from the HTML so we stay in sync if it ever changes.
  CSS_URL="$(python3 - "$TMP_HTML" <<'PY'
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text()
m = re.search(r'href="(https://fonts\.googleapis\.com/css2[^"]+)"', src)
print(m.group(1) if m else "")
PY
)"
  [[ -n "$CSS_URL" ]] || die "could not locate Google Fonts CSS URL in HTML"

  # Google Fonts negotiates format by UA: a browser-like UA gets variable-axis
  # woff2 (few small files); a generic UA falls back to per-weight TTFs (dozens
  # of large files). Always request as a modern browser.
  FONT_UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
  CSS_RAW="$FONT_DIR/fraunces.css"
  curl --fail --silent --show-error --location --retry 3 --max-time 30 \
       --user-agent "$FONT_UA" --output "$CSS_RAW" "$CSS_URL" \
    || die "Google Fonts CSS fetch failed"

  # Download each woff2 referenced in the CSS, then rewrite the URLs to local paths.
  python3 - "$CSS_RAW" "$FONT_DIR" <<'PY'
import re, subprocess, sys, pathlib, urllib.parse
css_path = pathlib.Path(sys.argv[1])
out_dir  = pathlib.Path(sys.argv[2])
css = css_path.read_text()
urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)))
for u in urls:
    name = pathlib.Path(urllib.parse.urlparse(u).path).name
    dest = out_dir / name
    subprocess.run(["curl", "--fail", "--silent", "--show-error", "--location",
                    "--retry", "3", "--max-time", "30",
                    "--output", str(dest), u], check=True)
    css = css.replace(u, name)
css_path.write_text(css)
print(f"vendored {len(urls)} font files")
PY

  # Rewrite the <link rel="stylesheet"> in the HTML to point at the local CSS.
  python3 - "$TMP_HTML" "$CSS_URL" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
old = sys.argv[2]
src = p.read_text()
src = src.replace(old, "vendor/fonts/fraunces.css")
# Strip the preconnect hints — pointless once self-hosted.
src = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>', '', src)
p.write_text(src)
PY
  mkdir -p "$TARGET/vendor/fonts"
  cp -f "$FONT_DIR"/* "$TARGET/vendor/fonts/"
  note "→ $TARGET/vendor/fonts/"
fi

# ─── atomic publish ──────────────────────────────────────────────────────────
DEST="$TARGET/index.html"
mv -f "$TMP_HTML" "$DEST.new"
mv -f "$DEST.new" "$DEST"
chmod 644 "$DEST"
note "wrote $DEST"

# ─── sample server config ────────────────────────────────────────────────────
if [[ "$WRITE_HEADERS" -eq 1 ]]; then
  cat >"$TARGET/headers.nginx.example" <<'CFG'
# Drop into a server { } or location / { } block.
# Tightens CSP further if you ran publish.sh --all (no CDN allowances needed).

add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'self'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "interest-cohort=()" always;

# brotli/gzip cuts the 1.5 MB file to ~200 KB
gzip on;
gzip_types text/html text/css application/javascript;

location = /index.html {
    add_header Cache-Control "public, max-age=300, must-revalidate" always;
}
location /vendor/ {
    add_header Cache-Control "public, max-age=31536000, immutable" always;
}
CFG

  cat >"$TARGET/headers.htaccess.example" <<'CFG'
# Apache equivalent — drop in the publishing directory as .htaccess.
<IfModule mod_headers.c>
  Header always set Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'self'"
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "interest-cohort=()"
  <FilesMatch "\.(html)$">
    Header set Cache-Control "public, max-age=300, must-revalidate"
  </FilesMatch>
  <FilesMatch "vendor/.*\.(css|js|woff2)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
</IfModule>
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript
</IfModule>
CFG
  note "wrote sample header configs (headers.nginx.example, headers.htaccess.example)"
fi

note "done."

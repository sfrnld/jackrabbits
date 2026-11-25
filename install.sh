#!/bin/bash
# Sales Studio installer (Mac/Linux). Downloads the app from GitHub (no git needed) and starts it.
#   curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh | bash
# Running it again updates the app in place; your data (.env, state/) is never touched.
REPO="${SALES_STUDIO_REPO:-sfrnld/jackrabbits}"          # <- GitHub "owner/repo" of this project
BRANCH="${SALES_STUDIO_BRANCH:-main}"
DIR="${SALES_STUDIO_DIR:-$HOME/Sales-Studio}"
URL="${SALES_STUDIO_SRC:-https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz}"

fail() { echo; echo "Maaf, pemasangan belum berhasil: $1"; echo "Coba lagi, atau unduh zip dari halaman GitHub lalu double-click Mulai.command."; [ -t 0 ] && read -r -p "Tekan Enter untuk menutup…" _; exit 1; }
for c in curl tar; do command -v "$c" >/dev/null 2>&1 || fail "'$c' tidak ditemukan di komputer ini."; done

echo "Mengunduh Sales Studio dari GitHub…  (sekitar 1 MB, perlu internet)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
curl -fL --progress-bar "$URL" -o "$TMP/app.tgz" || fail "gagal mengunduh. Cek koneksi internet."
mkdir -p "$TMP/src" && tar -xzf "$TMP/app.tgz" -C "$TMP/src" --strip-components=1 || fail "file unduhan rusak."
[ -f "$TMP/src/Mulai.command" ] || fail "isi unduhan tidak dikenali (Mulai.command tidak ada)."

if [ -f "$DIR/Mulai.command" ]; then echo "Memperbarui aplikasi di $DIR (data kamu aman)…"; else echo "Memasang ke $DIR …"; fi
mkdir -p "$DIR" && cp -R "$TMP/src/." "$DIR/" || fail "tidak bisa menulis ke $DIR."
chmod +x "$DIR/Mulai.command" 2>/dev/null
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null || true       # Mac: avoid the "unidentified developer" prompt

echo "Selesai. Lain kali cukup double-click Mulai.command di folder: $DIR"
[ -n "${SALES_STUDIO_NO_RUN:-}" ] && exit 0
cd "$DIR" && exec ./Mulai.command

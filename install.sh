#!/bin/bash
# Sales Studio installer (Mac/Linux). Downloads the app from GitHub (no git needed) and starts it.
#   (it asks where to install: current folder, home folder, or another folder)
#   curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh | bash
# Running it again updates the app in place; your data (.env, state/) is never touched.
REPO="${SALES_STUDIO_REPO:-sfrnld/jackrabbits}"          # <- GitHub "owner/repo" of this project
BRANCH="${SALES_STUDIO_BRANCH:-main}"
# Where to install: ask (current folder / home folder / another folder). The question is read from the terminal itself
# (/dev/tty), so it also works when the script is piped from curl. Skip the question with SALES_STUDIO_DIR=/some/path.
TTY="${SALES_STUDIO_TTY:-/dev/tty}"
HERE_APP=""; [ -f ./Mulai.command ] && [ -d ./app ] && HERE_APP=1
if [ -n "${SALES_STUDIO_DIR:-}" ]; then DIR="$SALES_STUDIO_DIR"
else
  if [ -n "$HERE_APP" ]; then DIR1="$PWD"; L1="Folder ini (perbarui aplikasi yang sudah ada di sini): $PWD"
  else DIR1="$PWD/Sales-Studio"; L1="Folder saat ini: $PWD/Sales-Studio"; fi
  DIR="$DIR1"
  if [ -t 1 ] || [ -n "${SALES_STUDIO_TTY:-}" ]; then
    if [ -r "$TTY" ]; then
      echo "Di mana Sales Studio dipasang?"
      echo "  1) $L1"
      echo "  2) Folder pengguna: $HOME/Sales-Studio"
      echo "  3) Folder lain (kamu ketik alamatnya)"
      printf "Pilih 1, 2, atau 3 [Enter = 1]: "
      exec 3< "$TTY"; ans=""; read -r ans <&3 || true
      case "$ans" in
        2) DIR="$HOME/Sales-Studio" ;;
        3) printf "Ketik alamat folder (contoh ~/Documents/Sales-Studio): "; p=""; read -r p <&3 || true
           case "$p" in "~") p="$HOME" ;; "~/"*) p="$HOME/${p#\~/}" ;; esac
           case "$p" in "") DIR="$DIR1" ;; /*) DIR="$p" ;; *) DIR="$PWD/$p" ;; esac ;;
        *) DIR="$DIR1" ;;
      esac
      echo
    fi
  fi
fi
URL="${SALES_STUDIO_SRC:-https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz}"

fail() { echo; echo "Maaf, pemasangan belum berhasil: $1"; echo "Coba lagi, atau unduh zip dari halaman GitHub lalu double-click Mulai.command."; [ -t 0 ] && read -r -p "Tekan Enter untuk menutup…" _; exit 1; }
for c in curl tar; do command -v "$c" >/dev/null 2>&1 || fail "'$c' tidak ditemukan di komputer ini."; done

[ -d "$DIR/.git" ] && fail "$DIR adalah clone Git (bisa ada perubahanmu). Perbarui dengan: git -C \"$DIR\" pull. Installer tidak menimpanya."

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

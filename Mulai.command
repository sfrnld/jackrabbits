#!/bin/bash
# Double-click to start Sales Studio (Mac). No terminal knowledge needed.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

fail() {
  echo; echo "Maaf, aplikasi belum bisa dimulai: $1"
  echo "Lihat README.md bagian 'Kalau ada masalah'."
  read -r -p "Tekan Enter untuk menutup jendela ini…" _; exit 1
}

if ! command -v uv >/dev/null 2>&1; then
  echo "Menyiapkan alat yang dibutuhkan (hanya sekali, perlu internet)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || fail "gagal memasang uv. Cek koneksi internet."
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 || fail "uv tidak ditemukan setelah dipasang."
fi

[ -d .venv ] || echo "Pertama kali: menyiapkan aplikasi (±1 menit, perlu internet)…"
echo "Membuka aplikasi di browser kamu…  (jangan tutup jendela ini selama memakai aplikasi)"
uv run --frozen --quiet python -m app.main || fail "server berhenti dengan error."

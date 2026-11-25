# Sales Studio

Sales Studio mengubah data penjualan mentah menjadi:

- **dashboard** yang bisa disaring dan ditelusuri,
- daftar **5 outlet terlemah**, dibandingkan secara adil,
- **laporan Telegram** untuk tim: gambar, ringkasan, dan tugas (*action items*) tiap penanggung jawab.

*English: install with the command in "1. Pasang aplikasi", then double-click `Mulai.command` (Mac) or `Mulai.bat` (Windows) whenever you want to open the app again. Your browser opens by itself and the app guides you.*

## Sebelum mulai

Siapkan:

- komputer Mac atau Windows,
- koneksi internet (untuk pemasangan pertama).

Kamu tidak perlu memasang Git, Node, atau Python sendiri. Aplikasi ini paling nyaman dipakai di browser komputer, walaupun bisa juga dibuka di HP.

## 1. Pasang aplikasi

Cara ini disarankan. Kalau tidak mau memakai terminal, lihat [Cara pasang lain](#cara-pasang-lain).

### Langkah 1: Jalankan perintah pemasangan

**Di Mac:**

1. Tekan `Cmd + Spasi`, ketik **Terminal**, lalu tekan Enter.
2. Salin perintah ini, tempel di Terminal, lalu tekan Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh | bash
```

**Di Windows:**

1. Tekan tombol Windows, ketik **cmd**, lalu tekan Enter.
2. Salin perintah ini, tempel di Command Prompt, lalu tekan Enter:

```bat
curl -L -o install.bat https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.bat && install.bat
```

### Langkah 2: Pilih folder

Pemasang akan bertanya di mana aplikasi disimpan:

```
Di mana Sales Studio dipasang?
  1) Folder saat ini: /Users/kamu/Sales-Studio
  2) Folder pengguna: /Users/kamu/Sales-Studio
  3) Folder lain (kamu ketik alamatnya)
Pilih 1, 2, atau 3 [Enter = 1]:
```

| Ketik | Aplikasi dipasang di |
|---|---|
| Enter atau `1` | Folder `Sales-Studio` di dalam folder tempat kamu menjalankan perintah |
| `2` | Folder `Sales-Studio` di folder pengguna |
| `3` | Alamat yang kamu ketik, misalnya `~/Projects/Sales-Studio` (Mac) atau `D:\Aplikasi\Sales-Studio` (Windows) |

Kalau Terminal baru saja dibuka, pilihan 1 dan 2 biasanya menunjuk ke folder yang sama.

### Langkah 3: Tunggu aplikasi terbuka

Setelah terpasang, aplikasi langsung berjalan. Pertama kali butuh sekitar 1 menit untuk menyiapkan Python dan komponen lain. Berikutnya jauh lebih cepat.

Browser akan terbuka sendiri.

## 2. Buka dan tutup aplikasi

**Membuka:**

1. Buka folder `Sales-Studio`.
2. Double-click **`Mulai.command`** (Mac) atau **`Mulai.bat`** (Windows).
3. **Biarkan jendela yang muncul tetap terbuka** selama kamu memakai aplikasi.

**Menutup:** tutup jendela tersebut, atau tekan `Ctrl+C` di dalamnya.

Setiap kali dibuka, server Sales Studio yang lama otomatis ditutup. Jadi, hanya satu salinan aplikasi yang bisa berjalan dalam satu waktu.

### Kalau muncul peringatan keamanan

- **Mac:** klik kanan `Mulai.command` → **Open** → **Open**. Cukup sekali. Kalau masih diblokir, buka Terminal, masuk ke folder aplikasi dengan `cd`, lalu jalankan:

  ```bash
  xattr -dr com.apple.quarantine . && ./Mulai.command
  ```

- **Windows:** pada layar biru SmartScreen, klik **More info** → **Run anyway**.

## 3. Pakai aplikasi

Ikuti petunjuk di layar. Aplikasi punya dua bagian:

| | Bagian 1: Persiapan (`/setup`) | Bagian 2: Sales Studio (`/studio`) |
|---|---|---|
| **Kapan** | Sekali saja, sekitar 1 menit | Setiap ada data baru |
| **Urutan** | Sambutan → instalasi → cek sistem → sambungkan Telegram → siap | Sumber data → pemetaan kolom → pembersihan → hasil pembersihan → dashboard → action items → bagikan |

Setelah persiapan selesai, aplikasi akan langsung masuk ke Sales Studio saat dibuka lagi.

> **Belum punya bot Telegram?** Klik **Lewati dulu** pada langkah Telegram. Kamu tetap bisa mencoba aplikasi, dan pengiriman diganti dengan pratinjau.

## Memperbarui aplikasi

Jalankan lagi [perintah pemasangan](#langkah-1-jalankan-perintah-pemasangan), lalu pilih folder yang **sama** dengan sebelumnya.

- File aplikasi diganti dengan versi terbaru.
- Token Telegram (`.env`) dan data tersimpan (folder `state/`) tetap aman.
- Kalau folder aplikasimu adalah hasil `git clone`, pemasang tidak akan menimpanya. Perbarui dengan `git pull`.

## Cara pasang lain

Kalau memakai salah satu cara ini, ikuti [Buka dan tutup aplikasi](#2-buka-dan-tutup-aplikasi) setelahnya.

### Unduh ZIP (tanpa terminal)

1. Di halaman GitHub, klik **Code** → **Download ZIP**.
2. Ekstrak file ZIP.
3. Double-click **`Mulai.command`** (Mac) atau **`Mulai.bat`** (Windows).

Kalau komputer memblokirnya, lihat [Kalau muncul peringatan keamanan](#kalau-muncul-peringatan-keamanan).

### Pakai Git

Di Mac:

```bash
git clone https://github.com/sfrnld/jackrabbits.git Sales-Studio && cd Sales-Studio && ./Mulai.command
```

Di Windows:

```bat
git clone https://github.com/sfrnld/jackrabbits.git Sales-Studio && cd Sales-Studio && Mulai.bat
```

## Tips pemasangan yang aman

- **Pilih folder milikmu sendiri**, misalnya `Documents` atau `Projects`.
- **Hindari folder yang tersinkron otomatis** (iCloud Drive, OneDrive, Dropbox). File `.env` berisi token Telegram, folder `state/` berisi data penerima, dan folder `.venv` berukuran besar.
- **Jangan pakai `sudo`.** Pemasang tidak membutuhkannya.
- **Ingin memeriksa skrip dulu? (Mac)** Unduh skripnya:

  ```bash
  curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh -o install.sh
  ```

  Baca isinya (tekan `q` untuk keluar):

  ```bash
  less install.sh
  ```

  Kalau sudah yakin, jalankan:

  ```bash
  bash install.sh
  ```

### Pengaturan tambahan (Mac)

Pengaturan ini opsional. Tulis **setelah** tanda `|`, tepat sebelum `bash`.

| Pengaturan | Kegunaan |
|---|---|
| `SALES_STUDIO_DIR` | Menentukan folder tujuan tanpa ditanya |
| `SALES_STUDIO_BRANCH` | Memasang dari branch selain `main` |
| `SALES_STUDIO_REPO` | Memasang dari repo lain, misalnya hasil fork |

Contoh:

```bash
curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh | SALES_STUDIO_DIR="$HOME/Projects/Sales-Studio" bash
```

## Kalau ada masalah

| Masalah | Yang perlu dilakukan |
|---|---|
| Halaman tidak terbuka | Buka `http://127.0.0.1:8765` di browser. Kalau port itu sedang dipakai, coba `8766`, `8767`, dan seterusnya. |
| Muncul "uv tidak bisa dipasang" atau unduhan gagal | Periksa internet, lalu jalankan aplikasi lagi. |
| Telegram "Tidak bisa terhubung" | Periksa internet. Sementara itu, salin laporan dan unduh gambarnya dari layar **Bagikan**. |
| Layar kosong atau angka terlihat aneh | Buka halaman **Status** (tautan di bar atas), lalu kirim isinya ke pengembang. |
| Ingin mulai dari nol | Tutup aplikasi, lalu hapus folder `state/`. **Perhatian:** daftar penerima, riwayat, dan pemetaan kolom tersimpan akan hilang. File data penjualanmu tidak ikut terhapus. |

## Untuk developer

### Struktur folder

| Lokasi | Isi |
|---|---|
| `Mulai.command`, `Mulai.bat` | Peluncur: memasang `uv` bila belum ada, lalu menjalankan aplikasi |
| `app/` | Server FastAPI: ingest, mapping, findings, analytics, assistant, actions, narrative, render, telegram, share |
| `web/src/` | Tampilan (Svelte 5 + Vite) |
| `web/dist/` | Hasil build tampilan. Ikut di-commit supaya pengguna tidak perlu Node |
| `data/sales.csv` | Data contoh |
| `design-system/` | Token dan aturan desain |
| `tests/` | Tes (pytest) |

### Perintah umum

Jalankan dari folder utama proyek.

Jalankan semua tes, termasuk menyalakan server sungguhan:

```bash
uv run pytest
```

Bangun ulang tampilan. Lakukan setiap kali mengubah `web/src/`, karena tes menolak `web/dist` yang basi:

```bash
(cd web && npm install && npm run build)
```

Build, tes, lalu buat ZIP siap kirim di `dist-zip/` (tidak di-commit):

```bash
bash scripts/ship.sh
```

Pasang hook pre-commit yang mencegah file rahasia ikut ter-commit (sekali saja setelah clone):

```bash
bash scripts/install_hooks.sh
```

### Demo Telegram tanpa bot sungguhan

Nyalakan server Telegram tiruan:

```bash
uv run python tests/fake_telegram_server.py &
```

Lalu jalankan aplikasi dengan token palsu:

```bash
TELEGRAM_API_BASE=http://127.0.0.1:8799 TELEGRAM_BOT_TOKEN=123:FAKE uv run python -m app.main
```

### Kalau kamu fork repo ini

1. Ganti nama repo di `install.sh` (baris `REPO=`) dan `install.bat` (baris `set "REPO=`).
2. Ganti alamat GitHub di README ini.
3. Pastikan repo bersifat publik dan folder `web/dist` ikut di-commit.

Tes `tests/test_install.py` memeriksa nama repo asli, jadi sesuaikan juga tes tersebut.

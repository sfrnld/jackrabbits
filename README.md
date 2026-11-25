# Sales Studio

**Pasang dengan satu perintah `curl` (lihat [Memasang & menjalankan](#memasang--menjalankan)), lalu double-click `Mulai.command` (Mac) atau `Mulai.bat` (Windows).** Browser terbuka sendiri dan aplikasi memandu kamu dari sana.

*English: install with one `curl` command (see "Memasang & menjalankan"), then double-click `Mulai.command` (Mac) or `Mulai.bat` (Windows). Your browser opens by itself and the app guides you from there.*

**Masalahnya:** export ERP penjualan Sep–Okt 2026 itu berantakan (region ditulis beda-beda, 3 baris dobel, retur, salesman kosong), jadi manajer tidak bisa langsung percaya angkanya. **Temuan utamanya:** setelah dibersihkan, net Rp 1,726 miliar (+3,6% Sep→Okt); Jawa Timur naik +92,4% hampir seluruhnya karena satu outlet (OUT1036), sementara Jawa Barat turun −13,9% karena OUT1014. **5 outlet terlemah** dinilai terhadap sesama tipe outlet (Grosir vs Warung), bukan sekadar yang total terkecil. **Satu menit untuk mencoba:** double-click, pakai data contoh, klik "Terapkan semua rekomendasi", buka Dashboard, lalu "Kirim ke saya dulu (demo)" di langkah Bagikan.

Sales Studio mengubah data penjualan mentah menjadi alat yang langsung dipakai manajer sales: dashboard yang bisa diiris-iris, 5 outlet terlemah yang adil, dan laporan Telegram (kartu gambar + ringkasan + action items per penanggung jawab) yang masuk ke HP tim.

> **Mac memblokir file ini?** Klik kanan `Mulai.command` → **Open** → **Open** (sekali saja). Cara cadangan lewat terminal: `cd` ke folder ini, lalu `xattr -d com.apple.quarantine Mulai.command && ./Mulai.command`.
> Membuka lagi? Peluncur otomatis menutup server Sales Studio lama, jadi kamu selalu mendapat versi terbaru.

> Aplikasi ini dikembangkan oleh agen-agen AI yang diorkestrasi oleh [Aldi](https://www.linkedin.com/in/sefrinaldi). Bisa dibuka di browser HP, tapi lebih nyaman lewat browser desktop.

## Memasang & menjalankan

Pilih **salah satu** cara. Cara A paling mudah: satu perintah, tanpa Git, tanpa terminal lain.

### Cara A: pasang lewat satu perintah (disarankan)

Perintah ini mengunduh aplikasi dari GitHub ke folder `Sales-Studio` di folder Home-mu, lalu langsung menjalankannya. Tidak perlu Git.

**Mac** — buka aplikasi **Terminal** (tekan `Cmd + Spasi`, ketik "Terminal", Enter), tempel, lalu Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.sh | bash
```

**Windows** — buka **Command Prompt** (tekan tombol Windows, ketik `cmd`, Enter), tempel, lalu Enter:

```bat
curl -L -o install.bat https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.bat && install.bat
```

Pilihan lain kalau tidak mau memakai terminal: unduh file `install.sh` (Mac, simpan sebagai `Pasang-Sales-Studio.command`) atau `install.bat` (Windows) dari halaman GitHub, lalu **double-click**. Mengunduh dengan `curl` tidak memicu peringatan keamanan Mac/Windows.

Setelah terpasang, lain kali cukup **double-click `Mulai.command` (Mac) atau `Mulai.bat` (Windows)** di folder `Sales-Studio`. Mau memperbarui ke versi terbaru? Jalankan perintah di atas lagi: aplikasi diperbarui, sedangkan token Telegram (`.env`) dan data tersimpan (`state/`) tidak disentuh.

### Cara B: unduh zip

1. Di halaman GitHub klik **Code → Download ZIP**, lalu ekstrak.
2. **Double-click `Mulai.command`** (Mac) atau **`Mulai.bat`** (Windows).

### Cara C: pakai Git (untuk yang sudah terbiasa)

```bash
git clone https://github.com/sfrnld/jackrabbits.git Sales-Studio && cd Sales-Studio && ./Mulai.command   # Windows: Mulai.bat
```

### Yang terjadi saat pertama kali

- **Pertama kali** perlu internet dan butuh sekitar 1 menit: peluncur memasang alat kecil bernama `uv`, yang mengunduh Python 3.12 dan pustaka aplikasi. Hanya sekali; setelah itu mulai dalam beberapa detik.
- **Mac:** kalau muncul "tidak bisa dibuka karena pengembang tidak dikenal" (terjadi pada Cara B), klik kanan `Mulai.command` → **Open** → **Open**, atau jalankan `xattr -dr com.apple.quarantine .` di dalam folder. Cukup sekali.
- **Windows:** kalau muncul layar biru SmartScreen, klik **More info** → **Run anyway**.
- Jendela peluncur menampilkan satu baris: "Membuka aplikasi di browser kamu…". **Biarkan jendela itu terbuka** selama memakai aplikasi. Menutupnya = menghentikan aplikasi. Browser terbuka sendiri.
- Ikuti layar di browser. Semua penjelasan ada di halaman, dan semua log ada di halaman **Status** (tautan di bar atas), bukan di jendela peluncur.

Berhenti: tutup jendela peluncur (atau tekan `Ctrl+C` di dalamnya).

*English: run the one-liner above (Terminal on Mac, Command Prompt on Windows). It downloads the app from GitHub into `~/Sales-Studio` (no Git needed) and starts it. Next time, double-click `Mulai.command` / `Mulai.bat`. Re-running the one-liner updates the app and keeps your `.env` and `state/`.*

> Fork repo ini? Ganti nama repo di `install.sh` (baris `REPO=`) dan `install.bat` (baris `set "REPO=`), atau jalankan dengan `SALES_STUDIO_REPO=namamu/nama-repo`. Pastikan repo publik dan folder `web/dist` ikut ter-commit (aplikasi dikirim dengan tampilan yang sudah di-build, jadi Node tidak diperlukan).

## Dua bagian aplikasi

| | Bagian 1: Persiapan (`/setup`) | Bagian 2: Sales Studio (`/studio`) |
|---|---|---|
| Untuk | Sekali saja, ±1 menit | Setiap ada data baru |
| Isi | Sambutan → instalasi → cek sistem → sambungkan Telegram → siap | Sumber data → pemetaan kolom → pembersihan → hasil pembersihan → dashboard → action items → bagikan |

Setelah Bagian 1 selesai sekali, membuka aplikasi berikutnya langsung masuk ke Sales Studio. Tombol **Lewati dulu** di langkah Telegram membuat semuanya tetap bisa dicoba tanpa bot (pengiriman diganti pratinjau).

**Tata letak:** di bar atas ada tiga tombol (hanya di desktop): 1 kolom (hanya tengah), 2 kolom (tengah dan detail), 3 kolom (perjalanan, tengah, detail). Kolom kanan juga bisa digeser lebarnya. Kolom kiri menyimpan perjalananmu; ikon di tiap langkah: ✓ selesai, ⏳ menunggu keputusanmu, 🔒 terkunci.

**Jackrabbit** adalah asisten kecil berwarna merah yang menjelaskan apa yang sedang terjadi di tiap layar (tanpa riwayat obrolan). Di desktop ia ada di kolom kiri; saat kolom kiri dilipat atau di HP, ia menjadi ikon: titik-titik bergerak berarti ada pesan baru, 💬 berarti pesan menunggu, ketuk untuk membuka. Tombol 👋 di bar atas menjelaskan siapa pembuat aplikasi ini.

Pintasan: `Ctrl/Cmd + K` membuka palet perintah. Kotak di panel asisten menerima perintah singkat: `jabar`, `brand sukro`, `grosir oktober`, `top 10 outlet`, `5 outlet terlemah`, `bandingkan sep vs okt`, `kenapa OUT1014 turun?`, `kirim ke tim jatim`, `reset`. Setiap perubahan filter punya tombol **Batalkan**.

## Telegram (opsional)

Kirim laporan butuh bot Telegram dan internet. Dua cara:

- **Token dikirim terpisah** (misalnya lewat email): simpan sebagai file `.env` di folder yang sama dengan `Mulai.command`, berisi satu baris `TELEGRAM_BOT_TOKEN=...` (contoh: `.env.example`).
- **Buat bot sendiri:** di Telegram buka `@BotFather`, kirim `/newbot`, ikuti langkahnya, lalu tempel token di langkah "Sambungkan Telegram" di aplikasi. Aplikasi menyimpannya hanya di `.env` lokal.

**Mengundang penerima:** di langkah Action items (kolom kanan) setiap penanggung jawab yang belum punya Telegram punya tombol **Undang**. Tombol itu membuat tautan pribadi: **salin** atau **bagikan** (lembar bagikan perangkat, atau WhatsApp bila tidak ada). Penerima cukup membuka tautan dan menekan **Start**; aplikasi mendeteksinya sendiri. Bisa juga lewat QR di langkah Bagikan.

**Pesan untuk tiap salesperson:** setiap orang hanya menerima aksi miliknya. Urutannya: **gambar data** dulu (penjualan Sep vs Okt dan empat nilai di balik skor tiap outlet), lalu pesan yang mudah dibaca: *Kenapa* aksi ini ada, *Yang perlu dilakukan*, *Tenggat*, dan *Yang perlu kamu jawab*. Aksi berstatus Selesai tidak ikut dikirim. Pilihan lain: kirim per region (kartu + ringkasan) atau kirim tampilan saat ini.

**Tidak mau mengundang siapa pun dulu?** Pakai **Kirim ke saya dulu (demo)**: semua pesan pemilik dikirim ke chat-mu sendiri, bertanda DEMO, sehingga alur terakhir tetap bisa dicoba. Pesan yang gagal terkirim tetap bisa disalin atau diunduh dari layar.

**Keamanan token dan data:** jangan taruh token di repo publik. `.gitignore` menutup `.env` dan `.env.*` (kecuali `.env.example`), `state/` (penerima, riwayat, pemetaan), kunci (`*.pem`, `*.key`), serta zip hasil build. Jalankan `bash scripts/install_hooks.sh` sekali setelah clone: hook **pre-commit** menolak commit yang memuat file rahasia, zip, atau teks berbentuk token bot Telegram. Tes `tests/test_no_secrets.py` ikut menjaga hal yang sama. Token tidak pernah ditampilkan di browser, error, atau log. Setelah proses rekrutmen selesai, **revoke token** lewat `@BotFather` (`/revoke`).

## Data

- Contoh Dua Kelinci (Sep–Okt 2026, 1.891 baris) di `data/sales.csv` bisa dipakai satu klik. **Kalau file itu tidak ada** (misalnya tidak ikut di-download), aplikasi tetap jalan: kartu data contoh diganti penjelasan, dan kamu mengunggah file sendiri. Mesinnya dirancang untuk data apa pun yang di-upload.
- Format: CSV/TSV (pemisah `,` `;` tab terdeteksi otomatis), Excel `.xlsx/.xls` (pilih sheet), JSON, Parquet. Tahan terhadap encoding berbeda, baris judul di atas header, format tanggal (`DD/MM/YYYY`, ISO, serial Excel), dan angka gaya Indonesia (`Rp 1.234.567,00`).
- Syarat minimum: tanggal, outlet, dan nilai penjualan. Kolom lain yang tidak ada (misalnya brand) membuat bab terkait disembunyikan, bukan error.
- Pemetaan kolom diprediksi dari nama (Indonesia/Inggris) dan isi, lalu kamu konfirmasi. Pemetaan diingat untuk format yang sama.
- **Privasi:** data tetap di komputermu. Yang keluar hanya laporan Telegram (gambar dan ringkasan agregat), bukan baris data mentah.

## Keputusan produk

- **Tidak ada yang diubah diam-diam.** Setiap temuan data (region ditulis beda, duplikat persis, retur, salesman kosong, nama outlet beda ejaan, plus pemeriksaan total/tanggal/nilai ekstrem) tampil sebagai kartu: contoh baris, dampak Rp, pilihan aksi dengan preview, satu opsi disarankan, dan Undo per temuan. Semua keputusan tercatat di jejak keputusan dan panel Kualitas data.
- **Tanpa LLM, dengan sengaja.** Asisten adalah mesin aturan dan ringkasan Telegram adalah templat yang diisi angka hasil analisis: deterministik (angka selalu cocok dengan tes), gratis dijalankan, bisa diaudit baris demi baris, dan data penjualan tidak keluar dari komputermu. LLM adalah langkah berikutnya yang jelas (bahasa bebas, narasi lebih kaya), dipasang di atas mesin angka yang sama.
- **Offline setelah setup.** Run pertama butuh internet (memasang `uv`, Python, pustaka). Setelah itu semuanya jalan offline; hanya pengiriman Telegram yang butuh internet.
- **Cerita dulu, chart kemudian:** tiap chart punya satu kalimat kesimpulan di atasnya.
- **Warna:** putih dan hitam; merah hanya untuk yang mendesak/negatif, hijau hanya untuk yang positif/selesai, selalu dengan ikon ▲▼✓ (tidak mengandalkan warna saja).
- Retur dikurangkan dari penjualan secara default (net tetap menyertakannya); bisa dipisah sebagai metrik retur atau dikeluarkan.

## Cara skor outlet terlemah bekerja (penjelasan paling sederhana)

**Masalah:** kalau toko diurutkan dari penjualan terkecil, yang muncul selalu toko kecil, padahal toko kecil memang jualannya kecil. Itu tidak adil dan tidak menolong.

**Idenya:** bandingkan setiap toko hanya dengan toko lain yang **sejenis** (toko besar dengan toko besar, warung dengan warung). Lalu beri skor 0 sampai 100. **Makin kecil skornya, makin lemah tokonya.**

**Langkahnya:**
1. Kumpulkan toko yang sejenis.
2. Beri tiap toko 4 nilai, masing-masing 0 sampai 100 (100 = terbaik di antara temannya, 0 = terburuk). Nilai ini berupa peringkat: kalau sebuah toko lebih baik dari 8 dari 10 toko sejenis, nilainya 80.
3. Campur keempat nilai dengan porsi tertentu menjadi satu skor.

| Yang dinilai | Porsi | Artinya dengan bahasa biasa |
|---|---|---|
| Uang yang masuk | 35% | Berapa banyak toko itu belanja, dibanding teman sejenisnya |
| Naik atau turun | 30% | Bulan terakhir naik atau turun dibanding bulan sebelumnya (kalau belum ada bulan sebelumnya, dianggap biasa saja) |
| Frekuensi pemesanan | 20% | Berapa kali toko itu memesan (jumlah nota) |
| Terakhir memesan | 15% | Sudah berapa hari sejak toko itu terakhir memesan; makin lama makin lemah |

**Rumus:** skor = 0,35 × nilai uang masuk + 0,30 × nilai naik-turun + 0,20 × nilai frekuensi + 0,15 × nilai terakhir memesan.

**Contoh:** sebuah warung dapat nilai 40 (uang), 20 (naik-turun), 60 (frekuensi pemesanan), 80 (terakhir memesan). Skor = 0,35×40 + 0,30×20 + 0,20×60 + 0,15×80 = 14 + 6 + 12 + 12 = **44**.

Akibatnya toko kecil yang tumbuh tidak dianggap lemah, sedangkan toko kecil yang turun jauh dan jarang memesan naik ke atas daftar. Setiap toko datang dengan alasannya dalam kalimat biasa. Kalau filter atau wilayah dipilih, perbandingan dilakukan di dalam cakupan itu. Porsi ada di `app/analytics.py` (`W`).

Di aplikasi, garis bawah titik-titik pada istilah (skor, terlemah, net sales, invoice, Δ%, retur, dan lainnya) menampilkan penjelasan sederhana kalau kursor diarahkan ke sana.

## Angka acuan (diuji otomatis)

Data contoh: 1.891 baris → 52 outlet. Setelah semua rekomendasi diterapkan (3 duplikat dibuang, retur dikurangkan, 4 ejaan region → 6 region):

- Total net bersih **Rp 1.725.966.000** (mentah Rp 1.728.036.900). Sep Rp 847.517.400; Okt Rp 878.448.600 (+3,6%).
- Jawa Timur +92,4%, hampir semuanya dari OUT1036 (+Rp 47,7 juta). Jawa Barat −13,9%, terutama OUT1014 (−Rp 31,6 juta, lebih besar dari total penurunan region itu).
- Jawa Barat bulan Oktober: Rp 143.882.800.

## Asumsi

- Tenggat action item = hari ini + 7 hari. Pemilik = salesman dominan outlet itu ("Belum ditentukan" jika tidak ada).
- "Bulan terakhir" dan "bulan sebelumnya" diambil dari dua bulan terakhir di data (setelah filter).
- Nama region mirip digabung dengan kamus singkatan (Jabar, Jateng, Jatim, DKI, …), kecocokan fuzzy, dan dicek silang dengan cabang. Kelompok yang diusulkan selalu ditampilkan sebelum digabung.
- Salesman kosong diberi label "Tidak diketahui" secara default; mengisi dengan salesman dominan ditandai sebagai prediksi.
- Teks asisten dan laporan Telegram berbahasa Indonesia; tombol dan label antarmuka bisa diganti ke English (toggle di bar atas).
- Pengiriman Telegram (termasuk gambar per salesperson dan mode demo) diuji dengan server Telegram tiruan, belum dengan bot sungguhan. Coba kirim pertama ke akunmu sendiri.

## Kalau ada masalah

- **Halaman tidak terbuka:** buka `http://127.0.0.1:8765` secara manual (port bisa bergeser ke 8766, 8767, … jika terpakai; jendela peluncur tetap membuka browser ke port yang benar).
- **"uv tidak bisa dipasang" / unduhan gagal:** cek internet, lalu jalankan peluncur lagi.
- **Telegram "Tidak bisa terhubung":** cek internet; laporan tetap bisa disalin dan gambarnya diunduh dari layar Bagikan.
- **Layar kosong atau angka aneh:** buka halaman **Status** dan kirim isinya ke pengembang (tidak ada token atau data mentah di sana).
- **Mulai ulang dari nol:** hapus folder `state/` (menghapus penerima, riwayat, dan pemetaan tersimpan; data kamu tidak tersentuh).

## Untuk developer

```
Mulai.command / Mulai.bat     peluncur (memasang uv bila belum ada, memilih port kosong, membuka browser)
app/                          FastAPI: ingest, mapping, findings, analytics, assistant, actions, narrative, render, telegram, share
web/src/                      Svelte 5 + Vite; web/dist = hasil build yang ikut di zip (reviewer tidak butuh Node)
data/sales.csv                data contoh        design-system/   token dan aturan desain
tests/                        pytest             tests/fake_telegram_server.py   Telegram tiruan untuk demo
```

```bash
uv run pytest                                  # semua tes (termasuk boot server sungguhan)
cd web && npm install && npm run build         # bangun ulang frontend; tes menolak web/dist yang basi
bash scripts/ship.sh                           # build, tes, lalu zip siap kirim di dist-zip/ (tidak di-commit)
bash scripts/install_hooks.sh                  # pasang hook pre-commit penjaga rahasia
# demo Telegram tanpa bot sungguhan:
uv run python tests/fake_telegram_server.py &
TELEGRAM_API_BASE=http://127.0.0.1:8799 TELEGRAM_BOT_TOKEN=123:FAKE uv run python -m app.main
```

## Tur singkat (storyboard demo 60–90 detik)

1. Double-click → layar sambutan (Jackrabbit menyapa). 2. Pakai data contoh → konfirmasi pemetaan. 3. Terapkan semua rekomendasi pembersihan. 4. Dashboard: klik Brand/Outlet, lihat 5 outlet terlemah. 5. Action items: ubah status, lihat siapa menerima apa. 6. Bagikan: "Kirim ke saya dulu (demo)". Tangkapan layar dan video bisa ditaruh di `docs/screenshots/`.

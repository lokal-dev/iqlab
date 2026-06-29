# Panduan Menjalankan iq.lab Secara Lokal Natively (Tanpa Docker / WSL)

Panduan ini menjelaskan cara menjalankan **iq.lab** langsung di Windows 10 menggunakan Python dan Node.js lokal, tanpa menggunakan Docker atau WSL.

Kami menggunakan **Metode Hybrid (Tailscale VPN)**: Proses AI (Whisper) yang berat dijalankan menggunakan CPU & RAM MiniPC Anda, sementara database diakses langsung secara aman dari VPS melalui jaringan privat Tailscale Anda.

---

## 🔌 Metode 1: Metode Hybrid (Tailscale VPN)
*Menjalankan AI secara lokal di MiniPC, terhubung ke database VPS melalui IP privat Tailscale.*

### Prasyarat di Windows:
1. **Python 3.10 atau 3.11**: Unduh dari [python.org](https://www.python.org/downloads/) (Pastikan centang opsi **"Add Python to PATH"** saat instalasi).
2. **Node.js (LTS)**: Unduh dari [nodejs.org](https://nodejs.org/).
3. **FFmpeg**: Dibutuhkan untuk memotong audio.
   * Unduh dari [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip).
   * Ekstrak dan masukkan folder `bin` ke dalam **Environment Variables (PATH)** Windows Anda.
4. **Tailscale**: Pastikan aplikasi Tailscale aktif dan terhubung di MiniPC Anda.

---

### Langkah-Langkah Menjalankan:

#### Langkah 1: Unduh dan Ekstrak Kode
Unduh file arsip ke folder pilihan Anda:
```bash
scp backdoor@203.194.115.246:/home/backdoor/iqlab-dev.tar.gz .
```
Ekstrak file `iqlab-dev.tar.gz` (bisa menggunakan 7-Zip atau WinRAR).

#### Langkah 2: Setup & Jalankan Backend (FastAPI)
Buka terminal (Command Prompt atau PowerShell) di folder `iqlab-dev`, lalu jalankan:

1. Buat Virtual Environment Python:
   ```cmd
   python -m venv venv
   ```
2. Aktifkan Virtual Environment:
   ```cmd
   # Di Command Prompt (CMD):
   venv\Scripts\activate.bat
   # Di PowerShell:
   .\venv\Scripts\Activate.ps1
   ```
3. Instal dependencies (termasuk PyTorch dan Whisper):
   ```cmd
   pip install -r requirements.txt
   ```
4. Set Environment Variables dan jalankan API:
   ```cmd
   # Menghubungkan langsung ke IP Tailscale VPS (100.71.144.89)
   set DATABASE_URL=postgresql://postgres:postgres@100.71.144.89:5432/iqlab
   set WHISPER_MODEL=medium
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *(API sekarang berjalan di `http://127.0.0.1:8000` dan terhubung aman ke database VPS Anda).*

#### Langkah 4: Setup & Jalankan Frontend (React)
Buka terminal baru di folder `iqlab-dev`, lalu jalankan:

1. Instal Node packages:
   ```cmd
   npm install
   ```
2. Ubah target proxy di `vite.config.js` dari `http://backend:8000` menjadi `http://127.0.0.1:8000` karena kita tidak menggunakan network Docker:
   ```javascript
   // Buka vite.config.js dan ubah bagian target:
   proxy: {
     '/api': {
       target: 'http://127.0.0.1:8000',
       changeOrigin: true,
     }
   }
   ```
3. Jalankan server dev:
   ```cmd
   npm run dev
   ```
   *(Frontend sekarang aktif di [http://localhost:5173](http://localhost:5173)).*

---

## 💾 Metode 2: 100% Lokal (Termasuk Database)
Jika Anda tidak ingin terhubung ke internet sama sekali dan ingin database berjalan offline di Windows:

1. Instal **PostgreSQL untuk Windows** melalui [EnterpriseDB Installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. Unduh pre-compiled binary **`pgvector` untuk Windows** dari [pgvector Releases](https://github.com/pgvector/pgvector/releases).
3. Copy file `vector.dll` ke folder `C:\Program Files\PostgreSQL\<version>\lib\`.
4. Copy file `.sql` dan `.control` ke `C:\Program Files\PostgreSQL\<version>\share\extension\`.
5. Buka `pgAdmin` atau `psql`, buat database `iqlab`, lalu jalankan:
   ```sql
   CREATE EXTENSION vector;
   CREATE EXTENSION pg_trgm;
   ```
6. Jalankan backend seperti di **Metode 1 (Langkah 3)** tetapi arahkan `DATABASE_URL` ke PostgreSQL lokal Anda, lalu jalankan `python backend/seed_all.py` untuk mengunduh dan mengisi data secara lokal.

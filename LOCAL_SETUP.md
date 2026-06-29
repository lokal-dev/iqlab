# Panduan Menjalankan iq.lab Secara Lokal (MiniPC Setup)

Dokumen ini menjelaskan langkah-langkah untuk mengunduh, mengekstrak, dan menjalankan proyek **iq.lab** di MiniPC Anda (Windows 10, Intel i7-6600U, 16GB RAM) menggunakan Docker.

---

## 📋 1. Prasyarat (Prerequisites)

Sebelum memulai, pastikan perangkat lunak berikut sudah terinstal di MiniPC Anda:

### A. Aktifkan WSL2 (Windows Subsystem for Linux)
Docker Desktop di Windows membutuhkan WSL2 untuk performa maksimal.
1. Buka **PowerShell** sebagai Administrator.
2. Jalankan perintah berikut:
   ```powershell
   wsl --install
   ```
3. **Nyalakan ulang (Restart) MiniPC Anda** setelah proses selesai.

### B. Instal Docker Desktop
1. Unduh dan instal [Docker Desktop untuk Windows](https://www.docker.com/products/docker-desktop/).
2. Saat instalasi, pastikan opsi **"Use the WSL 2 based engine"** dicentang.
3. Setelah terinstal, buka Docker Desktop dan pastikan statusnya "Running" (ikon hijau di pojok kiri bawah).

### C. Jalankan Aplikasi Terminal
Anda bisa menggunakan **Git Bash**, **PowerShell**, atau **Command Prompt (CMD)** untuk menjalankan perintah di bawah.

---

## 🚀 2. Langkah Demi Langkah (Step-by-Step)

### Langkah 1: Unduh Kode dari Server
Unduh file arsip ringan (`116 KB`) yang sudah disiapkan di server. Buka terminal di MiniPC Anda dan jalankan:

```bash
scp backdoor@203.194.115.246:/home/backdoor/iqlab-dev.tar.gz .
```
*(Masukkan password SSH Anda saat diminta).*

### Langkah 2: Ekstrak File Arsip
Ekstrak file `iqlab-dev.tar.gz` ke folder pilihan Anda.
* **Menggunakan Terminal**:
  ```bash
  tar -xvzf iqlab-dev.tar.gz
  ```
* **Menggunakan GUI**: Anda juga bisa klik kanan file tersebut dan ekstrak menggunakan aplikasi seperti **7-Zip** atau **WinRAR**.

### Langkah 3: Optimasi Spesifikasi i7 (Opsional tapi Direkomendasikan)
Karena MiniPC Anda memiliki **16GB RAM**, kita bisa meningkatkan akurasi kecerdasan buatan (ASR Whisper) dari model `small` ke **`medium`** agar deteksi tajweed & bacaan jauh lebih presisi.

1. Buka folder hasil ekstrak `iqlab-dev`.
2. Buka file `docker-compose.yml` menggunakan text editor (VS Code, Notepad, dll).
3. Cari bagian `backend` -> `environment` dan ubah `WHISPER_MODEL` menjadi `medium`:
   ```yaml
     backend:
       ...
       environment:
         - DATABASE_URL=postgresql://postgres:postgres@db:5432/iqlab
         - WHISPER_MODEL=medium  # <-- Diubah dari 'small' menjadi 'medium'
   ```
4. Simpan file tersebut.

### Langkah 4: Jalankan Docker Stack
Buka terminal Anda di dalam folder `iqlab-dev` (tempat file `docker-compose.yml` berada), lalu jalankan:

```bash
docker compose up --build
```
* Docker akan mengunduh image PostgreSQL, Node.js, dan membuat container backend & frontend.
* Proses build pertama kali mungkin memakan waktu 2-3 menit untuk mengunduh package.

### Langkah 5: Seed Database Al-Qur'an (114 Surah)
Setelah semua container berjalan (status "Running" di Docker Desktop), database lokal Anda masih kosong. Untuk mengunduh data Al-Qur'an dan membuat vector embedding secara otomatis di dalam container, buka terminal baru di folder yang sama dan jalankan:

```bash
docker compose exec backend python backend/seed_all.py
```
* Perintah ini akan memasukkan 6,236 ayat lengkap dengan terjemahan Indonesia dan menghitung koordinat vector-nya langsung di MiniPC Anda.

### Langkah 6: Jalankan Unit Test Makhraj (Verifikasi DSP)
Untuk memastikan algoritma deteksi Makhraj (`ح` vs `ه`) berjalan dengan benar di mesin lokal Anda, jalankan perintah tes berikut:

```bash
docker compose exec backend python tests/test_makhraj.py
```
*(Anda harus melihat output hijau `✅ ALL TESTS PASSED SUCCESSFULLY!`)*

---

## 🌐 3. Alamat Akses Lokal

Setelah semua langkah selesai, Anda dapat mengakses aplikasi langsung melalui browser:

* **Aplikasi Utama (Frontend)**: [http://localhost:5173](http://localhost:5173)
* **Dokumentasi API (Backend)**: [http://localhost:8000](http://localhost:8000)
* **Cek Kesehatan API**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 💡 Tips Pengembangan Selanjutnya
* **Hot Reload**: Jika Anda mengubah file kode di folder `src/` (frontend) atau `backend/` (backend) pada MiniPC Anda, aplikasi di dalam Docker akan otomatis terupdate secara instan tanpa perlu merestart Docker.
* **Mematikan Aplikasi**: Untuk menghentikan aplikasi, tekan `Ctrl + C` di terminal Docker Anda, atau jalankan `docker compose down`.

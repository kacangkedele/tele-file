# tele-file
Say Provides Bot Conver file bot telegram 

# FlenConvert Bot - Panduan Termux

Bot Telegram konversi file (TXT↔VCF, Gabung, Potong, Rapikan, MSG, XLS, ADM/NVY) yang dirancang khusus untuk dijalankan di **Termux** tanpa error.

---

## 📋 Persyaratan

- HP Android dengan Termux terinstall
- Koneksi internet stabil
- Akun Telegram + token bot dari @BotFather

---

## 🚀 Instalasi Cepat (5 menit)

### Langkah 1: Install Termux
Download Termux dari **F-Droid** (rekomendasi) atau Play Store.
> ⚠️ Versi Play Store sudah lama tidak diupdate, **disarankan F-Droid**.

### Langkah 2: Copy file bot ke Termux

**Opsi A: Lewat storage (mudah)**
```bash
# Di Termux, jalankan sekali:
termux-setup-storage
# Izinkan akses storage di HP Anda

# Copy folder flenconvert-bot ke /sdcard/Download/
# Lalu di Termux:
cp -r /sdcard/Download/flenconvert-bot ~/flenconvert-bot
cd ~/flenconvert-bot
```

**Opsi B: Paste manual lewat nano**
```bash
mkdir -p ~/flenconvert-bot && cd ~/flenconvert-bot
nano bot.py          # paste isi bot.py, save: Ctrl+O Enter Ctrl+X
nano converters.py   # paste isi converters.py
nano config.json     # paste isi config.json
nano requirements.txt
nano setup.sh
nano run.sh
nano test_bot.py
```

### Langkah 3: Jalankan setup

```bash
cd ~/flenconvert-bot
chmod +x setup.sh run.sh
./setup.sh
```

Setup akan otomatis:
- Update packages Termux
- Install Python + clang + openssl (untuk kompilasi & SSL)
- Install `python-telegram-bot` dan `openpyxl`
- Setup akses storage

### Langkah 4: Dapatkan token bot

1. Buka aplikasi **Telegram** di HP
2. Cari **@BotFather** (centang biru)
3. Kirim: `/newbot`
4. Ketik nama bot (bebas), contoh: `FlenConvert Bot`
5. Ketik username bot (harus akhir `bot`), contoh: `flenconvert_bot`
6. BotFather akan memberi **token** dengan format:
   ```
   1234567890:ABCdefGhi-JklMnoPqrStuVwxYz
   ```
7. **Copy** token tersebut

### Langkah 5: Edit config.json

```bash
nano config.json
```

Ganti baris:
```json
"bot_token": "PASTE_TOKEN_DARI_BOTFATHER_DISINI",
```
Menjadi:
```json
"bot_token": "1234567890:ABCdefGhi-JklMnoPqrStuVwxYz",
```

Ganti juga `admin_username` dengan username Telegram Anda (tanpa @):
```json
"admin_username": "AnggaOfficial",
```

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

### Langkah 6: Test kesiapan bot

```bash
python test_bot.py
```

Output yang diharapkan:
```
============================================================
  FlenConvert Bot - Pre-flight Diagnostic
============================================================

[1/6] Cek versi Python...
  ✅ Python 3.11.5
[2/6] Cek python-telegram-bot...
  ✅ python-telegram-bot v21.6
[3/6] Cek openpyxl (untuk fitur XLS)...
  ✅ openpyxl v3.1.5
[4/6] Cek config.json...
  ✅ Token terisi (format valid)
[5/6] Cek koneksi ke Telegram API...
  ✅ Telegram API (api.telegram.org:443) reachable
[6/6] Cek converters.py...
  ✅ converters.py OK (9 fungsi)

Bonus: Cek bot.py...
  ✅ bot.py siap dijalankan

============================================================
  RINGKASAN
============================================================
  ✅ Python
  ✅ python-telegram-bot
  ✅ openpyxl (optional)
  ✅ config.json + token
  ✅ Network (Telegram API)
  ✅ converters.py

✅ Semua cek lolos! Bot siap dijalankan.
```

### Langkah 7: Jalankan bot!

```bash
./run.sh
```

Atau manual:
```bash
python bot.py
```

Jika muncul:
```
============================================================
🤖 FlenConvert Bot
👤 Admin: @AnggaOfficial
💎 Premium features: blue branding link active
============================================================
Bot sedang berjalan... Tekan Ctrl+C untuk berhenti.
============================================================
```

**Bot sudah aktif!** Buka Telegram, cari bot Anda, kirim `/start`.

---

## 🎯 Cara Pakai Bot

Setelah kirim `/start`, akan muncul menu tombol di keyboard:

| Tombol | Fungsi |
|--------|--------|
| 💎 Status 💎 | Cek info bot & user ID |
| 🗂️ ADM & NVY 🗂️ | Convert nomor ke format ADM-001:+62xxx |
| 📜 Rapikan TXT 📜 | Hapus duplikat + normalisasi nomor |
| 📊 POTONG VCF 📊 | Pecah VCF besar jadi file kecil (zip) |
| 📂 MSG to TXT 📂 | Simpan pesan/forward ke file TXT |
| 📄 TXT to VCF 📄 | Convert daftar nomor ke kontak VCF |
| 📁 BAGI VCF 📁 | Alias POTONG VCF |
| 📈 XLS to TXT 📈 | Convert Excel ke TXT |
| ♻️ VCF to TXT ♻️ | Ekstrak nomor dari VCF |
| 📥 Gabung TXT 📥 | Gabung beberapa TXT jadi satu |
| 📥 Gabung VCF 📥 | Gabung beberapa VCF jadi satu |

**Cara pakai:**
1. Klik tombol menu
2. Bot kasih instruksi (kirim file / pilih opsi)
3. Kirim file sesuai format yang diminta
4. Bot balas dengan file hasil konversi

---

## 🔧 Troubleshooting

### Error: `pip install` gagal / "error: command 'clang' failed"

**Solusi:** Install build tools dulu
```bash
pkg install clang make pkg-config openssl libxml2 libxslt
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Error: `Permission denied` saat `./run.sh`

**Solusi:** Beri permission execute
```bash
chmod +x run.sh setup.sh
```

### Error: `ModuleNotFoundError: No module named 'telegram'`

**Solusi:** Reinstall dependencies
```bash
pip install --force-reinstall python-telegram-bot==21.6
```

### Error: `Network is unreachable` / `Connection refused`

**Penyebab:** WiFi kantor/sekolah memblokir Telegram

**Solusi:**
- Coba gunakan **kuota data seluler**
- Atau gunakan VPN
- Test koneksi: `python test_bot.py`

### Error: `Conflict: terminated by other getUpdates request`

**Penyebab:** Bot dijalankan dari 2 tempat sekaligus

**Solusi:**
- Pastikan hanya ada 1 instance bot berjalan
- Hentikan semua proses: `pkill -f bot.py`
- Jalankan ulang

### Error: `openpyxl tidak terinstall` (saat pakai XLS to TXT)

**Solusi:**
```bash
pip install openpyxl
# Jika gagal:
pkg install clang make
pip install --no-cache-dir openpyxl
```

Bot tetap bisa jalan tanpa openpyxl - hanya fitur **XLS to TXT** yang nonaktif.

### Bot tidak merespon / tidak menerima pesan

1. Cek apakah bot berjalan:
   ```bash
   ps aux | grep bot.py
   ```
2. Cek log error:
   ```bash
   python bot.py 2>&1 | tee bot.log
   ```
3. Pastikan token benar di config.json
4. Pastikan internet stabil

### Termux mati saat HP sleep

**Solusi:**
```bash
pkg install termux-wake-lock
termux-wake-lock
# Untuk release:
# termux-wake-unlock
```

Atau gunakan aplikasi **Tasker** atau **MacroDroid** untuk keep Termux alive.

---

## 📞 Bantuan

Jika masih bermasalah, jalankan diagnostic dan kirim outputnya:
```bash
python test_bot.py > diagnostic.txt 2>&1
```

Lalu kirim file `diagnostic.txt` ke admin: @AnggaOfficial

---

## 💎 Fitur Premium (Aktif)

- ✅ **Branding biru** - "Bot Convert File By Angga Official" tampil sebagai link biru di setiap pesan
- ✅ **Decorative separators** - garis pemisah `━━━━━━━━`
- ✅ **Inline keyboard** - tombol premium untuk multi-file ops
- ✅ **Format Markdown** - bold, italic, code blocks
- ✅ **State management** - bot mengingat mode user
- ✅ **Error handling** - graceful error, bot tidak crash
- ✅ **Auto cleanup** - temporary files otomatis dibersihkan

---

## 📁 Struktur File

```
flenconvert-bot/
├── bot.py              # File utama bot (semua handler)
├── converters.py       # Logika konversi (9 fitur)
├── config.json         # Token + pengaturan
├── requirements.txt    # Dependency Python
├── setup.sh            # Script install Termux
├── run.sh              # Script jalankan bot
├── test_bot.py         # Diagnostic pre-flight
└── README.md           # File ini
```

---

**Bot Convert File By Angga Official** - Dibuat dengan ❤️ untuk pengguna Termux

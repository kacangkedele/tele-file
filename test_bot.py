#!/usr/bin/env python3
# ============================================================
# FlenConvert Bot - Pre-flight Diagnostic
# Jalankan SEBELUM bot.py untuk memastikan semua siap:
#   python test_bot.py
# ============================================================

import sys
import os
import json
import socket
import importlib

# Warna ANSI (dimatikan kalau bukan TTY)
if sys.stdout.isatty():
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'
else:
    GREEN = RED = YELLOW = CYAN = NC = ''

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)


def header():
    print()
    print("=" * 60)
    print(CYAN + "  FlenConvert Bot - Pre-flight Diagnostic" + NC)
    print("=" * 60)
    print()


def step(num, total, msg):
    print(YELLOW + "[" + str(num) + "/" + str(total) + "]" + NC + " " + msg)


def ok(msg):
    print("  " + GREEN + "✅ " + msg + NC)


def warn(msg):
    print("  " + YELLOW + "⚠️  " + msg + NC)


def fail(msg):
    print("  " + RED + "❌ " + msg + NC)


def hint(msg):
    print("  " + YELLOW + "   " + msg + NC)


# --------------------------------------------------------------------
def check_python_version():
    """Cek versi Python (butuh 3.8+)."""
    step(1, 6, "Cek versi Python...")
    v = sys.version_info
    if v < (3, 8):
        fail("Python " + str(v.major) + "." + str(v.minor) + " - terlalu lama")
        hint("Butuh Python 3.8+. Install: pkg install python")
        return False
    ok("Python " + str(v.major) + "." + str(v.minor) + "." + str(v.micro))
    return True


def check_telegram_lib():
    """Cek python-telegram-bot terinstall."""
    step(2, 6, "Cek python-telegram-bot...")
    try:
        import telegram
        from telegram import __version__ as tver
        ok("python-telegram-bot v" + str(tver))
        return True
    except ImportError as e:
        fail("Tidak terinstall: " + str(e))
        hint("Install: pip install python-telegram-bot")
        return False


def check_openpyxl():
    """Cek openpyxl (optional - hanya untuk fitur XLS)."""
    step(3, 6, "Cek openpyxl (untuk fitur XLS)...")
    try:
        import openpyxl
        ok("openpyxl v" + str(openpyxl.__version__))
        return True
    except ImportError:
        warn("openpyxl belum terinstall")
        hint("Fitur 'XLS to TXT' akan dinonaktifkan, fitur lain tetap jalan")
        hint("Install: pip install openpyxl")
        return None  # Bukan error fatal


def check_config():
    """Cek config.json dan token."""
    step(4, 6, "Cek config.json...")
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    if not os.path.exists(config_path):
        fail("config.json tidak ditemukan di:")
        print("     " + config_path)
        return False
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        fail("config.json rusak: " + str(e))
        return False

    token = cfg.get('bot_token', '')
    if not token or 'PASTE_TOKEN' in token:
        fail("Token bot belum diisi!")
        hint("Edit config.json, ganti 'PASTE_TOKEN_DARI_BOTFATHER_DISINI'")
        hint("dengan token dari @BotFather")
        return False

    # Validasi format token: angka:huruf_angka
    if ':' not in token or len(token) < 20:
        fail("Format token tidak valid: '" + token[:10] + "...'")
        hint("Token harus format: 123456789:ABCdefGhi_Jkl")
        return False

    ok("Token terisi (format valid)")
    print("  " + CYAN + "   Admin: @" + cfg.get('admin_username', 'AnggaOfficial') + NC)
    print("  " + CYAN + "   Bot name: " + cfg.get('bot_name', 'FlenConvert') + NC)
    return True


def check_network():
    """Cek koneksi ke Telegram API."""
    step(5, 6, "Cek koneksi ke Telegram API...")
    try:
        sock = socket.create_connection(('api.telegram.org', 443), timeout=8)
        sock.close()
        ok("Telegram API (api.telegram.org:443) reachable")
        return True
    except (socket.timeout, OSError) as e:
        fail("Tidak bisa konek ke Telegram API: " + str(e))
        hint("Cek koneksi internet Anda")
        hint("Jika WiFi kantor/sekolah memblokir, coba kuota data")
        return False


def check_converters():
    """Cek modul converters.py bisa di-import."""
    step(6, 6, "Cek converters.py...")
    try:
        if 'converters' in sys.modules:
            importlib.reload(sys.modules['converters'])
        else:
            import converters
        # Test fungsi-fungsi inti
        funcs = ['txt_to_vcf', 'vcf_to_txt', 'merge_txt', 'merge_vcf',
                 'split_vcf', 'clean_txt', 'msg_to_txt', 'xls_to_txt',
                 'to_adm_nvy_format']
        missing = [f for f in funcs if not hasattr(converters, f)]
        if missing:
            fail("Fungsi hilang: " + str(missing))
            return False
        ok("converters.py OK (" + str(len(funcs)) + " fungsi)")
        return True
    except Exception as e:
        fail("Error import converters.py: " + str(e))
        return False


def check_bot_imports():
    """Bonus: cek bot.py bisa di-import."""
    print()
    print(CYAN + "Bonus: Cek bot.py..." + NC)
    try:
        if 'bot' in sys.modules:
            del sys.modules['bot']
        import bot
        ok("bot.py siap dijalankan")
        return True
    except SystemExit:
        # bot.py exit kalau token belum diisi (sudah dicek di check_config)
        warn("bot.py exit (kemungkinan token belum diisi)")
        return False
    except Exception as e:
        fail("Error import bot.py: " + str(e))
        return False


# --------------------------------------------------------------------
def main():
    header()

    results = {
        'Python': check_python_version(),
        'python-telegram-bot': check_telegram_lib(),
        'openpyxl (optional)': check_openpyxl(),
        'config.json + token': check_config(),
        'Network (Telegram API)': check_network(),
        'converters.py': check_converters(),
    }

    # Cek bot.py hanya kalau semua fatal check lolos
    all_fatal_ok = all(v for v in results.values() if v is not None)
    bot_ok = check_bot_imports() if all_fatal_ok else False

    print()
    print("=" * 60)
    print(CYAN + "  RINGKASAN" + NC)
    print("=" * 60)
    for name, ok_val in results.items():
        if ok_val is None:
            mark = YELLOW + "⚠️ " + NC
        elif ok_val:
            mark = GREEN + "✅ " + NC
        else:
            mark = RED + "❌ " + NC
        print("  " + mark + name)

    print()
    fatal_failed = [k for k, v in results.items() if v is False]
    if fatal_failed:
        fail("Ada " + str(len(fatal_failed)) + " masalah yang harus diperbaiki:")
        for f in fatal_failed:
            print("   • " + f)
        print()
        hint("Setelah diperbaiki, jalankan ulang: python test_bot.py")
        sys.exit(1)
    else:
        optional_failed = [k for k, v in results.items() if v is None]
        if optional_failed:
            ok("Bot siap dijalankan!")
            print("   " + YELLOW + "(fitur optional nonaktif: " + ", ".join(optional_failed) + ")" + NC)
        else:
            ok("Semua cek lolos! Bot siap dijalankan.")
        print()
        print(CYAN + "Jalankan dengan:" + NC + " ./run.sh")
        print(CYAN + "Atau manual:" + NC + "     python bot.py")
        sys.exit(0)


if __name__ == '__main__':
    main()

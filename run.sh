#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# FlenConvert Bot - Run Script
# Jalankan bot dengan auto-check kesiapan
# ============================================================

cd "$(dirname "$0")"

# Warna
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "============================================================"
echo -e "${CYAN}  FlenConvert Bot - Starting...${NC}"
echo "============================================================"
echo ""

# Cek file config ada
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ config.json tidak ditemukan!${NC}"
    echo -e "${YELLOW}   Pastikan Anda berada di direktori flenconvert-bot${NC}"
    exit 1
fi

# Cek apakah token masih default
if grep -q "PASTE_TOKEN_DARI_BOTFATHER_DISINI" config.json; then
    echo -e "${RED}❌ Token bot belum diisi!${NC}"
    echo ""
    echo -e "${YELLOW}Cara mendapatkan token:${NC}"
    echo "  1. Buka Telegram, cari @BotFather"
    echo "  2. Kirim /newbot"
    echo "  3. Ikuti instruksi"
    echo "  4. Copy token yang diberikan"
    echo ""
    echo -e "${YELLOW}Lalu edit config.json:${NC}"
    echo "  nano config.json"
    echo "  Ganti 'PASTE_TOKEN_DARI_BOTFATHER_DISINI' dengan token Anda"
    echo "  Save: Ctrl+O, Enter, Ctrl+X"
    exit 1
fi

# Cek apakah Python tersedia
if ! command -v python >/dev/null 2>&1; then
    echo -e "${RED}❌ Python tidak ditemukan!${NC}"
    echo -e "${YELLOW}   Jalankan: ./setup.sh${NC}"
    exit 1
fi

# Cek apakah python-telegram-bot terinstall
if ! python -c "import telegram" >/dev/null 2>&1; then
    echo -e "${RED}❌ python-telegram-bot belum terinstall!${NC}"
    echo -e "${YELLOW}   Jalankan: ./setup.sh${NC}"
    echo -e "${YELLOW}   Atau manual: pip install -r requirements.txt${NC}"
    exit 1
fi

# Quick pre-flight check
echo -e "${YELLOW}Pre-flight check...${NC}"
if python test_bot.py; then
    echo ""
    echo -e "${GREEN}✅ Semua siap, menjalankan bot...${NC}"
    echo ""
    echo "============================================================"
    # Jalankan bot
    python bot.py
else
    echo ""
    echo -e "${RED}❌ Pre-flight check gagal. Perbaiki dulu.${NC}"
    echo -e "${YELLOW}   Ketik 'y' untuk lanjut menjalankan bot, atau tekan lain untuk batal${NC}"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        echo ""
        echo "============================================================"
        python bot.py
    else
        exit 1
    fi
fi

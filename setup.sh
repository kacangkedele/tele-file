#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# FlenConvert Bot - Termux Setup Script (Enhanced)
# Mengatasi masalah umum di Termux:
#   - Build tools (clang, make) untuk kompilasi
#   - OpenSSL untuk koneksi HTTPS ke Telegram API
#   - libxml2/libxslt untuk openpyxl
#   - Storage permission untuk akses file
# ============================================================

set -e

# Warna untuk output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "  FlenConvert Bot - Termux Setup"
echo "============================================================"
echo ""

# Function untuk cek command tersedia
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ------------------------------------------------------------
# Step 1: Update & upgrade packages
# ------------------------------------------------------------
echo -e "${YELLOW}[1/7]${NC} Updating package lists..."
pkg update -y || {
    echo -e "${RED}❌ Gagal update pkg. Coba: pkg update${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}[2/7]${NC} Upgrading packages..."
pkg upgrade -y || true

# ------------------------------------------------------------
# Step 3: Install Python + build tools
# Termux butuh clang & make untuk compile beberapa Python package
# ------------------------------------------------------------
echo ""
echo -e "${YELLOW}[3/7]${NC} Installing Python and build tools..."
pkg install -y python python-pip clang make pkg-config || {
    echo -e "${RED}❌ Gagal install Python/build tools${NC}"
    exit 1
}

# ------------------------------------------------------------
# Step 4: Install libraries untuk SSL & Excel support
# ------------------------------------------------------------
echo ""
echo -e "${YELLOW}[4/7]${NC} Installing SSL and XML libraries..."
pkg install -y openssl libxml2 libxslt rust || {
    echo -e "${YELLOW}⚠️  Beberapa library gagal install, lanjut...${NC}"
}

# ------------------------------------------------------------
# Step 5: Setup storage (untuk akses /sdcard kalau perlu)
# ------------------------------------------------------------
echo ""
echo -e "${YELLOW}[5/7]${NC} Setting up storage access..."
if command_exists termux-setup-storage; then
    if [ ! -d "$HOME/storage" ]; then
        termux-setup-storage || true
        echo -e "${YELLOW}⚠️  Jika muncul dialog izin, klik ALLOW di HP Anda${NC}"
        sleep 3
    fi
    echo -e "${GREEN}✅ Storage access ready${NC}"
else
    echo -e "${YELLOW}⚠️  termux-setup-storage tidak tersedia (mungkin bukan Termux)${NC}"
fi

# ------------------------------------------------------------
# Step 6: Upgrade pip, setuptools, wheel
# ------------------------------------------------------------
echo ""
echo -e "${YELLOW}[6/7]${NC} Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel || {
    echo -e "${YELLOW}⚠️  Gagal upgrade pip, lanjut dengan versi existing...${NC}"
}

# ------------------------------------------------------------
# Step 7: Install bot dependencies
# ------------------------------------------------------------
echo ""
echo -e "${YELLOW}[7/7]${NC} Installing bot dependencies..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pip install -r requirements.txt || {
    echo -e "${RED}❌ Gagal install dependencies dari requirements.txt${NC}"
    echo -e "${YELLOW}Mencoba install satu per satu...${NC}"
    pip install "python-telegram-bot==21.6" || exit 1
    pip install "openpyxl==3.1.5" || echo -e "${YELLOW}⚠️  openpyxl gagal (fitur XLS akan dinonaktifkan)${NC}"
}

# ------------------------------------------------------------
# Make scripts executable
# ------------------------------------------------------------
chmod +x "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/setup.sh" 2>/dev/null || true

# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo -e "${GREEN}  ✅ Setup selesai!${NC}"
echo "============================================================"
echo ""
echo "Langkah selanjutnya:"
echo ""
echo -e "  ${YELLOW}1.${NC} Dapatkan token bot:"
echo "     - Buka Telegram, cari @BotFather"
echo "     - Kirim /newbot, ikuti instruksi"
echo "     - Copy token (format: 123456789:ABCdef...)"
echo ""
echo -e "  ${YELLOW}2.${NC} Edit config.json:"
echo "     nano config.json"
echo "     Ganti: \"PASTE_TOKEN_DARI_BOTFATHER_DISINI\""
echo "     Dengan token Anda. Simpan: Ctrl+O, Enter, Ctrl+X"
echo ""
echo -e "  ${YELLOW}3.${NC} Test kesiapan bot:"
echo "     python test_bot.py"
echo ""
echo -e "  ${YELLOW}4.${NC} Jalankan bot:"
echo "     ./run.sh"
echo ""
echo -e "  ${YELLOW}5.${NC} Buka Telegram, kirim /start ke bot Anda"
echo ""
echo "============================================================"

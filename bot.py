# ====================================================================
# FlenConvert Bot - Main Bot File
# Bot Telegram Konversi File dengan Reply Keyboard
#   - TXT <-> VCF
#   - Gabung TXT/VCF
#   - Potong VCF
#   - Rapikan TXT
#   - MSG to TXT
#   - XLS to TXT
#   - ADM & NVY Format
#
# Premium Features:
#   - Blue branding link (Markdown link)
#   - Bold/italic formatting
#   - Decorative separators
#   - Inline keyboard untuk multi-file ops
#
# Cara pakai di Termux:
#   1. Edit config.json, masukkan token dari @BotFather
#   2. pip install -r requirements.txt
#   3. python bot.py
# ====================================================================

import os
import re
import json
import logging
import tempfile
from datetime import datetime
from typing import Optional

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Import modul konversi
from converters import (
    txt_to_vcf,
    vcf_to_txt,
    merge_txt,
    merge_vcf,
    split_vcf,
    clean_txt,
    msg_to_txt,
    xls_to_txt,
    to_adm_nvy_format,
    zip_directory,
)

# --------------------------------------------------------------------
# KONFIGURASI
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

TOKEN = CONFIG['bot_token']
ADMIN_USERNAME = CONFIG.get('admin_username', 'AnggaOfficial')
BOT_NAME = CONFIG.get('bot_name', 'FlenConvert')
OWNER_ID = CONFIG.get('owner_id')
DEFAULT_CHUNK = CONFIG.get('default_vcf_chunk_size', 100)
MAX_MERGE = CONFIG.get('max_merge_files', 20)
NAME_PREFIX = CONFIG.get('contact_name_prefix', 'Contact')
ADM_FMT = CONFIG.get('adm_format', 'ADM-{num:03d}:{phone}')
NVY_FMT = CONFIG.get('nvy_format', 'NVY-{num:03d}:{phone}')

DEV_LINK = f"https://t.me/{ADMIN_USERNAME}"
# Branding blue link - ini yang muncul berwarna biru di Telegram
BRANDING_BLUE = f"[Bot Convert File By Angga Official]({DEV_LINK})"

# --------------------------------------------------------------------
# LOGGING
# --------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Kurangi noise dari library
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)


# --------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------
def md_escape(text: str) -> str:
    """Escape karakter special Markdown (legacy mode)."""
    if not text:
        return ""
    return re.sub(r'([_*\[\]\(\)`])', r'\\\1', str(text))


def get_main_menu() -> ReplyKeyboardMarkup:
    """Susunan tombol Reply Keyboard utama."""
    keyboard = [
        [KeyboardButton("💎 Status 💎")],
        [KeyboardButton("🗂️ ADM & NVY 🗂️"), KeyboardButton("📜 Rapikan TXT 📜")],
        [KeyboardButton("📊 POTONG VCF 📊"), KeyboardButton("📂 MSG to TXT 📂")],
        [KeyboardButton("📄 TXT to VCF 📄"), KeyboardButton("📁 BAGI VCF 📁")],
        [KeyboardButton("📈 XLS to TXT 📈"), KeyboardButton("♻️ VCF to TXT ♻️")],
        [KeyboardButton("📥 Gabung TXT 📥"), KeyboardButton("📥 Gabung VCF 📥")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_finish_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard untuk tombol 'Selesai' pada mode multi-file."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Selesai & Proses", callback_data="finish_collect")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_collect")],
    ])


def branding_footer() -> str:
    """Footer branding (warna biru karena link)."""
    return (
        f"\n\n━━━━━━━━━━━━━━━━━━\n"
        f"💎 {BRANDING_BLUE} 💎\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def safe_delete_message(func):
    """Decorator untuk handle error pada message edit/delete."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Message operation failed: {e}")
    return wrapper


# --------------------------------------------------------------------
# COMMAND HANDLERS
# --------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start - menampilkan welcome + keyboard."""
    user = update.effective_user
    name = md_escape(user.first_name or "User")

    welcome = (
        f"👋 Hai, *{name}*!\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *{BOT_NAME}* ⚡\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Saya dapat convert file secara instan 🚀\n\n"
        f"⚠️ *Note:* Order bot ini hanya melalui "
        f"[{ADMIN_USERNAME}]({DEV_LINK}), "
        f"selain itu dipastikan *SCAM*‼️\n"
        f"{branding_footer()}\n\n"
        f"Pilih menu di bawah untuk mulai 👇"
    )

    # Reset state user
    context.user_data.clear()

    await update.message.reply_text(
        welcome,
        reply_markup=get_main_menu(),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help."""
    help_text = (
        f"📖 *Panduan Penggunaan*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📄 *TXT to VCF* - Convert daftar nomor ke kontak VCF\n"
        f"♻️ *VCF to TXT* - Ekstrak nomor dari VCF ke TXT\n"
        f"📥 *Gabung TXT/VCF* - Gabungkan beberapa file\n"
        f"📊 *Potong VCF* - Pecah VCF besar jadi kecil\n"
        f"📜 *Rapikan TXT* - Hapus duplikat & format nomor\n"
        f"📂 *MSG to TXT* - Simpan pesan ke file TXT\n"
        f"📈 *XLS to TXT* - Convert Excel ke TXT\n"
        f"🗂️ *ADM & NVY* - Format kontak khusus\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Cukup klik tombol menu, lalu ikuti instruksi.\n"
        f"{branding_footer()}"
    )
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=get_main_menu(),
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /cancel - batalkan operasi saat ini."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Operasi dibatalkan.\nKlik menu untuk mulai lagi 👇",
        reply_markup=get_main_menu(),
    )


# --------------------------------------------------------------------
# STATUS
# --------------------------------------------------------------------
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan status bot & user."""
    user = update.effective_user
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    status_text = (
        f"📊 *Status Bot*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Nama: {md_escape(user.first_name or '-')}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"🤖 Bot: *{BOT_NAME}*\n"
        f"⚡ Status: *Online*\n"
        f"🕐 Server Time: `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📞 Admin: [{ADMIN_USERNAME}]({DEV_LINK})\n"
        f"{branding_footer()}"
    )
    await update.message.reply_text(
        status_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=get_main_menu(),
    )


# --------------------------------------------------------------------
# 1. TXT -> VCF
# --------------------------------------------------------------------
async def start_txt_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'txt_to_vcf'
    await update.message.reply_text(
        f"📄 *TXT to VCF Converter*\n\n"
        f"Kirim file *TXT* berisi daftar nomor (satu nomor per baris).\n\n"
        f"Format yang didukung: `0812xxx`, `+62812xxx`, `62812xxx`\n\n"
        f"Kirim /cancel untuk batal.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu(),
    )


async def process_txt_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("⚠️ File harus berformat *.txt*", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await update.message.reply_text("⏳ Mengunduh & memproses...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_path = os.path.join(tmp, 'output.vcf')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            await status_msg.edit_text("⏳ Konversi sedang berjalan...")
            success, total = txt_to_vcf(input_path, output_path, NAME_PREFIX)

            if success == 0:
                await status_msg.edit_text(
                    "❌ Tidak ada nomor valid ditemukan dalam file.\n"
                    "Pastikan format: `0812xxx` atau `+62812xxx`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"converted_{success}_contacts.vcf",
                    caption=(
                        f"✅ *Konversi Berhasil!*\n\n"
                        f"📊 Total baris: *{total}*\n"
                        f"✅ Nomor valid: *{success}*\n"
                        f"❌ Nomor invalid: *{total - success}*\n"
                        f"📦 Format: VCF v3.0\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("TXT to VCF error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data['mode'] = None


# --------------------------------------------------------------------
# 2. VCF -> TXT
# --------------------------------------------------------------------
async def start_vcf_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'vcf_to_txt'
    await update.message.reply_text(
        f"♻️ *VCF to TXT Converter*\n\n"
        f"Kirim file *VCF* (kontak telepon).\n"
        f"Bot akan ekstrak semua nomor ke format TXT.\n\n"
        f"Kirim /cancel untuk batal.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu(),
    )


async def process_vcf_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(('.vcf', '.vcard')):
        await update.message.reply_text("⚠️ File harus berformat *.vcf*", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await update.message.reply_text("⏳ Memproses...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_path = os.path.join(tmp, 'extracted.txt')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            count = vcf_to_txt(input_path, output_path)

            if count == 0:
                await status_msg.edit_text("❌ Tidak ada nomor ditemukan dalam VCF.")
                return

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"extracted_{count}_numbers.txt",
                    caption=(
                        f"✅ *Ekstraksi Berhasil!*\n\n"
                        f"📊 Nomor diekstrak: *{count}*\n"
                        f"📦 Format: TXT (satu nomor per baris)\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("VCF to TXT error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data['mode'] = None


# --------------------------------------------------------------------
# 3. Gabung TXT
# --------------------------------------------------------------------
async def start_merge_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'merge_txt'
    context.user_data['files'] = []
    context.user_data['tmpdir'] = tempfile.mkdtemp(prefix='merge_txt_')
    await update.message.reply_text(
        f"📥 *Gabung TXT*\n\n"
        f"Kirim semua file *TXT* yang ingin digabung (maks {MAX_MERGE} file).\n"
        f"Duplikat akan otomatis dihapus.\n\n"
        f"Setelah selesai kirim semua file, klik tombol *Selesai* di bawah 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def add_merge_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("⚠️ File harus *.txt*. Atau klik Selesai jika sudah selesai.")
        return

    files = context.user_data.get('files', [])
    if len(files) >= MAX_MERGE:
        await update.message.reply_text(f"⚠️ Maksimal {MAX_MERGE} file. Klik Selesai.")
        return

    tmpdir = context.user_data.get('tmpdir')
    if not tmpdir or not os.path.exists(tmpdir):
        tmpdir = tempfile.mkdtemp(prefix='merge_txt_')
        context.user_data['tmpdir'] = tmpdir

    save_path = os.path.join(tmpdir, f"file_{len(files)+1}_{doc.file_name}")
    file = await doc.get_file()
    await file.download_to_drive(save_path)
    files.append(save_path)
    context.user_data['files'] = files

    await update.message.reply_text(
        f"✅ File `{len(files)}` tersimpan: `{md_escape(doc.file_name)}`\n"
        f"Kirim file berikutnya atau klik *Selesai*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def finish_merge_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    files = context.user_data.get('files', [])
    if not files:
        await query.edit_message_text("❌ Tidak ada file dikumpulkan. Operasi dibatalkan.")
        context.user_data.clear()
        return

    status_msg = await query.edit_message_text("⏳ Menggabungkan file...")
    await context.bot.send_chat_action(query.message.chat.id, ChatAction.TYPING)

    tmpdir = context.user_data.get('tmpdir')
    output_path = os.path.join(tmpdir, 'merged.txt')

    try:
        final_count, original_count = merge_txt(files, output_path, dedupe=True)

        with open(output_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=query.message.chat.id,
                document=f,
                filename=f"merged_{final_count}_lines.txt",
                caption=(
                    f"✅ *Gabungan Berhasil!*\n\n"
                    f"📁 File digabung: *{len(files)}*\n"
                    f"📊 Total baris asli: *{original_count}*\n"
                    f"✅ Baris unik: *{final_count}*\n"
                    f"🗑️ Duplikat dihapus: *{original_count - final_count}*\n"
                    f"{branding_footer()}"
                ),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        await status_msg.delete()
    except Exception as e:
        logger.exception("Merge TXT error")
        await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)
    finally:
        # Cleanup
        tmpdir = context.user_data.get('tmpdir')
        if tmpdir and os.path.exists(tmpdir):
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        context.user_data.clear()


# --------------------------------------------------------------------
# 4. Gabung VCF
# --------------------------------------------------------------------
async def start_merge_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'merge_vcf'
    context.user_data['files'] = []
    context.user_data['tmpdir'] = tempfile.mkdtemp(prefix='merge_vcf_')
    await update.message.reply_text(
        f"📥 *Gabung VCF*\n\n"
        f"Kirim semua file *VCF* yang ingin digabung (maks {MAX_MERGE} file).\n\n"
        f"Setelah selesai, klik tombol *Selesai* di bawah 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def add_merge_vcf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(('.vcf', '.vcard')):
        await update.message.reply_text("⚠️ File harus *.vcf*. Atau klik Selesai jika sudah selesai.")
        return

    files = context.user_data.get('files', [])
    if len(files) >= MAX_MERGE:
        await update.message.reply_text(f"⚠️ Maksimal {MAX_MERGE} file. Klik Selesai.")
        return

    tmpdir = context.user_data.get('tmpdir')
    if not tmpdir or not os.path.exists(tmpdir):
        tmpdir = tempfile.mkdtemp(prefix='merge_vcf_')
        context.user_data['tmpdir'] = tmpdir

    save_path = os.path.join(tmpdir, f"file_{len(files)+1}_{doc.file_name}")
    file = await doc.get_file()
    await file.download_to_drive(save_path)
    files.append(save_path)
    context.user_data['files'] = files

    await update.message.reply_text(
        f"✅ File `{len(files)}` tersimpan: `{md_escape(doc.file_name)}`\n"
        f"Kirim file berikutnya atau klik *Selesai*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def finish_merge_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    files = context.user_data.get('files', [])
    if not files:
        await query.edit_message_text("❌ Tidak ada file dikumpulkan. Operasi dibatalkan.")
        context.user_data.clear()
        return

    status_msg = await query.edit_message_text("⏳ Menggabungkan VCF...")
    await context.bot.send_chat_action(query.message.chat.id, ChatAction.TYPING)

    tmpdir = context.user_data.get('tmpdir')
    output_path = os.path.join(tmpdir, 'merged.vcf')

    try:
        count = merge_vcf(files, output_path)

        with open(output_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=query.message.chat.id,
                document=f,
                filename=f"merged_{count}_contacts.vcf",
                caption=(
                    f"✅ *Gabungan VCF Berhasil!*\n\n"
                    f"📁 File digabung: *{len(files)}*\n"
                    f"👥 Total kontak: *{count}*\n"
                    f"{branding_footer()}"
                ),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        await status_msg.delete()
    except Exception as e:
        logger.exception("Merge VCF error")
        await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)
    finally:
        tmpdir = context.user_data.get('tmpdir')
        if tmpdir and os.path.exists(tmpdir):
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        context.user_data.clear()


# --------------------------------------------------------------------
# 5. Potong VCF (Split VCF)
# --------------------------------------------------------------------
async def start_split_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'split_vcf'
    # Tampilkan pilihan ukuran chunk via inline keyboard
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("50 kontak", callback_data="split_50"),
            InlineKeyboardButton("100 kontak", callback_data="split_100"),
            InlineKeyboardButton("200 kontak", callback_data="split_200"),
        ],
        [InlineKeyboardButton("500 kontak", callback_data="split_500"),
         InlineKeyboardButton("1000 kontak", callback_data="split_1000")],
    ])
    await update.message.reply_text(
        f"📊 *Potong VCF*\n\n"
        f"Pilih jumlah kontak per file hasil pecahan:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb,
    )


async def handle_split_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chunk_size = int(query.data.split('_')[1])
    context.user_data['split_chunk'] = chunk_size
    context.user_data['mode'] = 'split_vcf'

    await query.edit_message_text(
        f"✅ Chunk size: *{chunk_size} kontak/file*\n\n"
        f"Sekarang kirim file *VCF* yang ingin dipecah.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def process_split_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(('.vcf', '.vcard')):
        await update.message.reply_text("⚠️ File harus berformat *.vcf*", parse_mode=ParseMode.MARKDOWN)
        return

    chunk_size = context.user_data.get('split_chunk', DEFAULT_CHUNK)
    status_msg = await update.message.reply_text(f"⏳ Memecah VCF (chunk: {chunk_size})...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_dir = os.path.join(tmp, 'output')
        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(tmp, 'split_vcf.zip')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            file_count, total_contacts = split_vcf(input_path, output_dir, chunk_size)

            if file_count == 0:
                await status_msg.edit_text("❌ Tidak ada kontak ditemukan dalam VCF.")
                return

            # Zip semua file hasil pecahan
            zip_directory(output_dir, zip_path)

            with open(zip_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"split_{file_count}_files_{total_contacts}_contacts.zip",
                    caption=(
                        f"✅ *VCF Berhasil Dipecah!*\n\n"
                        f"📊 Total kontak: *{total_contacts}*\n"
                        f"📁 Jumlah file: *{file_count}*\n"
                        f"📦 Per file: *{chunk_size} kontak*\n"
                        f"🗜️ Format: ZIP (berisi semua file VCF)\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("Split VCF error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data.clear()


# --------------------------------------------------------------------
# 6. Rapikan TXT
# --------------------------------------------------------------------
async def start_clean_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'clean_txt'
    await update.message.reply_text(
        f"📜 *Rapikan TXT*\n\n"
        f"Kirim file *TXT* berisi daftar nomor.\n"
        f"Bot akan:\n"
        f"  • Hapus duplikat\n"
        f"  • Normalisasi format (ke +62)\n"
        f"  • Sortir secara alfabetis\n\n"
        f"Kirim /cancel untuk batal.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu(),
    )


async def process_clean_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("⚠️ File harus berformat *.txt*", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await update.message.reply_text("⏳ Merapikan file...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_path = os.path.join(tmp, 'cleaned.txt')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            final_count, original_count, duplicates = clean_txt(input_path, output_path)

            if final_count == 0:
                await status_msg.edit_text("❌ Tidak ada nomor valid ditemukan.")
                return

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"cleaned_{final_count}_unique.txt",
                    caption=(
                        f"✅ *File Dirapikan!*\n\n"
                        f"📊 Total baris asli: *{original_count}*\n"
                        f"✅ Nomor unik: *{final_count}*\n"
                        f"🗑️ Duplikat dihapus: *{duplicates}*\n"
                        f"🔧 Format: +62xxx (sorted)\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("Clean TXT error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data['mode'] = None


# --------------------------------------------------------------------
# 7. MSG to TXT
# --------------------------------------------------------------------
async def start_msg_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'msg_to_txt'
    context.user_data['messages'] = []
    await update.message.reply_text(
        f"📂 *MSG to TXT Converter*\n\n"
        f"Kirim atau *forward* pesan-pesan yang ingin disimpan ke TXT.\n"
        f"Bot akan kumpulkan semua pesan, lalu simpan ke satu file.\n\n"
        f"Setelah selesai, klik *Selesai* di bawah 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def collect_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kumpulkan pesan teks yang dikirim user."""
    msg = update.message
    text_parts = []

    # Ambil teks pesan
    if msg.text:
        text_parts.append(msg.text)
    elif msg.caption:
        text_parts.append(msg.caption)

    # Jika forward_date, tambahkan info pengirim asli
    if msg.forward_origin:
        try:
            origin = msg.forward_origin
            sender_name = getattr(origin, 'sender_user_name', None) or \
                          getattr(origin, 'hidden_sender_name', None) or \
                          getattr(origin, 'sender_chat_title', None) or "Unknown"
            text_parts.insert(0, f"[Forwarded from: {sender_name}]")
        except Exception:
            pass

    if not text_parts:
        await update.message.reply_text(
            "⚠️ Pesan tidak ada teks. Kirim pesan teks atau forward pesan.",
            reply_markup=get_finish_keyboard(),
        )
        return

    messages = context.user_data.get('messages', [])
    messages.append('\n'.join(text_parts))
    context.user_data['messages'] = messages

    await update.message.reply_text(
        f"✅ Pesan `{len(messages)}` tersimpan.\n"
        f"Kirim pesan berikutnya atau klik *Selesai*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_finish_keyboard(),
    )


async def finish_msg_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = context.user_data.get('messages', [])
    if not messages:
        await query.edit_message_text("❌ Tidak ada pesan dikumpulkan. Operasi dibatalkan.")
        context.user_data.clear()
        return

    status_msg = await query.edit_message_text("⏳ Menyusun file TXT...")

    with tempfile.TemporaryDirectory() as tmp:
        output_path = os.path.join(tmp, 'messages.txt')
        try:
            total_chars = msg_to_txt(messages, output_path)

            with open(output_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=query.message.chat.id,
                    document=f,
                    filename=f"messages_{len(messages)}_items.txt",
                    caption=(
                        f"✅ *Pesan Tersimpan!*\n\n"
                        f"📊 Jumlah pesan: *{len(messages)}*\n"
                        f"📝 Total karakter: *{total_chars}*\n"
                        f"📦 Format: TXT\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("MSG to TXT error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data.clear()


# --------------------------------------------------------------------
# 8. XLS to TXT
# --------------------------------------------------------------------
async def start_xls_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'xls_to_txt'
    await update.message.reply_text(
        f"📈 *XLS to TXT Converter*\n\n"
        f"Kirim file *Excel* (.xlsx atau .xls).\n"
        f"Bot akan convert semua sheet ke format TXT (tab-separated).\n\n"
        f"Kirim /cancel untuk batal.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu(),
    )


async def process_xls_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(('.xlsx', '.xls')):
        await update.message.reply_text("⚠️ File harus berformat *.xlsx* atau *.xls*", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await update.message.reply_text("⏳ Mengonversi Excel...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_path = os.path.join(tmp, 'output.txt')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            rows, sheets = xls_to_txt(input_path, output_path)

            if rows == 0:
                await status_msg.edit_text("❌ File Excel kosong atau tidak terbaca.")
                return

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"converted_{rows}_rows.txt",
                    caption=(
                        f"✅ *Konversi Excel Berhasil!*\n\n"
                        f"📊 Sheet diproses: *{sheets}*\n"
                        f"📋 Baris ditulis: *{rows}*\n"
                        f"📦 Format: TXT (tab-separated)\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except RuntimeError as e:
            # Error khusus: openpyxl belum terinstall
            logger.exception("XLS to TXT - openpyxl missing")
            await status_msg.edit_text(
                f"❌ *Module openpyxl belum terinstall*\n\n"
                f"Jalankan di Termux:\n"
                f"`pip install openpyxl`\n\n"
                f"Atau jalankan ulang `./setup.sh`",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.exception("XLS to TXT error")
            await status_msg.edit_text(
                f"❌ Error: `{md_escape(str(e))}`\n\n"
                f"Pastikan file Excel valid (.xlsx).",
                parse_mode=ParseMode.MARKDOWN
            )

    context.user_data['mode'] = None


# --------------------------------------------------------------------
# 9. ADM & NVY Format
# --------------------------------------------------------------------
async def start_adm_nvy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'adm_nvy_await'
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗂️ ADM Format", callback_data="fmt_ADM"),
         InlineKeyboardButton("🗂️ NVY Format", callback_data="fmt_NVY")],
    ])
    await update.message.reply_text(
        f"🗂️ *ADM & NVY Format Converter*\n\n"
        f"Pilih format output:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb,
    )


async def handle_adm_nvy_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    fmt = query.data.split('_')[1]
    context.user_data['mode'] = 'adm_nvy'
    context.user_data['format'] = fmt

    await query.edit_message_text(
        f"✅ Format dipilih: *{fmt}*\n\n"
        f"Kirim file *TXT* berisi daftar nomor.\n"
        f"Output: `{fmt}-001:+62xxx` (per baris)\n\n"
        f"Kirim /cancel untuk batal.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def process_adm_nvy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("⚠️ File harus berformat *.txt*", parse_mode=ParseMode.MARKDOWN)
        return

    fmt = context.user_data.get('format', 'ADM')
    status_msg = await update.message.reply_text(f"⏳ Konversi ke format {fmt}...")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, doc.file_name)
        output_path = os.path.join(tmp, f'output_{fmt.lower()}.txt')

        try:
            file = await doc.get_file()
            await file.download_to_drive(input_path)

            success, total = to_adm_nvy_format(input_path, output_path, fmt)

            if success == 0:
                await status_msg.edit_text("❌ Tidak ada nomor valid ditemukan.")
                return

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"{fmt.lower()}_{success}_numbers.txt",
                    caption=(
                        f"✅ *Konversi {fmt} Berhasil!*\n\n"
                        f"📊 Total baris: *{total}*\n"
                        f"✅ Nomor valid: *{success}*\n"
                        f"❌ Invalid: *{total - success}*\n"
                        f"📦 Format: `{fmt}-001:+62xxx`\n"
                        f"{branding_footer()}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            await status_msg.delete()
        except Exception as e:
            logger.exception("ADM/NVY error")
            await status_msg.edit_text(f"❌ Error: `{md_escape(str(e))}`", parse_mode=ParseMode.MARKDOWN)

    context.user_data.clear()


# --------------------------------------------------------------------
# ROUTING UTAMA
# --------------------------------------------------------------------
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routing pesan teks berdasarkan menu yang dipilih."""
    text = update.message.text
    mode = context.user_data.get('mode')

    # Jika sedang mode MSG to TXT, kumpulkan pesan
    if mode == 'msg_to_txt':
        await collect_msg(update, context)
        return

    # Mapping menu ke handler
    menu_map = {
        "💎 Status 💎": show_status,
        "🗂️ ADM & NVY 🗂️": start_adm_nvy,
        "📜 Rapikan TXT 📜": start_clean_txt,
        "📊 POTONG VCF 📊": start_split_vcf,
        "📂 MSG to TXT 📂": start_msg_to_txt,
        "📄 TXT to VCF 📄": start_txt_to_vcf,
        "📁 BAGI VCF 📁": start_split_vcf,
        "📈 XLS to TXT 📈": start_xls_to_txt,
        "♻️ VCF to TXT ♻️": start_vcf_to_txt,
        "📥 Gabung TXT 📥": start_merge_txt,
        "📥 Gabung VCF 📥": start_merge_vcf,
    }

    handler = menu_map.get(text)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text(
            f"ℹ️ Pilih menu dari keyboard di bawah.\n"
            f"Ketik /help untuk panduan.",
            reply_markup=get_main_menu(),
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routing file yang dikirim berdasarkan mode aktif."""
    mode = context.user_data.get('mode')

    if mode == 'txt_to_vcf':
        await process_txt_to_vcf(update, context)
    elif mode == 'vcf_to_txt':
        await process_vcf_to_txt(update, context)
    elif mode == 'merge_txt':
        await add_merge_txt_file(update, context)
    elif mode == 'merge_vcf':
        await add_merge_vcf_file(update, context)
    elif mode == 'split_vcf':
        await process_split_vcf(update, context)
    elif mode == 'clean_txt':
        await process_clean_txt(update, context)
    elif mode == 'xls_to_txt':
        await process_xls_to_txt(update, context)
    elif mode == 'adm_nvy':
        await process_adm_nvy(update, context)
    else:
        await update.message.reply_text(
            f"ℹ️ Pilih menu dulu sebelum kirim file.\n"
            f"Klik menu di keyboard bawah 👇",
            reply_markup=get_main_menu(),
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routing callback dari inline keyboard."""
    query = update.callback_query
    data = query.data

    if data == "finish_collect":
        mode = context.user_data.get('mode')
        if mode == 'merge_txt':
            await finish_merge_txt(update, context)
        elif mode == 'merge_vcf':
            await finish_merge_vcf(update, context)
        elif mode == 'msg_to_txt':
            await finish_msg_to_txt(update, context)
        else:
            await query.answer("Tidak ada operasi aktif.")
            await query.edit_message_text("ℹ️ Tidak ada operasi yang sedang berjalan.")
            context.user_data.clear()
    elif data == "cancel_collect":
        await query.answer("Dibatalkan")
        # Cleanup tmpdir jika ada
        tmpdir = context.user_data.get('tmpdir')
        if tmpdir and os.path.exists(tmpdir):
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        context.user_data.clear()
        await query.edit_message_text("❌ Operasi dibatalkan.")
    elif data.startswith("split_"):
        await handle_split_choice(update, context)
    elif data.startswith("fmt_"):
        await handle_adm_nvy_choice(update, context)
    else:
        await query.answer("Unknown action")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handler error global."""
    logger.error("Exception:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                f"❌ Terjadi error internal. Coba lagi ya.\n"
                f"Jika persisten, hubungi [{ADMIN_USERNAME}]({DEV_LINK}).",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=get_main_menu(),
            )
    except Exception:
        pass


# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main():
    if TOKEN == "PASTE_TOKEN_DARI_BOTFATHER_DISINI" or not TOKEN:
        print("=" * 60)
        print("❌ ERROR: Token bot belum diisi!")
        print("=" * 60)
        print("Edit file config.json dan masukkan token dari @BotFather.")
        print("Format config.json:")
        print('  { "bot_token": "123456789:ABC...", ... }')
        print("=" * 60)
        return

    print("=" * 60)
    print(f"🤖 {BOT_NAME} Bot")
    print(f"👤 Admin: @{ADMIN_USERNAME}")
    print(f"💎 Premium features: blue branding link active")
    print("=" * 60)
    print("Bot sedang berjalan... Tekan Ctrl+C untuk berhenti.")
    print("=" * 60)

    # Build application
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("cancel", cmd_cancel))

    # Text message handler (route menu)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message,
    ))

    # Document handler (route file ke processor)
    application.add_handler(MessageHandler(
        filters.Document.ALL,
        handle_document,
    ))

    # Inline callback handler
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Error handler
    application.add_error_handler(error_handler)

    # Run
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

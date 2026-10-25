# ====================================================================
# FlenConvert Bot - File Converter Module
# Berisi logika konversi untuk semua fitur:
#   1. TXT -> VCF          5. Rapikan TXT
#   2. VCF -> TXT          6. MSG -> TXT
#   3. Gabung TXT/VCF      7. XLS -> TXT
#   4. Potong VCF          8. ADM & NVY Format
# ====================================================================

import os
import re
import zipfile
from typing import List, Tuple


# --------------------------------------------------------------------
# Helper: Normalisasi Nomor Telepon
# --------------------------------------------------------------------
def normalize_phone(phone: str, country_code: str = "+62") -> str:
    """
    Normalisasi nomor telepon ke format internasional.
    - Menghapus spasi, dash, kurung
    - Mengubah prefix 0 menjadi +62 (Indonesia default)
    - Mengubah 62xxx menjadi +62xxx
    """
    phone = phone.strip()
    if not phone:
        return ""

    # Hapus karakter non-digit kecuali + di depan
    cleaned = re.sub(r'[\s\-\(\)\.\/]', '', phone)

    # Konversi prefix
    if cleaned.startswith('+'):
        return cleaned
    if cleaned.startswith('00'):
        return '+' + cleaned[2:]
    if cleaned.startswith('0'):
        return country_code + cleaned[1:]
    if cleaned.startswith('62'):
        return '+' + cleaned
    if cleaned.isdigit() and len(cleaned) >= 8:
        return country_code + cleaned
    return cleaned


def is_valid_phone(phone: str) -> bool:
    """Cek apakah string adalah nomor telepon yang valid."""
    digits = re.sub(r'\D', '', phone)
    return 8 <= len(digits) <= 15


# --------------------------------------------------------------------
# 1. TXT -> VCF
# --------------------------------------------------------------------
def txt_to_vcf(input_path: str, output_path: str,
               name_prefix: str = "Contact") -> Tuple[int, int]:
    """
    Konversi file TXT (satu nomor per baris) menjadi VCF kontak.
    Returns: (success_count, total_count)
    """
    success = 0
    total = 0

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    with open(output_path, 'w', encoding='utf-8') as out:
        idx = 0
        for line in lines:
            phone = line.strip()
            if not phone:
                continue
            total += 1
            normalized = normalize_phone(phone)
            if not is_valid_phone(normalized):
                continue
            idx += 1
            out.write("BEGIN:VCARD\n")
            out.write("VERSION:3.0\n")
            out.write(f"FN:{name_prefix} {idx}\n")
            out.write(f"N:{name_prefix};;;;\n")
            out.write(f"TEL;TYPE=CELL:{normalized}\n")
            out.write("END:VCARD\n\r\n")

    return idx, total


# --------------------------------------------------------------------
# 2. VCF -> TXT
# --------------------------------------------------------------------
def vcf_to_txt(input_path: str, output_path: str) -> int:
    """
    Ekstrak nomor telepon dari file VCF ke format TXT.
    Returns: jumlah nomor berhasil diekstrak
    """
    phones = []
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Cari semua baris TEL
    pattern = re.compile(r'^TEL[^:]*:(.+)$', re.IGNORECASE | re.MULTILINE)
    for match in pattern.finditer(content):
        phone = match.group(1).strip()
        if phone:
            phones.append(phone)

    with open(output_path, 'w', encoding='utf-8') as out:
        for phone in phones:
            out.write(phone + '\n')

    return len(phones)


# --------------------------------------------------------------------
# 3. Gabung TXT
# --------------------------------------------------------------------
def merge_txt(input_paths: List[str], output_path: str,
              dedupe: bool = True) -> Tuple[int, int]:
    """
    Gabungkan beberapa file TXT menjadi satu.
    Returns: (final_count, original_count)
    """
    seen = set()
    lines = []
    original = 0

    for path in input_paths:
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                original += 1
                if dedupe:
                    if line not in seen:
                        seen.add(line)
                        lines.append(line)
                else:
                    lines.append(line)

    with open(output_path, 'w', encoding='utf-8') as out:
        for line in lines:
            out.write(line + '\n')

    return len(lines), original


# --------------------------------------------------------------------
# 4. Gabung VCF
# --------------------------------------------------------------------
def merge_vcf(input_paths: List[str], output_path: str) -> int:
    """
    Gabungkan beberapa file VCF menjadi satu.
    Returns: jumlah kontak berhasil digabung
    """
    count = 0
    with open(output_path, 'w', encoding='utf-8') as out:
        for path in input_paths:
            if not os.path.exists(path):
                continue
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
            if not content:
                continue
            # Hitung jumlah VCARD
            count += content.count('BEGIN:VCARD')
            # Pastikan diakhiri newline
            if not content.endswith('\n'):
                content += '\n'
            out.write(content)

    return count


# --------------------------------------------------------------------
# 5. Potong VCF (Split VCF)
# --------------------------------------------------------------------
def split_vcf(input_path: str, output_dir: str,
              chunk_size: int = 100) -> Tuple[int, int]:
    """
    Pecah file VCF besar menjadi beberapa file kecil.
    Returns: (file_count, total_contacts)
    """
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract semua VCARD entries
    vcards = re.findall(r'BEGIN:VCARD.*?END:VCARD', content, re.DOTALL)
    total = len(vcards)

    if total == 0:
        return 0, 0

    file_count = 0
    for i in range(0, total, chunk_size):
        chunk = vcards[i:i + chunk_size]
        file_count += 1
        out_path = os.path.join(output_dir, f'vcf_part_{file_count:03d}.vcf')
        with open(out_path, 'w', encoding='utf-8') as out:
            for vcard in chunk:
                out.write(vcard + '\n\r\n')

    return file_count, total


def zip_directory(dir_path: str, zip_path: str) -> str:
    """Zip seluruh isi direktori menjadi satu file zip."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dir_path)
                zf.write(file_path, arcname)
    return zip_path


# --------------------------------------------------------------------
# 6. Rapikan TXT
# --------------------------------------------------------------------
def clean_txt(input_path: str, output_path: str,
              country_code: str = "+62") -> Tuple[int, int, int]:
    """
    Rapikan file TXT:
      - Hapus duplikat
      - Normalisasi nomor
      - Sortir
    Returns: (final_count, original_count, duplicate_count)
    """
    phones = set()
    original = 0

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            original += 1
            normalized = normalize_phone(line, country_code)
            if is_valid_phone(normalized):
                phones.add(normalized)

    sorted_phones = sorted(phones)
    duplicates = original - len(sorted_phones)

    with open(output_path, 'w', encoding='utf-8') as out:
        for phone in sorted_phones:
            out.write(phone + '\n')

    return len(sorted_phones), original, duplicates


# --------------------------------------------------------------------
# 7. MSG -> TXT
# --------------------------------------------------------------------
def msg_to_txt(messages: List[str], output_path: str,
               include_timestamp: bool = False) -> int:
    """
    Simpan list pesan teks ke file TXT.
    Returns: total karakter
    """
    total_chars = 0
    with open(output_path, 'w', encoding='utf-8') as out:
        for i, msg in enumerate(messages, 1):
            if include_timestamp:
                from datetime import datetime
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                line = f"[{ts}] Message {i}:\n{msg}\n{'='*40}\n"
            else:
                line = f"--- Message {i} ---\n{msg}\n\n"
            out.write(line)
            total_chars += len(line)
    return total_chars


# --------------------------------------------------------------------
# 8. XLS/XLSX -> TXT
# --------------------------------------------------------------------
def xls_to_txt(input_path: str, output_path: str,
               delimiter: str = '\t') -> Tuple[int, int]:
    """
    Konversi file XLSX ke TXT (tab-separated by default).
    Returns: (rows_written, sheets_processed)
    """
    # Lazy import: openpyxl hanya dibutuhkan saat fitur XLS dipakai
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise RuntimeError(
            "openpyxl tidak terinstall. Jalankan:\n"
            "  pip install openpyxl\n"
            "Atau install build tools dulu:\n"
            "  pkg install clang make openssl"
        )

    wb = load_workbook(input_path, read_only=True, data_only=True)
    rows_written = 0
    sheets = 0

    with open(output_path, 'w', encoding='utf-8') as out:
        for sheet_name in wb.sheetnames:
            sheets += 1
            ws = wb[sheet_name]
            for row in ws.iter_rows(values_only=True):
                cells = []
                for c in row:
                    if c is None:
                        cells.append('')
                    else:
                        cells.append(str(c).strip())
                # Skip baris kosong
                if any(c for c in cells):
                    out.write(delimiter.join(cells) + '\n')
                    rows_written += 1

    wb.close()
    return rows_written, sheets


# --------------------------------------------------------------------
# 9. ADM & NVY Format Converter
# --------------------------------------------------------------------
def to_adm_nvy_format(input_path: str, output_path: str,
                      fmt: str = "ADM") -> Tuple[int, int]:
    """
    Konversi TXT berisi nomor ke format ADM atau NVY.
    Format default:
      ADM-001:+62xxx
      NVY-001:+62xxx
    Returns: (success_count, total_count)
    """
    success = 0
    total = 0

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    with open(output_path, 'w', encoding='utf-8') as out:
        idx = 0
        for line in lines:
            phone = line.strip()
            if not phone:
                continue
            total += 1
            normalized = normalize_phone(phone)
            if not is_valid_phone(normalized):
                continue
            idx += 1
            # Format: ADM-001:+62xxx atau NVY-001:+62xxx
            out.write(f"{fmt}-{idx:03d}:{normalized}\n")
            success += 1

    return success, total


# --------------------------------------------------------------------
# Self-test (dijalankan saat: python converters.py --test)
# --------------------------------------------------------------------
if __name__ == '__main__':
    import tempfile
    print("[TEST] Menjalankan self-test converters.py...")

    with tempfile.TemporaryDirectory() as tmp:
        # Test TXT -> VCF -> TXT
        txt_in = os.path.join(tmp, 'test.txt')
        with open(txt_in, 'w') as f:
            f.write("081234567890\n+6281234567891\n6281234567892\n")
            f.write("invalid_line\n0212345678\n")

        vcf_out = os.path.join(tmp, 'test.vcf')
        s, t = txt_to_vcf(txt_in, vcf_out, "Test")
        print(f"  TXT->VCF: {s}/{t} valid")

        txt_back = os.path.join(tmp, 'back.txt')
        n = vcf_to_txt(vcf_out, txt_back)
        print(f"  VCF->TXT: {n} nomor diekstrak")

        # Test clean
        clean_out = os.path.join(tmp, 'clean.txt')
        f_, o, d = clean_txt(txt_in, clean_out)
        print(f"  Rapikan: {f_} unik dari {o} asli, {d} duplikat")

        # Test ADM/NVY
        adm_out = os.path.join(tmp, 'adm.txt')
        a, at = to_adm_nvy_format(txt_in, adm_out, "ADM")
        print(f"  ADM format: {a}/{at} nomor")

    print("[OK] Self-test selesai.")

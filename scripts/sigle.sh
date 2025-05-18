#!/usr/bin/env bash
set -euo pipefail

# Cập nhật danh sách file đã OCR
python src/check.py

# Các thư mục PDF nguồn
PDF_DIRS=(
  "/workspace/preprocess-medical-data/data/pdf/lao_khoa"
  "/workspace/preprocess-medical-data/data/pdf/noi_co_so"
)

# Thư mục Markdown đích
MD_DIR="./data/md/raw"
mkdir -p "$MD_DIR"

# File ghi dấu đã OCR xong
DONE_OCR_FILE="./data/done_ocr.json"

echo "=== Bắt đầu quét và xử lý PDF từng file ==="
for DIR in "${PDF_DIRS[@]}"; do
  # Duyệt toàn bộ PDF trong thư mục
  find "$DIR" -maxdepth 1 -type f -name "*.pdf" | while read -r pdf_file; do
    filename="$(basename "$pdf_file" .pdf)"

    # Bỏ qua nếu đã OCR
    if grep -q "\"$filename\"" "$DONE_OCR_FILE"; then
      echo "Bỏ qua: $filename.pdf (đã OCR)"
      continue
    fi

    echo "Đang xử lý: $filename.pdf"
    # Convert duy nhất file hiện tại
    marker_single "$pdf_file" \
      --output_dir "$MD_DIR" \
      --output_format markdown \
      --disable_image_extraction \
      --languages "vi,en" \
      --force_ocr

    # (Tùy chọn) cập nhật done_ocr.json ngay sau khi xử lý xong 1 file
    # jq '. + ["'"$filename"'"]' "$DONE_OCR_FILE" > "$DONE_OCR_FILE.tmp" && mv "$DONE_OCR_FILE.tmp" "$DONE_OCR_FILE"
  done
done

# Cập nhật lại danh sách OCR sau khi hoàn tất
python src/check.py
echo "=== Hoàn thành toàn bộ ==="

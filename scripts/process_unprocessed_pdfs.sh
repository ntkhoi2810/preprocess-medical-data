#!/bin/bash

# Đường dẫn đến thư mục PDF và MD
PDF_DIR="/teamspace/studios/this_studio/preprocess-medical-data/Nội khoa"

MD_DIR="./data/md/raw"

# Đường dẫn đến file done_ocr.json
DONE_OCR_FILE="./data/done_ocr.json"

# Lấy danh sách các file PDF
pdf_files=$(find "$PDF_DIR" -maxdepth 1 -name "*.pdf" -type f)

# Tạo thư mục tạm chứa các file PDF chưa được xử lý
TEMP_DIR="$PDF_DIR/temp_unprocessed"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Đếm số lượng file cần xử lý
count=0

# Kiểm tra từng file PDF
for pdf_file in $pdf_files; do
    # Lấy tên file không có đường dẫn và đuôi .pdf
    filename=$(basename "$pdf_file" .pdf)
    
    # Kiểm tra xem file đã có trong danh sách done_ocr.json chưa
    if ! grep -q "\"$filename\"" "$DONE_OCR_FILE"; then
        echo "Đánh dấu để xử lý: $filename.pdf"
        # Tạo symlink tới file chưa được xử lý trong thư mục tạm
        ln -sf "$(realpath "$pdf_file")" "$TEMP_DIR/$(basename "$pdf_file")"
        count=$((count + 1))
    else
        echo "Bỏ qua file đã xử lý: $filename.pdf"
    fi
done

# Chỉ chạy marker nếu có file chưa được xử lý
if [ $count -gt 0 ]; then
    echo "Bắt đầu xử lý $count file PDF chưa được OCR..."
    # Chạy marker cho thư mục chứa các file chưa được xử lý
    marker "$TEMP_DIR" --output_dir "$MD_DIR" --output_format markdown --disable_image_extraction --languages "vi,en"
    echo "Hoàn thành! Đã xử lý $count file PDF."
else
    echo "Không có file nào cần xử lý."
fi

# Dọn dẹp
rm -rf "$TEMP_DIR"

# # Cập nhật file done_ocr.json
python data/check.py




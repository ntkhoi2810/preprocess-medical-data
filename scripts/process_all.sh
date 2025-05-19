#!/bin/bash
# # Cập nhật file done_ocr.json
python src/check.py

# Đường dẫn cơ sở đến thư mục PDF
BASE_PDF_DIR="/workspace/preprocess-medical-data/data/pdf"
MD_DIR="./data/md/raw"

# Đường dẫn đến file done_ocr.json
DONE_OCR_FILE="./data/done_ocr.json"

# Lấy danh sách tất cả các thư mục con trong data/pdf
subdirs=$(find "$BASE_PDF_DIR" -mindepth 1 -maxdepth 1 -type d)

# Duyệt qua từng thư mục con
for PDF_DIR in $subdirs; do
    python src/check.py
    echo "Đang xử lý thư mục: $PDF_DIR"
    
    # Lấy danh sách các file PDF (cả .pdf và .PDF)
    pdf_files=$(find "$PDF_DIR" -maxdepth 1 -type f \( -name "*.pdf" -o -name "*.PDF" \))

    # Tạo thư mục tạm chứa các file PDF chưa được xử lý
    TEMP_DIR="$PDF_DIR/temp_unprocessed"
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"

    # Đếm số lượng file cần xử lý
    count=0

    # Kiểm tra từng file PDF
    for pdf_file in $pdf_files; do
        # Lấy tên file không có đường dẫn và đuôi .pdf hoặc .PDF
        filename=$(basename "$pdf_file" | sed -E 's/\.(pdf|PDF)$//')
        
        # Kiểm tra xem file đã có trong danh sách done_ocr.json chưa
        if ! grep -q "\"$filename\"" "$DONE_OCR_FILE"; then
            echo "Đánh dấu để xử lý: $filename"
            # Tạo symlink tới file chưa được xử lý trong thư mục tạm
            ln -sf "$(realpath "$pdf_file")" "$TEMP_DIR/$(basename "$pdf_file")"
            count=$((count + 1))
        else
            echo "Bỏ qua file đã xử lý: $filename"
        fi
    done

    # Chỉ chạy marker nếu có file chưa được xử lý
    if [ $count -gt 0 ]; then
        echo "Bắt đầu xử lý $count file PDF chưa được OCR trong thư mục $PDF_DIR..."
        # Chạy marker cho thư mục chứa các file chưa được xử lý
        marker "$TEMP_DIR" --output_dir "$MD_DIR" --output_format markdown --disable_image_extraction --languages "vi,en" --workers 8 --force_ocr
        echo "Hoàn thành! Đã xử lý $count file PDF."
    else
        echo "Không có file nào cần xử lý trong thư mục $PDF_DIR."
    fi

    # Dọn dẹp
    rm -rf "$TEMP_DIR"
    
    # Cập nhật file done_ocr.json sau mỗi thư mục
    python src/check.py
done

echo "Đã hoàn thành xử lý tất cả thư mục trong data/pdf"
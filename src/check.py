import os

# Đường dẫn đến thư mục raw
raw_dir = "./data/md/raw"

# Lấy danh sách tất cả các thư mục trong raw_dir
folders = set([f for f in os.listdir(raw_dir) if os.path.isdir(os.path.join(raw_dir, f)) and any(file.endswith('.md') for file in os.listdir(os.path.join(raw_dir, f)))])

# Lưu danh sách thư mục vào file dạng JSON
import json

# Đọc file cũ nếu tồn tại
existing_folders = []
if os.path.exists('data/done_ocr.json'):
    with open('data/done_ocr.json', 'r', encoding='utf-8') as f:
        existing_folders = json.load(f)

# Kết hợp danh sách cũ và mới, loại bỏ trùng lặp
all_folders = sorted(list(set(existing_folders + list(folders))))

# Lưu lại vào file
with open('data/done_ocr.json', 'w', encoding='utf-8') as f:
    json.dump(all_folders, f, ensure_ascii=False, indent=2)
import os
import json
from pathlib import Path

# Get the absolute path to the project root
project_root = Path(__file__).parent.parent.absolute()
# Đường dẫn đến thư mục raw
raw_dir = project_root / "data" / "md" / "raw"
done_ocr_path = project_root / "data" / "done_ocr.json"

# Hàm đệ quy để tìm tất cả file .md
def find_md_files(directory: Path) -> set[str]:
    md_files = set()
    for item in directory.iterdir():
        if item.is_file() and item.suffix == '.md':
            # Chỉ lấy tên file không có đường dẫn
            md_files.add(item.stem)
        elif item.is_dir():
            md_files.update(find_md_files(item))
    return md_files

# Lấy danh sách tất cả các file .md
md_files = find_md_files(raw_dir)
print(f"Found {len(md_files)} .md files in {raw_dir}")

# Đọc file cũ nếu tồn tại
existing_files = []
if done_ocr_path.exists():
    with open(done_ocr_path, 'r', encoding='utf-8') as f:
        existing_files = json.load(f)
    print(f"Loaded {len(existing_files)} entries from {done_ocr_path}")

# Kết hợp danh sách cũ và mới, loại bỏ trùng lặp
all_files = sorted(list(set(existing_files + list(md_files))))
print(f"Combined unique files: {len(all_files)}")

# Kiểm tra xem có file mới nào được thêm vào không
new_files = set(md_files) - set(existing_files)
if new_files:
    print(f"Added {len(new_files)} new files")
    for file in sorted(new_files):
        print(f"  - {file}")

# Lưu lại vào file
with open(done_ocr_path, 'w', encoding='utf-8') as f:
    json.dump(all_files, f, ensure_ascii=False, indent=2)
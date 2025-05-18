import os
from pathlib import Path
import logging
import unicodedata
import re

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def normalize_folder_name(folder_name: str) -> str:
    """
    Chuyển đổi tên thư mục thành dạng viết thường, không dấu và nối bằng dấu gạch dưới
    
    Args:
        folder_name: Tên thư mục cần chuyển đổi
        
    Returns:
        str: Tên thư mục đã được chuẩn hóa
    """
    # Xử lý các ký tự đặc biệt của tiếng Việt
    special_chars = {
        'đ': 'd', 'Đ': 'D',
        'ê': 'e', 'Ê': 'E',
        'ơ': 'o', 'Ơ': 'O',
        'ư': 'u', 'Ư': 'U',
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'ô': 'o', 'Ô': 'O'
    }
    
    for vietnamese_char, latin_char in special_chars.items():
        folder_name = folder_name.replace(vietnamese_char, latin_char)
    
    # Chuyển về dạng không dấu
    normalized = unicodedata.normalize('NFKD', folder_name)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Chuyển về chữ thường và thay thế khoảng trắng bằng dấu gạch dưới
    normalized = normalized.lower()
    normalized = normalized.replace(' ', '_')
    
    # Loại bỏ các ký tự đặc biệt còn lại
    normalized = re.sub(r'[^\w_]', '', normalized)
    
    return normalized

def rename_folders() -> dict:
    """
    Đổi tên các thư mục bên trong preprocess-medical-data/data/pdf
    
    Returns:
        dict: Kết quả xử lý với các thư mục thành công và thất bại
    """
    result = {
        "success": [],
        "failed": []
    }
    
    try:
        # Lấy đường dẫn đến thư mục pdf
        pdf_dir = Path("data/pdf")
        if not pdf_dir.exists():
            raise Exception(f"Không tìm thấy thư mục {pdf_dir}")
            
        # Lấy danh sách các thư mục bên trong thư mục pdf
        folders = [f for f in pdf_dir.iterdir() if f.is_dir() 
                  and f.name != "__pycache__" 
                  and not f.name.startswith('.')]
        
        # Để theo dõi các tên đã được sử dụng
        used_names = {}
        
        # Xử lý từng thư mục
        for folder in folders:
            try:
                old_name = folder.name
                base_new_name = normalize_folder_name(old_name)
                
                # Xử lý trùng tên
                new_name = base_new_name
                counter = 1
                while new_name in used_names:
                    counter += 1
                    new_name = f"{base_new_name}_{counter}"
                
                used_names[new_name] = True
                
                # Tạo đường dẫn mới
                new_path = folder.parent / new_name
                
                # Đổi tên thư mục
                os.rename(folder, new_path)
                
                result["success"].append({
                    "old_name": str(folder),
                    "new_name": str(new_path)
                })
                
                logging.info(f"Đã đổi tên thư mục: {old_name} -> {new_name}")
                
            except Exception as exc:
                result["failed"].append({
                    "folder": str(folder),
                    "reason": str(exc)
                })
                logging.error(f"Lỗi khi đổi tên thư mục {folder}: {exc}")
                
        return result
        
    except Exception as exc:
        logging.exception("Lỗi khi xử lý các thư mục")
        return result

if __name__ == "__main__":
    result = rename_folders()
    
    # In kết quả
    print("\nKết quả đổi tên thư mục:")
    print(f"- Thành công: {len(result['success'])} thư mục")
    print(f"- Thất bại: {len(result['failed'])} thư mục")
    
    if result['failed']:
        print("\nChi tiết lỗi:")
        for fail in result['failed']:
            print(f"- {fail['folder']}: {fail['reason']}")

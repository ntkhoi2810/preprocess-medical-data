import os
from pathlib import Path
import logging
from PyPDF2 import PdfReader, PdfWriter
import re
from typing import Dict, List, Any
import sys
import argparse

# Setup logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_split.log')
    ]
)

def validate_pdf_file(file_path: Path) -> bool:
    """Validate if PDF file exists and is readable"""
    if not file_path.exists():
        logging.error(f"File không tồn tại: {file_path}")
        return False
    if not file_path.is_file():
        logging.error(f"Đường dẫn không phải là file: {file_path}")
        return False
    return True

def split_large_pdfs(input_dir: Path, max_pages: int = 300) -> Dict[str, List[Dict[str, Any]]]:
    """
    Tìm và chia nhỏ các file PDF có nhiều hơn max_pages trang
    
    Args:
        input_dir: Đường dẫn thư mục chứa các file PDF cần xử lý
        max_pages: Số trang tối đa cho mỗi file PDF sau khi chia
        
    Returns:
        Dict chứa kết quả thành công và thất bại
    """
    result = {
        "success": [],
        "failed": []
    }
    
    try:
        if not input_dir.exists():
            raise Exception(f"Không tìm thấy thư mục {input_dir}")
            
        pdf_files = list(input_dir.glob("**/*.pdf"))
        
        if not pdf_files:
            logging.warning(f"Không tìm thấy file PDF nào trong thư mục {input_dir}")
            return result
            
        for pdf_file in pdf_files:
            try:
                if not validate_pdf_file(pdf_file):
                    continue
                    
                if "__pycache__" in str(pdf_file):
                    continue
                    
                logging.info(f"Đang xử lý file: {pdf_file}")
                reader = PdfReader(str(pdf_file), strict=False)
                
                valid_pages = []
                total_pages = len(reader.pages)
                
                # Kiểm tra và lọc các trang hợp lệ
                for i in range(total_pages):
                    try:
                        page = reader.pages[i]
                        if page and page.get_contents():  # Kiểm tra nội dung trang
                            valid_pages.append(i)
                    except Exception as e:
                        logging.warning(f"Không thể đọc trang {i+1} trong file {pdf_file.name}: {str(e)}")
                
                if not valid_pages:
                    raise Exception("Không có trang nào trong PDF có thể đọc được")
                
                total_valid_pages = len(valid_pages)
                logging.info(f"Số trang hợp lệ: {total_valid_pages}/{total_pages}")
                
                if total_valid_pages > max_pages:
                    num_parts = (total_valid_pages + max_pages - 1) // max_pages
                    
                    # Tạo thư mục backup nếu chưa tồn tại
                    backup_dir = pdf_file.parent / "backup"
                    backup_dir.mkdir(exist_ok=True)
                    
                    # Backup file gốc trước khi xử lý
                    backup_path = backup_dir / pdf_file.name
                    if not backup_path.exists():
                        os.rename(pdf_file, backup_path)
                    
                    for i in range(num_parts):
                        writer = PdfWriter()
                        
                        start_idx = i * max_pages
                        end_idx = min((i + 1) * max_pages, total_valid_pages)
                        
                        for j in range(start_idx, end_idx):
                            page_num = valid_pages[j]
                            try:
                                writer.add_page(reader.pages[page_num])
                            except Exception as e:
                                logging.warning(f"Bỏ qua trang {page_num+1} do lỗi: {str(e)}")
                        
                        new_name = f"{pdf_file.stem}-P{i+1}.pdf"
                        new_path = pdf_file.parent / new_name
                        
                        try:
                            with open(new_path, 'wb') as output_file:
                                writer.write(output_file)
                            
                            result["success"].append({
                                "original": str(pdf_file),
                                "split": str(new_path),
                                "pages": f"{valid_pages[start_idx]+1}-{valid_pages[end_idx-1]+1}"
                            })
                            
                            logging.info(f"Đã chia file {pdf_file.name} thành {new_name}")
                        except Exception as e:
                            logging.error(f"Lỗi khi lưu file {new_name}: {str(e)}")
                            raise
                    
                    # Xóa file gốc sau khi chia xong
                    if backup_path.exists():
                        os.remove(backup_path)
                        logging.info(f"Đã xóa file gốc: {pdf_file.name}")
                    
            except Exception as exc:
                error_msg = str(exc)
                if "Object" in error_msg and "not defined" in error_msg:
                    logging.error(f"PDF bị hỏng: {pdf_file}. Lỗi: {error_msg}")
                else:
                    logging.error(f"Lỗi khi xử lý file {pdf_file}: {exc}")
                
                result["failed"].append({
                    "file": str(pdf_file),
                    "reason": error_msg
                })
                
        return result
        
    except Exception as exc:
        logging.exception("Lỗi khi xử lý các thư mục")
        return result

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Chia nhỏ các file PDF lớn')
    parser.add_argument('--input-dir', type=str, default='./data/pdf_copy',
                      help='Đường dẫn thư mục chứa các file PDF cần xử lý')
    parser.add_argument('--max-pages', type=int, default=300,
                      help='Số trang tối đa cho mỗi file PDF sau khi chia')
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_arguments()
        input_dir = Path(args.input_dir)
        
        result = split_large_pdfs(input_dir=input_dir, max_pages=args.max_pages)
        
        print("\nKết quả chia file PDF:")
        print(f"- Thành công: {len(result['success'])} file")
        print(f"- Thất bại: {len(result['failed'])} file")
        
        if result['success']:
            print("\nChi tiết các file đã chia:")
            for success in result['success']:
                print(f"- {success['original']} -> {success['split']} ({success['pages']})")
                
        if result['failed']:
            print("\nChi tiết lỗi:")
            for fail in result['failed']:
                print(f"- {fail['file']}: {fail['reason']}")
                
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình theo yêu cầu người dùng")
        sys.exit(0)
    except Exception as e:
        logging.exception("Lỗi không xác định:")
        sys.exit(1)

from __future__ import annotations
import time
import io
import json
import logging
import os
from pathlib import Path
from typing import List, Union, Dict, Any

import dotenv
dotenv.load_dotenv()

import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image


# ──────────────────────────────  Cấu hình logging  ─────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ─────────────────────────────  Hằng số & Prompt  ──────────────────────────────
SYSTEM_PROMPT = """
Bạn là chuyên gia OCR & chuẩn hóa metadata bìa sách/TL.

Yêu cầu:
1  Đọc bìa (hoặc trang tiêu đề) và **trích xuất**:
    • Tên sách/tài liệu
    • Năm xuất bản (4 chữ số)
    • Tập/Phần (TAP1, TAP2…)
    • Nhà xuất bản, trường ĐH hoặc nguồn gốc (viết ngắn gọn)

2  **Chuẩn hóa**:
    • Chỉ A-Z, 0-9, dấu "_" ; chữ HOA ; bỏ dấu TViệt
    • Khoảng trắng → "_" ; gộp liên tiếp thành 1
    • Trường không tìm thấy đặt `null`
    • Thuộc tính `file_name` ghép thành
      <TEN_TAI_LIEU>_<NAM_XUAT_BAN>_<TAP>_<NGUON>.<ext_goc>
      Bỏ qua thành phần `null` cùng dấu "_"

3  Trả về **DUY NHẤT** một JSON hợp schema – không giải thích thêm.
""".strip()

JSON_SCHEMA: Dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "ten_tai_lieu": {
            "type": "STRING",
            "description": "Tên tài liệu (chữ HOA, không dấu, cách bằng ''_'')",
        },
        "nam_xuat_ban": {
            "type": "INTEGER",
            "description": "Năm xuất bản (4 chữ số) hoặc null",
            "nullable": True,
        },
        "tap": {
            "type": "STRING",
            "description": "Tập/Phần dạng TAPx hoặc null",
            "nullable": True,
        },
        "nguon": {
            "type": "STRING",
            "description": "Nguồn/NXB/ĐH viết tắt hoặc null",
            "nullable": True,
        },
    },
    "required": ["ten_tai_lieu"],
}

# ─────────────────────────────  Hàm tiện ích  ──────────────────────────────────


def _pdf_to_images(
    pdf_path: Path,
    first_page: int,
    last_page: int | None,
    poppler_path: str | None,
) -> List[Image.Image]:
    """Chuyển PDF sang danh sách ảnh PIL."""
    logging.info('Đang chuyển "%s" thành ảnh ...', pdf_path.name)
    return convert_from_path(
        pdf_path,
        first_page=first_page,
        last_page=last_page,
        poppler_path=poppler_path,
    )


def _pil_to_jpeg_bytes(img: Image.Image) -> bytes:
    """Chuyển ảnh PIL → bytes JPEG (RGB)."""
    with io.BytesIO() as buffer:
        img.convert("RGB").save(buffer, format="JPEG")
        return buffer.getvalue()


# ─────────────────────────────  Hàm chính  ─────────────────────────────────────
def extract_cover_metadata(
    pdf_file: Union[str, Path],
    *,
    first_page: int = 1,
    last_page: int | None = None,
    images_per_request: int = 1,
    model_name: str = "gemini-2.0-flash",
    poppler_path: str | None = None,
) -> List[dict] | str:
    """
    Trích xuất & chuẩn hóa metadata bìa sách/tài liệu PDF bằng Gemini.

    Parameters
    ----------
    pdf_file : Union[str, Path]
        Đường dẫn tới file PDF.
    first_page : int, optional
        Trang bắt đầu, mặc định 1.
    last_page : int | None, optional
        Trang kết thúc. None → đến cuối file.
    images_per_request : int, optional
        Số trang (ảnh) gửi cho Gemini mỗi lần.
    model_name : str
        Tên model Gemini.
    poppler_path : str | None
        Đường dẫn Poppler nếu cần (Windows).

    Returns
    -------
    List[dict] | str
        Danh sách kết quả JSON từ Gemini hoặc thông báo lỗi.
    """
    try:
        pdf_path = Path(pdf_file).expanduser().resolve()
        if not pdf_path.is_file():
            return f"Error: File không tồn tại – {pdf_path}"

        original_ext = pdf_path.suffix  # Lưu lại đuôi gốc

        # 1️⃣  Chuyển PDF → ảnh -------------------------------------------------
        images = _pdf_to_images(pdf_path, first_page, last_page, poppler_path)
        if not images:
            return "Error: Không chuyển được PDF thành ảnh."

        # 2️⃣  Lấy API‑key & khởi tạo Gemini -----------------------------------
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: Chưa thiết lập biến môi trường GEMINI_API_KEY."
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(model_name)
        generation_cfg = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_schema": JSON_SCHEMA,
        }

        # 3️⃣  Gọi model theo từng batch ảnh -----------------------------------
        results: List[dict] = []

        for i in range(0, len(images), images_per_request):
            batch = images[i: i + images_per_request]

            parts = (
                [{"text": SYSTEM_PROMPT}]
                + [
                    {
                        "inline_data": {
                            "data": _pil_to_jpeg_bytes(img),
                            "mime_type": "image/jpeg",
                        }
                    }
                    for img in batch
                ]
            )

            response = model.generate_content(
                contents=[{"parts": parts}],
                generation_config=generation_cfg,
            )

            if not hasattr(response, "text"):
                results.append(
                    {"error": "Gemini không trả về thuộc tính text."})
                continue

            try:
                data = json.loads(response.text)

                # Sửa lại đuôi file_name (Gemini hay trả về .jpg)
                if data.get("file_name", "").endswith(".jpg"):
                    data["file_name"] = data["file_name"][:-4] + original_ext

                results.append(data)

            except Exception as exc:  # parsing JSON thất bại
                results.append(
                    {
                        "error": f"Parse JSON fail: {exc}",
                        "raw_text": response.text,
                    }
                )

        return results

    except Exception as exc:  # pragma: no cover
        logging.exception("Lỗi ngoài ý muốn")
        return f"Error: {exc}"


def get_new_filename(file_path: str) -> str:
    """
    Trích xuất metadata từ file PDF và tạo tên file mới.

    Parameters
    ----------
    file_path : str
        Đường dẫn tới file PDF cần đổi tên

    Returns
    -------
    str
        Tên file mới được tạo từ metadata hoặc tên file gốc nếu có lỗi
    """
    output = extract_cover_metadata(
        file_path,
        first_page=1,
        last_page=3,        # Thường bìa + bìa phụ
        images_per_request=3,
        model_name="gemini-2.0-flash",
    )

    # Kiểm tra nếu output là string (thông báo lỗi)
    if isinstance(output, str):
        logging.error(f"Lỗi khi trích xuất metadata từ {file_path}: {output}")
        # Trả về tên file gốc nếu có lỗi
        return Path(file_path).stem

    # Kiểm tra nếu output là list rỗng
    if not output or not isinstance(output, list):
        logging.error(f"Không có dữ liệu trích xuất từ {file_path}")
        return Path(file_path).stem
    
    # Lấy phần tử đầu tiên từ danh sách kết quả
    metadata = output[0]
    
    if not isinstance(metadata, dict):
        logging.error(f"Dữ liệu metadata không hợp lệ từ {file_path}: {metadata}")
        return Path(file_path).stem

    # Lấy các giá trị từ metadata
    ten_tai_lieu = metadata.get("ten_tai_lieu")
    nam_xuat_ban = metadata.get("nam_xuat_ban")
    tap = metadata.get("tap")
    nguon = metadata.get("nguon")

    # Nếu không có tên tài liệu, trả về tên file gốc
    if not ten_tai_lieu:
        return Path(file_path).stem

    # Tạo list các giá trị không None và chuyển sang string
    list_of_json = []
    for item in [ten_tai_lieu, nam_xuat_ban, tap, nguon]:
        if item is not None:
            list_of_json.append(str(item))

    # Nếu không có thông tin nào, trả về tên file gốc
    if not list_of_json:
        return Path(file_path).stem

    return "-".join(list_of_json)

# Test thử hàm
# test_file = "Điện tâm đồ (thông tin dạn ảnh)/BLOCK 1- 5_A.pdf"
# print(get_new_filename(test_file))


def get_files_in_folder(folder_path: str) -> list:
    try:
        # Chuyển đổi đường dẫn thành Path object
        path = Path(folder_path).expanduser().resolve()

        # Kiểm tra thư mục tồn tại
        if not path.is_dir():
            return []

        # Lấy danh sách các file (không bao gồm thư mục con)
        files = [f"{folder_path}/{f.name}" for f in path.iterdir()
                 if f.is_file()]

        return files

    except Exception as exc:
        logging.exception(f"Lỗi khi quét thư mục {folder_path}")
        return []

# get_files_in_folder("Điện tâm đồ (thông tin dạn ảnh)")


def rename_files_in_folder(folder_path: str) -> dict:
    """
    Đổi tên tất cả các file trong thư mục sử dụng hàm get_new_filename.

    Parameters
    ----------
    folder_path : str
        Đường dẫn đến thư mục chứa các file cần đổi tên.

    Returns
    -------
    dict
        Dictionary chứa thông tin về các file đã đổi tên:
        {
            "success": list các file đổi tên thành công (old_name -> new_name),
            "failed": list các file đổi tên thất bại và lý do
        }
    """

    result = {
        "success": [],
        "failed": []
    }

    try:
        # Lấy danh sách các file trong thư mục
        files = get_files_in_folder(folder_path)

        if not files:
            logging.warning(
                f"Không tìm thấy file nào trong thư mục {folder_path}")
            return result

        # Duyệt qua từng file và đổi tên
        for file_path in files:
            try:
                # Lấy tên file mới
                new_name = get_new_filename(file_path)

                if not new_name:
                    result["failed"].append({
                        "file": file_path,
                        "reason": "Không thể tạo tên mới"
                    })
                    continue

                # Tạo đường dẫn đầy đủ cho file mới
                old_path = Path(file_path)
                new_path = old_path.parent / f"{new_name}{old_path.suffix}"

                # Đổi tên file
                os.rename(old_path, new_path)

                result["success"].append({
                    "old_name": str(old_path),
                    "new_name": str(new_path)
                })

                logging.info(f"Đã đổi tên: {old_path.name} -> {new_path.name}")

                # Thêm time sleep để tránh vượt quá RPM limit (15 requests per minute)
                time.sleep(3)  # 60/15 = 4 giây mỗi request

            except Exception as exc:
                result["failed"].append({
                    "file": file_path,
                    "reason": str(exc)
                })
                logging.error(f"Lỗi khi đổi tên file {file_path}: {exc}")

        return result

    except Exception as exc:
        logging.exception(
            f"Lỗi khi đổi tên các file trong thư mục {folder_path}")
        return result


# Test thử hàm rename_files_in_folder
# Uncomment dòng dưới đây để chạy thử
if __name__ == "__main__":
    # đổi tên file trong thư mục test
    rename_result = rename_files_in_folder("/teamspace/studios/this_studio/tai-lieu-y-khoa-mien-phi-noi-khoa-raw/tai-lieu-y-khoa-mien-phi-v2")
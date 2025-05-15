import time
import logging
import os
import requests
import json
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)


def generate_with_yescale(prompt: str, 
                          model: str = "gemini-2.0-flash", 
                          temperature: float = 0.1,
                          max_attempts: int = 5,
                          base_delay: float = 2.0,
                          max_delay: float = 32.0,
                          system_prompt: Optional[str] = None) -> Optional[str]:
    """Generate text using YesScale API.
    
    Args:
        prompt: The prompt to send to the model
        model: Model name to use
        temperature: Temperature for generation
        max_attempts: Maximum number of attempts if API fails
        base_delay: Base delay between retries (will be exponentially increased)
        max_delay: Maximum delay between retries
        system_prompt: Optional system prompt to guide the model
        
    Returns:
        Generated text or None if API call fails
    """
    url = "https://api.yescale.io/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('YESCALE_API_KEY')}"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            return None
            
        except Exception as exc:
            wait = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logging.warning(f"YesScale API error ({type(exc).__name__}) - attempt {attempt}/{max_attempts}; waiting {wait}s before retry...")
            
            if attempt < max_attempts:
                time.sleep(wait)
            else:
                logging.error(f"Failed to connect to YesScale API after {max_attempts} attempts: {exc}")
                return None


def process_markdown_file(file_path, model, max_retries=3, retry_delay=5):
    """Process a single markdown chunk file using YesScale API.
    
    Args:
        file_path: Path to the markdown file
        model: The model name to use
        max_retries: Maximum number of retries for API calls
        retry_delay: Delay between retries in seconds
        
    Returns:
        Boolean indicating whether processing was successful
    """
    logger.info(f"Processing {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            logger.info(f"Skipping {file_path} - empty file")
            return False
        
        system_prompt = """Bạn là một LLM chuyên xử lý văn bản y khoa để phục vụ tiền huấn luyện mô hình ngôn ngữ.

            Nhiệm vụ của bạn là **chỉnh sửa văn bản theo các yêu cầu dưới đây và CHỈ TRẢ VỀ VĂN BẢN ĐÃ ĐƯỢC XỬ LÝ, KHÔNG GIẢI THÍCH, KHÔNG THÊM BẤT KỲ NỘI DUNG MỚI NÀO**.

            Yêu cầu:
            1. **Chỉ giữ lại nội dung liên quan đến bệnh học**: các mô tả, phân loại, triệu chứng, nguyên nhân, chẩn đoán, điều trị, tiên lượng, cơ chế bệnh sinh, biến chứng, phòng ngừa,...  
            2. **Loại bỏ toàn bộ thông tin không liên quan đến bệnh học**, ví dụ: giới thiệu không cần thiết, các ghi chú hành chính, thông tin cá nhân, ví dụ minh hoạ không cần thiết,...  
            3. Sửa lỗi **chính tả, ngữ pháp tiếng Việt**.  
            4. **Format lại định dạng heading Markdown cho phù hợp** vì có những file bị lỗi heading 1, 2, 3. Nhiệm vụ của bạn là dựa vào kinh nghiệm của chính mình để format lại.  
            5. Nếu có **bảng**, format lại theo dạng phù hợp làm data pretrain cho model LLMs.  
            6. Giữ nguyên **toàn bộ thuật ngữ y khoa**, không dịch hay thay đổi từ chuyên ngành.  
            7. Tuyệt đối **không thay đổi nội dung chuyên môn** – chỉ cải thiện cách trình bày và loại bỏ thông tin ngoài bệnh học.  
            8. Nếu có **công thức toán học**, hãy định dạng lại theo cú pháp LaTeX trong Markdown: `$$...$$`."""
            
        prompt = f"""Văn bản cần xử lý:
{content}
        """
        
        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Sending request to YesScale API (attempt {retries+1}/{max_retries})")
                
                cleaned_text = generate_with_yescale(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                    max_attempts=max_retries,
                    base_delay=retry_delay
                )
                
                if cleaned_text is None:
                    raise Exception("Failed to get response from YesScale API")
                
                logger.info(f"Successfully received response from YesScale API")
                
                # Clean response if it contains markdown code blocks
                if "```" in cleaned_text:
                    logger.info("Cleaning code blocks from response")
                    parts = cleaned_text.split("```")
                    if len(parts) >= 3:
                        if parts[1].strip().startswith("markdown"):
                            cleaned_text = parts[1].replace("markdown", "", 1).strip()
                        else:
                            cleaned_text = parts[1].strip()
                
                # Write the processed content and rename file
                done_file_path = f"{file_path[:-3]}_done.md"
                with open(done_file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
                
                # Remove original file
                os.remove(file_path)
                
                logger.info(f"Successfully processed and saved to {done_file_path}")
                return True
                
            except Exception as e:
                retries += 1
                logger.warning(f"Error on attempt {retries}/{max_retries}: {str(e)}")
                
                if retries < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        logger.error(f"Failed to process {file_path} after {max_retries} attempts")
        return False
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

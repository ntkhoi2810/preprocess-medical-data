import google.generativeai as genai
import time
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Set up the API
def setup_genai(api_key):
    """
    Set up the Gemini API with your API key
    """
    if not api_key:
        logger.error("No Gemini API key provided")
        raise ValueError("Gemini API key is required")
    
    logger.info("Configuring Gemini API")
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully")

# Process a single markdown chunk file
def process_markdown_file(file_path, model, max_retries=3, retry_delay=5):
    """
    Process a single markdown chunk file using Gemini
    
    Args:
        file_path: Path to the markdown file
        model: The Gemini model instance
        max_retries: Maximum number of retries for API calls
        retry_delay: Delay between retries in seconds
    """
    logger.info(f"Processing {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    try:
        # Read the markdown content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Skip empty files
        if not content:
            logger.info(f"Skipping {file_path} - empty file")
            return False
        
        # Create a prompt for Gemini
        prompt = f"""
            Bạn là một LLM chuyên xử lý văn bản y khoa để phục vụ tiền huấn luyện mô hình ngôn ngữ.

            Nhiệm vụ của bạn là **chỉnh sửa văn bản theo các yêu cầu dưới đây và CHỈ TRẢ VỀ VĂN BẢN ĐÃ ĐƯỢC XỬ LÝ, KHÔNG GIẢI THÍCH, KHÔNG THÊM BẤT KỲ NỘI DUNG MỚI NÀO**.

            Yêu cầu:
            1. **Chỉ giữ lại nội dung liên quan đến bệnh học**: các mô tả, phân loại, triệu chứng, nguyên nhân, chẩn đoán, điều trị, tiên lượng, cơ chế bệnh sinh, biến chứng, phòng ngừa,...  
            2. **Loại bỏ toàn bộ thông tin không liên quan đến bệnh học**, ví dụ: giới thiệu không cần thiết, các ghi chú hành chính, thông tin cá nhân, ví dụ minh hoạ không cần thiết,...  
            3. Sửa lỗi **chính tả, ngữ pháp tiếng Việt**.  
            4. **Format lại định dạng heading Markdown cho phù hợp** vì có những file bị lỗi heading 1, 2, 3. Nhiệm vụ của bạn là dựa vào kinh nghiệm của chính mình để format lại.  
            5. Nếu có **bảng**, format lại theo dạng phù hợp làm data pretrain cho model LLMs.  
            6. Giữ nguyên **toàn bộ thuật ngữ y khoa**, không dịch hay thay đổi từ chuyên ngành.  
            7. Tuyệt đối **không thay đổi nội dung chuyên môn** – chỉ cải thiện cách trình bày và loại bỏ thông tin ngoài bệnh học.  
            8. Nếu có **công thức toán học**, hãy định dạng lại theo cú pháp LaTeX trong Markdown: `$$...$$`.

            Đầu vào:
            {content}
        """
        
        # Retry logic for API calls
        retries = 0
        success = False
        last_error = None
        
        while retries < max_retries and not success:
            try:
                logger.info(f"Sending request to Gemini API (attempt {retries+1}/{max_retries})")
                
                # Get response from Gemini with temperature = 0.1
                response = model.generate_content(
                    prompt, 
                    generation_config={"temperature": 0.1, "max_output_tokens": 8192}
                )
                
                # Process the response
                cleaned_text = response.text
                logger.info(f"Successfully received response from Gemini API")
                
                # Sometimes the model might include backticks or explanations, let's clean that
                if "```" in cleaned_text:
                    logger.info("Cleaning code blocks from response")
                    # Try to extract content between the first and last backticks
                    parts = cleaned_text.split("```")
                    if len(parts) >= 3:  # At least one complete code block
                        # Get the content of the first code block
                        if parts[1].strip().startswith("markdown"):
                            cleaned_text = parts[1].replace("markdown", "", 1).strip()
                        else:
                            cleaned_text = parts[1].strip()
                
                # Write the processed content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
                
                logger.info(f"Successfully processed {file_path}")
                success = True
                
            except Exception as e:
                last_error = str(e)
                retries += 1
                logger.warning(f"Error on attempt {retries}/{max_retries}: {last_error}")
                
                if retries < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        if not success:
            logger.error(f"Failed to process {file_path} after {max_retries} attempts: {last_error}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

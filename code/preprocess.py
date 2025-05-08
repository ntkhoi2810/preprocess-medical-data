import os
import glob
import google.generativeai as genai
from pathlib import Path
import time
import argparse

# Set up the API
def setup_genai(api_key):
    """
    Set up the Gemini API with your API key
    """
    genai.configure(api_key=api_key)

# Process a single markdown file
def process_md_file(file_path, model):
    """
    Process a single markdown file using Gemini
    """
    print(f"Processing {file_path}")
    
    try:
        # Read the content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip empty files
        if not content.strip():
            print(f"Skipping {file_path} - empty file")
            return
            
        # Create a prompt for Gemini
        prompt = f"""
            Bạn là một LLM chuyên xử lý văn bản y khoa để phục vụ tiền huấn luyện mô hình ngôn ngữ.

            Nhiệm vụ của bạn là **chỉnh sửa văn bản theo các yêu cầu dưới đây và CHỈ TRẢ VỀ VĂN BẢN ĐÃ ĐƯỢC XỬ LÝ, KHÔNG GIẢI THÍCH, KHÔNG THÊM BẤT KỲ NỘI DUNG MỚI NÀO**.

            Yêu cầu:
            1. **Chỉ giữ lại nội dung liên quan đến bệnh học**: các mô tả, phân loại, triệu chứng, nguyên nhân, chẩn đoán, điều trị, tiên lượng, cơ chế bệnh sinh, biến chứng, phòng ngừa,...  
            2. **Loại bỏ toàn bộ thông tin không liên quan đến bệnh học**, ví dụ: giới thiệu không cần thiết, các ghi chú hành chính, thông tin cá nhân, ví dụ minh hoạ không cần thiết,...  
            3. Sửa lỗi **chính tả, ngữ pháp tiếng Việt**.  
            4. **Giữ nguyên định dạng Markdown** gốc.  
            5. Nếu có **bảng**, định dạng lại bảng cho đúng chuẩn Markdown.  
            6. Giữ nguyên **toàn bộ thuật ngữ y khoa**, không dịch hay thay đổi từ chuyên ngành.  
            7. Tuyệt đối **không thay đổi nội dung chuyên môn** – chỉ cải thiện cách trình bày và loại bỏ thông tin ngoài bệnh học.  
            8. Nếu có **công thức toán học**, hãy định dạng lại theo cú pháp LaTeX trong Markdown: `$$...$$`.

            Đầu vào:
            {content}
        """
        
        # Get response from Gemini with temperature = 0.1
        response = model.generate_content(prompt, generation_config={"temperature": 0.1})
        
        # Process the response (extract just the cleaned text)
        cleaned_text = response.text
        
        # Sometimes the model might include backticks or explanations, let's clean that
        if "```" in cleaned_text:
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
            
        print(f"Successfully processed {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Process markdown files using Gemini AI')
    parser.add_argument('--api_key', required=True, help='Google API Key for Gemini')
    parser.add_argument('--dir', default='../benhhoc4_chunks', help='Directory containing markdown files')
    parser.add_argument('--model', default='gemini-2.5-flash-preview-04-17', help='Gemini model to use')
    parser.add_argument('--delay', type=int, default=10, help='Delay between API calls in seconds')
    parser.add_argument('--temperature', type=float, default=0.1, help='Temperature parameter for Gemini model (0.0 to 1.0)')
    args = parser.parse_args()
    
    # Setup API
    setup_genai(args.api_key)
    
    # Get model
    model = genai.GenerativeModel(args.model)
    
    # Get all markdown files
    md_files_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.dir, "*.md")
    md_files = glob.glob(md_files_path)
    
    if not md_files:
        print(f"No markdown files found in {args.dir}")
        return
    
    print(f"Found {len(md_files)} markdown files to process")
    
    # Process each file
    success_count = 0
    for file_path in md_files:
        success = process_md_file(file_path, model)
        if success:
            success_count += 1
        
        # Add delay between API calls to avoid rate limiting
        time.sleep(args.delay)
    
    print(f"Processing complete. Successfully processed {success_count}/{len(md_files)} files.")

if __name__ == "__main__":
    main()

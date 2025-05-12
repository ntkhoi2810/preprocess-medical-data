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

# Process a single markdown chunk file
def process_markdown_file(file_path, model):
    """
    Process a single markdown chunk file using Gemini
    """
    print(f"Processing {file_path}")
    
    try:
        # Read the markdown content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Skip empty files
        if not content:
            print(f"Skipping {file_path} - empty file")
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
    parser = argparse.ArgumentParser(description='Process markdown chunks using Gemini AI')
    parser.add_argument('--api_key', required=True, help='Google API Key for Gemini')
    parser.add_argument('--chunks_dir', default='../data/processed/chunks', help='Directory containing chunk folders')
    parser.add_argument('--model', default='gemini-2.0-flash', help='Gemini model to use')
    parser.add_argument('--delay', type=int, default=10, help='Delay between API calls in seconds')
    args = parser.parse_args()
    
    # Setup API
    setup_genai(args.api_key)
    
    # Get model
    model = genai.GenerativeModel(args.model)
    
    # Get the absolute path of the chunks directory
    chunks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.chunks_dir)
    
    # Get all document folders
    doc_folders = [f for f in os.listdir(chunks_dir) if os.path.isdir(os.path.join(chunks_dir, f))]
    
    if not doc_folders:
        print(f"No document folders found in {chunks_dir}")
        return
    
    total_processed = 0
    total_files = 0
    
    # Process each document folder
    for doc_folder in doc_folders:
        folder_path = os.path.join(chunks_dir, doc_folder)
        # Get all markdown files in the folder
        md_files = glob.glob(os.path.join(folder_path, "*.md"))
        total_files += len(md_files)
        
        print(f"\nProcessing folder: {doc_folder}")
        print(f"Found {len(md_files)} chunks to process")
        
        # Process each markdown file
        for file_path in md_files:
            success = process_markdown_file(file_path, model)
            if success:
                total_processed += 1
            
            # Add delay between API calls to avoid rate limiting
            time.sleep(args.delay)
    
    print(f"\nProcessing complete. Successfully processed {total_processed}/{total_files} files.")

if __name__ == "__main__":
    main()

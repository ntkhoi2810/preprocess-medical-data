import os
import re
from pathlib import Path
import requests
import json
import time
from typing import Optional
from loguru import logger

import dotenv
dotenv.load_dotenv()


def extract_book_information(file_path):
    """
    Extract the first 5 pages and the last 5 pages of a book.
    
    Args:
        file_path (str): Path to the markdown book file
        
    Returns:
        str: A markdown string containing the extracted first and last 5 pages
    """
    # Ensure the file exists
    if not os.path.isfile(file_path):
        raise ValueError(f"File {file_path} does not exist")
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get book title from filename
    book_file = os.path.basename(file_path)
    book_title = os.path.splitext(book_file)[0].replace('_', ' ')
    
    genre = file_path.split('/')[-2]
    # Initialize result markdown
    result_md = f"# {book_title}\n\n"
    result_md += f"## Genre: Nội Khoa, {genre}\n\n"
    
    # Split content by page markers or approximate pages
    # This assumes pages are either marked by page breaks or we estimate ~3000 characters per page
    pages = []
    
    # Try to find page break markers (common in markdown)
    page_markers = re.split(r'\n\s*---\s*\n|\n\s*\*\*\*\s*\n|\n\s*___\s*\n', content)
    
    if len(page_markers) > 1:
        # If we found page markers, use those
        pages = page_markers
    else:
        # Otherwise estimate pages based on character count
        # Assume approximately 3000 characters per page
        chars_per_page = 3000
        total_chars = len(content)
        total_pages = max(10, (total_chars + chars_per_page - 1) // chars_per_page)
        
        for i in range(min(total_pages, 5)):
            start_idx = i * chars_per_page
            end_idx = min((i + 1) * chars_per_page, total_chars)
            pages.append(content[start_idx:end_idx])
        
        # Add last 5 pages if there are more than 10 pages
        if total_pages > 10:
            for i in range(max(5, total_pages - 5), total_pages):
                start_idx = i * chars_per_page
                end_idx = min((i + 1) * chars_per_page, total_chars)
                pages.append(content[start_idx:end_idx])
    
    # Extract first 5 pages
    result_md += "## First 5 Pages\n\n"
    for i, page in enumerate(pages[:3]):
        result_md += f"### Page {i+1}\n\n{page.strip()}\n\n"
    
    # Extract last 5 pages
    result_md += "## Last 3 Pages\n\n"
    for i, page in enumerate(pages[-3:]):
        result_md += f"### Page {len(pages)-4+i}\n\n{page.strip()}\n\n"
    
    return result_md


def generate_with_yescale(prompt: str,
                          model: str = "gemini-2.5-flash-preview-04-17",
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
    api_key = os.getenv('YESCALE_API_KEY')  
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_mime_type": "application/json"
    }
    
    # Add thinking configuration for Gemini models to completely disable thinking
    if "gemini-2.5" in model.lower():
        data["generationConfig"] = {
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    # print(data)
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            response_data = response.json()
            # print(response_data)
            
            # Check if response contains an error field
            if "error" in response_data:
                error_msg = response_data.get("error", {}).get("message", "Unknown error")
                error_code = response_data.get("error", {}).get("code", "unknown")
                logger.warning(f"YesScale API returned error: {error_code} - {error_msg}")
                # Continue to retry as this is a server error
                raise Exception(f"API error: {error_msg}")
            
            # Check for valid response with choices
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
                
            # If we get here, response is invalid but doesn't have an error field
            logger.warning(f"YesScale API returned invalid response format: {response_data}")
            raise Exception("Invalid API response format")
            
        except Exception as exc:
            wait = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(f"YesScale API error ({type(exc).__name__}: {str(exc)}) - attempt {attempt}/{max_attempts}; waiting {wait}s before retry...")
            
            if attempt < max_attempts:
                time.sleep(wait)
            else:
                logger.error(f"Failed to connect to YesScale API after {max_attempts} attempts: {exc}")
                return None

def extract_book_metadata(book_info: str, 
                           model: str = "gemini-2.5-flash-preview-04-17",
                           temperature: float = 0.1) -> Optional[dict]:
    """
    Extract metadata from book information using Gemini through YesScale API.
    
    Args:
        book_info (str): Book information in markdown format (from extract_book_information)
        model (str): Model name to use
        temperature (float): Temperature for generation
        
    Returns:
        dict: Extracted metadata with the following structure:
        {
            "title": str,                     # Book title
            "author": str | list[str],        # Author(s) name(s)
            "publication_year": int | None,   # Year of publication
            "genre": list[str],               # List of genres/categories
            "publisher": str | None,          # Publisher name
            "language": str | None,           # Main language of the book
            "topics": list[str],              # List of main topics or keywords
        }
        or None if extraction fails
    """
    # System prompt to guide Gemini
    system_prompt = """You are an expert in extracting book metadata. 
    Analyze the provided book content and extract relevant metadata.
    Return ONLY a JSON object without any explanation or additional text."""
    
    # Construct the prompt for Gemini with specific output structure
    prompt = f"""Based on the following book content, extract all possible metadata in Vietnamese with the following JSON structure:
    
    ```json
    {{
        "title": "string",                     // Book title in Vietnamese
        "publisher": "string",                 // Publisher name (null if unknown)
        "publication_year": number,            // Year of publication (null if unknown)
        "edition": number,                      // Edition number (null if unknown)
        "genre": ["string", "string"],         // List of genres/categories, e.g. ["Nội khoa", "Cơ xương khớp"]
        "language": "string",                  // Main language of the book (null if unknown), e.g. "Vietnamese", "English", .etc
        "keywords": ["string", "string", "string"],        // List of 3 topics or keywords that are most relevant to the book
    }}

    If you cannot determine a field with confidence, use null for that field.
    For fields that expect arrays, provide an empty array [] if no values are found.
    Format your response as a valid JSON object ONLY, with no additional text.

    BOOK CONTENT:
    {book_info}
    """
    
    # Call YesScale API with Gemini
    response = generate_with_yescale(
        prompt=prompt, 
        model=model, 
        temperature=temperature, 
        system_prompt=system_prompt
    )
    
    if not response:
        logger.error("Failed to extract book metadata")
        return None
    
    # Parse the JSON response
    try:
        # Clean response to remove markdown code block formatting if present
        clean_response = response
        if response.startswith("```json"):
            clean_response = re.sub(r'^```json\s*', '', response)
            clean_response = re.sub(r'\s*```$', '', clean_response)
        elif response.startswith("```"):
            clean_response = re.sub(r'^```\s*', '', response)
            clean_response = re.sub(r'\s*```$', '', clean_response)
            
        metadata = json.loads(clean_response)
        
        # Ensure the response has the expected structure
        expected_fields = ["title", "publication_year", "genre", "publisher", 
                           "language", "keywords"]
        
        # Add any missing fields with default values
        for field in expected_fields:
            if field not in metadata:
                if field in ["keywords"]:
                    metadata[field] = []
                else:
                    metadata[field] = None
        
        return metadata
    except json.JSONDecodeError:
        logger.error(f"Failed to parse metadata response as JSON: {response[:200]}...")
        return None

def main():
    """
    Process all markdown files in the raw/ directory, extract metadata,
    and write to a JSON file.
    """
    # Define base path for raw data
    base_path = Path("/teamspace/studios/this_studio/preprocess-medical-data/data/md/raw")
    
    # Output file for metadata
    output_file = "/teamspace/studios/this_studio/preprocess-medical-data/data/md/noi-khoa-metadata.json"
    
    # Get all folders in raw/
    folders = [f for f in base_path.iterdir() if f.is_dir()]
    
    # Dictionary to store all metadata
    all_metadata = {}
    
    # Process each folder
    for folder in folders:
        genre = folder.name
        logger.info(f"Processing folder: {genre}")
        
        # Get all markdown files in this folder
        md_files = list(folder.glob("*.md"))
        
        # Process each file
        for md_file in md_files:
            file_path = str(md_file)
            logger.info(f"Processing file: {md_file.name}")
            
            try:
                # Extract book information and metadata
                book_info = extract_book_information(file_path)
                metadata = extract_book_metadata(book_info)
                
                if metadata:
                    # Add to collection using file name as key
                    all_metadata[md_file.stem] = metadata
                    logger.success(f"Successfully extracted metadata for {md_file.name}")
                else:
                    logger.warning(f"Failed to extract metadata for {md_file.name}")
            
            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {str(e)}")
    
    # Write all metadata to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        logger.success(f"Successfully wrote metadata to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to JSON file: {str(e)}")

if __name__ == "__main__":
    main()
    # Example of processing a single file:
    # book_info = extract_book_information("/teamspace/studios/this_studio/preprocess-medical-data/data/md/raw/CO-XUONG-KHOP/BENH_THAP_KHOP_DH_Y_HA_NOI.md")
    # metadata = extract_book_metadata(book_info)
    # print(metadata)
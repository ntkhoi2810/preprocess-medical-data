#!/usr/bin/env python3
import sys
import logging
import dotenv
from chunking import split_markdown_into_chunks
from merge_chunks import merge_markdown_files
from upload_to_huggingface import load_data_to_json, push_data_to_hf
import process_chunks
import os
import time
from google.generativeai import GenerativeModel
import glob
import huggingface_hub

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration parameters
CONFIGS = {
    # Paths
    'pdf_dir': '../preprocess-medical-data/data/pdf',
    'md_raw_dir': '../preprocess-medical-data/data/md/raw',
    'md_chunks_dir': '../preprocess-medical-data/data/md/chunks',
    'md_processed_dir': '../preprocess-medical-data/data/md/processed',
    'jsonl_output': '../preprocess-medical-data/output/dataset.jsonl',
    'hf_repo': 'ntkhoi/book-medical-corpus',
    
    # Chunking
    'chunk_size': 3000,
    
    # Model
    'model': 'gemini-2.0-flash',
    'delay': 2,  # Increased delay between API calls
    'max_retries': 3,
    'retry_delay': 10
}

def run_pipeline():
    """Run the complete data processing pipeline"""

    # Step 1: Chunk raw markdown data
    logger.info("Step 1: Running chunking process...")
    
    input_directory = CONFIGS['md_raw_dir']
    chunks_directory = CONFIGS['md_chunks_dir']
    split_markdown_into_chunks(input_directory, chunks_directory, CONFIGS['chunk_size'])
    logger.info("Chunking process completed.")
    
    # Step 2: Process chunks using Gemini
    logger.info("Step 2: Running process_chunks to refine with Gemini...")
    
    # Setup Google Generative AI with API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set. Please set it and try again.")
        return False
    
    try:
        process_chunks.setup_genai(api_key)
        
        # Load the model
        logger.info(f"Loading Gemini model: {CONFIGS['model']}")
        try:
            model = GenerativeModel(CONFIGS['model'])
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
        
        # Process all markdown files in the chunks directory
        chunk_files = glob.glob(os.path.join(CONFIGS['md_chunks_dir'], '**/*.md'), recursive=True)
        
        if not chunk_files:
            logger.warning(f"No markdown files found in {CONFIGS['md_chunks_dir']}")
            return False
        
        logger.info(f"Found {len(chunk_files)} files to process")
        
        successful_files = 0
        for file_path in chunk_files:
            try:
                success = process_chunks.process_markdown_file(
                    file_path, 
                    model, 
                    max_retries=CONFIGS['max_retries'],
                    retry_delay=CONFIGS['retry_delay']
                )
                
                if success:
                    successful_files += 1
                    
                # Add a delay to avoid rate limiting
                logger.info(f"Waiting {CONFIGS['delay']} seconds before next request...")
                time.sleep(CONFIGS['delay'])
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        logger.info(f"Processing completed. Successfully processed {successful_files}/{len(chunk_files)} files.")
        
        if successful_files == 0:
            logger.error("No files were successfully processed. Aborting pipeline.")
            return False
        
    except Exception as e:
        logger.error(f"Error in process_chunks phase: {str(e)}")
        return False
    
    # Step 3: Merge processed chunks
    logger.info("Step 3: Running merge_chunks to combine processed chunks...")
    
    source_directory = CONFIGS['md_chunks_dir']
    output_directory = CONFIGS['md_processed_dir']
    merge_markdown_files(source_directory, output_directory)
    logger.info("Merging chunks completed.")
    
    # Step 4: Upload processed data to Hugging Face
    logger.info("Step 4: Running upload_to_huggingface to push data to HF...")
    
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        logger.error("HF_TOKEN environment variable is not set. Please set it and try again.")
        return False
    
    try:
        os.environ["HF_TOKEN"] = hf_token
        huggingface_hub.login(token=hf_token)
        
        load_data_to_json(CONFIGS["md_processed_dir"], CONFIGS["jsonl_output"])
        push_data_to_hf(CONFIGS["jsonl_output"], CONFIGS["hf_repo"])
        logger.info("Upload to Hugging Face completed.")
    except Exception as e:
        logger.error(f"Error in upload to Hugging Face phase: {str(e)}")
        return False
    
    logger.info("Pipeline completed successfully!")
    return True

if __name__ == "__main__":
    success = run_pipeline()
    if not success:
        logger.error("Pipeline failed to complete successfully.")
        sys.exit(1)
    sys.exit(0)

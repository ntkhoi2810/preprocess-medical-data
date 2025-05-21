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
import glob
import huggingface_hub
import threading
import concurrent.futures
from queue import Queue
from threading import Semaphore

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
    'hf_repo': 'ntkhoi/noi-khoa-2-with-metadata',
    
    # Chunking
    'chunk_size': 3000,
    
    # Model
    # 'model': 'gemini-2.0-flash',
    'model': 'gemini-2.5-flash-preview-04-17',
    'delay': 2,  # Delay between API calls
    'max_retries': 3,
    'retry_delay': 10,
    
    # Threading
    'max_workers': 100,  # Maximum number of parallel workers
    'rate_limit_rpm': 1000  # Rate limit in requests per minute
}

# Create a rate limiter to manage API requests
class RateLimiter:
    def __init__(self, max_calls, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()
        self.requests_sent = 0
        self.responses_received = 0
        
    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            # Remove timestamps older than the period
            self.calls = [ts for ts in self.calls if now - ts < self.period]
            
            if len(self.calls) >= self.max_calls:
                # Wait until we can make another call
                sleep_time = self.calls[0] + self.period - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Clean up the calls list again after sleeping
                    now = time.time()
                    self.calls = [ts for ts in self.calls if now - ts < self.period]
            
            # Record this call
            self.calls.append(time.time())
            
    def increment_sent(self):
        with self.lock:
            self.requests_sent += 1
            logger.info(f"Request sent. Total requests sent: {self.requests_sent}")
            
    def increment_received(self):
        with self.lock:
            self.responses_received += 1
            logger.info(f"Response received. Total responses received: {self.responses_received}")

def process_file_worker(file_path, model, max_retries, retry_delay, rate_limiter, results):
    """Process a single markdown file with rate limiting"""
    try:
        # Wait if we're exceeding the rate limit
        rate_limiter.wait_if_needed()
        
        # Log that we're sending a request
        rate_limiter.increment_sent()
        
        success = process_chunks.process_markdown_file(
            file_path,
            model,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Log that we've received a response
        rate_limiter.increment_received()
        
        if success:
            results['successful'] += 1
        
        logger.info(f"Processed {file_path}, success: {success}")
        return success
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

def run_pipeline():
    """Run the complete data processing pipeline"""

    # Step 1: Chunk raw markdown data
    logger.info("Step 1: Running chunking process...")
    
    input_directory = CONFIGS['md_raw_dir']
    chunks_directory = CONFIGS['md_chunks_dir']
    split_markdown_into_chunks(input_directory, chunks_directory, CONFIGS['chunk_size'])
    logger.info("Chunking process completed.")
    
    # Step 2: Process chunks using YesScale API
    logger.info("Step 2: Running process_chunks to refine with YesScale API...")
    
    try:
        # Check for YesScale API key
        yescale_api_key = os.getenv("YESCALE_API_KEY")
        if not yescale_api_key:
            logger.error("YESCALE_API_KEY environment variable is not set. Please set it and try again.")
            return False
            
        # Process all markdown files in the chunks directory
        chunk_files = glob.glob(os.path.join(CONFIGS['md_chunks_dir'], '**/*.md'), recursive=True)
        
        if not chunk_files:
            logger.warning(f"No markdown files found in {CONFIGS['md_chunks_dir']}")
            return False
        
        logger.info(f"Found {len(chunk_files)} files to process")
        
        # Initialize rate limiter and results counter
        rate_limiter = RateLimiter(CONFIGS['rate_limit_rpm'])
        results = {'successful': 0}
        
        # Process files in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIGS['max_workers']) as executor:
            futures = []
            for file_path in chunk_files:
                if file_path.endswith('_done.md'):
                    continue
                future = executor.submit(
                    process_file_worker,
                    file_path,
                    CONFIGS['model'],
                    CONFIGS['max_retries'],
                    CONFIGS['retry_delay'],
                    rate_limiter,
                    results
                )
                futures.append(future)
            
            # Wait for all futures to complete
            concurrent.futures.wait(futures)
        
        logger.info(f"Processing completed. Successfully processed {results['successful']}/{len(chunk_files)} files.")
        logger.info(f"Total API requests sent: {rate_limiter.requests_sent}, Total responses received: {rate_limiter.responses_received}")
        
        if results['successful'] == 0:
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

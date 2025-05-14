set -e 

# Define directories
INPUT_DIR="../data/pdf"
OUTPUT_DIR="../data/md/raw"

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Run marker
echo "Converting PDFs to Markdown"
marker $INPUT_DIR --output_dir $OUTPUT_DIR --output_format markdown --disable_image_extraction --languages "vi,en"

# Chunk markdown files into smaller chunks
echo "Chunking markdown files"
python ../scr/chunk_markdown.py 

# Refine chunks with Gemini
echo "Refining chunks with Gemini"
python ../scr/process_chunks.py 

# Merge refined chunks
echo "Merging refined chunks"
python ../scr/merge_chunks.py 

# Upload data to Hugging Face
echo "Uploading to Hugging Face"
python ../scr/upload_to_huggingface.py 
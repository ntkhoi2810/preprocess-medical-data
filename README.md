# Medical Data Preprocessing Pipeline

This repository contains tools for preprocessing medical documents, converting PDFs to markdown, and preparing data for further processing.

## Setup

### 1. Create required folder structure

```bash
# Create main data directory
mkdir -p data/pdf
mkdir -p data/md/raw
mkdir -p data/md/chunks
mkdir -p data/md/processed

# Create output directory
mkdir -p output
```

### 2. Install required dependencies

```bash
pip install -r requirements.txt
```

### 3. Convert PDF to Markdown using marker

Place your PDF files in the `data/pdf` directory, then run:

```bash
marker data/pdf --output_dir data/md/raw --output_format markdown --disable_image_extraction --languages "vi,en"
```

### 4. Create environment file

Create a `.env` file in the root directory with the following variables:

```
GEMINI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
```

### 5. Configure and run the pipeline

You can adjust the configuration parameters in `src/main.py` if needed, including:
- Paths for input/output directories
- Chunk size for text splitting
- Gemini model to use
- Delay between API calls

Then run the pipeline:

```bash
python src/main.py
```

## Pipeline Process

The pipeline performs the following steps:
1. Splits the raw markdown files into manageable chunks
2. Processes each chunk using the Gemini model
3. Merges the processed chunks back together
4. Uploads the processed data to Hugging Face

## Requirements

- Python 3.10+
- marker-pdf
- Python packages listed in requirements.txt

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

### 3. Create environment file

Create a `.env` file in the root directory with the following variables:

```
GEMINI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
```

### 4. Add your PDF files

Place your PDF files in the `data/pdf` directory.

### 5. Run the pipeline

You can run the entire pipeline using the provided script:

```bash
./scripts/run.sh
```

This script will:
1. Convert PDFs to markdown using marker
2. Run the preprocessing pipeline

## Pipeline Process

The pipeline performs the following steps:
1. Splits the raw markdown files into manageable chunks
2. Processes each chunk using the Gemini model
3. Merges the processed chunks back together
4. Uploads the processed data to Hugging Face

## Configuration

You can adjust the configuration parameters in `src/main.py` if needed, including:
- Paths for input/output directories
- Chunk size for text splitting
- Gemini model to use
- Delay between API calls

## Requirements

- Python 3.10+
- marker-pdf
- Python packages listed in requirements.txt

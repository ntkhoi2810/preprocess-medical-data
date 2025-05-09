import os
import re
from pathlib import Path

def split_markdown_into_chunks(input_dir, output_dir, words_per_chunk=2000):
    """
    Split markdown files into chunks of approximately specified word count,
    ensuring chunks break at paragraph boundaries ("\n\n")
    
    Args:
        input_dir (str): Path to input directory containing markdown files
        output_dir (str): Path to output directory for chunked files
        words_per_chunk (int): Approximate number of words per chunk
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize chunk counter
    chunk_counter = 1
    
    # Find all markdown files in the input directory
    markdown_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    
    # Process each file
    for md_file in markdown_files:
        print(f"Processing {md_file}...")
        
        # Read file content
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into paragraphs
        paragraphs = content.split("\n\n")
        
        # Initialize variables for chunking
        current_chunk = []
        current_word_count = 0
        
        # Process each paragraph
        for paragraph in paragraphs:
            # Count words in paragraph
            paragraph_words = len(re.findall(r'\b\w+\b', paragraph))
            
            # If adding this paragraph exceeds the word limit and we already have content,
            # save the current chunk and start a new one
            if current_word_count + paragraph_words > words_per_chunk and current_chunk:
                # Join paragraphs with double newlines to maintain formatting
                chunk_content = "\n\n".join(current_chunk)
                
                # Save chunk to file
                chunk_filename = f"{chunk_counter:03d}.md"
                chunk_path = os.path.join(output_dir, chunk_filename)
                
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)
                
                print(f"Created chunk {chunk_filename} with approximately {current_word_count} words")
                chunk_counter += 1
                
                # Reset for next chunk
                current_chunk = [paragraph]
                current_word_count = paragraph_words
            else:
                # Add paragraph to current chunk
                current_chunk.append(paragraph)
                current_word_count += paragraph_words
        
        # Don't forget to save the last chunk if it has content
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunk_filename = f"{chunk_counter:03d}.md"
            chunk_path = os.path.join(output_dir, chunk_filename)
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk_content)
            
            print(f"Created chunk {chunk_filename} with approximately {current_word_count} words")
            chunk_counter += 1

if __name__ == "__main__":
    input_directory = "./data/markdown"  # Path to markdown files
    output_directory = "./data/processed/chunks"  # Output directory for chunks
    
    # Create the output directory
    os.makedirs(output_directory, exist_ok=True)
    
    split_markdown_into_chunks(input_directory, output_directory)

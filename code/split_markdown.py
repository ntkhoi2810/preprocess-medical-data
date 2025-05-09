import re
import os
from typing import List 

def chunk_markdown_by_h3(markdown_content: str) -> List[str]:
    """
    Split a markdown string into chunks based on level 3 headings (### headings).
    Each chunk starts with a level 3 heading and includes all content until the next level 3 heading.
    
    Args:
        markdown_content: The markdown content to split

    Returns:
        A list of markdown chunks
    """
    # Pattern to match level 3 headings
    h3_pattern = r'^###\s+.*$'
    
    # Split the content by level 3 headings
    lines = markdown_content.split('\n')
    chunks = []
    current_chunk = []
    
    for line in lines:
        # If we find a level 3 heading and we have content in current_chunk,
        # save the current chunk and start a new one
        if re.match(h3_pattern, line) and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
        # If we find a level 3 heading and have no current chunk, start a new chunk
        elif re.match(h3_pattern, line):
            current_chunk = [line]
        # Otherwise add the line to the current chunk if we have one
        elif current_chunk:
            current_chunk.append(line)
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def split_large_chunk(chunk: str, max_length: int = 20000) -> List[str]:
    """
    Split a large chunk into smaller sub-chunks if it exceeds the maximum length.
    
    Args:
        chunk: The markdown chunk to split
        max_length: Maximum length allowed for a chunk
        
    Returns:
        A list of smaller chunks
    """
    if len(chunk) <= max_length:
        return [chunk]
    
    # Extract the first line (heading)
    lines = chunk.split('\n')
    heading = lines[0]
    content = '\n'.join(lines[1:])
    
    # Split the content into sub-chunks
    sub_chunks = []
    while content:
        # If remaining content is less than max_length, add it as the last sub-chunk
        if len(content) <= max_length:
            sub_chunks.append(f"{heading}\n{content}")
            break
        
        # Find a good split point (preferably at paragraph boundary)
        split_point = content[:max_length].rfind('\n\n')
        if split_point == -1:  # If no paragraph boundary found, try line break
            split_point = content[:max_length].rfind('\n')
        if split_point == -1:  # If no line break found, split at max_length
            split_point = max_length - 1
        
        # Create sub-chunk with the heading
        sub_chunks.append(f"{heading} (Part {len(sub_chunks) + 1})\n{content[:split_point + 1]}")
        
        # Remove the extracted content
        content = content[split_point + 1:]
    
    return sub_chunks

def save_chunks_to_files(chunks: List[str], output_dir: str) -> None:
    """
    Save markdown chunks to individual numbered files.
    Split chunks larger than 20000 characters into smaller chunks.
    
    Args:
        chunks: List of markdown chunks to save
        output_dir: Directory to save the files in
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    file_counter = 1
    total_chunks = 0
    
    # Save each chunk to a numbered file
    for chunk in chunks:
        # Split large chunks
        sub_chunks = split_large_chunk(chunk)
        total_chunks += len(sub_chunks)
        
        for sub_chunk in sub_chunks:
            filename = f"{file_counter:03d}.md"  # Format: 001.md, 002.md, etc.
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sub_chunk)
            
            file_counter += 1
            
    print(f"Saved {total_chunks} files to {output_dir}")

def main():
    # Input markdown file
    md_file = '/teamspace/studios/this_studio/preprocess-medical-data/benhhoc_4.md'
    
    # Output directory
    output_dir = '/teamspace/studios/this_studio/preprocess-medical-data/benhhoc4_chunks'
    
    # Read the markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into chunks
    chunks = chunk_markdown_by_h3(content)
    
    # Save chunks to files
    save_chunks_to_files(chunks, output_dir)
    
    print(f"Split markdown into {len(chunks)} initial chunks")
    
if __name__ == "__main__":
    main() 
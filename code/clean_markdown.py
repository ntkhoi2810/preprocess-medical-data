import re
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


# def chunk_markdown_file_by_h3(file_path: str) -> List[str]:
#     """
#     Read a markdown file and split it into chunks based on level 3 headings.
    
#     Args:
#         file_path: Path to the markdown file
        
#     Returns:
#         A list of markdown chunks
#     """
#     with open(file_path, 'r', encoding='utf-8') as f:
#         content = f.read()
    
#     return chunk_markdown_by_h3(content)

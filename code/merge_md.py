import os
import re

def natural_sort_key(s):
    """Sort strings with numerical parts naturally (e.g., '1', '2', '10' instead of '1', '10', '2')"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def merge_markdown_files(source_dir, output_file):
    """Merge markdown files from source_dir into a single output file in numerical order"""
    # Check if source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return False
    
    # Get all markdown files
    md_files = [f for f in os.listdir(source_dir) if f.endswith('.md')]
    
    if not md_files:
        print(f"No markdown files found in '{source_dir}'.")
        return False
    
    # Sort files naturally
    md_files.sort(key=natural_sort_key)
    
    print(f"Found {len(md_files)} markdown files to merge.")
    
    # Merge files
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for md_file in md_files:
            file_path = os.path.join(source_dir, md_file)
            print(f"Adding {md_file}")
            
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                
                # Add a newline at the end of each file's content if it doesn't have one
                if content and not content.endswith('\n'):
                    content += '\n\n'
                
                outfile.write(content)
    
    print(f"Successfully merged files into '{output_file}'")
    return True

if __name__ == "__main__":
    source_directory = "/teamspace/studios/this_studio/preprocess-medical-data/benhhoc4_chunks"
    output_filename = "/teamspace/studios/this_studio/preprocess-medical-data/Bách khoa thư bệnh học tập 4.md"
    
    merge_markdown_files(source_directory, output_filename)

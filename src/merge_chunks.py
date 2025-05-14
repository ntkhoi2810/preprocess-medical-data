import os
import re

def natural_sort_key(s):
    """Sort strings with numerical parts naturally (e.g., '1', '2', '10' instead of '1', '10', '2')"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def merge_markdown_files(source_dir, output_dir):
    """Merge markdown files from inner folders in source_dir into separate files in output_dir"""
    # Check if source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all directories in the source folder
    inner_folders = [f for f in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, f))]
    
    if not inner_folders:
        print(f"No inner folders found in '{source_dir}'.")
        return False
    
    print(f"Found {len(inner_folders)} folders to process.")
    
    for folder in inner_folders:
        folder_path = os.path.join(source_dir, folder)
        output_file = os.path.join(output_dir, f"{folder}.md")
        
        print(f"\nProcessing folder: {folder}")
        
        # Get all markdown files in the current folder
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files:
            print(f"No markdown files found in '{folder}'.")
            continue
        
        # Sort files naturally
        md_files.sort(key=natural_sort_key)
        
        print(f"Found {len(md_files)} markdown files to merge.")
        
        # Merge files
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for md_file in md_files:
                file_path = os.path.join(folder_path, md_file)
                print(f"Adding {md_file}")
                
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    
                    # Add a newline at the end of each file's content if it doesn't have one
                    if content and not content.endswith('\n'):
                        content += '\n\n'
                    
                    outfile.write(content)
        
        print(f"Successfully merged files into '{output_file}'")
    
    return True
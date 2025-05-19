#♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦#

repo_hf_dataset="________" #Chỉnh lại thành tên dataset của bạn

#♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦♦#









































































bash scripts/setup_1.sh

if [ -d "data/pdf" ] && [ "$(ls -A data/pdf)" ]; then
    echo "Repository already exists and has content. Skipping clone and extraction."
else
    echo "Cloning repository..."
    git clone https://huggingface.co/datasets/$repo_hf_dataset data/pdf
    
    if ls data/pdf/*.zip 1> /dev/null 2>&1; then
        echo "Found zip files, extracting..."
        unzip "data/pdf/*.zip" -d "data/pdf"
        echo "Extraction complete"
    else
        echo "No zip files found"
    fi
fi

bash scripts/setup_2.sh

bash scripts/process_all.sh
mkdir -p data/pdf
mkdir -p data/md/raw
mkdir -p data/md/chunks
mkdir -p data/md/processed
mkdir -p output
pip install -r requirements.txt

touch .env

python src/rename-folders.py
python src/split-lagre-pdf.py

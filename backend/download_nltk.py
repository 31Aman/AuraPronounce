import os
import urllib.request
import zipfile

print("--- Downloading NLTK datasets for production ---")

nltk_data_dir = "nltk_data"
corpora_dir = os.path.join(nltk_data_dir, "corpora")
taggers_dir = os.path.join(nltk_data_dir, "taggers")

os.makedirs(corpora_dir, exist_ok=True)
os.makedirs(taggers_dir, exist_ok=True)

# Define downloads
downloads = {
    "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/cmudict.zip": os.path.join(corpora_dir, "cmudict.zip"),
    "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger.zip": os.path.join(taggers_dir, "averaged_perceptron_tagger.zip")
}

for url, dest in downloads.items():
    print(f"Downloading {url} to {dest}...")
    try:
        urllib.request.urlretrieve(url, dest)
        extract_to = os.path.dirname(dest)
        print(f"Extracting {dest} to {extract_to}...")
        with zipfile.ZipFile(dest, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Success.")
    except Exception as e:
        print(f"[ERROR] Failed to download/extract {url}: {e}")

print("NLTK pre-download process completed successfully!")

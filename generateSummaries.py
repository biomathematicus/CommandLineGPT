import os
import json
import PyPDF2
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk
from nltk.data import find, path as nltk_path
from datetime import datetime
# Install tokenizers with: 
# python -c "import nltk; nltk.download('punkt_tab')"

# Constant value identifying the OPUS version
OPUS = 4235

# Percentage of total sentences to include in summary
SUMMARY_PERCENTAGE = 25  # Adjustable summary length control

# Path to the base OPUS JSON structure used as a template
OPUS_PATH = "opus_4235.json"

# Directory containing unit folders named in a specific format
OPUS_MATERIALS = "C:\\temp\\Units"

# Directory to store tokenizer data and generated JSON files
OUTPUT_DIR = os.path.dirname(OPUS_PATH)
NLTK_DATA_DIR = os.path.abspath(OUTPUT_DIR)
nltk_path.append(NLTK_DATA_DIR)  # Add to nltk search path

# Setup log file
log_file_path = os.path.join(OUTPUT_DIR, "log.txt")
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(full_message + "\n")

# Ensure 'punkt' tokenizer is available in OUTPUT_DIR
try:
    find('tokenizers/punkt')
    log("[✓] 'punkt' tokenizer found.")
except LookupError:
    log("[!] 'punkt' tokenizer not found. Downloading to output directory...")
    nltk.download('punkt', download_dir=NLTK_DATA_DIR)
    log(f"[✓] 'punkt' tokenizer downloaded to: {NLTK_DATA_DIR}")

# Show all directories NLTK will search
log(f"[!] NLTK search paths: {nltk_path}")

# List to hold [folder path, descriptor] pairs
folder_descriptor_pairs = []

# Iterate through entries in the OPUS_MATERIALS directory
log("[!] Scanning OPUS_MATERIALS directory...")
for entry in os.listdir(OPUS_MATERIALS):
    full_path = os.path.join(OPUS_MATERIALS, entry)
    if os.path.isdir(full_path):
        descriptor = entry.split()[0]
        folder_descriptor_pairs.append([full_path, descriptor])
log(f"[✓] Found {len(folder_descriptor_pairs)} unit folders.")

# Extract text from a PDF file given its path
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        log("-------------------------------")
        log(f"[✓] Extracted text from: {pdf_path}")
    except Exception as e:
        log("-------------------------------")
        log(f"[✗] Error reading PDF {pdf_path}: {str(e)}")
        return "Error reading PDF."
    return text.strip().replace("\n", " ")

# Generate a summary using the TextRank algorithm via sumy
def generate_summary(text):
    if not text:
        return "No content found."
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    total_sentences = len(list(parser.document.sentences))
    sentence_count = max(1, total_sentences * SUMMARY_PERCENTAGE // 100)
    log(f"[!] Total sentences: {total_sentences}, Summarized sentences: {sentence_count}")
    summarizer = TextRankSummarizer()
    summary_sentences = summarizer(parser.document, sentence_count)
    return " ".join(str(sentence) for sentence in summary_sentences)

# Recursively gather all PDF file paths in a folder
def process_folder(folder_path):
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for name in files:
            if name.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, name))
    log(f"[✓] Found {len(pdf_files)} PDFs in: {folder_path}")
    return pdf_files

# Process each folder-descriptor pair
for folder_path, descriptor in folder_descriptor_pairs:
    log("==============================")
    log(f"[!] Processing folder: {folder_path} with descriptor: {descriptor}")
    knowledge_entries = []
    pdfs = process_folder(folder_path)
    for pdf_path in pdfs:
        content = extract_text_from_pdf(pdf_path)
        summary = generate_summary(content)
        knowledge_entries.append({"file": pdf_path, "summary": summary})

    try:
        with open(OPUS_PATH, 'r') as base_file:
            opus_data = json.load(base_file)
        opus_data['knowledgeBase'] = knowledge_entries
        output_filename = os.path.join(OUTPUT_DIR, f"opus_{OPUS}_{descriptor}.json")
        with open(output_filename, 'w') as output_file:
            json.dump(opus_data, output_file, indent=2)
        log(f"[✓] Written summary JSON: {output_filename}")
    except Exception as e:
        log(f"[✗] Failed to write JSON for descriptor {descriptor}: {str(e)}")

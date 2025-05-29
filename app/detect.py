import fitz  # PyMuPDF
import numpy as np
from difflib import SequenceMatcher

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def tokenize(text):
    # Tokenize text by splitting into words (you can refine this with a more sophisticated tokenizer if needed)
    return text.lower().split()

def compare_token_sequences(template_pdf, new_pdf):
    template_text = extract_text(template_pdf)
    new_text = extract_text(new_pdf)

    # Tokenize the text
    template_tokens = tokenize(template_text)
    new_tokens = tokenize(new_text)

    # Compute sequence similarity using Levenshtein distance (ratio of similarity)
    similarity_ratio = SequenceMatcher(None, template_tokens, new_tokens).ratio()

    return similarity_ratio

# Example usage
template_pdf = "../sample_invoices/iabe/iabe_1.pdf"
new_pdf = "../sample_invoices/iabe/iabe.pdf"
similarity = compare_token_sequences(template_pdf, new_pdf)

# Set a threshold for similarity (e.g., 90% similarity)
threshold = 0.9
if similarity >= threshold:
    print(f"The PDFs are structurally similar with a similarity score of {similarity:.2f}")
else:
    print(f"The PDFs are not similar. Similarity score: {similarity:.2f}")

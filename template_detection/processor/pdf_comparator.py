import fitz
from difflib import SequenceMatcher
import logging

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def tokenize(text):
    # Tokenize text by splitting into words
    return text.lower().split()

def compare_token_sequences(template_pdf, new_pdf):
    template_text = extract_text(template_pdf)
    new_text = extract_text(new_pdf)

    # Tokenize the text
    template_tokens = tokenize(template_text)
    new_tokens = tokenize(new_text)

    # Compute sequence similarity using Levenshtein distance (ratio of similarity)
    similarity_ratio = SequenceMatcher(None, template_tokens, new_tokens).ratio()

    logging.info(f"Compared {template_pdf} and {new_pdf}. Similarity: {similarity_ratio:.2f}")
    return similarity_ratio

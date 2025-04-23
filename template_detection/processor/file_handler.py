import os
import shutil
import logging

def move_to_unprocessed(file_path, destination_folder):
    """Moves a file to the unprocessed folder"""
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    try:
        shutil.move(file_path, destination_folder)
        logging.info(f"Moved {file_path} to {destination_folder}")
    except Exception as e:
        logging.error(f"Error moving file {file_path}: {e}")

def get_all_files_in_folder(folder_path):
    """Returns all PDF files from the folder"""
    return [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

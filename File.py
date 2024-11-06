import os
import random
import string
import time
from datetime import datetime
import subprocess
import uuid

def generate_random_word(length=8):
    """Generate a random word using letters and numbers."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_folder_structure():
    author_name = "MD. Naiem Islam Nahid"
    base_dir = "generated_folders"
    
    # Create base directory if it doesn't exist
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # Create 1000 folders
    for folder_num in range(1, 1001):
        # Generate random folder name with serial number
        random_word = generate_random_word()
        folder_name = f"{folder_num:04d}_{random_word}"
        folder_path = os.path.join(base_dir, folder_name)
        
        # Create folder
        os.makedirs(folder_path)
        
        # Git commit for folder creation
        subprocess.run(['git', 'add', folder_path])
        commit_msg = f"Created folder: {folder_name}"
        subprocess.run(['git', 'commit', '-m', commit_msg])
        
        # Create 100 files in the folder
        for file_num in range(1, 101):
            # Get current timestamp with nanoseconds
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime('%Y-%m-%d_%H-%M-%S-%f')
            
            # Create unique file name
            file_name = f"{folder_name}_{timestamp_str}.txt"
            file_path = os.path.join(folder_path, file_name)
            
            # Write content to file
            with open(file_path, 'w') as f:
                content = f"""Timestamp: {timestamp}
Date: {timestamp.strftime('%Y-%m-%d')}
Created by: {author_name}
Folder: {folder_name}
File: {file_name}
UUID: {uuid.uuid4()}"""
                f.write(content)
            
            # Git commit for file creation
            subprocess.run(['git', 'add', file_path])
            commit_msg = f"Created file in {folder_name}: {file_name}"
            subprocess.run(['git', 'commit', '-m', commit_msg])
        
        print(f"Completed folder {folder_num}/1000: {folder_name}")

if __name__ == "__main__":
    try:
        create_folder_structure()
        print("Successfully created all folders and files with git commits!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
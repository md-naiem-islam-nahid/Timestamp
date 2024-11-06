# Random File & Folder Generator with Git Automation 🗂️

Welcome to the **Random File & Folder Generator with Git Automation** repository! This project is an exploration of generating complex file and folder structures across multiple programming languages (Python, C++, and C), with custom content, metadata, and automated Git commits. Each script creates numerous files and folders with randomized names, UUIDs, timestamps, and unique information embedded in each file.

## 📋 Project Overview

This repository contains scripts in Python, C++, and C that automate the creation of:
- **Thousands of Folders**: Each folder is given a unique identifier and stored in a specific directory.
- **Hundreds of Files per Folder**: Each file has a unique name, a timestamp, and metadata that includes author information, UUID, and a custom message.
- **Randomized Content and Metadata**: Each file includes author name, timestamps with high precision, a unique UUID, folder information, and occasionally, a random emoji.
- **Automated Git Commits**: After every folder or file is created, it is staged and committed to Git with a descriptive commit message, preserving the creation history in version control.

## 🛠 Script Summaries

### Python Script: `file_generator.py`

The Python script creates 1000 folders, each containing 100 files with unique timestamps and metadata. It stages and commits each file automatically, making this an entirely automated repository management tool.

- **Folder Structure**: Each folder name includes a sequential number and a randomly generated word.
- **File Content**:
  - **Timestamp**: Detailed timestamp down to microseconds.
  - **Date**: Readable format, e.g., `Monday, 7 November 2024`.
  - **UUID**: Unique identifier generated for each file.
  - **Git Integration**: Each folder and file is committed with a unique message.
- **Usage**:
  ```bash
  python file_generator.py
  ```

#### Example Python File Content
```
Timestamp: 2024-11-07_12-45-00-123456
Date: 2024-11-07
Created by: MD. Naiem Islam Nahid
Folder: 0001_A1b2C3d4
File: 0001_A1b2C3d4_2024-11-07_12-45-00-123456.txt
UUID: 123e4567-e89b-12d3-a456-426614174000
===========================================
```

### C++ Script: `folder_generator.cpp`

The C++ script uses the `filesystem` library to create directories and files in a similar structure, with random UUIDs, high-precision timestamps, and automated Git commits. It is parallelized to optimize the generation of thousands of files and folders efficiently.

- **Custom Functions**:
  - `generateRandomWord`: Creates a random alphanumeric string for naming.
  - `getCurrentTimestamp`: Gets a timestamp with nanosecond precision.
  - `generateUUID`: Generates a UUID-like string for each file.
  - **Git Commit**: Executes a commit after every folder and file creation using system calls.
- **Usage**:
  ```bash
  g++ -o folder_generator folder_generator.cpp -std=c++17
  ./folder_generator
  ```

#### Example C++ File Content
```
Timestamp: 2024-11-07_12-45-00-123456789
Date: 2024-11-07
Created by: MD. Naiem Islam Nahid
Folder: 0001_A1b2C3d4
File: 0001_A1b2C3d4_2024-11-07_12-45-00-123456789.txt
UUID: 123e4567-e89b-12d3-a456-426614174000
```

### C Script: `folder_generator.c`

The C script performs similar operations, creating folders and files with unique metadata. It uses standard C libraries for generating timestamps, UUIDs, and commits each file and folder creation using `system` calls.

- **Unique Features**:
  - Uses Windows system libraries for timestamp generation with milliseconds.
  - Each file’s name and metadata contain a unique UUID and timestamp.
  - **Git Commit**: Each file is committed individually.
- **Usage**:
  ```bash
  gcc folder_generator.c -o folder_generator
  ./folder_generator
  ```

#### Example C File Content
```
Timestamp: 2024-11-07_12-45-00-123
Date: 2024-11-07
Created by: MD. Naiem Islam Nahid
Folder: 0001_A1b2C3d4
File: 0001_A1b2C3d4_2024-11-07_12-45-00-123.txt
UUID: 123e4567-e89b-12d3-a456-426614174000
```

## 📂 Example Directory Structure

Each script generates a directory structure similar to the following:

```
generated_folders/
├── 0001_A1b2C3d4/
│   ├── 0001_A1b2C3d4_2024-11-07_12-45-00-123456.txt
│   ├── 0001_A1b2C3d4_2024-11-07_12-46-00-123457.txt
│   └── ...
├── 0002_X9y8Z7w6/
│   ├── 0002_X9y8Z7w6_2024-11-07_12-47-00-123458.txt
│   ├── 0002_X9y8Z7w6_2024-11-07_12-48-00-123459.txt
│   └── ...
```

## 💻 Requirements

- **Python**: Python 3.6+ for running the Python script.
- **C++**: C++17 or higher, with a compiler supporting the `filesystem` library.
- **C**: Standard C library and compiler.
- **Git**: Initialized in the repository to handle commits for all scripts.

## 🛠️ Running Each Script

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/random-file-generator.git
   cd random-file-generator
   ```

2. Run the Python, C++, or C script as needed (see usage examples above).

3. **Explore the Files**: Browse the generated folders and files, and view the Git history to see auto-generated commit messages.

## 📢 Acknowledgments

Special thanks to the inspiration from programming and automation! This project is a creative exercise in file generation, metadata manipulation, Git automation, and cross-language scripting.

Happy coding! 🎉

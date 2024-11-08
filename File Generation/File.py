# main.py
import os
import time
import uuid
import random
import string
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import subprocess
from tqdm import tqdm
import importlib.util
from content_generators import (
    QuoteGenerator, 
    JokeGenerator, 
    FactGenerator, 
    AsciiArtGenerator
)

class WordListManager:
    """Manages word lists with efficient caching"""
    
    def __init__(self, word_lists_dir: str):
        self.word_lists = {
            'primary': self._load_word_list(os.path.join(word_lists_dir, 'primary.txt')),
            'secondary': self._load_word_list(os.path.join(word_lists_dir, 'secondary.txt')),
            'technical': self._load_word_list(os.path.join(word_lists_dir, 'technical.txt'))
        }
        
        # Create word caches
        self.cached_combinations = {
            key: self._generate_combinations(words, 100)
            for key, words in self.word_lists.items()
        }

    def _load_word_list(self, file_path: str) -> List[str]:
        """Load and validate word list"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return ["default"]

    def _generate_combinations(self, words: List[str], count: int) -> List[str]:
        """Pre-generate word combinations"""
        return [
            f"{random.choice(words)}_{random.choice(string.ascii_letters)}{random.randint(100, 999)}"
            for _ in range(count)
        ]

    def get_random_word(self, category: str) -> str:
        """Get a random pre-generated word combination"""
        return random.choice(self.cached_combinations.get(category, self.cached_combinations['primary']))

class TemplateManager:
    """Manages templates with caching"""
    
    def __init__(self, template_path: str):
        self.templates = self._load_templates(template_path)
        self.template_cache = {}
        
    def _load_templates(self, path: str) -> List[str]:
        """Load templates from the templates.py file"""
        try:
            spec = importlib.util.spec_from_file_location("templates", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            content_templates = getattr(module, 'ContentTemplates', None)
            if content_templates:
                return content_templates().templates
        except Exception as e:
            print(f"Error loading templates: {e}")
        return []

    def get_random_template(self) -> str:
        """Get a random template with caching"""
        return random.choice(self.templates)

class ContentCache:
    """Caches generated content for reuse"""
    
    def __init__(self):
        self.quote_gen = QuoteGenerator()
        self.joke_gen = JokeGenerator()
        self.fact_gen = FactGenerator()
        self.art_gen = AsciiArtGenerator()
        
        # Initialize caches
        self.quotes = self.quote_gen.generate_batch(100)
        self.jokes = self.joke_gen.generate_batch(100)
        self.facts = self.fact_gen.generate_batch(100)
        self.arts = self.art_gen.generate_batch(50)
        
        self.lock = threading.Lock()
        
    def get_content(self) -> Dict[str, str]:
        """Get a random set of content"""
        with self.lock:
            return {
                'quote': random.choice(self.quotes),
                'joke': random.choice(self.jokes),
                'fact': random.choice(self.facts),
                'art': random.choice(self.arts)
            }

    def refresh_caches(self):
        """Refresh all content caches"""
        with self.lock:
            self.quotes = self.quote_gen.generate_batch(100)
            self.jokes = self.joke_gen.generate_batch(100)
            self.facts = self.fact_gen.generate_batch(100)
            self.arts = self.art_gen.generate_batch(50)

class GitManager:
    """Manages git operations with batch commits"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.commit_queue = []
        self.lock = threading.Lock()
        
    def queue_commit(self, message: str, paths: List[str]):
        """Queue a git commit"""
        with self.lock:
            self.commit_queue.append((message, paths))
            if len(self.commit_queue) >= 50:
                self.process_commits()
                
    def process_commits(self):
        """Process queued commits"""
        with self.lock:
            if not self.commit_queue:
                return
                
            try:
                subprocess.run(['git', 'add', '.'], 
                             cwd=self.repo_path, stdout=subprocess.DEVNULL)
                
                for message, _ in self.commit_queue:
                    subprocess.run(
                        ['git', 'commit', '-m', message, '--quiet'],
                        cwd=self.repo_path, stdout=subprocess.DEVNULL
                    )
                    
                self.commit_queue.clear()
            except Exception as e:
                print(f"Git error: {e}")

class FastFileGenerator:
    """Main file generation orchestrator"""
    
    def __init__(self, base_dir: str = "generated_folders"):
        self.base_dir = base_dir
        self.template_manager = TemplateManager("templates/templates.py")
        self.word_manager = WordListManager("word_lists")
        self.content_cache = ContentCache()
        self.git_manager = GitManager(base_dir)
        
        # Create directories
        os.makedirs(base_dir, exist_ok=True)
        if not os.path.exists(os.path.join(base_dir, '.git')):
            subprocess.run(['git', 'init'], cwd=base_dir, 
                         stdout=subprocess.DEVNULL)
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def generate_folder_name(self, serial: int) -> str:
        """Generate unique folder name"""
        primary = self.word_manager.get_random_word('primary')
        secondary = self.word_manager.get_random_word('secondary')
        random_num = ''.join(random.choices(string.digits, k=10))
        return f"{serial:04d}_{primary}_{secondary}_{random_num}"

    def create_readme(self, folder_path: str, folder_name: str) -> str:
        """Create initial README.md"""
        content = f"""# Folder: {folder_name}

## Information
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Generator: FastFileGenerator v2.0
- Author: MD. Naiem Islam Nahid

## Content Statistics
- Files Planned: 1000
- Status: In Progress

## Template Usage
Will be updated upon completion...

## Files
"""
        readme_path = os.path.join(folder_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return readme_path

    def update_readme(self, folder_path: str, stats: Dict[str, Any]):
        """Update README with completion information"""
        readme_path = os.path.join(folder_path, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add completion statistics
        completion_stats = f"""
## Completion Statistics
- Total Files: {stats['total_files']}
- Time Taken: {stats['duration']:.2f} seconds
- Average Time Per File: {stats['avg_time']:.4f} seconds
- Templates Used: {stats['templates_used']}
- Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Generated Files
"""
        for file_name in sorted(stats['files']):
            completion_stats += f"- {file_name}\n"

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content + completion_stats)

    def create_file_content(self, folder_name: str, file_num: int) -> str:
        """Generate file content using templates and cached content"""
        template = self.template_manager.get_random_template()
        content = self.content_cache.get_content()
        
        return template.format(
            file_num=file_num,
            uuid=str(uuid.uuid4()),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            magic_number=random.randint(1000, 9999),
            folder_name=folder_name,
            **content
        )

    def process_file_batch(self, folder_path: str, folder_name: str, 
                          start_idx: int, batch_size: int) -> List[str]:
        """Process a batch of files"""
        created_files = []
        
        for i in range(start_idx, min(start_idx + batch_size, 1000)):
            # Generate file name
            technical = self.word_manager.get_random_word('technical')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            random_text = ''.join(random.choices(string.ascii_letters, k=10))
            random_num = ''.join(random.choices(string.digits, k=10))
            
            file_name = f"{i:04d}_{folder_name}_{technical}_{random_text}_{random_num}_{timestamp}.txt"
            file_path = os.path.join(folder_path, file_name)
            
            # Create file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.create_file_content(folder_name, i))
                created_files.append(file_name)
            except Exception as e:
                print(f"Error creating file {file_name}: {e}")
                
        return created_files

    def process_folder(self, folder_num: int) -> tuple:
        """Process complete folder creation"""
        start_time = time.time()
        
        # Create folder
        folder_name = self.generate_folder_name(folder_num)
        folder_path = os.path.join(self.base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Create README
        readme_path = self.create_readme(folder_path, folder_name)
        self.git_manager.queue_commit(
            f"Created folder #{folder_num:04d}: {folder_name}",
            [folder_path]
        )
        
        # Process files in batches
        all_files = []
        templates_used = set()
        batch_size = 50
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for start_idx in range(0, 1000, batch_size):
                future = executor.submit(
                    self.process_file_batch,
                    folder_path, folder_name, start_idx, batch_size
                )
                futures.append(future)
                
            for future in futures:
                batch_files = future.result()
                all_files.extend(batch_files)
                
                # Commit batch
                self.git_manager.queue_commit(
                    f"Added files batch in {folder_name}",
                    [os.path.join(folder_path, f) for f in batch_files]
                )
        
        # Update README
        duration = time.time() - start_time
        stats = {
            'total_files': len(all_files),
            'duration': duration,
            'avg_time': duration / len(all_files),
            'templates_used': len(templates_used),
            'files': all_files
        }
        self.update_readme(folder_path, stats)
        
        # Final commit
        self.git_manager.queue_commit(
            f"Completed folder {folder_name} with {len(all_files)} files",
            [readme_path]
        )
        
        return folder_name, duration

    def generate(self, num_folders: int):
        """Generate all folders and files"""
        print(f"Starting generation of {num_folders} folders...")
        total_start = time.time()
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for folder_num in range(1, num_folders + 1):
                future = executor.submit(self.process_folder, folder_num)
                futures.append(future)
            
            with tqdm(total=num_folders, desc="Creating folders") as pbar:
                for future in futures:
                    folder_name, duration = future.result()
                    pbar.update(1)
                    pbar.set_description(
                        f"Created {folder_name} ({duration:.2f}s)"
                    )
        
        total_time = time.time() - total_start
        print(f"\nGeneration complete!")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per folder: {total_time/num_folders:.2f} seconds")

if __name__ == "__main__":
    try:
        generator = FastFileGenerator()
        generator.generate(num_folders=10)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"An error occurred: {e}")
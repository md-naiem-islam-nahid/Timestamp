import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import shutil
from datetime import datetime
import json

class FileHandler:
    """
    Manages file and folder operations with efficient I/O and parallel processing.
    Implements buffered writing and batch operations for maximum performance.
    """
    
    def __init__(self, base_dir: str = "output", 
                 batch_size: int = 100,
                 max_workers: int = 4,
                 buffer_size: int = 8192):
        """
        Initialize FileHandler with configuration.
        
        Args:
            base_dir: Base directory for file generation
            batch_size: Number of files per batch
            max_workers: Maximum number of worker threads
            buffer_size: File write buffer size
        """
        from core.content_generator import ContentGenerator
        
        # Initialize paths
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.buffer_size = buffer_size
        
        # Initialize components
        self.content_generator = ContentGenerator()
        
        # Thread safety
        self._lock = threading.RLock()
        self._write_queue = Queue(maxsize=1000)
        self._active = True
        
        # Statistics
        self.stats = {
            'folders_created': 0,
            'files_created': 0,
            'total_bytes_written': 0,
            'total_time': 0.0
        }
        self._stats_lock = threading.Lock()
        
        # Start background writer
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._start_background_writer()
        
    def _start_background_writer(self):
        """Start background thread for writing files"""
        def write_files_background():
            while self._active or not self._write_queue.empty():
                try:
                    if not self._write_queue.empty():
                        file_path, content = self._write_queue.get_nowait()
                        self._write_file(file_path, content)
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Background writer error: {e}")
                    time.sleep(1)
                    
        self._executor.submit(write_files_background)
        
    def _write_file(self, file_path: Path, content: str):
        """Write content to file with buffering"""
        try:
            with open(file_path, 'w', encoding='utf-8', buffering=self.buffer_size) as f:
                f.write(content)
                
            with self._stats_lock:
                self.stats['total_bytes_written'] += len(content.encode('utf-8'))
                self.stats['files_created'] += 1
                
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            
    def _create_readme(self, folder_path: Path, folder_name: str) -> Path:
        """Create initial README.md for folder"""
        readme_path = folder_path / "README.md"
        content = f"""# Folder: {folder_name}

## Generation Information
- Created: {datetime.now().isoformat()}
- Generator Version: 2.0
- Target Files: 1000
- Batch Size: {self.batch_size}
- Status: In Progress

## Files
Will be updated upon completion...
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return readme_path
        
    def _update_readme(self, readme_path: Path, stats: Dict):
        """Update README with completion information"""
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        completion_info = f"""
## Completion Statistics
- Total Files: {stats['files_created']}
- Total Size: {stats['total_bytes_written'] / 1024 / 1024:.2f} MB
- Time Taken: {stats['total_time']:.2f} seconds
- Files/Second: {stats['files_created'] / stats['total_time']:.2f}
- Completed: {datetime.now().isoformat()}

## Generated Files
"""
        for file_name in sorted(stats['file_list']):
            completion_info += f"- {file_name}\n"
            
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content + completion_info)
            
    def create_folder(self, folder_num: int, 
                     progress_callback: Optional[Callable] = None) -> Dict:
        """
        Create a folder with generated files.
        
        Args:
            folder_num: Folder number in sequence
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict: Statistics about the created folder
        """
        start_time = time.time()
        
        # Generate folder name and create directory
        folder_name = self.content_generator.generate_folder_name(folder_num)
        folder_path = self.base_dir / folder_name
        folder_path.mkdir(exist_ok=True)
        
        # Create README
        readme_path = self._create_readme(folder_path, folder_name)
        
        # Initialize folder statistics
        folder_stats = {
            'folder_name': folder_name,
            'files_created': 0,
            'total_bytes_written': 0,
            'file_list': []
        }
        
        # Process files in batches
        for batch_start in range(0, 1000, self.batch_size):
            batch_end = min(batch_start + self.batch_size, 1000)
            batch = self.content_generator.generate_batch(
                folder_name, 
                batch_start, 
                batch_end - batch_start
            )
            
            # Queue files for writing
            for file_name, content in batch:
                file_path = folder_path / file_name
                self._write_queue.put((file_path, content))
                folder_stats['file_list'].append(file_name)
                
            if progress_callback:
                progress_callback(folder_num, batch_end, 1000)
                
        # Wait for all files to be written
        while not self._write_queue.empty():
            time.sleep(0.1)
            
        # Update statistics
        end_time = time.time()
        folder_stats['total_time'] = end_time - start_time
        
        with self._stats_lock:
            self.stats['folders_created'] += 1
            folder_stats.update({
                'files_created': len(folder_stats['file_list']),
                'total_bytes_written': sum(
                    os.path.getsize(folder_path / f) 
                    for f in folder_stats['file_list']
                )
            })
            
        # Update README with final statistics
        self._update_readme(readme_path, folder_stats)
        
        return folder_stats
        
    def create_folders(self, num_folders: int, 
                      progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Create multiple folders in parallel.
        
        Args:
            num_folders: Number of folders to create
            progress_callback: Optional callback for progress updates
            
        Returns:
            List[Dict]: Statistics for each created folder
        """
        stats = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for folder_num in range(1, num_folders + 1):
                futures.append(
                    executor.submit(
                        self.create_folder,
                        folder_num,
                        progress_callback
                    )
                )
                
            for future in futures:
                try:
                    folder_stats = future.result()
                    stats.append(folder_stats)
                except Exception as e:
                    print(f"Error creating folder: {e}")
                    
        return stats
        
    def get_statistics(self) -> Dict:
        """Get handler statistics"""
        with self._stats_lock:
            return {
                **self.stats,
                'content_stats': self.content_generator.get_statistics(),
                'queue_size': self._write_queue.qsize(),
            }
            
    def cleanup(self, remove_files: bool = False):
        """
        Cleanup resources and optionally remove generated files.
        
        Args:
            remove_files: If True, removes all generated files
        """
        self._active = False
        self._executor.shutdown(wait=True)
        self.content_generator.cleanup()
        
        if remove_files and self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            
    def save_statistics(self, file_path: str):
        """
        Save generation statistics to file.
        
        Args:
            file_path: Path to save statistics
        """
        stats = self.get_statistics()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

# Example usage and testing
if __name__ == "__main__":
    def progress_update(folder_num: int, files_done: int, total_files: int):
        print(f"\rFolder {folder_num}: {files_done}/{total_files} files", end="")
        
    # Initialize handler
    handler = FileHandler(base_dir="test_output", batch_size=50)
    
    try:
        # Create test folders
        print("Creating test folders...")
        stats = handler.create_folders(2, progress_callback=progress_update)
        
        print("\n\nGeneration Statistics:")
        for folder_stat in stats:
            print(f"\nFolder: {folder_stat['folder_name']}")
            print(f"Files: {folder_stat['files_created']}")
            print(f"Size: {folder_stat['total_bytes_written'] / 1024 / 1024:.2f} MB")
            print(f"Time: {folder_stat['total_time']:.2f} seconds")
            
        # Save statistics
        handler.save_statistics("generation_stats.json")
        
    finally:
        # Cleanup
        handler.cleanup()
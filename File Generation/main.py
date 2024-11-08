import os
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json
import signal
from tqdm import tqdm

from core.file_handler import FileHandler
from core.git_manager import GitManager

class FastFileGenerator:
    """
    Main coordinator class for fast file generation.
    Orchestrates all components and provides user interface.
    """
    
    def __init__(self, 
                 output_dir: str = "output",
                 batch_size: int = 100,
                 max_workers: int = 4,
                 enable_git: bool = True,
                 log_file: Optional[str] = "generator.log"):
        """
        Initialize the generator with configuration.
        
        Args:
            output_dir: Directory for generated files
            batch_size: Files per batch
            max_workers: Maximum worker threads
            enable_git: Enable git integration
            log_file: Log file path (None for no logging)
        """
        self.start_time = datetime.now()
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Set up logging
        if log_file:
            logging.basicConfig(
                filename=log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        
        # Initialize components
        self.file_handler = FileHandler(
            base_dir=output_dir,
            batch_size=batch_size,
            max_workers=max_workers
        )
        
        self.git_manager = GitManager(
            repo_path=output_dir,
            batch_size=batch_size,
            auto_commit=enable_git
        ) if enable_git else None
        
        # Statistics and state
        self.stats = {
            'start_time': self.start_time.isoformat(),
            'folders_completed': 0,
            'total_files': 0,
            'total_size': 0,
            'errors': 0
        }
        
        # Progress tracking
        self.progress_bar = None
        self._running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
    def _handle_interrupt(self, signum, frame):
        """Handle interruption signals gracefully"""
        print("\nReceived interrupt signal. Cleaning up...")
        self._running = False
        self.cleanup()
        
    def _update_progress(self, folder_num: int, files_done: int, 
                        total_files: int):
        """Update progress bar and git integration"""
        if self.progress_bar is not None:
            self.progress_bar.update(1)
            self.progress_bar.set_description(
                f"Folder {folder_num}: {files_done}/{total_files} files"
            )
            
    def _process_folder(self, folder_num: int) -> Dict:
        """
        Process a single folder creation.
        
        Args:
            folder_num: Folder number in sequence
            
        Returns:
            Dict: Folder statistics
        """
        try:
            # Create folder and files
            folder_stats = self.file_handler.create_folder(
                folder_num,
                self._update_progress
            )
            
            # Git integration
            if self.git_manager and self._running:
                folder_path = self.output_dir / folder_stats['folder_name']
                
                # Commit folder creation and completion
                self.git_manager.commit_folder_creation(
                    folder_path,
                    folder_stats['folder_name']
                )
                self.git_manager.commit_folder_completion(
                    folder_path,
                    folder_stats
                )
            
            # Update statistics
            with self.file_handler._stats_lock:
                self.stats['folders_completed'] += 1
                self.stats['total_files'] += folder_stats['files_created']
                self.stats['total_size'] += folder_stats['total_bytes_written']
                
            return folder_stats
            
        except Exception as e:
            logging.error(f"Error processing folder {folder_num}: {e}")
            self.stats['errors'] += 1
            raise
            
    def generate(self, num_folders: int):
        """
        Generate specified number of folders with files.
        
        Args:
            num_folders: Number of folders to generate
        """
        print(f"\nStarting generation of {num_folders} folders...")
        print(f"Output directory: {self.output_dir}")
        print(f"Batch size: {self.batch_size}")
        print(f"Worker threads: {self.max_workers}")
        print(f"Git integration: {'Enabled' if self.git_manager else 'Disabled'}")
        print("\nPress Ctrl+C to stop gracefully\n")
        
        try:
            total_files = num_folders * 1000
            self.progress_bar = tqdm(
                total=total_files,
                unit='files',
                unit_scale=True
            )
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for folder_num in range(1, num_folders + 1):
                    if not self._running:
                        break
                    futures.append(
                        executor.submit(self._process_folder, folder_num)
                    )
                
                # Process results
                folder_stats = []
                for future in futures:
                    try:
                        if not self._running:
                            break
                        stats = future.result()
                        folder_stats.append(stats)
                    except Exception as e:
                        logging.error(f"Folder processing failed: {e}")
                        
            return folder_stats
            
        finally:
            if self.progress_bar:
                self.progress_bar.close()
                
    def save_statistics(self):
        """Save generation statistics to file"""
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['duration'] = (
            datetime.fromisoformat(self.stats['end_time']) -
            datetime.fromisoformat(self.stats['start_time'])
        ).total_seconds()
        
        # Add component statistics
        self.stats.update({
            'file_handler_stats': self.file_handler.get_statistics(),
            'git_stats': self.git_manager.get_statistics() if self.git_manager else None
        })
        
        # Calculate performance metrics
        if self.stats['duration'] > 0:
            self.stats.update({
                'files_per_second': self.stats['total_files'] / self.stats['duration'],
                'mb_per_second': (self.stats['total_size'] / 1024 / 1024) / 
                                self.stats['duration']
            })
        
        # Save to file
        stats_file = self.output_dir / "generation_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
            
        return stats_file
        
    def cleanup(self):
        """Cleanup resources and save statistics"""
        try:
            if self.git_manager:
                self.git_manager.cleanup()
            self.file_handler.cleanup()
            stats_file = self.save_statistics()
            
            print("\nGeneration Statistics:")
            print(f"Folders completed: {self.stats['folders_completed']}")
            print(f"Total files: {self.stats['total_files']}")
            print(f"Total size: {self.stats['total_size'] / 1024 / 1024:.2f} MB")
            print(f"Duration: {self.stats['duration']:.2f} seconds")
            print(f"Files per second: {self.stats.get('files_per_second', 0):.2f}")
            print(f"MB per second: {self.stats.get('mb_per_second', 0):.2f}")
            print(f"Errors encountered: {self.stats['errors']}")
            print(f"\nDetailed statistics saved to: {stats_file}")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fast File Generator - Generates multiple folders with files"
    )
    
    parser.add_argument(
        '-n', '--num-folders',
        type=int,
        default=1000,
        help='Number of folders to generate (default: 10)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '-b', '--batch-size',
        type=int,
        default=50,
        help='Files per batch (default: 100)'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        help='Maximum worker threads (default: 4)'
    )
    
    parser.add_argument(
        '--no-git',
        action='store_true',
        help='Disable git integration'
    )
    
    parser.add_argument(
        '--no-log',
        action='store_true',
        help='Disable logging to file'
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    generator = FastFileGenerator(
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        max_workers=args.workers,
        enable_git=not args.no_git,
        log_file=None if args.no_log else "generator.log"
    )
    
    try:
        generator.generate(args.num_folders)
    finally:
        generator.cleanup()

if __name__ == "__main__":
    main()
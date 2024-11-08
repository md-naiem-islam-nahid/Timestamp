import subprocess
import threading
from typing import List, Dict, Optional
from pathlib import Path
from queue import Queue
import time
from datetime import datetime
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor

@dataclass
class CommitInfo:
    """Information for a git commit"""
    message: str
    paths: List[str]
    timestamp: str
    commit_id: Optional[str] = None

class GitManager:
    """
    Manages git operations with batching and async processing.
    Optimizes git operations to minimize impact on file generation performance.
    """
    
    def __init__(self, repo_path: str, 
                 batch_size: int = 50,
                 auto_commit: bool = True):
        """
        Initialize GitManager with repository configuration.
        
        Args:
            repo_path: Path to git repository
            batch_size: Number of files per commit batch
            auto_commit: Whether to automatically commit changes
        """
        self.repo_path = Path(repo_path)
        self.batch_size = batch_size
        self.auto_commit = auto_commit
        
        # Thread safety
        self._lock = threading.RLock()
        self._commit_queue = Queue()
        self._active = True
        
        # Statistics
        self.stats = {
            'commits': 0,
            'files_committed': 0,
            'batch_commits': 0,
            'commit_times': []
        }
        self._stats_lock = threading.Lock()
        
        # Initialize repository if needed
        self._init_repository()
        
        # Start background commit processor
        self._executor = ThreadPoolExecutor(max_workers=1)
        if auto_commit:
            self._start_commit_processor()
            
    def _init_repository(self):
        """Initialize git repository if not exists"""
        try:
            if not (self.repo_path / '.git').exists():
                self._run_git_command(['init'])
                self._configure_git()
        except Exception as e:
            logging.error(f"Failed to initialize repository: {e}")
            raise
            
    def _configure_git(self):
        """Configure git settings"""
        configs = [
            ['config', 'user.name', 'FastFileGenerator'],
            ['config', 'user.email', 'generator@example.com'],
            ['config', 'core.autocrlf', 'false'],
            ['config', 'core.compression', '0'],  # Faster commits
            ['config', 'core.bigFileThreshold', '1m']  # Better handling of large files
        ]
        
        for config in configs:
            self._run_git_command(config)
            
    def _run_git_command(self, command: List[str], 
                        check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command safely.
        
        Args:
            command: Git command and arguments
            check: Whether to check for command success
            
        Returns:
            subprocess.CompletedProcess: Command result
        """
        try:
            return subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Git command failed: {e.cmd}\nOutput: {e.output}")
            if check:
                raise
            return e
            
    def _start_commit_processor(self):
        """Start background thread for processing commits"""
        def process_commits():
            batch: List[CommitInfo] = []
            last_commit_time = time.time()
            
            while self._active or not self._commit_queue.empty():
                try:
                    # Process available commits
                    while len(batch) < self.batch_size:
                        try:
                            commit = self._commit_queue.get_nowait()
                            batch.append(commit)
                        except Queue.Empty:
                            break
                            
                    # Commit batch if it's full or enough time has passed
                    current_time = time.time()
                    if (batch and 
                        (len(batch) >= self.batch_size or 
                         current_time - last_commit_time >= 5)):
                        self._process_commit_batch(batch)
                        batch = []
                        last_commit_time = current_time
                    else:
                        time.sleep(0.1)
                        
                except Exception as e:
                    logging.error(f"Error processing commits: {e}")
                    time.sleep(1)
                    
        self._executor.submit(process_commits)
        
    def _process_commit_batch(self, batch: List[CommitInfo]):
        """
        Process a batch of commits.
        
        Args:
            batch: List of CommitInfo objects to process
        """
        if not batch:
            return
            
        try:
            start_time = time.time()
            
            # Add all files to staging
            all_paths = set()
            for commit in batch:
                all_paths.update(commit.paths)
                
            if all_paths:
                self._run_git_command(['add'] + list(all_paths))
            
            # Create commit
            message = f"Batch commit: {len(batch)} operations\n\n"
            message += "\n".join(f"- {commit.message}" for commit in batch)
            
            result = self._run_git_command(
                ['commit', '-m', message],
                check=False
            )
            
            commit_hash = None
            if result.returncode == 0:
                # Extract commit hash
                commit_hash = self._run_git_command(
                    ['rev-parse', 'HEAD']
                ).stdout.strip()
                
                # Update commit info
                for commit in batch:
                    commit.commit_id = commit_hash
                
                # Update statistics
                with self._stats_lock:
                    self.stats['commits'] += 1
                    self.stats['batch_commits'] += 1
                    self.stats['files_committed'] += len(all_paths)
                    self.stats['commit_times'].append(time.time() - start_time)
                    
        except Exception as e:
            logging.error(f"Failed to process commit batch: {e}")
            
    def queue_commit(self, message: str, paths: List[str]):
        """
        Queue a commit for processing.
        
        Args:
            message: Commit message
            paths: List of paths to commit
        """
        commit_info = CommitInfo(
            message=message,
            paths=[str(p) for p in paths],
            timestamp=datetime.now().isoformat()
        )
        
        self._commit_queue.put(commit_info)
        
    def commit_folder_creation(self, folder_path: Path, folder_name: str):
        """
        Commit folder creation.
        
        Args:
            folder_path: Path to created folder
            folder_name: Name of created folder
        """
        message = f"Created folder: {folder_name}"
        self.queue_commit(message, [str(folder_path)])
        
    def commit_file_batch(self, folder_path: Path, files: List[str], 
                         batch_num: int):
        """
        Commit a batch of files.
        
        Args:
            folder_path: Parent folder path
            files: List of file names
            batch_num: Batch number
        """
        message = f"Added file batch {batch_num} to {folder_path.name}"
        paths = [str(folder_path / f) for f in files]
        self.queue_commit(message, paths)
        
    def commit_folder_completion(self, folder_path: Path, 
                               stats: Dict):
        """
        Commit folder completion.
        
        Args:
            folder_path: Folder path
            stats: Folder statistics
        """
        message = (f"Completed folder {folder_path.name}\n"
                  f"Files: {stats['files_created']}\n"
                  f"Size: {stats['total_bytes_written'] / 1024 / 1024:.2f} MB\n"
                  f"Time: {stats['total_time']:.2f} seconds")
        
        self.queue_commit(message, [str(folder_path)])
        
    def get_statistics(self) -> Dict:
        """Get git operation statistics"""
        with self._stats_lock:
            avg_commit_time = (sum(self.stats['commit_times']) / 
                             len(self.stats['commit_times'])
                             if self.stats['commit_times'] else 0)
            
            return {
                'total_commits': self.stats['commits'],
                'batch_commits': self.stats['batch_commits'],
                'files_committed': self.stats['files_committed'],
                'average_commit_time': avg_commit_time,
                'queue_size': self._commit_queue.qsize()
            }
            
    def cleanup(self, wait: bool = True):
        """
        Cleanup resources.
        
        Args:
            wait: Whether to wait for queued commits
        """
        self._active = False
        if wait:
            while not self._commit_queue.empty():
                time.sleep(0.1)
        self._executor.shutdown(wait=wait)

# Example usage and testing
if __name__ == "__main__":
    def create_test_files(path: Path, count: int = 5):
        """Create test files for demonstration"""
        files = []
        for i in range(count):
            file_path = path / f"test_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}")
            files.append(file_path.name)
        return files
    
    # Initialize manager
    test_path = Path("test_repo")
    test_path.mkdir(exist_ok=True)
    git_manager = GitManager(str(test_path))
    
    try:
        # Test folder creation
        folder_path = test_path / "test_folder"
        folder_path.mkdir(exist_ok=True)
        git_manager.commit_folder_creation(folder_path, "test_folder")
        
        # Test file batch commits
        files = create_test_files(folder_path)
        git_manager.commit_file_batch(folder_path, files, 1)
        
        # Test folder completion
        stats = {
            'files_created': len(files),
            'total_bytes_written': 1000,
            'total_time': 1.5
        }
        git_manager.commit_folder_completion(folder_path, stats)
        
        # Wait for commits to process
        time.sleep(2)
        
        # Print statistics
        print("\nGit Manager Statistics:")
        stats = git_manager.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
            
    finally:
        # Cleanup
        git_manager.cleanup()
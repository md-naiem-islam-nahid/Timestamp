import os
import time
import random
import string
import threading
from typing import Generator, Any, Callable, TypeVar
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
import hashlib
import logging
from functools import wraps

T = TypeVar('T')

class ThreadSafeGenerator:
    """Thread-safe random string generator"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._random = random.Random()
        
    def random_string(self, length: int, chars: str = string.ascii_letters) -> str:
        """Generate random string thread-safely"""
        with self._lock:
            return ''.join(self._random.choices(chars, k=length))
            
    def random_digits(self, length: int) -> str:
        """Generate random digits thread-safely"""
        return self.random_string(length, string.digits)

# Initialize global generator
safe_generator = ThreadSafeGenerator()

def generate_unique_id(prefix: str = "") -> str:
    """Generate unique identifier"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    random_suffix = safe_generator.random_string(6)
    return f"{prefix}_{timestamp}_{random_suffix}" if prefix else f"{timestamp}_{random_suffix}"

@contextmanager
def timing_context(operation: str) -> Generator[None, None, None]:
    """Context manager for timing operations"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logging.info(f"{operation} took {duration:.2f} seconds")

def retry_operation(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return path"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def clean_filename(name: str) -> str:
    """Clean and validate filename"""
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned = ''.join(c for c in name if c in valid_chars)
    return cleaned[:255]  # Max filename length

@contextmanager
def file_lock(lock_file: Path):
    """File-based lock for cross-process synchronization"""
    while True:
        try:
            with open(lock_file, 'x'):  # Atomic file creation
                try:
                    yield
                finally:
                    lock_file.unlink()
            break
        except FileExistsError:
            time.sleep(0.1)

def batch_generator(items: list, batch_size: int) -> Generator[list, None, None]:
    """Generate batches from list"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = {}
        self._lock = threading.Lock()
        
    def record_operation(self, operation: str, duration: float):
        """Record operation duration"""
        with self._lock:
            if operation not in self.operation_times:
                self.operation_times[operation] = []
            self.operation_times[operation].append(duration)
            
    def get_statistics(self) -> dict:
        """Get performance statistics"""
        with self._lock:
            stats = {}
            for operation, times in self.operation_times.items():
                stats[operation] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'average_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
            return stats

class ResourceTracker:
    """Track system resource usage"""
    
    def __init__(self):
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory
        self._lock = threading.Lock()
        
    def _get_memory_usage(self) -> int:
        """Get current memory usage"""
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
        
    def update(self):
        """Update resource tracking"""
        with self._lock:
            current_memory = self._get_memory_usage()
            self.peak_memory = max(self.peak_memory, current_memory)
            
    def get_statistics(self) -> dict:
        """Get resource usage statistics"""
        current_memory = self._get_memory_usage()
        return {
            'start_memory': self.start_memory,
            'current_memory': current_memory,
            'peak_memory': self.peak_memory,
            'memory_increase': current_memory - self.start_memory
        }

# Initialize global monitors
performance_monitor = PerformanceMonitor()
resource_tracker = ResourceTracker()

def monitor_performance(operation: str):
    """Decorator to monitor operation performance"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_operation(operation, duration)
                return result
            finally:
                resource_tracker.update()
        return wrapper
    return decorator

# Example usage
if __name__ == "__main__":
    # Test unique ID generation
    print(f"Unique ID: {generate_unique_id('test')}")
    
    # Test timing context
    with timing_context("test_operation"):
        time.sleep(1)
        
    # Test retry decorator
    @retry_operation(max_attempts=3)
    def test_function():
        raise ValueError("Test error")
        
    try:
        test_function()
    except ValueError:
        print("Retry failed as expected")
        
    # Test performance monitoring
    @monitor_performance("test_operation")
    def test_monitored_function():
        time.sleep(0.1)
        
    test_monitored_function()
    print("Performance stats:", performance_monitor.get_statistics())
    print("Resource stats:", resource_tracker.get_statistics())
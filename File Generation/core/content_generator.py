import threading
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from queue import Queue
import random
from concurrent.futures import ThreadPoolExecutor

@dataclass
class GenerationStats:
    """Statistics for content generation"""
    total_generated: int = 0
    cache_hits: int = 0
    generation_time: float = 0.0
    template_usage: Dict[int, int] = None
    
    def __post_init__(self):
        if self.template_usage is None:
            self.template_usage = {}

class ContentGenerator:
    """
    Generates content for files using WordManager and TemplateManager.
    Implements efficient caching and parallel content generation.
    """
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialize ContentGenerator with caching and threading support.
        
        Args:
            cache_size: Maximum number of cached contents
        """
        # Import managers
        from core.word_manager import WordManager
        from core.template_manager import TemplateManager
        
        # Initialize managers
        self.word_manager = WordManager()
        self.template_manager = TemplateManager()
        
        # Threading and synchronization
        self._lock = threading.RLock()
        self._stats_lock = threading.Lock()
        self._generation_queue = Queue(maxsize=cache_size)
        self._cache: Dict[str, str] = {}
        self._cache_size = cache_size
        
        # Statistics tracking
        self.stats = GenerationStats()
        
        # Initialize worker pool for parallel generation
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Start background content generator
        self._start_background_generator()
        
    def _start_background_generator(self):
        """Start background thread for content pre-generation"""
        def generate_content_background():
            while True:
                try:
                    if self._generation_queue.qsize() < self._cache_size // 2:
                        content = self._generate_base_content()
                        if not self._generation_queue.full():
                            self._generation_queue.put(content)
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Background generation error: {e}")
                    time.sleep(1)
                    
        self._executor.submit(generate_content_background)
        
    def _generate_base_content(self) -> Dict[str, str]:
        """Generate base content components"""
        return {
            'art': 'ASCII ART PLACEHOLDER',  # Replace with actual art generation
            'quote': 'Sample quote',         # Replace with actual quote generation
            'fact': 'Interesting fact',      # Replace with actual fact generation
            'joke': 'Funny joke'             # Replace with actual joke generation
        }
        
    def _get_cached_content(self, key: str) -> Optional[str]:
        """Get content from cache if available"""
        with self._lock:
            content = self._cache.get(key)
            if content:
                with self._stats_lock:
                    self.stats.cache_hits += 1
            return content
            
    def _cache_content(self, key: str, content: str):
        """Cache generated content"""
        with self._lock:
            if len(self._cache) >= self._cache_size:
                # Remove random entries if cache is full
                remove_keys = random.sample(list(self._cache.keys()), 
                                         self._cache_size // 4)
                for k in remove_keys:
                    self._cache.pop(k, None)
            self._cache[key] = content
            
    def generate_folder_name(self, serial: int) -> str:
        """
        Generate a unique folder name.
        
        Args:
            serial: Folder serial number
            
        Returns:
            str: Generated folder name
        """
        primary_word = self.word_manager.get_word('primary')
        random_text = self.word_manager.get_random_text(8)
        random_digits = self.word_manager.get_random_digits(10)
        
        return f"{serial:04d}_{primary_word}_{random_text}_{random_digits}"
        
    def generate_file_name(self, folder_name: str, file_num: int) -> str:
        """
        Generate a unique file name.
        
        Args:
            folder_name: Parent folder name
            file_num: File serial number
            
        Returns:
            str: Generated file name
        """
        tech_word = self.word_manager.get_word('technical')
        random_text = self.word_manager.get_random_text(10)
        random_digits = self.word_manager.get_random_digits(10)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return (f"{file_num:04d}_{folder_name}_{tech_word}_"
                f"{random_text}_{random_digits}_{timestamp}.txt")
                
    def generate_file_content(self, folder_name: str, file_num: int, 
                            thread_id: Optional[int] = None) -> Tuple[str, str]:
        """
        Generate file name and content.
        
        Args:
            folder_name: Parent folder name
            file_num: File serial number
            thread_id: Optional thread identifier
            
        Returns:
            Tuple[str, str]: (file_name, file_content)
        """
        start_time = time.time()
        
        # Generate file name
        file_name = self.generate_file_name(folder_name, file_num)
        
        # Try to get cached content
        cache_key = f"{folder_name}:{file_num}"
        content = self._get_cached_content(cache_key)
        
        if not content:
            # Get pre-generated base content or generate new
            try:
                base_content = self._generation_queue.get_nowait()
            except Queue.Empty:
                base_content = self._generate_base_content()
            
            # Generate content using template
            content = self.template_manager.generate_file_content(
                folder_name=folder_name,
                file_num=file_num,
                thread_id=thread_id,
                **base_content
            )
            
            # Cache the content
            self._cache_content(cache_key, content)
        
        # Update statistics
        with self._stats_lock:
            self.stats.total_generated += 1
            self.stats.generation_time += time.time() - start_time
        
        return file_name, content
        
    def generate_batch(self, folder_name: str, start_num: int, 
                      count: int) -> list[Tuple[str, str]]:
        """
        Generate a batch of files in parallel.
        
        Args:
            folder_name: Parent folder name
            start_num: Starting file number
            count: Number of files to generate
            
        Returns:
            List[Tuple[str, str]]: List of (file_name, content) pairs
        """
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(start_num, start_num + count):
                futures.append(
                    executor.submit(
                        self.generate_file_content,
                        folder_name,
                        i,
                        hash(threading.current_thread())
                    )
                )
            
            return [future.result() for future in futures]
            
    def get_statistics(self) -> Dict[str, any]:
        """
        Get generation statistics.
        
        Returns:
            Dict with usage statistics
        """
        with self._stats_lock:
            avg_time = (self.stats.generation_time / self.stats.total_generated 
                       if self.stats.total_generated > 0 else 0)
            
            return {
                'total_generated': self.stats.total_generated,
                'cache_hits': self.stats.cache_hits,
                'average_generation_time': avg_time,
                'cache_size': len(self._cache),
                'queue_size': self._generation_queue.qsize(),
                'template_stats': self.template_manager.get_statistics(),
                'word_stats': self.word_manager.get_statistics()
            }
            
    def cleanup(self):
        """Cleanup and release resources"""
        self._executor.shutdown(wait=False)
        self._cache.clear()
        while not self._generation_queue.empty():
            try:
                self._generation_queue.get_nowait()
            except Queue.Empty:
                break

# Example usage and testing
if __name__ == "__main__":
    # Initialize generator
    generator = ContentGenerator()
    
    # Test folder name generation
    folder_name = generator.generate_folder_name(1)
    print(f"\nGenerated folder name: {folder_name}")
    
    # Test single file generation
    file_name, content = generator.generate_file_content(folder_name, 1)
    print(f"\nGenerated file name: {file_name}")
    print(f"Content length: {len(content)}")
    print(f"First 100 characters: {content[:100]}...")
    
    # Test batch generation
    print("\nGenerating batch of files...")
    start_time = time.time()
    batch = generator.generate_batch(folder_name, 1, 5)
    end_time = time.time()
    
    print(f"\nGenerated {len(batch)} files in {end_time - start_time:.4f} seconds")
    
    # Print statistics
    print("\nGenerator statistics:")
    stats = generator.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
        
    # Cleanup
    generator.cleanup()
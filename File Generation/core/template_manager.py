import random
import threading
from typing import Dict, List, Optional
from string import Template
from datetime import datetime
import uuid
from pathlib import Path
import time

class TemplateManager:
    """
    Manages templates with efficient caching and fast content generation.
    Handles template rotation, caching, and optimized string formatting.
    """
    
    def __init__(self):
        """Initialize TemplateManager with caching and threading support."""
        # Import templates only when needed
        # Change this line in core/template_manager.py
        from templates.templates import ContentTemplates  # Update the import path
        
        # Thread safety
        self._lock = threading.Lock()
        self._template_lock = threading.RLock()
        
        # Template storage
        self._raw_templates: List[str] = ContentTemplates().templates
        self._compiled_templates: Dict[int, Template] = {}
        self._template_usage: Dict[int, int] = {}
        
        # Performance optimization
        self._template_cache: Dict[str, str] = {}
        self._cache_size = 1000
        self._last_template_idx: Dict[int, int] = {}  # Thread-specific last used template
        
        # Initialize caches
        self._compile_templates()
        self._init_common_values()
        
    def _compile_templates(self) -> None:
        """Pre-compile all templates for faster string formatting."""
        with self._template_lock:
            for idx, template in enumerate(self._raw_templates):
                self._compiled_templates[idx] = Template(template)
                self._template_usage[idx] = 0
                
    def _init_common_values(self) -> None:
        """Initialize commonly used values for faster substitution."""
        self._common_values = {
            'magic_numbers': [str(i) for i in range(1000, 10000)],
            'uuids': [str(uuid.uuid4()) for _ in range(1000)],
            'timestamps': []  # Will be refreshed periodically
        }
        self._refresh_timestamps()
        
    def _refresh_timestamps(self) -> None:
        """Refresh timestamp cache."""
        current_time = datetime.now()
        self._common_values['timestamps'] = [
            (current_time.replace(microsecond=i * 1000)).strftime('%Y-%m-%d %H:%M:%S.%f')
            for i in range(1000)
        ]
        
    def _get_cached_value(self, key: str) -> str:
        """Get a cached common value."""
        values = self._common_values.get(key, [])
        return random.choice(values) if values else ''
        
    def get_template_id(self, thread_id: int = None) -> int:
        """
        Get next template ID ensuring good distribution and no consecutive repeats.
        
        Args:
            thread_id: Optional thread identifier for tracking
            
        Returns:
            int: Template index
        """
        with self._template_lock:
            last_idx = self._last_template_idx.get(thread_id, -1)
            
            # Get least used templates
            usage_items = sorted(self._template_usage.items(), key=lambda x: x[1])
            least_used = [idx for idx, _ in usage_items[:10]]
            
            # Filter out last used template
            available = [idx for idx in least_used if idx != last_idx]
            
            # Select template
            template_idx = random.choice(available)
            
            # Update tracking
            self._last_template_idx[thread_id] = template_idx
            self._template_usage[template_idx] += 1
            
            return template_idx
            
    def format_template(self, template_idx: int, **kwargs) -> str:
        """
        Format template with provided values.
        Uses caching for improved performance.
        
        Args:
            template_idx: Template index to use
            **kwargs: Values for template substitution
            
        Returns:
            str: Formatted template content
        """
        # Create cache key from template_idx and values
        cache_key = f"{template_idx}:{hash(frozenset(kwargs.items()))}"
        
        # Check cache first
        with self._lock:
            if cache_key in self._template_cache:
                return self._template_cache[cache_key]
        
        # Format template
        try:
            template = self._compiled_templates[template_idx]
            
            # Add common values if not provided
            if 'uuid' not in kwargs:
                kwargs['uuid'] = self._get_cached_value('uuids')
            if 'timestamp' not in kwargs:
                kwargs['timestamp'] = self._get_cached_value('timestamps')
            if 'magic_number' not in kwargs:
                kwargs['magic_number'] = self._get_cached_value('magic_numbers')
            
            # Format the template
            result = template.safe_substitute(**kwargs)
            
            # Cache the result
            with self._lock:
                if len(self._template_cache) >= self._cache_size:
                    # Remove random entries if cache is full
                    remove_keys = random.sample(list(self._template_cache.keys()), 
                                             self._cache_size // 4)
                    for key in remove_keys:
                        self._template_cache.pop(key, None)
                
                self._template_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"Error formatting template {template_idx}: {e}")
            return self._raw_templates[0].format(**kwargs)  # Fallback to first template
            
    def generate_file_content(self, folder_name: str, file_num: int,
                            thread_id: Optional[int] = None, **extra_values) -> str:
        """
        Generate complete file content using templates.
        
        Args:
            folder_name: Name of the current folder
            file_num: File number in sequence
            thread_id: Optional thread identifier
            **extra_values: Additional template values
            
        Returns:
            str: Generated file content
        """
        # Get template
        template_idx = self.get_template_id(thread_id)
        
        # Prepare values
        values = {
            'file_num': file_num,
            'folder_name': folder_name,
            **extra_values
        }
        
        # Format template
        return self.format_template(template_idx, **values)
        
    def cleanup(self) -> None:
        """Cleanup caches and refresh timestamps."""
        with self._lock:
            self._template_cache.clear()
            self._refresh_timestamps()
            
    def get_statistics(self) -> Dict[str, any]:
        """
        Get usage statistics for monitoring.
        
        Returns:
            Dict with usage statistics
        """
        with self._template_lock:
            return {
                'total_uses': sum(self._template_usage.values()),
                'template_usage': dict(self._template_usage),
                'cache_size': len(self._template_cache),
                'cache_hit_ratio': self._calculate_cache_hit_ratio()
            }
            
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio for performance monitoring."""
        total = sum(self._template_usage.values())
        if total == 0:
            return 0.0
        hits = len(self._template_cache)
        return hits / total if total > 0 else 0.0

# Example usage and testing
if __name__ == "__main__":
    # Initialize template manager
    template_mgr = TemplateManager()
    
    # Test template generation
    print("Generating sample content...")
    
    # Example values
    test_values = {
        'folder_name': 'test_folder',
        'art': 'ASCII ART HERE',
        'quote': 'Sample quote',
        'fact': 'Interesting fact',
        'joke': 'Funny joke'
    }
    
    # Generate some test content
    start_time = time.time()
    for i in range(5):
        content = template_mgr.generate_file_content(
            folder_name='test_folder',
            file_num=i,
            thread_id=0,
            **test_values
        )
        print(f"\nGenerated content length: {len(content)}")
        print(f"First 100 characters: {content[:100]}...")
    
    # Print performance stats
    end_time = time.time()
    print(f"\nTime taken for 5 generations: {end_time - start_time:.4f} seconds")
    print("\nTemplate statistics:")
    print(template_mgr.get_statistics())
from typing import Dict, Any
from pathlib import Path
import os
import json
import threading

class Settings:
    """Global settings and configuration management"""
    
    # System settings
    BASE_DIR = Path("output")
    WORD_LISTS_DIR = Path("word_lists")
    TEMPLATE_DIR = Path("templates")
    LOG_DIR = Path("logs")
    
    # Performance settings
    BATCH_SIZE = 100
    MAX_WORKERS = 4
    BUFFER_SIZE = 8192
    MAX_MEMORY_PERCENT = 80.0
    MAX_CPU_PERCENT = 80.0
    PARALLEL_FOLDERS = 2
    
    # Cache settings
    TEMPLATE_CACHE_SIZE = 1000
    WORD_CACHE_SIZE = 1000
    CONTENT_CACHE_SIZE = 1000
    
    # File generation settings
    FILES_PER_FOLDER = 1000
    FILE_NAME_LENGTH = 8
    RANDOM_DIGITS_LENGTH = 10
    
    # Git settings
    GIT_ENABLED = True
    GIT_BATCH_SIZE = 50
    GIT_COMPRESSION = 0
    
    # Monitoring settings
    ENABLE_MONITORING = True
    MONITOR_REFRESH_RATE = 1.0
    METRICS_HISTORY_SIZE = 1000
    
    # Report settings
    REPORT_FORMATS = ['html', 'excel', 'json']
    REPORT_DIR = Path("reports")
    
    # Error handling
    MAX_RETRIES = 3
    ERROR_SNAPSHOT_DIR = Path("error_snapshots")
    
    @classmethod
    def load_from_file(cls, config_file: Path) -> None:
        """Load settings from configuration file"""
        if not config_file.exists():
            return
            
        with open(config_file) as f:
            config = json.load(f)
            
        for key, value in config.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
                
    @classmethod
    def get_paths(cls) -> Dict[str, Path]:
        """Get all configured paths"""
        return {
            'base_dir': cls.BASE_DIR,
            'word_lists': cls.WORD_LISTS_DIR,
            'templates': cls.TEMPLATE_DIR,
            'logs': cls.LOG_DIR,
            'reports': cls.REPORT_DIR,
            'error_snapshots': cls.ERROR_SNAPSHOT_DIR
        }
        
    @classmethod
    def create_directories(cls) -> None:
        """Create all required directories"""
        for path in cls.get_paths().values():
            path.mkdir(parents=True, exist_ok=True)
            
    @classmethod
    def get_performance_settings(cls) -> Dict[str, Any]:
        """Get performance-related settings"""
        return {
            'batch_size': cls.BATCH_SIZE,
            'max_workers': cls.MAX_WORKERS,
            'buffer_size': cls.BUFFER_SIZE,
            'max_memory_percent': cls.MAX_MEMORY_PERCENT,
            'max_cpu_percent': cls.MAX_CPU_PERCENT,
            'parallel_folders': cls.PARALLEL_FOLDERS
        }
        
    @classmethod
    def get_cache_settings(cls) -> Dict[str, int]:
        """Get cache-related settings"""
        return {
            'template_cache': cls.TEMPLATE_CACHE_SIZE,
            'word_cache': cls.WORD_CACHE_SIZE,
            'content_cache': cls.CONTENT_CACHE_SIZE
        }
        
    @classmethod
    def get_git_settings(cls) -> Dict[str, Any]:
        """Get git-related settings"""
        return {
            'enabled': cls.GIT_ENABLED,
            'batch_size': cls.GIT_BATCH_SIZE,
            'compression': cls.GIT_COMPRESSION
        }
        
    @classmethod
    def validate(cls) -> bool:
        """Validate settings"""
        try:
            assert cls.BATCH_SIZE > 0, "Batch size must be positive"
            assert cls.MAX_WORKERS > 0, "Max workers must be positive"
            assert cls.BUFFER_SIZE > 0, "Buffer size must be positive"
            assert 0 <= cls.MAX_MEMORY_PERCENT <= 100, "Invalid memory percent"
            assert 0 <= cls.MAX_CPU_PERCENT <= 100, "Invalid CPU percent"
            return True
        except AssertionError as e:
            print(f"Settings validation failed: {e}")
            return False

# Initialize settings from environment variables
for key in dir(Settings):
    if key.isupper():
        env_value = os.environ.get(f"FASTGEN_{key}")
        if env_value is not None:
            # Convert value to appropriate type
            current_value = getattr(Settings, key)
            if isinstance(current_value, bool):
                setattr(Settings, key, env_value.lower() == 'true')
            elif isinstance(current_value, int):
                setattr(Settings, key, int(env_value))
            elif isinstance(current_value, float):
                setattr(Settings, key, float(env_value))
            elif isinstance(current_value, Path):
                setattr(Settings, key, Path(env_value))
            else:
                setattr(Settings, key, env_value)

# Create required directories
Settings.create_directories()
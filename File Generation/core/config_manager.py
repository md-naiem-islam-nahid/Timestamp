import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
import threading
from datetime import datetime
import shutil
import socket
from contextlib import contextmanager

@dataclass
class SystemConfig:
    """System configuration settings"""
    base_dir: str = "output"
    batch_size: int = 100
    max_workers: int = 4
    buffer_size: int = 8192
    enable_git: bool = True
    enable_monitoring: bool = True
    log_level: str = "INFO"
    
    # Performance settings
    parallel_folders: int = 2
    max_memory_percent: float = 80.0
    max_cpu_percent: float = 80.0
    disk_buffer_size: int = 1024 * 1024  # 1MB
    
    # Template settings
    template_cache_size: int = 1000
    word_cache_size: int = 1000
    
    # Git settings
    git_batch_size: int = 50
    git_compression: int = 0
    
    # Monitoring settings
    monitor_refresh_rate: float = 1.0
    metrics_history_size: int = 1000
    
    def validate(self):
        """Validate configuration settings"""
        errors = []
        
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")
        if self.max_workers <= 0:
            errors.append("max_workers must be positive")
        if self.buffer_size <= 0:
            errors.append("buffer_size must be positive")
        if not isinstance(self.enable_git, bool):
            errors.append("enable_git must be boolean")
            
        if errors:
            raise ConfigurationError("\n".join(errors))

@dataclass
class RuntimeState:
    """Runtime state tracking"""
    start_time: datetime = field(default_factory=datetime.now)
    hostname: str = field(default_factory=socket.gethostname)
    process_id: int = field(default_factory=os.getpid)
    active_threads: int = 0
    total_memory: int = 0
    errors: Dict[str, int] = field(default_factory=dict)
    component_status: Dict[str, bool] = field(default_factory=dict)

class ConfigurationError(Exception):
    """Configuration validation error"""
    pass

class SystemError(Exception):
    """System-level error"""
    pass

class ComponentError(Exception):
    """Component-specific error"""
    pass

class ConfigurationManager:
    """
    Manages system configuration, error handling, and runtime state.
    Provides centralized configuration and error management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = SystemConfig()
        self.state = RuntimeState()
        
        # Thread safety
        self._lock = threading.RLock()
        self._config_path = Path(config_path) if config_path else None
        
        # Error handling
        self._error_handlers: Dict[type, callable] = {}
        self._setup_error_handlers()
        
        # Logging setup
        self._setup_logging()
        
        # Load configuration
        if self._config_path and self._config_path.exists():
            self.load_configuration()
            
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config.base_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / "system.log",
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        )
        
        # Add console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger('').addHandler(console)
        
    def _setup_error_handlers(self):
        """Setup default error handlers"""
        self._error_handlers = {
            ConfigurationError: self._handle_config_error,
            SystemError: self._handle_system_error,
            ComponentError: self._handle_component_error,
            Exception: self._handle_unknown_error
        }
        
    def register_error_handler(self, error_type: type, 
                             handler: callable):
        """Register custom error handler"""
        with self._lock:
            self._error_handlers[error_type] = handler
            
    def _handle_config_error(self, error: ConfigurationError):
        """Handle configuration errors"""
        logging.error(f"Configuration error: {error}")
        self.state.errors['config'] = self.state.errors.get('config', 0) + 1
        raise
        
    def _handle_system_error(self, error: SystemError):
        """Handle system-level errors"""
        logging.error(f"System error: {error}")
        self.state.errors['system'] = self.state.errors.get('system', 0) + 1
        self._create_error_snapshot()
        raise
        
    def _handle_component_error(self, error: ComponentError):
        """Handle component-specific errors"""
        logging.error(f"Component error: {error}")
        self.state.errors['component'] = self.state.errors.get('component', 0) + 1
        
    def _handle_unknown_error(self, error: Exception):
        """Handle unknown errors"""
        logging.error(f"Unknown error: {error}")
        self.state.errors['unknown'] = self.state.errors.get('unknown', 0) + 1
        self._create_error_snapshot()
        
    def _create_error_snapshot(self):
        """Create system state snapshot on error"""
        snapshot_dir = Path(self.config.base_dir) / "error_snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = snapshot_dir / f"error_snapshot_{timestamp}.json"
        
        snapshot = {
            'timestamp': timestamp,
            'state': asdict(self.state),
            'config': asdict(self.config),
            'system_info': {
                'memory': psutil.virtual_memory()._asdict(),
                'cpu': psutil.cpu_percent(interval=1),
                'disk': psutil.disk_usage('/')._asdict()
            }
        }
        
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
            
    @contextmanager
    def error_handler(self):
        """Context manager for error handling"""
        try:
            yield
        except Exception as e:
            handler = self._error_handlers.get(type(e), self._handle_unknown_error)
            handler(e)
            
    def load_configuration(self):
        """Load configuration from file"""
        try:
            if self._config_path.suffix == '.json':
                with open(self._config_path) as f:
                    config_data = json.load(f)
            elif self._config_path.suffix in ['.yml', '.yaml']:
                with open(self._config_path) as f:
                    config_data = yaml.safe_load(f)
            else:
                raise ConfigurationError(f"Unsupported config format: {self._config_path.suffix}")
                
            # Update configuration
            with self._lock:
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                        
            # Validate configuration
            self.config.validate()
            
            logging.info(f"Configuration loaded from {self._config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
            
    def save_configuration(self, path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = Path(path) if path else self._config_path
        if not save_path:
            raise ConfigurationError("No configuration path specified")
            
        try:
            # Create backup if file exists
            if save_path.exists():
                backup_path = save_path.with_suffix(f'.bak_{int(time.time())}')
                shutil.copy2(save_path, backup_path)
                
            # Save configuration
            config_data = asdict(self.config)
            
            if save_path.suffix == '.json':
                with open(save_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            elif save_path.suffix in ['.yml', '.yaml']:
                with open(save_path, 'w') as f:
                    yaml.dump(config_data, f)
            else:
                raise ConfigurationError(f"Unsupported config format: {save_path.suffix}")
                
            logging.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
            
    def update_configuration(self, updates: Dict[str, Any]):
        """Update configuration settings"""
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    logging.warning(f"Unknown configuration key: {key}")
                    
            # Validate new configuration
            self.config.validate()
            
    def update_state(self, updates: Dict[str, Any]):
        """Update runtime state"""
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
                    
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """Get configuration for specific component"""
        with self._lock:
            config_dict = asdict(self.config)
            return {
                k: v for k, v in config_dict.items()
                if k.startswith(f"{component}_")
            }
            
    def validate_system(self) -> bool:
        """Validate system requirements"""
        try:
            # Check directory permissions
            base_dir = Path(self.config.base_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
            test_file = base_dir / '.test'
            test_file.touch()
            test_file.unlink()
            
            # Check memory
            memory = psutil.virtual_memory()
            if memory.percent > self.config.max_memory_percent:
                raise SystemError(f"Insufficient memory: {memory.percent}%")
                
            # Check CPU
            if psutil.cpu_percent(interval=1) > self.config.max_cpu_percent:
                raise SystemError(f"High CPU usage: {psutil.cpu_percent()}%")
                
            # Check disk space
            disk = psutil.disk_usage(str(base_dir))
            if disk.percent > 90:
                raise SystemError(f"Insufficient disk space: {disk.free / (1024**3):.2f}GB free")
                
            return True
            
        except Exception as e:
            self._handle_system_error(SystemError(f"System validation failed: {e}"))
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        with self._lock:
            return {
                'config': asdict(self.config),
                'state': asdict(self.state),
                'errors': dict(self.state.errors),
                'components': dict(self.state.component_status)
            }

# Example usage
if __name__ == "__main__":
    # Create test configuration
    test_config = {
        'base_dir': 'test_output',
        'batch_size': 200,
        'max_workers': 8
    }
    
    # Initialize manager
    config_manager = ConfigurationManager()
    
    try:
        # Update configuration
        config_manager.update_configuration(test_config)
        
        # Validate system
        if config_manager.validate_system():
            print("System validation passed")
            
        # Test error handling
        with config_manager.error_handler():
            raise ComponentError("Test error")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Print status
        status = config_manager.get_status()
        print("\nSystem Status:")
        print(json.dumps(status, indent=2, default=str))
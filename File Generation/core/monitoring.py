import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
import psutil
import json
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from queue import Queue
import curses
from collections import deque

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_write_speed: float  # MB/s
    files_per_second: float
    current_folder: str
    files_completed: int
    total_files: int
    queue_sizes: Dict[str, int]
    errors: int
    
class MonitoringSystem:
    """
    Real-time performance monitoring and statistics tracking system.
    Provides live dashboard and performance metrics collection.
    """
    
    def __init__(self, base_dir: Path, refresh_rate: float = 1.0):
        """
        Initialize monitoring system.
        
        Args:
            base_dir: Base directory for generated files
            refresh_rate: Dashboard refresh rate in seconds
        """
        self.base_dir = Path(base_dir)
        self.refresh_rate = refresh_rate
        
        # Performance tracking
        self._metrics_history: List[PerformanceMetrics] = []
        self._metrics_queue = Queue(maxsize=1000)
        self._recent_metrics = deque(maxlen=60)  # Last minute of metrics
        
        # State tracking
        self._running = False
        self._start_time = None
        self._last_size = 0
        self._last_files = 0
        
        # Threading
        self._lock = threading.RLock()
        self._monitor_thread = None
        self._dashboard_thread = None
        
        # Initialize logging
        self._setup_logging()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'min_files_per_second': 50.0
        }
        
    def _setup_logging(self):
        """Setup performance logging"""
        log_path = self.base_dir / 'logs'
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_path / 'performance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def start(self, callback: Optional[Callable] = None):
        """
        Start monitoring system.
        
        Args:
            callback: Optional callback for metrics updates
        """
        self._running = True
        self._start_time = time.time()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_performance,
            args=(callback,)
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        # Start dashboard thread
        self._dashboard_thread = threading.Thread(
            target=self._run_dashboard
        )
        self._dashboard_thread.daemon = True
        self._dashboard_thread.start()
        
    def stop(self):
        """Stop monitoring system"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join()
        if self._dashboard_thread:
            self._dashboard_thread.join()
            
    def collect_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics.
        
        Returns:
            PerformanceMetrics: Current system metrics
        """
        with self._lock:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Disk metrics
            current_size = sum(
                f.stat().st_size
                for f in self.base_dir.rglob('*')
                if f.is_file()
            )
            disk_write_speed = (
                (current_size - self._last_size) / 
                (1024 * 1024 * self.refresh_rate)  # MB/s
            )
            self._last_size = current_size
            
            # File metrics
            current_files = len(list(self.base_dir.rglob('*.txt')))
            files_per_second = (
                (current_files - self._last_files) / 
                self.refresh_rate
            )
            self._last_files = current_files
            
            # Queue sizes from components
            queue_sizes = {
                'write_queue': 0,  # To be updated from components
                'git_queue': 0
            }
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_write_speed=disk_write_speed,
                files_per_second=files_per_second,
                current_folder="",  # To be updated from components
                files_completed=current_files,
                total_files=0,  # To be updated from components
                queue_sizes=queue_sizes,
                errors=0  # To be updated from components
            )
            
            self._recent_metrics.append(metrics)
            return metrics
            
    def _monitor_performance(self, callback: Optional[Callable]):
        """Background performance monitoring thread"""
        while self._running:
            try:
                metrics = self.collect_metrics()
                self._metrics_queue.put(metrics)
                self._check_thresholds(metrics)
                
                if callback:
                    callback(metrics)
                    
                time.sleep(self.refresh_rate)
                
            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")
                time.sleep(self.refresh_rate)
                
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check metrics against thresholds"""
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            logging.warning(f"High CPU usage: {metrics.cpu_percent}%")
            
        if metrics.memory_percent > self.thresholds['memory_percent']:
            logging.warning(f"High memory usage: {metrics.memory_percent}%")
            
        if (metrics.files_per_second < 
            self.thresholds['min_files_per_second']):
            logging.warning(
                f"Low file generation rate: {metrics.files_per_second} files/s"
            )
            
    def _run_dashboard(self):
        """Run the live performance dashboard"""
        try:
            curses.wrapper(self._dashboard_loop)
        except Exception as e:
            logging.error(f"Dashboard error: {e}")
            
    def _dashboard_loop(self, stdscr):
        """Main dashboard rendering loop"""
        curses.curs_set(0)
        curses.use_default_colors()
        stdscr.nodelay(1)
        
        while self._running:
            try:
                stdscr.clear()
                
                # Get latest metrics
                if self._recent_metrics:
                    metrics = self._recent_metrics[-1]
                    
                    # Header
                    stdscr.addstr(0, 0, "Fast File Generator - Performance Monitor")
                    stdscr.addstr(1, 0, "=" * 50)
                    
                    # System metrics
                    stdscr.addstr(3, 0, f"CPU Usage: {metrics.cpu_percent:.1f}%")
                    stdscr.addstr(4, 0, f"Memory Usage: {metrics.memory_percent:.1f}%")
                    stdscr.addstr(5, 0, f"Disk Write Speed: {metrics.disk_write_speed:.2f} MB/s")
                    
                    # Generation metrics
                    stdscr.addstr(7, 0, f"Files/Second: {metrics.files_per_second:.2f}")
                    stdscr.addstr(8, 0, f"Files Completed: {metrics.files_completed}")
                    if metrics.total_files:
                        progress = (metrics.files_completed / metrics.total_files) * 100
                        stdscr.addstr(9, 0, f"Progress: {progress:.1f}%")
                        
                    # Queue sizes
                    stdscr.addstr(11, 0, "Queue Sizes:")
                    for i, (queue, size) in enumerate(metrics.queue_sizes.items()):
                        stdscr.addstr(12 + i, 2, f"{queue}: {size}")
                        
                    # Error count
                    stdscr.addstr(15, 0, f"Errors: {metrics.errors}")
                    
                    # Runtime
                    if self._start_time:
                        runtime = time.time() - self._start_time
                        stdscr.addstr(17, 0, f"Runtime: {runtime:.1f}s")
                        
                    # Update screen
                    stdscr.refresh()
                    
                time.sleep(self.refresh_rate)
                
            except curses.error:
                pass
                
    def save_metrics(self):
        """Save collected metrics to file"""
        metrics_file = self.base_dir / 'performance_metrics.json'
        
        with self._lock:
            # Collect all metrics from queue
            while not self._metrics_queue.empty():
                try:
                    metrics = self._metrics_queue.get_nowait()
                    self._metrics_history.append(metrics)
                except Queue.Empty:
                    break
            
            # Calculate averages
            if self._metrics_history:
                avg_metrics = {
                    'avg_cpu_percent': sum(m.cpu_percent for m in self._metrics_history) / len(self._metrics_history),
                    'avg_memory_percent': sum(m.memory_percent for m in self._metrics_history) / len(self._metrics_history),
                    'avg_disk_write_speed': sum(m.disk_write_speed for m in self._metrics_history) / len(self._metrics_history),
                    'avg_files_per_second': sum(m.files_per_second for m in self._metrics_history) / len(self._metrics_history),
                    'total_runtime': time.time() - self._start_time if self._start_time else 0,
                    'total_errors': sum(m.errors for m in self._metrics_history)
                }
                
                # Save metrics
                with open(metrics_file, 'w') as f:
                    json.dump({
                        'metrics_history': [asdict(m) for m in self._metrics_history],
                        'averages': avg_metrics
                    }, f, indent=2)
                    
        return metrics_file
        
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent metrics"""
        return self._recent_metrics[-1] if self._recent_metrics else None
        
    def update_component_stats(self, stats: Dict):
        """Update stats from components"""
        with self._lock:
            if self._recent_metrics:
                metrics = self._recent_metrics[-1]
                metrics.queue_sizes.update(stats.get('queue_sizes', {}))
                metrics.total_files = stats.get('total_files', 0)
                metrics.errors = stats.get('errors', 0)
                metrics.current_folder = stats.get('current_folder', '')

# Example usage
if __name__ == "__main__":
    def metrics_callback(metrics: PerformanceMetrics):
        print(f"Files/second: {metrics.files_per_second:.2f}")
        
    # Initialize monitoring
    monitor = MonitoringSystem(Path("test_output"))
    
    try:
        # Start monitoring
        monitor.start(callback=metrics_callback)
        
        # Simulate work
        time.sleep(30)
        
    finally:
        # Stop monitoring and save metrics
        monitor.stop()
        metrics_file = monitor.save_metrics()
        print(f"Metrics saved to: {metrics_file}")
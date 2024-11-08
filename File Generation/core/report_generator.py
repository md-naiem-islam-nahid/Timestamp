import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import humanize
from jinja2 import Environment, FileSystemLoader
import logging
import shutil
from dataclasses import dataclass

@dataclass
class ReportMetrics:
    """Metrics for report generation"""
    total_folders: int
    total_files: int
    total_size: int
    generation_time: float
    avg_files_per_second: float
    peak_memory_usage: float
    peak_cpu_usage: float
    error_count: int
    git_commits: int

class ReportGenerator:
    """
    Generates detailed HTML reports with performance visualizations and statistics.
    Includes interactive charts and detailed analysis.
    """
    
    def __init__(self, base_dir: Path, template_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            base_dir: Base directory containing generated files
            template_dir: Directory containing report templates
        """
        self.base_dir = Path(base_dir)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / 'templates'
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
        
        # Initialize metrics storage
        self.metrics = None
        
        # Create report directory
        self.report_dir = self.base_dir / 'reports'
        self.report_dir.mkdir(exist_ok=True)
        
    def _load_performance_data(self) -> pd.DataFrame:
        """Load performance metrics data"""
        metrics_file = self.base_dir / 'performance_metrics.json'
        if not metrics_file.exists():
            raise FileNotFoundError("Performance metrics file not found")
            
        with open(metrics_file) as f:
            data = json.load(f)
            
        # Convert to DataFrame
        df = pd.DataFrame(data['metrics_history'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
        
    def _create_performance_charts(self, df: pd.DataFrame) -> Dict[str, str]:
        """Create performance visualization charts"""
        charts = {}
        
        # CPU and Memory Usage
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('CPU & Memory Usage', 'File Generation Rate')
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['cpu_percent'],
                      name='CPU Usage', line=dict(color='blue')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['memory_percent'],
                      name='Memory Usage', line=dict(color='red')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['files_per_second'],
                      name='Files/Second', line=dict(color='green')),
            row=2, col=1
        )
        
        fig.update_layout(height=800, showlegend=True)
        charts['performance'] = fig.to_html(full_html=False)
        
        # Disk Write Speed
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['disk_write_speed'],
                      name='Write Speed (MB/s)', line=dict(color='purple'))
        )
        fig.update_layout(title='Disk Write Speed')
        charts['disk_speed'] = fig.to_html(full_html=False)
        
        return charts
        
    def _calculate_metrics(self, df: pd.DataFrame) -> ReportMetrics:
        """Calculate report metrics"""
        return ReportMetrics(
            total_folders=len(set(df['current_folder'])),
            total_files=df['files_completed'].max(),
            total_size=sum(df['disk_write_speed'] * 1024 * 1024),  # Convert MB/s to bytes
            generation_time=(df['timestamp'].max() - df['timestamp'].min()).total_seconds(),
            avg_files_per_second=df['files_per_second'].mean(),
            peak_memory_usage=df['memory_percent'].max(),
            peak_cpu_usage=df['cpu_percent'].max(),
            error_count=df['errors'].sum(),
            git_commits=0  # To be updated from git stats
        )
        
    def _create_folder_summary(self) -> List[Dict[str, Any]]:
        """Create summary of generated folders"""
        folders = []
        for folder_path in sorted(self.base_dir.glob('*')):
            if folder_path.is_dir() and not folder_path.name.startswith('.'):
                readme_path = folder_path / 'README.md'
                if readme_path.exists():
                    with open(readme_path) as f:
                        readme_content = f.read()
                        
                folders.append({
                    'name': folder_path.name,
                    'files': len(list(folder_path.glob('*.txt'))),
                    'size': humanize.naturalsize(sum(f.stat().st_size for f in folder_path.glob('*'))),
                    'readme': readme_content
                })
                
        return folders
        
    def _copy_static_files(self):
        """Copy static files for report"""
        static_dir = self.template_dir / 'static'
        if static_dir.exists():
            report_static = self.report_dir / 'static'
            if report_static.exists():
                shutil.rmtree(report_static)
            shutil.copytree(static_dir, report_static)
            
    def generate_report(self) -> Path:
        """
        Generate HTML report.
        
        Returns:
            Path: Path to generated report
        """
        try:
            # Load performance data
            df = self._load_performance_data()
            
            # Create visualizations
            charts = self._create_performance_charts(df)
            
            # Calculate metrics
            self.metrics = self._calculate_metrics(df)
            
            # Get folder summary
            folders = self._create_folder_summary()
            
            # Copy static files
            self._copy_static_files()
            
            # Load template
            template = self.env.get_template('report.html')
            
            # Generate report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.report_dir / f'report_{timestamp}.html'
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(template.render(
                    timestamp=datetime.now().isoformat(),
                    metrics=self.metrics,
                    charts=charts,
                    folders=folders,
                    humanize=humanize
                ))
                
            logging.info(f"Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            raise
            
    def generate_excel_report(self) -> Path:
        """
        Generate Excel report with detailed statistics.
        
        Returns:
            Path: Path to generated Excel file
        """
        try:
            df = self._load_performance_data()
            
            # Create Excel writer
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_path = self.report_dir / f'statistics_{timestamp}.xlsx'
            
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                # Performance metrics
                df.to_excel(writer, sheet_name='Performance Metrics', index=False)
                
                # Summary statistics
                summary = pd.DataFrame([{
                    'Metric': key,
                    'Value': value
                    for key, value in vars(self.metrics).items()
                }])
                summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Folder statistics
                folders_df = pd.DataFrame(self._create_folder_summary())
                folders_df.to_excel(writer, sheet_name='Folders', index=False)
                
            return excel_path
            
        except Exception as e:
            logging.error(f"Error generating Excel report: {e}")
            raise
            
    def generate_json_report(self) -> Path:
        """
        Generate JSON report with all metrics.
        
        Returns:
            Path: Path to generated JSON file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = self.report_dir / f'report_{timestamp}.json'
            
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': vars(self.metrics),
                'folders': self._create_folder_summary(),
                'performance_data': json.loads(
                    self._load_performance_data().to_json(orient='records')
                )
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
                
            return json_path
            
        except Exception as e:
            logging.error(f"Error generating JSON report: {e}")
            raise

# Example HTML template (templates/report.html)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Generation Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">File Generation Report</h1>
        
        <!-- Summary -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-2xl font-semibold mb-4">Summary</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="p-4 bg-blue-50 rounded">
                    <div class="text-sm text-gray-600">Total Folders</div>
                    <div class="text-2xl font-bold">{{ metrics.total_folders }}</div>
                </div>
                <div class="p-4 bg-green-50 rounded">
                    <div class="text-sm text-gray-600">Total Files</div>
                    <div class="text-2xl font-bold">{{ metrics.total_files }}</div>
                </div>
                <div class="p-4 bg-yellow-50 rounded">
                    <div class="text-sm text-gray-600">Total Size</div>
                    <div class="text-2xl font-bold">{{ humanize.naturalsize(metrics.total_size) }}</div>
                </div>
                <div class="p-4 bg-red-50 rounded">
                    <div class="text-sm text-gray-600">Errors</div>
                    <div class="text-2xl font-bold">{{ metrics.error_count }}</div>
                </div>
            </div>
        </div>
        
        <!-- Performance Charts -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-2xl font-semibold mb-4">Performance</h2>
            {{ charts.performance | safe }}
        </div>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-2xl font-semibold mb-4">Disk Write Speed</h2>
            {{ charts.disk_speed | safe }}
        </div>
        
        <!-- Folder List -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-2xl font-semibold mb-4">Generated Folders</h2>
            <div class="grid gap-4">
                {% for folder in folders %}
                <div class="border p-4 rounded">
                    <h3 class="font-bold">{{ folder.name }}</h3>
                    <div class="text-sm text-gray-600">
                        Files: {{ folder.files }} | Size: {{ folder.size }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""

# Example usage
if __name__ == "__main__":
    # Initialize generator
    report_gen = ReportGenerator(Path("test_output"))
    
    try:
        # Generate reports
        html_report = report_gen.generate_report()
        excel_report = report_gen.generate_excel_report()
        json_report = report_gen.generate_json_report()
        
        print(f"Generated reports:")
        print(f"HTML: {html_report}")
        print(f"Excel: {excel_report}")
        print(f"JSON: {json_report}")
        
    except Exception as e:
        print(f"Error generating reports: {e}")
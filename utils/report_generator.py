"""
Report Generator Module
Creates comprehensive benchmark reports in multiple formats
"""

from datetime import datetime
from typing import Dict
import platform


class ReportGenerator:
    """Generate benchmark reports in various formats"""
    
    def __init__(self):
        self.system_info = self.get_system_info()
    
    def get_system_info(self) -> Dict:
        """Collect system information"""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
    
    def generate_text_report(self, raw_results: Dict, normalized_results: Dict, 
                            output_file: str):
        """Generate a comprehensive text report"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("HARDWARE BENCHMARK REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # System Information
        lines.append("SYSTEM INFORMATION")
        lines.append("-" * 80)
        for key, value in self.system_info.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")
        lines.append("")
        
        # Overall Score
        lines.append("OVERALL PERFORMANCE SCORE")
        lines.append("-" * 80)
        overall = normalized_results.get('overall_score', 0)
        lines.append(f"Score: {overall}/100")
        lines.append(self.get_performance_rating(overall))
        lines.append("")
        
        # CPU Results
        if 'cpu' in raw_results:
            lines.extend(self.format_cpu_section(raw_results['cpu'], 
                                                 normalized_results.get('cpu', {})))
        
        # Memory Results
        if 'memory' in raw_results:
            lines.extend(self.format_memory_section(raw_results['memory'], 
                                                    normalized_results.get('memory', {})))
        
        # Disk Results
        if 'disk' in raw_results:
            lines.extend(self.format_disk_section(raw_results['disk'], 
                                                  normalized_results.get('disk', {})))
        
        # Network Results
        if 'network' in raw_results:
            lines.extend(self.format_network_section(raw_results['network'], 
                                                     normalized_results.get('network', {})))
        
        # Footer
        lines.append("=" * 80)
        lines.append("End of Report")
        lines.append("=" * 80)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
    
    def format_cpu_section(self, raw: Dict, normalized: Dict) -> list:
        """Format CPU benchmark section"""
        lines = ["CPU BENCHMARK RESULTS", "-" * 80]
        
        if 'error' in raw:
            lines.append(f"Error: {raw['error']}")
            lines.append("")
            return lines
        
        stats = raw.get('statistics', {})
        eps = stats.get('events_per_second', {})
        
        lines.append(f"Events per Second: {eps.get('mean', 0):.2f}")
        lines.append(f"Standard Deviation: {eps.get('stdev', 0):.2f}")
        lines.append(f"Variance: {eps.get('variance_percent', 0):.2f}%")
        lines.append(f"Normalized Score: {normalized.get('score', 0)}/100")
        lines.append("")
        
        return lines
    
    def format_memory_section(self, raw: Dict, normalized: Dict) -> list:
        """Format memory benchmark section"""
        lines = ["MEMORY BENCHMARK RESULTS", "-" * 80]
        
        if 'error' in raw:
            lines.append(f"Error: {raw['error']}")
            lines.append("")
            return lines
        
        stats = raw.get('statistics', {})
        rate = stats.get('transfer_rate_mib_sec', {})
        
        lines.append(f"Transfer Rate: {rate.get('mean', 0):.2f} MiB/sec")
        lines.append(f"Standard Deviation: {rate.get('stdev', 0):.2f}")
        lines.append(f"Variance: {rate.get('variance_percent', 0):.2f}%")
        lines.append(f"Normalized Score: {normalized.get('score', 0)}/100")
        lines.append("")
        
        return lines
    
    def format_disk_section(self, raw: Dict, normalized: Dict) -> list:
        """Format disk benchmark section"""
        lines = ["DISK I/O BENCHMARK RESULTS", "-" * 80]
        
        for test_type in ['randread', 'randwrite', 'read', 'write']:
            if test_type not in raw:
                continue
            
            test_data = raw[test_type]
            norm_data = normalized.get(test_type, {})
            
            lines.append(f"\n{test_type.upper()}:")
            
            if 'error' in test_data:
                lines.append(f"  Error: {test_data['error']}")
                continue
            
            stats = test_data.get('statistics', {})
            
            if 'rand' in test_type:
                iops = stats.get('iops', {})
                lines.append(f"  IOPS: {iops.get('mean', 0):.2f}")
                lines.append(f"  Variance: {iops.get('variance_percent', 0):.2f}%")
            else:
                bw = stats.get('bandwidth_kb', {})
                lines.append(f"  Bandwidth: {bw.get('mean', 0):.2f} KB/s")
                lines.append(f"  Variance: {bw.get('variance_percent', 0):.2f}%")
            
            lines.append(f"  Normalized Score: {norm_data.get('score', 0)}/100")
        
        lines.append(f"\nAverage Disk Score: {normalized.get('average_score', 0)}/100")
        lines.append("")
        
        return lines
    
    def format_network_section(self, raw: Dict, normalized: Dict) -> list:
        """Format network benchmark section"""
        lines = ["NETWORK BENCHMARK RESULTS", "-" * 80]
        
        if 'error' in raw:
            lines.append(f"Error: {raw['error']}")
            lines.append("")
            return lines
        
        stats = raw.get('statistics', {})
        bw = stats.get('bandwidth_mbps', {})
        
        lines.append(f"Bandwidth: {bw.get('mean', 0):.2f} Mbps")
        lines.append(f"Standard Deviation: {bw.get('stdev', 0):.2f}")
        lines.append(f"Variance: {bw.get('variance_percent', 0):.2f}%")
        lines.append(f"Normalized Score: {normalized.get('score', 0)}/100")
        lines.append("")
        
        return lines
    
    def get_performance_rating(self, score: float) -> str:
        """Get performance rating based on score"""
        if score >= 90:
            return "Rating: Excellent ⭐⭐⭐⭐⭐"
        elif score >= 75:
            return "Rating: Very Good ⭐⭐⭐⭐"
        elif score >= 60:
            return "Rating: Good ⭐⭐⭐"
        elif score >= 40:
            return "Rating: Fair ⭐⭐"
        else:
            return "Rating: Needs Improvement ⭐"
    
    def generate_html_report(self, raw_results: Dict, normalized_results: Dict, 
                            output_file: str):
        """Generate an HTML report with visualizations"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .score-box {{ background: #4CAF50; color: white; padding: 20px; border-radius: 5px; text-align: center; font-size: 24px; margin: 20px 0; }}
        .metric {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .metric-title {{ font-weight: bold; color: #333; }}
        .metric-value {{ font-size: 18px; color: #4CAF50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        .variance-good {{ color: green; }}
        .variance-bad {{ color: red; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Hardware Benchmark Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="score-box">
            Overall Performance Score: {normalized_results.get('overall_score', 0)}/100
        </div>
        
        {self.generate_html_cpu(raw_results.get('cpu', {}), normalized_results.get('cpu', {}))}
        {self.generate_html_memory(raw_results.get('memory', {}), normalized_results.get('memory', {}))}
        {self.generate_html_disk(raw_results.get('disk', {}), normalized_results.get('disk', {}))}
        {self.generate_html_network(raw_results.get('network', {}), normalized_results.get('network', {}))}
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
    
    def generate_html_cpu(self, raw: Dict, normalized: Dict) -> str:
        if not raw or 'error' in raw:
            return ""
        
        stats = raw.get('statistics', {})
        eps = stats.get('events_per_second', {})
        
        return f"""
        <h2>CPU Performance</h2>
        <div class="metric">
            <div class="metric-title">Events per Second</div>
            <div class="metric-value">{eps.get('mean', 0):.2f}</div>
            <div>Variance: {eps.get('variance_percent', 0):.2f}%</div>
            <div>Normalized Score: {normalized.get('score', 0)}/100</div>
        </div>
        """
    
    def generate_html_memory(self, raw: Dict, normalized: Dict) -> str:
        if not raw or 'error' in raw:
            return ""
        
        stats = raw.get('statistics', {})
        rate = stats.get('transfer_rate_mib_sec', {})
        
        return f"""
        <h2>Memory Performance</h2>
        <div class="metric">
            <div class="metric-title">Transfer Rate</div>
            <div class="metric-value">{rate.get('mean', 0):.2f} MiB/sec</div>
            <div>Variance: {rate.get('variance_percent', 0):.2f}%</div>
            <div>Normalized Score: {normalized.get('score', 0)}/100</div>
        </div>
        """
    
    def generate_html_disk(self, raw: Dict, normalized: Dict) -> str:
        if not raw:
            return ""
        
        html = "<h2>Disk I/O Performance</h2><table><tr><th>Test Type</th><th>Value</th><th>Score</th></tr>"
        
        for test_type in ['randread', 'randwrite', 'read', 'write']:
            if test_type in raw and 'error' not in raw[test_type]:
                stats = raw[test_type].get('statistics', {})
                norm = normalized.get(test_type, {})
                
                if 'rand' in test_type:
                    value = f"{stats.get('iops', {}).get('mean', 0):.2f} IOPS"
                else:
                    value = f"{stats.get('bandwidth_kb', {}).get('mean', 0):.2f} KB/s"
                
                html += f"<tr><td>{test_type}</td><td>{value}</td><td>{norm.get('score', 0)}/100</td></tr>"
        
        html += "</table>"
        return html
    
    def generate_html_network(self, raw: Dict, normalized: Dict) -> str:
        if not raw or 'error' in raw:
            return ""
        
        stats = raw.get('statistics', {})
        bw = stats.get('bandwidth_mbps', {})
        
        return f"""
        <h2>Network Performance</h2>
        <div class="metric">
            <div class="metric-title">Bandwidth</div>
            <div class="metric-value">{bw.get('mean', 0):.2f} Mbps</div>
            <div>Variance: {bw.get('variance_percent', 0):.2f}%</div>
            <div>Normalized Score: {normalized.get('score', 0)}/100</div>
        </div>
        """
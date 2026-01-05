"""
Hardware Comparison Tool
Compare benchmark results across multiple systems
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


class HardwareComparison:
    """Compare benchmark results from multiple systems"""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.systems = []
    
    def load_system_results(self, result_path: str, system_name: str = None):
        """Load benchmark results for a system"""
        result_path = Path(result_path)
        
        # Load normalized results
        norm_file = result_path / "normalized_results.json"
        if not norm_file.exists():
            print(f"Warning: {norm_file} not found")
            return False
        
        with open(norm_file, 'r') as f:
            normalized = json.load(f)
        
        # Load raw results
        raw_file = result_path / "raw_results.json"
        with open(raw_file, 'r') as f:
            raw = json.load(f)
        
        # Extract system name from path if not provided
        if system_name is None:
            system_name = result_path.name
        
        self.systems.append({
            'name': system_name,
            'path': str(result_path),
            'normalized': normalized,
            'raw': raw
        })
        
        print(f"✓ Loaded results for: {system_name}")
        return True
    
    def generate_comparison_report(self, output_dir: str = "reports"):
        """Generate comprehensive comparison report"""
        if len(self.systems) < 2:
            print("Need at least 2 systems to compare")
            return
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = output_dir / f"comparison_{timestamp}"
        report_dir.mkdir(exist_ok=True)
        
        print(f"\nGenerating comparison report...")
        
        # Create comparison table
        self.generate_comparison_table(report_dir)
        
        # Create visualizations
        self.generate_comparison_charts(report_dir)
        
        # Create HTML report
        self.generate_html_comparison(report_dir)
        
        print(f"\n✓ Comparison report saved to: {report_dir}")
        print(f"  - comparison_table.csv")
        print(f"  - comparison_charts.png")
        print(f"  - comparison_report.html")
    
    def generate_comparison_table(self, output_dir: Path):
        """Create CSV comparison table"""
        data = []
        
        for system in self.systems:
            row = {
                'System': system['name'],
                'Overall Score': system['normalized'].get('overall_score', 0),
            }
            
            # CPU metrics
            if 'cpu' in system['normalized']:
                cpu = system['normalized']['cpu']
                row['CPU Score'] = cpu.get('score', 0)
                row['CPU Events/sec'] = cpu.get('raw_value', 0)
                row['CPU Variance %'] = cpu.get('variance', 0)
            
            # Memory metrics
            if 'memory' in system['normalized']:
                mem = system['normalized']['memory']
                row['Memory Score'] = mem.get('score', 0)
                row['Memory MiB/sec'] = mem.get('raw_value', 0)
                row['Memory Variance %'] = mem.get('variance', 0)
            
            # Disk metrics
            if 'disk' in system['normalized']:
                disk = system['normalized']['disk']
                row['Disk Score'] = disk.get('average_score', 0)
                
                # Random read IOPS
                if 'randread' in disk:
                    row['Rand Read IOPS'] = disk['randread'].get('raw_value', 0)
                
                # Random write IOPS
                if 'randwrite' in disk:
                    row['Rand Write IOPS'] = disk['randwrite'].get('raw_value', 0)
            
            data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        csv_file = output_dir / "comparison_table.csv"
        df.to_csv(csv_file, index=False, float_format='%.2f')
        
        # Also save as formatted text
        txt_file = output_dir / "comparison_table.txt"
        with open(txt_file, 'w') as f:
            f.write("HARDWARE PERFORMANCE COMPARISON\n")
            f.write("=" * 80 + "\n\n")
            f.write(df.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
        
        print(f"  ✓ Comparison table created")
    
    def generate_comparison_charts(self, output_dir: Path):
        """Create comparison visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Hardware Performance Comparison', fontsize=16, fontweight='bold')
        
        system_names = [s['name'] for s in self.systems]
        
        # 1. Overall Scores
        overall_scores = [s['normalized'].get('overall_score', 0) for s in self.systems]
        axes[0, 0].bar(system_names, overall_scores, color='#4CAF50')
        axes[0, 0].set_title('Overall Performance Score')
        axes[0, 0].set_ylabel('Score (0-100)')
        axes[0, 0].set_ylim(0, 100)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. CPU Performance
        cpu_scores = []
        for s in self.systems:
            cpu = s['normalized'].get('cpu', {})
            cpu_scores.append(cpu.get('score', 0))
        
        axes[0, 1].bar(system_names, cpu_scores, color='#2196F3')
        axes[0, 1].set_title('CPU Performance')
        axes[0, 1].set_ylabel('Score (0-100)')
        axes[0, 1].set_ylim(0, 100)
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. Memory Performance
        mem_scores = []
        for s in self.systems:
            mem = s['normalized'].get('memory', {})
            mem_scores.append(mem.get('score', 0))
        
        axes[1, 0].bar(system_names, mem_scores, color='#FF9800')
        axes[1, 0].set_title('Memory Performance')
        axes[1, 0].set_ylabel('Score (0-100)')
        axes[1, 0].set_ylim(0, 100)
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. Disk Performance
        disk_scores = []
        for s in self.systems:
            disk = s['normalized'].get('disk', {})
            disk_scores.append(disk.get('average_score', 0))
        
        axes[1, 1].bar(system_names, disk_scores, color='#9C27B0')
        axes[1, 1].set_title('Disk I/O Performance')
        axes[1, 1].set_ylabel('Score (0-100)')
        axes[1, 1].set_ylim(0, 100)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        chart_file = output_dir / "comparison_charts.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Comparison charts created")
    
    def generate_html_comparison(self, output_dir: Path):
        """Generate HTML comparison report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Hardware Performance Comparison</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 4px solid #4CAF50; padding-bottom: 15px; margin-bottom: 30px; }}
        h2 {{ color: #555; margin-top: 40px; border-left: 5px solid #4CAF50; padding-left: 15px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; min-width: 200px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .summary-card h3 {{ margin: 0; font-size: 16px; font-weight: normal; opacity: 0.9; }}
        .summary-card .value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }}
        tr:hover {{ background: #f5f5f5; }}
        .winner {{ background: #e8f5e9; font-weight: bold; }}
        .chart-container {{ margin: 40px 0; text-align: center; }}
        .chart-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .metric-badge {{ display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin: 5px; }}
        .badge-excellent {{ background: #4CAF50; color: white; }}
        .badge-good {{ background: #8BC34A; color: white; }}
        .badge-fair {{ background: #FFC107; color: white; }}
        .badge-poor {{ background: #FF5722; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Hardware Performance Comparison Report</h1>
        <p style="color: #666; font-size: 14px;"><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Systems Compared</h3>
                <div class="value">{len(self.systems)}</div>
            </div>
            <div class="summary-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>Best Overall</h3>
                <div class="value" style="font-size: 20px;">{self.get_best_system()}</div>
            </div>
            <div class="summary-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>Avg Variance</h3>
                <div class="value">{self.get_average_variance():.1f}%</div>
            </div>
        </div>
        
        <h2>📊 Performance Overview</h2>
        <div class="chart-container">
            <img src="comparison_charts.png" alt="Performance Comparison Charts">
        </div>
        
        <h2>📈 Detailed Comparison Table</h2>
        {self.generate_html_table()}
        
        <h2>🏆 Performance Winners</h2>
        {self.generate_winners_section()}
    </div>
</body>
</html>
        """
        
        html_file = output_dir / "comparison_report.html"
        with open(html_file, 'w') as f:
            f.write(html)
        
        print(f"  ✓ HTML comparison report created")
    
    def get_best_system(self) -> str:
        """Find system with best overall score"""
        best = max(self.systems, key=lambda s: s['normalized'].get('overall_score', 0))
        return best['name']
    
    def get_average_variance(self) -> float:
        """Calculate average variance across all systems"""
        total_var = 0
        count = 0
        
        for system in self.systems:
            cpu_var = system['normalized'].get('cpu', {}).get('variance', 0)
            mem_var = system['normalized'].get('memory', {}).get('variance', 0)
            
            total_var += cpu_var + mem_var
            count += 2
        
        return total_var / count if count > 0 else 0
    
    def generate_html_table(self) -> str:
        """Generate HTML comparison table"""
        html = "<table><thead><tr>"
        headers = ['System', 'Overall', 'CPU', 'Memory', 'Disk']
        for h in headers:
            html += f"<th>{h}</th>"
        html += "</tr></thead><tbody>"
        
        for system in self.systems:
            html += "<tr>"
            html += f"<td><strong>{system['name']}</strong></td>"
            
            overall = system['normalized'].get('overall_score', 0)
            html += f"<td>{overall:.1f}/100 {self.get_badge(overall)}</td>"
            
            cpu = system['normalized'].get('cpu', {}).get('score', 0)
            html += f"<td>{cpu:.1f}/100 {self.get_badge(cpu)}</td>"
            
            mem = system['normalized'].get('memory', {}).get('score', 0)
            html += f"<td>{mem:.1f}/100 {self.get_badge(mem)}</td>"
            
            disk = system['normalized'].get('disk', {}).get('average_score', 0)
            html += f"<td>{disk:.1f}/100 {self.get_badge(disk)}</td>"
            
            html += "</tr>"
        
        html += "</tbody></table>"
        return html
    
    def get_badge(self, score: float) -> str:
        """Get performance badge HTML"""
        if score >= 70:
            return '<span class="metric-badge badge-excellent">Good</span>'
        elif score >= 50:
            return '<span class="metric-badge badge-good">Fair</span>'
        elif score >= 30:
            return '<span class="metric-badge badge-fair">Below Avg</span>'
        else:
            return '<span class="metric-badge badge-poor">Poor</span>'
    
    def generate_winners_section(self) -> str:
        """Generate winners section"""
        categories = {
            'CPU': lambda s: s['normalized'].get('cpu', {}).get('score', 0),
            'Memory': lambda s: s['normalized'].get('memory', {}).get('score', 0),
            'Disk': lambda s: s['normalized'].get('disk', {}).get('average_score', 0)
        }
        
        html = "<ul style='font-size: 18px; line-height: 2;'>"
        for cat, func in categories.items():
            winner = max(self.systems, key=func)
            score = func(winner)
            html += f"<li><strong>{cat}:</strong> 🏆 {winner['name']} ({score:.1f}/100)</li>"
        
        html += "</ul>"
        return html


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare hardware benchmark results')
    parser.add_argument('result_dirs', nargs='+', help='Directories containing benchmark results')
    parser.add_argument('-n', '--names', nargs='+', help='Names for each system')
    parser.add_argument('-o', '--output', default='reports', help='Output directory')
    
    args = parser.parse_args()
    
    comparator = HardwareComparison()
    
    # Load all systems
    for i, result_dir in enumerate(args.result_dirs):
        name = args.names[i] if args.names and i < len(args.names) else None
        comparator.load_system_results(result_dir, name)
    
    # Generate comparison
    comparator.generate_comparison_report(args.output)


if __name__ == "__main__":
    main()
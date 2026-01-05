#!/usr/bin/env python3
"""
Automated Hardware Benchmarking Tool
Main controller for executing and managing benchmarks
"""

import os
import sys
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path

# Import benchmark modules
from benchmarks.cpu_benchmark import CPUBenchmark
from benchmarks.memory_benchmark import MemoryBenchmark
from benchmarks.disk_benchmark import DiskBenchmark
from benchmarks.network_benchmark import NetworkBenchmark

# Import utility modules
from utils.report_generator import ReportGenerator
from utils.data_normalizer import DataNormalizer


class BenchmarkController:
    """Main controller for hardware benchmarking"""
    
    def __init__(self, config_path="config/benchmark_config.yaml"):
        self.config = self.load_config(config_path)
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_config(self, config_path):
        """Load benchmark configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            'cpu': {'enabled': True, 'threads': 4, 'duration': 30},
            'memory': {'enabled': True, 'block_size': '1M', 'total_size': '10G'},
            'disk': {'enabled': True, 'size': '1G', 'test_file': 'C:\\Temp\\benchmark_test'},
            'network': {'enabled': False, 'server_ip': None, 'duration': 10},
            'runs': 3,
            'output_dir': 'results'
        }
    
    def run_all_benchmarks(self):
        """Execute all enabled benchmarks"""
        print("=" * 60)
        print("Starting Hardware Benchmark Suite")
        print(f"Timestamp: {self.timestamp}")
        print("=" * 60)
        
        # CPU Benchmark
        if self.config['cpu']['enabled']:
            print("\n[1/4] Running CPU Benchmark...")
            cpu_bench = CPUBenchmark(self.config['cpu'])
            self.results['cpu'] = cpu_bench.run(self.config['runs'])
            print(f"✓ CPU Benchmark completed")
        
        # Memory Benchmark
        if self.config['memory']['enabled']:
            print("\n[2/4] Running Memory Benchmark...")
            mem_bench = MemoryBenchmark(self.config['memory'])
            self.results['memory'] = mem_bench.run(self.config['runs'])
            print(f"✓ Memory Benchmark completed")
        
        # Disk Benchmark
        if self.config['disk']['enabled']:
            print("\n[3/4] Running Disk I/O Benchmark...")
            disk_bench = DiskBenchmark(self.config['disk'])
            self.results['disk'] = disk_bench.run(self.config['runs'])
            print(f"✓ Disk Benchmark completed")
        
        # Network Benchmark
        if self.config['network']['enabled'] and self.config['network']['server_ip']:
            print("\n[4/4] Running Network Benchmark...")
            net_bench = NetworkBenchmark(self.config['network'])
            self.results['network'] = net_bench.run(self.config['runs'])
            print(f"✓ Network Benchmark completed")
        
        print("\n" + "=" * 60)
        print("All Benchmarks Completed!")
        print("=" * 60)
    
    def normalize_results(self):
        """Normalize benchmark results for comparison"""
        print("\nNormalizing results...")
        normalizer = DataNormalizer()
        self.normalized_results = normalizer.normalize(self.results)
        print("✓ Results normalized")
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\nGenerating reports...")
        
        # Create output directory
        output_dir = Path(self.config['output_dir']) / self.timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw results
        raw_file = output_dir / "raw_results.json"
        with open(raw_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Raw results saved: {raw_file}")
        
        # Save normalized results
        norm_file = output_dir / "normalized_results.json"
        with open(norm_file, 'w') as f:
            json.dump(self.normalized_results, f, indent=2)
        print(f"✓ Normalized results saved: {norm_file}")
        
        # Generate text report
        report_gen = ReportGenerator()
        report_file = output_dir / "benchmark_report.txt"
        report_gen.generate_text_report(
            self.results, 
            self.normalized_results, 
            report_file
        )
        print(f"✓ Text report saved: {report_file}")
        
        # Generate HTML report
        html_file = output_dir / "benchmark_report.html"
        report_gen.generate_html_report(
            self.results,
            self.normalized_results,
            html_file
        )
        print(f"✓ HTML report saved: {html_file}")
        
        return output_dir
    
    def run(self):
        """Main execution flow"""
        try:
            self.run_all_benchmarks()
            self.normalize_results()
            output_dir = self.generate_report()
            
            print("\n" + "=" * 60)
            print("SUCCESS! Benchmark suite completed")
            print(f"Results saved in: {output_dir}")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\nBenchmark interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\nError during benchmark execution: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Automated Hardware Benchmarking Tool'
    )
    parser.add_argument(
        '-c', '--config',
        default='config/benchmark_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--cpu-only',
        action='store_true',
        help='Run only CPU benchmark'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick benchmarks (reduced duration)'
    )
    
    args = parser.parse_args()
    
    # Initialize controller
    controller = BenchmarkController(args.config)
    
    # Modify config based on arguments
    if args.cpu_only:
        controller.config['memory']['enabled'] = False
        controller.config['disk']['enabled'] = False
        controller.config['network']['enabled'] = False
    
    if args.quick:
        controller.config['runs'] = 1
        controller.config['cpu']['duration'] = 10
    
    # Run benchmarks
    controller.run()


if __name__ == "__main__":
    main()
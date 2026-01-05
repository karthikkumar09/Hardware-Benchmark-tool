"""
Memory Benchmark Module
Uses sysbench to benchmark memory performance
"""

import subprocess
import re
import statistics
from typing import Dict, List


class MemoryBenchmark:
    """Memory performance benchmark using sysbench"""
    
    def __init__(self, config: Dict):
        self.block_size = config.get('block_size', '1M')
        self.total_size = config.get('total_size', '10G')
        self.threads = config.get('threads', 1)
        self.operation = config.get('operation', 'write')  # read, write, or none
    
    def run_single_test(self) -> Dict:
        """Execute a single memory benchmark"""
        cmd = [
            'sysbench',
            'memory',
            f'--memory-block-size={self.block_size}',
            f'--memory-total-size={self.total_size}',
            f'--memory-oper={self.operation}',
            f'--threads={self.threads}',
            'run'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return self.parse_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return {'error': 'Benchmark timed out'}
        except FileNotFoundError:
            return {'error': 'sysbench not found. Please install it.'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_output(self, output: str) -> Dict:
        """Parse sysbench memory output"""
        results = {}
        
        # Extract transfer rate (MiB/sec)
        transfer_match = re.search(r'transferred \([\d.]+\s+MiB/sec,\s+([\d.]+)\s+MB/sec', output)
        if not transfer_match:
            transfer_match = re.search(r'([\d.]+)\s+MiB/sec', output)
        
        if transfer_match:
            results['transfer_rate_mib_sec'] = float(transfer_match.group(1))
        
        # Extract total operations
        ops_match = re.search(r'total number of events:\s+(\d+)', output)
        if ops_match:
            results['total_operations'] = int(ops_match.group(1))
        
        # Extract operations per second
        ops_sec_match = re.search(r'events per second:\s+([\d.]+)', output)
        if ops_sec_match:
            results['operations_per_second'] = float(ops_sec_match.group(1))
        
        # Extract latency
        lat_avg = re.search(r'avg:\s+([\d.]+)', output)
        if lat_avg:
            results['latency_avg_ms'] = float(lat_avg.group(1))
        
        return results
    
    def run(self, num_runs: int = 3) -> Dict:
        """Run benchmark multiple times and aggregate results"""
        all_results = []
        
        for i in range(num_runs):
            print(f"  Run {i+1}/{num_runs}...", end='', flush=True)
            result = self.run_single_test()
            
            if 'error' in result:
                print(f" ERROR: {result['error']}")
                return result
            
            all_results.append(result)
            rate = result.get('transfer_rate_mib_sec', 0)
            print(f" {rate:.2f} MiB/sec")
        
        return self.aggregate_results(all_results)
    
    def aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate multiple benchmark runs"""
        if not results:
            return {}
        
        aggregated = {
            'runs': results,
            'statistics': {}
        }
        
        metrics = ['transfer_rate_mib_sec', 'operations_per_second', 'latency_avg_ms']
        
        for metric in metrics:
            values = [r.get(metric) for r in results if metric in r]
            if values:
                aggregated['statistics'][metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'variance_percent': (statistics.stdev(values) / statistics.mean(values) * 100) 
                                       if len(values) > 1 and statistics.mean(values) > 0 else 0
                }
        
        return aggregated
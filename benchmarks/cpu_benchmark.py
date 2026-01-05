"""
CPU Benchmark Module
Uses sysbench to benchmark CPU performance
"""

import subprocess
import re
import statistics
from typing import Dict, List


class CPUBenchmark:
    """CPU performance benchmark using sysbench"""
    
    def __init__(self, config: Dict):
        self.threads = config.get('threads', 4)
        self.duration = config.get('duration', 30)
        self.max_prime = config.get('max_prime', 20000)
    
    def run_single_test(self) -> Dict:
        """Execute a single CPU benchmark"""
        cmd = [
            'sysbench',
            'cpu',
            f'--threads={self.threads}',
            f'--time={self.duration}',
            f'--cpu-max-prime={self.max_prime}',
            'run'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.duration + 30
            )
            
            return self.parse_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            return {'error': 'Benchmark timed out'}
        except FileNotFoundError:
            return {'error': 'sysbench not found. Please install it.'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_output(self, output: str) -> Dict:
        """Parse sysbench output"""
        results = {}
        
        # Extract events per second
        events_match = re.search(r'events per second:\s+([\d.]+)', output)
        if events_match:
            results['events_per_second'] = float(events_match.group(1))
        
        # Extract total events
        total_match = re.search(r'total number of events:\s+(\d+)', output)
        if total_match:
            results['total_events'] = int(total_match.group(1))
        
        # Extract latency metrics
        lat_avg = re.search(r'avg:\s+([\d.]+)', output)
        lat_min = re.search(r'min:\s+([\d.]+)', output)
        lat_max = re.search(r'max:\s+([\d.]+)', output)
        lat_95p = re.search(r'95th percentile:\s+([\d.]+)', output)
        
        if lat_avg:
            results['latency_avg_ms'] = float(lat_avg.group(1))
        if lat_min:
            results['latency_min_ms'] = float(lat_min.group(1))
        if lat_max:
            results['latency_max_ms'] = float(lat_max.group(1))
        if lat_95p:
            results['latency_95p_ms'] = float(lat_95p.group(1))
        
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
            print(f" {result.get('events_per_second', 0):.2f} events/sec")
        
        # Calculate statistics
        return self.aggregate_results(all_results)
    
    def aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate multiple benchmark runs"""
        if not results:
            return {}
        
        aggregated = {
            'runs': results,
            'statistics': {}
        }
        
        # Calculate statistics for key metrics
        metrics = ['events_per_second', 'latency_avg_ms', 'latency_95p_ms']
        
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
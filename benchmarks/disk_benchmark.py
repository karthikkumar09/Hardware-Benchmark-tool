"""
Disk I/O Benchmark Module
Uses fio (Flexible I/O Tester) for disk benchmarking
"""

import subprocess
import json
import statistics
import os
from typing import Dict, List


class DiskBenchmark:
    """Disk I/O benchmark using fio"""
    
    def __init__(self, config: Dict):
        self.size = config.get('size', '1G')
        self.test_file = config.get('test_file', 'C:\\Temp\\benchmark_test')
        self.runtime = config.get('runtime', 30)
        self.iodepth = config.get('iodepth', 16)
    
    def run_single_test(self, test_type: str) -> Dict:
        """
        Execute a single disk benchmark
        test_type: 'randread', 'randwrite', 'read', 'write'
        """
        cmd = [
            'fio',
            '--name=benchmark',
            f'--filename={self.test_file}',
            f'--size={self.size}',
            f'--rw={test_type}',
            '--bs=4k',
            f'--iodepth={self.iodepth}',
            '--direct=0',
            '--ioengine=sync',
            f'--runtime={self.runtime}',
            '--time_based',
            '--group_reporting',
            '--output-format=json'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.runtime + 60
            )
            
            # Clean up test file
            try:
                if os.path.exists(self.test_file):
                    os.remove(self.test_file)
            except:
                pass
            
            return self.parse_output(result.stdout, test_type)
            
        except subprocess.TimeoutExpired:
            return {'error': 'Benchmark timed out'}
        except FileNotFoundError:
            return {'error': 'fio not found. Please install it.'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_output(self, output: str, test_type: str) -> Dict:
        """Parse fio JSON output"""
        try:
            # Find the JSON part (sometimes fio outputs warnings before JSON)
            json_start = output.find('{')
            if json_start != -1:
                output = output[json_start:]
            
            data = json.loads(output)
            job = data['jobs'][0]
            
            results = {
                'test_type': test_type
            }
            
            # Determine if read or write test
            if 'read' in test_type:
                io_data = job['read']
                results['iops'] = io_data['iops']
                results['bandwidth_kb'] = io_data['bw']
                results['latency_mean_us'] = io_data['lat_ns']['mean'] / 1000
                results['latency_stddev_us'] = io_data['lat_ns']['stddev'] / 1000
            else:
                io_data = job['write']
                results['iops'] = io_data['iops']
                results['bandwidth_kb'] = io_data['bw']
                results['latency_mean_us'] = io_data['lat_ns']['mean'] / 1000
                results['latency_stddev_us'] = io_data['lat_ns']['stddev'] / 1000
            
            return results
            
        except (json.JSONDecodeError, KeyError) as e:
            return {'error': f'Failed to parse fio output: {e}'}
    
    def run(self, num_runs: int = 3) -> Dict:
        """Run multiple disk benchmarks"""
        test_types = ['randread', 'randwrite', 'read', 'write']
        all_results = {}
        
        for test_type in test_types:
            print(f"\n  Testing {test_type}...")
            test_results = []
            
            for i in range(num_runs):
                print(f"    Run {i+1}/{num_runs}...", end='', flush=True)
                result = self.run_single_test(test_type)
                
                if 'error' in result:
                    print(f" ERROR: {result['error']}")
                    all_results[test_type] = result
                    break
                
                test_results.append(result)
                iops = result.get('iops', 0)
                print(f" {iops:.2f} IOPS")
            
            if test_results:
                all_results[test_type] = self.aggregate_results(test_results)
        
        return all_results
    
    def aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate multiple benchmark runs"""
        if not results:
            return {}
        
        aggregated = {
            'runs': results,
            'statistics': {}
        }
        
        metrics = ['iops', 'bandwidth_kb', 'latency_mean_us']
        
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
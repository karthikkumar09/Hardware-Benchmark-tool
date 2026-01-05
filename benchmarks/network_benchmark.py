"""
Network Benchmark Module
Uses iperf3 for network performance testing
"""

import subprocess
import json
import statistics
from typing import Dict, List


class NetworkBenchmark:
    """Network performance benchmark using iperf3"""
    
    def __init__(self, config: Dict):
        self.server_ip = config.get('server_ip', '127.0.0.1')
        self.port = config.get('port', 5201)
        self.duration = config.get('duration', 10)
        self.protocol = config.get('protocol', 'tcp')  # tcp or udp
    
    def run_single_test(self) -> Dict:
        """Execute a single network benchmark"""
        cmd = [
            'iperf3',
            '-c', self.server_ip,
            '-p', str(self.port),
            '-t', str(self.duration),
            '-J'  # JSON output
        ]
        
        if self.protocol == 'udp':
            cmd.extend(['-u', '-b', '0'])  # UDP with unlimited bandwidth
        
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
            return {'error': 'iperf3 not found. Please install it.'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_output(self, output: str) -> Dict:
        """Parse iperf3 JSON output"""
        try:
            data = json.loads(output)
            
            results = {
                'protocol': self.protocol
            }
            
            # Extract summary data
            if 'end' in data:
                summary = data['end']['sum_sent']
                
                results['bandwidth_mbps'] = summary['bits_per_second'] / 1_000_000
                results['bytes_transferred'] = summary['bytes']
                results['retransmits'] = summary.get('retransmits', 0)
                
                # Extract sender/receiver data
                if 'sum_received' in data['end']:
                    recv = data['end']['sum_received']
                    results['bandwidth_received_mbps'] = recv['bits_per_second'] / 1_000_000
            
            return results
            
        except (json.JSONDecodeError, KeyError) as e:
            return {'error': f'Failed to parse iperf3 output: {e}'}
    
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
            bw = result.get('bandwidth_mbps', 0)
            print(f" {bw:.2f} Mbps")
        
        return self.aggregate_results(all_results)
    
    def aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate multiple benchmark runs"""
        if not results:
            return {}
        
        aggregated = {
            'runs': results,
            'statistics': {}
        }
        
        metrics = ['bandwidth_mbps', 'bandwidth_received_mbps', 'retransmits']
        
        for metric in metrics:
            values = [r.get(metric) for r in results if metric in r and r.get(metric) is not None]
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
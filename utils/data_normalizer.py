"""
Data Normalizer Module
Normalizes benchmark results to comparable scores (0-100 scale)
"""

from typing import Dict, Any


class DataNormalizer:
    """Normalize benchmark results for cross-platform comparison"""
    
    def __init__(self):
        # Reference baselines (adjust based on typical hardware)
        self.baselines = {
            'cpu': {
                'events_per_second': {'min': 100, 'max': 10000, 'higher_better': True}
            },
            'memory': {
                'transfer_rate_mib_sec': {'min': 1000, 'max': 50000, 'higher_better': True}
            },
            'disk': {
                'randread': {
                    'iops': {'min': 100, 'max': 100000, 'higher_better': True}
                },
                'randwrite': {
                    'iops': {'min': 100, 'max': 100000, 'higher_better': True}
                },
                'read': {
                    'bandwidth_kb': {'min': 10000, 'max': 5000000, 'higher_better': True}
                },
                'write': {
                    'bandwidth_kb': {'min': 10000, 'max': 5000000, 'higher_better': True}
                }
            },
            'network': {
                'bandwidth_mbps': {'min': 10, 'max': 10000, 'higher_better': True}
            }
        }
    
    def normalize(self, results: Dict) -> Dict:
        """Normalize all benchmark results"""
        normalized = {}
        
        if 'cpu' in results:
            normalized['cpu'] = self.normalize_cpu(results['cpu'])
        
        if 'memory' in results:
            normalized['memory'] = self.normalize_memory(results['memory'])
        
        if 'disk' in results:
            normalized['disk'] = self.normalize_disk(results['disk'])
        
        if 'network' in results:
            normalized['network'] = self.normalize_network(results['network'])
        
        # Calculate overall score
        normalized['overall_score'] = self.calculate_overall_score(normalized)
        
        return normalized
    
    def normalize_value(self, value: float, min_val: float, max_val: float, 
                       higher_better: bool = True) -> float:
        """
        Normalize a value to 0-100 scale
        """
        if value is None:
            return 0
        
        # Clamp value to min/max range
        clamped = max(min_val, min(max_val, value))
        
        # Normalize to 0-100
        if higher_better:
            normalized = ((clamped - min_val) / (max_val - min_val)) * 100
        else:
            normalized = ((max_val - clamped) / (max_val - min_val)) * 100
        
        return round(normalized, 2)
    
    def normalize_cpu(self, cpu_results: Dict) -> Dict:
        """Normalize CPU benchmark results"""
        if 'error' in cpu_results:
            return cpu_results
        
        stats = cpu_results.get('statistics', {})
        eps = stats.get('events_per_second', {}).get('mean', 0)
        
        baseline = self.baselines['cpu']['events_per_second']
        score = self.normalize_value(eps, baseline['min'], baseline['max'], 
                                     baseline['higher_better'])
        
        return {
            'score': score,
            'raw_value': eps,
            'metric': 'events_per_second',
            'variance': stats.get('events_per_second', {}).get('variance_percent', 0)
        }
    
    def normalize_memory(self, memory_results: Dict) -> Dict:
        """Normalize memory benchmark results"""
        if 'error' in memory_results:
            return memory_results
        
        stats = memory_results.get('statistics', {})
        rate = stats.get('transfer_rate_mib_sec', {}).get('mean', 0)
        
        baseline = self.baselines['memory']['transfer_rate_mib_sec']
        score = self.normalize_value(rate, baseline['min'], baseline['max'], 
                                     baseline['higher_better'])
        
        return {
            'score': score,
            'raw_value': rate,
            'metric': 'transfer_rate_mib_sec',
            'variance': stats.get('transfer_rate_mib_sec', {}).get('variance_percent', 0)
        }
    
    def normalize_disk(self, disk_results: Dict) -> Dict:
        """Normalize disk benchmark results"""
        normalized = {}
        
        for test_type in ['randread', 'randwrite', 'read', 'write']:
            if test_type not in disk_results:
                continue
            
            test_data = disk_results[test_type]
            if 'error' in test_data:
                normalized[test_type] = test_data
                continue
            
            stats = test_data.get('statistics', {})
            
            # For random I/O, use IOPS
            if 'rand' in test_type:
                iops = stats.get('iops', {}).get('mean', 0)
                baseline = self.baselines['disk'][test_type]['iops']
                score = self.normalize_value(iops, baseline['min'], baseline['max'], 
                                            baseline['higher_better'])
                
                normalized[test_type] = {
                    'score': score,
                    'raw_value': iops,
                    'metric': 'iops',
                    'variance': stats.get('iops', {}).get('variance_percent', 0)
                }
            # For sequential I/O, use bandwidth
            else:
                bw = stats.get('bandwidth_kb', {}).get('mean', 0)
                baseline = self.baselines['disk'][test_type]['bandwidth_kb']
                score = self.normalize_value(bw, baseline['min'], baseline['max'], 
                                            baseline['higher_better'])
                
                normalized[test_type] = {
                    'score': score,
                    'raw_value': bw,
                    'metric': 'bandwidth_kb',
                    'variance': stats.get('bandwidth_kb', {}).get('variance_percent', 0)
                }
        
        # Calculate average disk score
        scores = [v['score'] for v in normalized.values() if isinstance(v, dict) and 'score' in v]
        normalized['average_score'] = round(sum(scores) / len(scores), 2) if scores else 0
        
        return normalized
    
    def normalize_network(self, network_results: Dict) -> Dict:
        """Normalize network benchmark results"""
        if 'error' in network_results:
            return network_results
        
        stats = network_results.get('statistics', {})
        bw = stats.get('bandwidth_mbps', {}).get('mean', 0)
        
        baseline = self.baselines['network']['bandwidth_mbps']
        score = self.normalize_value(bw, baseline['min'], baseline['max'], 
                                     baseline['higher_better'])
        
        return {
            'score': score,
            'raw_value': bw,
            'metric': 'bandwidth_mbps',
            'variance': stats.get('bandwidth_mbps', {}).get('variance_percent', 0)
        }
    
    def calculate_overall_score(self, normalized: Dict) -> float:
        """Calculate weighted overall performance score"""
        weights = {
            'cpu': 0.3,
            'memory': 0.2,
            'disk': 0.3,
            'network': 0.2
        }
        
        total_score = 0
        total_weight = 0
        
        for component, weight in weights.items():
            if component in normalized:
                if component == 'disk':
                    score = normalized[component].get('average_score', 0)
                else:
                    score = normalized[component].get('score', 0)
                
                total_score += score * weight
                total_weight += weight
        
        return round(total_score / total_weight, 2) if total_weight > 0 else 0
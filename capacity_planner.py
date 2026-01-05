"""
Capacity Planning Tool
Helps make hardware selection decisions based on workload requirements
"""

import json
from pathlib import Path
from typing import Dict, List
import pandas as pd


class CapacityPlanner:
    """Capacity planning and hardware recommendation engine"""
    
    def __init__(self):
        self.workload_profiles = {
            'web_server': {
                'cpu_weight': 0.35,
                'memory_weight': 0.30,
                'disk_weight': 0.20,
                'network_weight': 0.15,
                'min_scores': {'cpu': 60, 'memory': 50, 'disk': 40, 'network': 50}
            },
            'database': {
                'cpu_weight': 0.30,
                'memory_weight': 0.35,
                'disk_weight': 0.30,
                'network_weight': 0.05,
                'min_scores': {'cpu': 70, 'memory': 80, 'disk': 75, 'network': 30}
            },
            'file_server': {
                'cpu_weight': 0.15,
                'memory_weight': 0.20,
                'disk_weight': 0.50,
                'network_weight': 0.15,
                'min_scores': {'cpu': 40, 'memory': 50, 'disk': 80, 'network': 60}
            },
            'compute_intensive': {
                'cpu_weight': 0.60,
                'memory_weight': 0.25,
                'disk_weight': 0.10,
                'network_weight': 0.05,
                'min_scores': {'cpu': 85, 'memory': 70, 'disk': 40, 'network': 30}
            },
            'general_purpose': {
                'cpu_weight': 0.30,
                'memory_weight': 0.25,
                'disk_weight': 0.25,
                'network_weight': 0.20,
                'min_scores': {'cpu': 60, 'memory': 60, 'disk': 60, 'network': 50}
            }
        }
        
        self.systems = []
    
    def load_system(self, result_path: str, system_name: str, cost: float = None):
        """Load a system's benchmark results"""
        result_path = Path(result_path)
        norm_file = result_path / "normalized_results.json"
        
        if not norm_file.exists():
            print(f"Error: {norm_file} not found")
            return False
        
        with open(norm_file, 'r') as f:
            normalized = json.load(f)
        
        self.systems.append({
            'name': system_name,
            'normalized': normalized,
            'cost': cost
        })
        
        print(f"✓ Loaded: {system_name}")
        return True
    
    def recommend_for_workload(self, workload_type: str) -> List[Dict]:
        """Recommend systems for specific workload"""
        if workload_type not in self.workload_profiles:
            print(f"Unknown workload type: {workload_type}")
            print(f"Available: {list(self.workload_profiles.keys())}")
            return []
        
        profile = self.workload_profiles[workload_type]
        recommendations = []
        
        for system in self.systems:
            score = self.calculate_workload_score(system, profile)
            meets_requirements = self.check_requirements(system, profile)
            
            recommendations.append({
                'system': system['name'],
                'workload_score': score,
                'meets_requirements': meets_requirements,
                'cost': system.get('cost'),
                'cost_performance_ratio': score / system.get('cost') if system.get('cost') else None
            })
        
        # Sort by workload score
        recommendations.sort(key=lambda x: x['workload_score'], reverse=True)
        
        return recommendations
    
    def calculate_workload_score(self, system: Dict, profile: Dict) -> float:
        """Calculate weighted score for workload"""
        norm = system['normalized']
        
        cpu_score = norm.get('cpu', {}).get('score', 0)
        mem_score = norm.get('memory', {}).get('score', 0)
        disk_score = norm.get('disk', {}).get('average_score', 0)
        net_score = norm.get('network', {}).get('score', 0)
        
        workload_score = (
            cpu_score * profile['cpu_weight'] +
            mem_score * profile['memory_weight'] +
            disk_score * profile['disk_weight'] +
            net_score * profile['network_weight']
        )
        
        return round(workload_score, 2)
    
    def check_requirements(self, system: Dict, profile: Dict) -> bool:
        """Check if system meets minimum requirements"""
        norm = system['normalized']
        min_scores = profile['min_scores']
        
        cpu_score = norm.get('cpu', {}).get('score', 0)
        mem_score = norm.get('memory', {}).get('score', 0)
        disk_score = norm.get('disk', {}).get('average_score', 0)
        net_score = norm.get('network', {}).get('score', 0)
        
        return (
            cpu_score >= min_scores['cpu'] and
            mem_score >= min_scores['memory'] and
            disk_score >= min_scores['disk'] and
            net_score >= min_scores['network']
        )
    
    def generate_recommendation_report(self, workload_type: str, output_file: str):
        """Generate detailed recommendation report"""
        recommendations = self.recommend_for_workload(workload_type)
        
        if not recommendations:
            print("No recommendations available")
            return
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"CAPACITY PLANNING REPORT - {workload_type.upper()}")
        lines.append("=" * 80)
        lines.append("")
        
        # Workload profile
        profile = self.workload_profiles[workload_type]
        lines.append("WORKLOAD PROFILE")
        lines.append("-" * 80)
        lines.append(f"CPU Weight: {profile['cpu_weight']*100:.0f}%")
        lines.append(f"Memory Weight: {profile['memory_weight']*100:.0f}%")
        lines.append(f"Disk Weight: {profile['disk_weight']*100:.0f}%")
        lines.append(f"Network Weight: {profile['network_weight']*100:.0f}%")
        lines.append("")
        
        lines.append("MINIMUM REQUIREMENTS")
        lines.append("-" * 80)
        for component, score in profile['min_scores'].items():
            lines.append(f"{component.upper()}: {score}/100")
        lines.append("")
        
        # Recommendations
        lines.append("SYSTEM RECOMMENDATIONS (Ranked)")
        lines.append("-" * 80)
        
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"\n{i}. {rec['system']}")
            lines.append(f"   Workload Score: {rec['workload_score']:.2f}/100")
            lines.append(f"   Meets Requirements: {'✓ YES' if rec['meets_requirements'] else '✗ NO'}")
            
            if rec['cost']:
                lines.append(f"   Cost: ${rec['cost']:,.2f}")
                lines.append(f"   Cost/Performance: ${rec['cost']/rec['workload_score']:.2f} per point")
        
        # Best value recommendation
        lines.append("\n" + "=" * 80)
        lines.append("RECOMMENDATION SUMMARY")
        lines.append("=" * 80)
        
        best_performance = recommendations[0]
        lines.append(f"\n🏆 Best Performance: {best_performance['system']}")
        lines.append(f"   Score: {best_performance['workload_score']:.2f}/100")
        
        # Find best value if costs are provided
        with_cost = [r for r in recommendations if r['cost_performance_ratio']]
        if with_cost:
            best_value = min(with_cost, key=lambda x: x['cost_performance_ratio'])
            lines.append(f"\n💰 Best Value: {best_value['system']}")
            lines.append(f"   Score: {best_value['workload_score']:.2f}/100")
            lines.append(f"   Cost/Performance: ${best_value['cost_performance_ratio']:.2f} per point")
        
        # Systems that don't meet requirements
        failed = [r for r in recommendations if not r['meets_requirements']]
        if failed:
            lines.append(f"\n⚠️  Systems NOT Meeting Requirements: {len(failed)}")
            for f in failed:
                lines.append(f"   - {f['system']}")
        
        lines.append("\n" + "=" * 80)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✓ Recommendation report saved: {output_file}")
    
    def compare_all_workloads(self, output_file: str):
        """Compare systems across all workload types"""
        comparison = []
        
        for workload in self.workload_profiles.keys():
            recommendations = self.recommend_for_workload(workload)
            
            for rec in recommendations:
                comparison.append({
                    'Workload': workload,
                    'System': rec['system'],
                    'Score': rec['workload_score'],
                    'Meets_Requirements': rec['meets_requirements'],
                    'Cost': rec['cost']
                })
        
        # Create DataFrame
        df = pd.DataFrame(comparison)
        
        # Pivot to show systems vs workloads
        pivot = df.pivot(index='System', columns='Workload', values='Score')
        
        # Save to CSV
        csv_file = output_file.replace('.txt', '_matrix.csv')
        pivot.to_csv(csv_file, float_format='%.2f')
        
        print(f"✓ Workload comparison matrix saved: {csv_file}")
        
        # Also save detailed comparison
        df.to_csv(output_file.replace('.txt', '_detailed.csv'), index=False, float_format='%.2f')
        print(f"✓ Detailed comparison saved: {output_file.replace('.txt', '_detailed.csv')}")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hardware Capacity Planning Tool')
    parser.add_argument('--workload', '-w', 
                       choices=['web_server', 'database', 'file_server', 'compute_intensive', 'general_purpose'],
                       required=True,
                       help='Workload type')
    parser.add_argument('--systems', '-s', nargs='+', required=True,
                       help='System result directories')
    parser.add_argument('--names', '-n', nargs='+',
                       help='System names')
    parser.add_argument('--costs', '-c', nargs='+', type=float,
                       help='System costs')
    parser.add_argument('--output', '-o', default='capacity_plan.txt',
                       help='Output file')
    
    args = parser.parse_args()
    
    planner = CapacityPlanner()
    
    # Load systems
    for i, sys_dir in enumerate(args.systems):
        name = args.names[i] if args.names and i < len(args.names) else f"System_{i+1}"
        cost = args.costs[i] if args.costs and i < len(args.costs) else None
        planner.load_system(sys_dir, name, cost)
    
    # Generate recommendation
    planner.generate_recommendation_report(args.workload, args.output)


if __name__ == "__main__":
    main()
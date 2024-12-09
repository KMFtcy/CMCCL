import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from topos.fattree_with_broadcast import create_fattree_network_with_broadcast
from collective.ring_allreduce import RingAllReduce
from collective.tree_allreduce import TreeAllReduce, BinaryTreeAllReduce, BroadcastTreeAllReduce
import matplotlib.pyplot as plt

def calculate_nodes(k):
    """Calculate number of nodes in a k-ary FatTree"""
    core = (k//2)**2
    aggr = k * (k//2)
    edge = k * (k//2)
    hosts = k**3//4
    total = core + aggr + edge + hosts
    return {
        'core': core,
        'aggregation': aggr,
        'edge': edge,
        'hosts': hosts,
        'total': total
    }

def run_allreduce_test(k: int, data_size: int, algorithm: str):
    """Run AllReduce test with specified parameters"""
    env = simpy.Environment()
    network = create_fattree_network_with_broadcast(k, env)
    
    hosts = sorted([n for n in network.nodes() if network.nodes[n]["type"] == "host"])
    
    if algorithm == "ring":
        allreduce = RingAllReduce(env, network, hosts, data_size)
    elif algorithm == "binary_tree":
        allreduce = BinaryTreeAllReduce(env, network, hosts, data_size)
    else:  # broadcast_tree
        allreduce = BroadcastTreeAllReduce(env, network, hosts, data_size)
    
    start_time = env.now
    env.process(allreduce.reduce())  # Single process for all algorithms
    env.run()
    end_time = env.now
    total_time = end_time - start_time
    
    n_workers = len(hosts)
    if algorithm == "ring":
        total_data = data_size * 2 * (n_workers - 1)
    else:
        total_data = data_size * (2 * n_workers - 2)
    
    return {
        'latency': total_time,
        'bandwidth': total_data / total_time if total_time > 0 else 0,
        'total_data': total_data
    }

def plot_results(k_values, data_size, results):
    """Plot the results for a specific data size"""
    plt.figure(figsize=(12, 8))
    
    algorithms = ['ring', 'binary_tree', 'broadcast_tree']
    styles = [
        {'color': 'blue', 'marker': 'o', 'linestyle': '-'},
        {'color': 'green', 'marker': '^', 'linestyle': '-'},
        {'color': '#800080', 'marker': 'D', 'linestyle': '-'}
    ]
    
    for alg, style in zip(algorithms, styles):
        latencies = [results[k][alg]['latency'] for k in k_values]
        plt.plot(k_values, latencies, 
                color=style['color'],
                marker=style['marker'],
                linestyle=style['linestyle'],
                label=f'{alg.replace("_", " ").title()}',
                linewidth=2, 
                markersize=8)
    
    plt.title(f'AllReduce Latency Comparison (Data Size: {data_size/1e6:.0f}MB)', fontsize=14)
    plt.xlabel('k (FatTree parameter)', fontsize=12)
    plt.ylabel('Latency (simulation time)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    plt.xticks(k_values)
    
    plt.grid(True, which='minor', linestyle=':', alpha=0.4)
    plt.minorticks_on()
    plt.tight_layout()
    
    os.makedirs('logs', exist_ok=True)
    plt.savefig(f'logs/allreduce_comparison_{data_size/1e6:.0f}MB.png', dpi=300)
    plt.close()

def main():
    k_values = [4, 6, 8]  # FatTree parameter k
    data_sizes = [10e6, 100e6, 1e9]  # 10MB, 100MB, 1GB
    algorithms = ['ring', 'binary_tree', 'broadcast_tree']
    
    results = {k: {alg: {} for alg in algorithms} for k in k_values}
    
    for k in k_values:
        nodes = calculate_nodes(k)
        print(f"\nTesting FatTree with k={k} ({nodes['hosts']} hosts)")
        
        for data_size in data_sizes:
            print(f"\nTesting with data size: {data_size/1e6:.0f}MB")
            
            for algorithm in algorithms:
                print(f"Testing {algorithm} algorithm...")
                results[k][algorithm] = run_allreduce_test(k, int(data_size), algorithm)
                print(f"Latency: {results[k][algorithm]['latency']:.2f}")
                print(f"Bandwidth: {results[k][algorithm]['bandwidth']:.2e}")
    
    for data_size in data_sizes:
        plot_results(k_values, data_size, results)

if __name__ == "__main__":
    main() 
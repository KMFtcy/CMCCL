import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from topos.star import create_star_network
from collective.ps_allreduce import PSAllReduce

def run_single_test(num_nodes: int, data_size: int = 1024*1024) -> Tuple[float, float]:
    """Run a single PS-AllReduce test with specified number of nodes
    
    Args:
        num_nodes: Number of worker nodes (excluding switch)
        data_size: Size of data to be transferred (bytes)
    
    Returns:
        Tuple[float, float]: (latency, bandwidth)
    """
    # Create simulation environment
    env = simpy.Environment()
    
    # Create star network with num_nodes + 1 nodes (including switch)
    network = create_star_network(
        env=env,
        num_nodes=num_nodes + 1,  # +1 for switch
        bandwidth=100,    # 100Mbps
        latency=5,        # 5ms
        processing_delay=0.1
    )
    
    # Start node processes
    for node in network.nodes.values():
        env.process(node.receive())
    
    # Create and run PS-AllReduce
    ps_allreduce = PSAllReduce(
        env=env,
        network=network,
        ps_node_id=0,     # Switch is PS
        data_size=data_size
    )
    
    # Run simulation
    start_time = env.now
    env.process(ps_allreduce.run())
    env.run(until=100)  # Longer timeout for larger networks
    end_time = env.now
    
    # Calculate metrics
    latency = end_time - start_time
    total_data = data_size * num_nodes * 2  # Data sent up and down
    bandwidth = (total_data * 8 / 1e6) / latency  # Mbps
    
    return latency, bandwidth

def run_scalability_test():
    """Run scalability test with increasing number of nodes"""
    # node_counts = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
    node_counts = [4, 8, 16, 32]
    results: List[Tuple[float, float]] = []
    
    print("Starting scalability test...")
    for num_nodes in node_counts:
        print(f"\nTesting with {num_nodes} worker nodes...")
        latency, bandwidth = run_single_test(num_nodes)
        results.append((latency, bandwidth))
        print(f"Latency: {latency:.2f} time units")
        print(f"Bandwidth: {bandwidth:.2f} Mbps")
    
    # Plot results
    latencies = [r[0] for r in results]
    bandwidths = [r[1] for r in results]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Plot latency
    ax1.plot(node_counts, latencies, 'b-o', linewidth=2)
    ax1.set_xscale('log', base=2)
    ax1.set_xlabel('Number of Worker Nodes')
    ax1.set_ylabel('Latency (time units)')
    ax1.set_title('PS-AllReduce Latency Scaling')
    ax1.grid(True)
    
    # Plot bandwidth
    ax2.plot(node_counts, bandwidths, 'r-o', linewidth=2)
    ax2.set_xscale('log', base=2)
    ax2.set_xlabel('Number of Worker Nodes')
    ax2.set_ylabel('Effective Bandwidth (Mbps)')
    ax2.set_title('PS-AllReduce Bandwidth Scaling')
    ax2.grid(True)
    
    # Add some styling
    for ax in [ax1, ax2]:
        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.set_axisbelow(True)
        
    plt.tight_layout()
    plt.savefig('ps_allreduce_scalability.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    with open('ps_allreduce_scalability.txt', 'w') as f:
        f.write("Nodes\tLatency\tBandwidth\n")
        for i, n in enumerate(node_counts):
            f.write(f"{n}\t{latencies[i]:.2f}\t{bandwidths[i]:.2f}\n")
    
    print("\nResults have been saved to:")
    print("- ps_allreduce_scalability.png")
    print("- ps_allreduce_scalability.txt")

if __name__ == "__main__":
    run_scalability_test() 
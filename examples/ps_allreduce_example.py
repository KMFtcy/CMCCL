import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from collective.ps_allreduce import UnicastPSAllReduce, BroadcastPSAllReduce
from topos.star_with_broadcast import create_star_network_with_broadcast
import matplotlib.pyplot as plt
import time

def run_ps_allreduce_test(num_nodes: int, data_size: int, use_broadcast: bool = False):
    """Run a PS-AllReduce test with specified parameters"""
    # Create environment and network
    env = simpy.Environment()
    network = create_star_network_with_broadcast(num_nodes, env)
    
    # Define workers and server
    server_id = 0
    workers = list(range(1, num_nodes))  # All nodes except server
    
    # Create PS-AllReduce instance
    ps_allreduce = BroadcastPSAllReduce(env, network, workers, server_id, data_size) if use_broadcast \
        else UnicastPSAllReduce(env, network, workers, server_id, data_size)
    
    # Start time
    start_time = env.now
    
    # Create processes for each worker
    for worker_id in workers:
        env.process(ps_allreduce.reduce(worker_id))
    
    # Run simulation
    env.run()
    
    # Return total time
    return env.now - start_time

def compare_methods():
    """Compare unicast and broadcast methods with different parameters"""
    # Test parameters
    node_counts = [5, 9, 17, 33]  # 4+1, 8+1, 16+1, 32+1 nodes
    data_sizes = [1e6, 10e6, 100e6]  # 1MB, 10MB, 100MB
    
    results = {
        'unicast': {},
        'broadcast': {}
    }
    
    # Run tests
    for data_size in data_sizes:
        results['unicast'][data_size] = []
        results['broadcast'][data_size] = []
        
        for num_nodes in node_counts:
            print(f"\nTesting with {num_nodes} nodes and {data_size/1e6}MB data size")
            
            # Test unicast
            print("Testing unicast method...")
            time_unicast = run_ps_allreduce_test(num_nodes, int(data_size), use_broadcast=False)
            results['unicast'][data_size].append(time_unicast)
            
            # Test broadcast
            print("Testing broadcast method...")
            time_broadcast = run_ps_allreduce_test(num_nodes, int(data_size), use_broadcast=True)
            results['broadcast'][data_size].append(time_broadcast)
    
    # Plot results
    plot_results(node_counts, data_sizes, results)

def plot_results(node_counts, data_sizes, results):
    """Plot the comparison results"""
    plt.figure(figsize=(15, 5))
    
    for idx, data_size in enumerate(data_sizes, 1):
        plt.subplot(1, 3, idx)
        
        plt.plot(node_counts, results['unicast'][data_size], 'b-o', label='Unicast')
        plt.plot(node_counts, results['broadcast'][data_size], 'r-o', label='Broadcast')
        
        plt.title(f'Data Size: {data_size/1e6}MB')
        plt.xlabel('Number of Nodes')
        plt.ylabel('Simulation Time')
        plt.grid(True)
        plt.legend()
    
    plt.tight_layout()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    plt.savefig('logs/ps_allreduce_comparison.png')
    plt.close()

    # Also save numerical results
    print("\nNumerical Results:")
    print("\nUnicast method:")
    for data_size in data_sizes:
        print(f"\nData size: {data_size/1e6}MB")
        for nodes, time in zip(node_counts, results['unicast'][data_size]):
            print(f"Nodes: {nodes}, Time: {time}")
    
    print("\nBroadcast method:")
    for data_size in data_sizes:
        print(f"\nData size: {data_size/1e6}MB")
        for nodes, time in zip(node_counts, results['broadcast'][data_size]):
            print(f"Nodes: {nodes}, Time: {time}")

if __name__ == "__main__":
    compare_methods() 
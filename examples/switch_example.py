import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from topos.star_with_broadcast import create_star_network_with_broadcast
from network import send
import matplotlib.pyplot as plt
import time
import numpy as np
from collections import defaultdict

def unicast_broadcast(env: simpy.Environment, network, src_id: int, num_nodes: int):
    """Broadcast by sending unicast messages to each node"""
    start_time = env.now
    sent_size = 0
    for dst_id in range(1, num_nodes):
        if dst_id != src_id:
            message = Message(
                source_id=src_id,
                target_id=dst_id,
                data=f"Unicast broadcast from {src_id} to {dst_id}",
                msg_type=MessageType.BROADCAST,
                timestamp=env.now
            )
            send(env, network, src_id, dst_id, message)
            sent_size += 1.5e6  # packet size
            yield env.timeout(1)  # Wait a bit between sends
    return env.now - start_time, sent_size

def direct_broadcast(env: simpy.Environment, network, src_id: int):
    """Broadcast using the broadcast mechanism"""
    start_time = env.now
    message = Message(
        source_id=src_id,
        target_id=-1,
        data=f"Direct broadcast from {src_id}",
        msg_type=MessageType.BROADCAST,
        timestamp=env.now
    )
    send(env, network, src_id, -1, message, is_broadcast=True)
    yield env.timeout(1)
    return env.now - start_time, 1.5e6  # Single packet size

def run_test(num_nodes: int):
    """Run test for a specific network size"""
    env = simpy.Environment()
    network = create_star_network_with_broadcast(num_nodes, env)
    results = {}

    # Test unicast broadcast
    print(f"\nTesting unicast broadcast with {num_nodes} nodes:")
    unicast_process = env.process(unicast_broadcast(env, network, src_id=2, num_nodes=num_nodes))
    env.run(until=unicast_process)
    sim_time, sent_size = unicast_process.value
    results['unicast'] = {
        'latency': sim_time,  # Use simulation time instead of real time
        'bandwidth': sent_size / sim_time if sim_time > 0 else 0
    }

    # Reset environment for direct broadcast test
    env = simpy.Environment()
    network = create_star_network_with_broadcast(num_nodes, env)

    # Test direct broadcast
    print(f"Testing direct broadcast with {num_nodes} nodes:")
    broadcast_process = env.process(direct_broadcast(env, network, src_id=2))
    env.run(until=broadcast_process)
    sim_time, sent_size = broadcast_process.value
    results['broadcast'] = {
        'latency': sim_time,  # Use simulation time instead of real time
        'bandwidth': sent_size / sim_time if sim_time > 0 else 0
    }

    return results

def plot_results(node_counts, results):
    """Plot and save the results"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Prepare data for plotting
    metrics = {
        'latency': {'title': 'Simulation Latency vs Network Size', 'ylabel': 'Latency (simulation time)'},
        'bandwidth': {'title': 'Bandwidth vs Network Size', 'ylabel': 'Bandwidth (bytes/simulation time)'}
    }

    for metric, info in metrics.items():
        plt.figure(figsize=(10, 6))
        
        # Plot data for both methods
        unicast_data = [results[n]['unicast'][metric] for n in node_counts]
        broadcast_data = [results[n]['broadcast'][metric] for n in node_counts]
        
        plt.plot(node_counts, unicast_data, 'b-o', label='Unicast Broadcast')
        plt.plot(node_counts, broadcast_data, 'r-o', label='Direct Broadcast')
        
        plt.title(info['title'])
        plt.xlabel('Number of Nodes')
        plt.ylabel(info['ylabel'])
        plt.grid(True)
        plt.legend()
        
        # Save the plot
        plt.savefig(f'logs/{metric}_comparison.png')
        plt.close()

def main():
    # Test different network sizes
    node_counts = [5, 9, 17, 33]  # 4+1, 8+1, 16+1, 32+1 nodes
    all_results = {}
    
    for num_nodes in node_counts:
        print(f"\nTesting network with {num_nodes} nodes")
        all_results[num_nodes] = run_test(num_nodes)

    # Plot and save results
    plot_results(node_counts, all_results)

if __name__ == "__main__":
    main() 
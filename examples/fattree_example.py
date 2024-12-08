import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from topos.fattree_with_broadcast import create_fattree_network_with_broadcast
from network import send
import matplotlib.pyplot as plt
import time

def unicast_broadcast(env: simpy.Environment, network, src_id: str, hosts: set):
    """Broadcast by sending unicast messages to each host"""
    start_time = env.now
    sent_size = 0
    for dst_id in hosts:
        if dst_id != src_id:
            message = Message(
                source_id=src_id,
                target_id=dst_id,
                data=f"Unicast broadcast from {src_id} to {dst_id}",
                msg_type=MessageType.BROADCAST,
                timestamp=env.now
            )
            send(env, network, src_id, dst_id, message)
            sent_size += 1.5e9  # packet size
            yield env.timeout(1)  # Wait a bit between sends
    return env.now - start_time, sent_size

def direct_broadcast(env: simpy.Environment, network, src_id: str):
    """Broadcast using the broadcast mechanism"""
    start_time = env.now
    message = Message(
        source_id=src_id,
        target_id=-1,  # Broadcast address
        data=f"Direct broadcast from {src_id}",
        msg_type=MessageType.BROADCAST,
        timestamp=env.now
    )
    send(env, network, src_id, -1, message, is_broadcast=True)
    yield env.timeout(1)
    return env.now - start_time, 1.5e9  # Single packet size

def run_test(k: int):
    """Run test for FatTree with parameter k"""
    # Create environment and network
    env = simpy.Environment()
    network = create_fattree_network_with_broadcast(k, env)
    
    # Get all hosts
    hosts = {n for n in network.nodes() if network.nodes[n]["type"] == "host"}
    src_id = "h0"  # Use first host as source
    
    results = {}

    # Test unicast broadcast
    print(f"\nTesting unicast broadcast in FatTree (k={k}):")
    unicast_process = env.process(unicast_broadcast(env, network, src_id, hosts))
    env.run()
    sim_time, sent_size = unicast_process.value
    results['unicast'] = {
        'latency': sim_time,
        'bandwidth': sent_size / sim_time if sim_time > 0 else 0
    }

    # Reset environment for direct broadcast test
    env = simpy.Environment()
    network = create_fattree_network_with_broadcast(k, env)

    # Test direct broadcast
    print(f"\nTesting direct broadcast in FatTree (k={k}):")
    broadcast_process = env.process(direct_broadcast(env, network, src_id))
    env.run()
    sim_time, sent_size = broadcast_process.value
    results['broadcast'] = {
        'latency': sim_time,
        'bandwidth': sent_size / sim_time if sim_time > 0 else 0
    }

    return results

def plot_results(k_values, all_results):
    """Plot the comparison results"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Prepare data for plotting
    metrics = {
        'latency': {'title': 'Latency vs Network Size in FatTree', 'ylabel': 'Latency (simulation time)'},
        'bandwidth': {'title': 'Bandwidth vs Network Size in FatTree', 'ylabel': 'Bandwidth (bytes/simulation time)'}
    }

    for metric, info in metrics.items():
        plt.figure(figsize=(12, 8))  # 增加图表大小
        
        # Extract data for plotting
        unicast_data = [all_results[k]['unicast'][metric] for k in k_values]
        broadcast_data = [all_results[k]['broadcast'][metric] for k in k_values]
        
        # Create line plots with larger markers and lines
        plt.plot(k_values, unicast_data, 'b-o', label='Unicast', linewidth=2, markersize=8)
        plt.plot(k_values, broadcast_data, 'r-o', label='Broadcast', linewidth=2, markersize=8)
        
        plt.title(info['title'], fontsize=14)
        plt.xlabel('k (FatTree parameter)', fontsize=12)
        plt.ylabel(info['ylabel'], fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(fontsize=12)
        
        # 设置 x 轴刻度为实际的 k 值
        plt.xticks(k_values, k_values)
        
        # 添加次网格线
        plt.grid(True, which='minor', linestyle=':', alpha=0.4)
        plt.minorticks_on()
        
        # 调整布局
        plt.tight_layout()
        
        # Save the plot with high DPI
        plt.savefig(f'logs/fattree_{metric}_comparison.png', dpi=300)
        plt.close()

    # Print numerical results with better formatting
    print("\nNumerical Results:")
    for k in k_values:
        print(f"\nk = {k}:")
        for method in ['unicast', 'broadcast']:
            print(f"\n{method.capitalize()} method:")
            for metric in metrics:
                print(f"{metric}: {all_results[k][method][metric]:.2f}")

def main():
    # Test different FatTree sizes
    k_values = [4, 8,  16]  # k must be even
    all_results = {}
    
    for k in k_values:
        print(f"\nTesting FatTree topology with k={k}")
        all_results[k] = run_test(k)

    # Plot and save results
    plot_results(k_values, all_results)

if __name__ == "__main__":
    main() 
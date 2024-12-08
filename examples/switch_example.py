import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
import matplotlib.pyplot as plt
from message import Message, MessageType
from node import Node, SwitchNode, EndNode
from topos.star import create_star_network

def unicast_process(env: simpy.Environment, node: Node, network, done_event):
    """Process for point-to-point transmission test"""
    env.process(node.receive())
    
    if node.node_id == 1:
        yield env.timeout(1)
        print("Node 1 starts unicast messages")
        
        for target_id in range(2, len(network.nodes)):
            print(f"Time {env.now:.2f}: Node 1 sending to Node {target_id}")
            yield from network.transmit(1, target_id, f"Unicast to Node {target_id}", MessageType.DATA)
            print(f"Time {env.now:.2f}: Completed sending to Node {target_id}")
        
        print(f"Time {env.now:.2f}: Node 1 completed all unicast transmissions")
        done_event.succeed()

def broadcast_process(env: simpy.Environment, node: Node, network, done_event):
    """Process for broadcast transmission test"""
    env.process(node.receive())
    
    if node.node_id == 1:
        yield env.timeout(1)
        print("Node 1 starts broadcast message")
        
        print(f"Time {env.now:.2f}: Node 1 broadcasting to all nodes")
        yield from network.transmit(1, 0, "Broadcast message", MessageType.BROADCAST)
        print(f"Time {env.now:.2f}: Completed broadcasting")
        
        done_event.succeed()

def run_test(num_nodes: int, is_broadcast: bool):
    """Run test with specified number of nodes and transmission type"""
    env = simpy.Environment()
    done_event = env.event()
    
    network = create_star_network(
        env=env,
        num_nodes=num_nodes + 1,
        bandwidth=100,
        latency=5,
        processing_delay=0.1
    )
    
    start_time = env.now
    process_func = broadcast_process if is_broadcast else unicast_process
    
    for node in network.nodes.values():
        env.process(process_func(env, node, network, done_event))
    
    env.run(until=done_event)
    end_time = env.now
    
    total_time = end_time - start_time - 1
    avg_time = total_time / (num_nodes - 2)
    
    # Print statistics
    print(f"\nResults for {num_nodes} nodes ({'Broadcast' if is_broadcast else 'Unicast'}):")
    print(f"Total time: {total_time:.2f} time units")
    print(f"Average time per message: {avg_time:.2f} time units")
    print("Message counts:")
    for node in network.nodes.values():
        node_type = "Switch" if isinstance(node, SwitchNode) else "Node"
        print(f"{node_type} {node.node_id} received {node.messages_received} messages")
    print("-" * 50)
    
    return total_time, avg_time

def main():
    print("Starting switch transmission tests...")
    node_counts = [4, 8, 16, 32]
    
    # Store results
    results = {
        'unicast': {'total': [], 'avg': []},
        'broadcast': {'total': [], 'avg': []}
    }
    
    # Run tests
    for num_nodes in node_counts:
        # Unicast test
        total_time, avg_time = run_test(num_nodes, False)
        results['unicast']['total'].append(total_time)
        results['unicast']['avg'].append(avg_time)
        
        # Broadcast test
        total_time, avg_time = run_test(num_nodes, True)
        results['broadcast']['total'].append(total_time)
        results['broadcast']['avg'].append(avg_time)
    
    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot total latencies
    ax1.plot(node_counts, results['unicast']['total'], 'b-o', label='Unicast')
    ax1.plot(node_counts, results['broadcast']['total'], 'r-o', label='Broadcast')
    ax1.set_xscale('log', base=2)
    ax1.set_xticks(node_counts)
    ax1.set_xticklabels(node_counts)
    ax1.set_xlabel('Number of Nodes (log2 scale)')
    ax1.set_ylabel('Total Time (time units)')
    ax1.set_title('Total Transmission Time')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot average latencies
    ax2.plot(node_counts, results['unicast']['avg'], 'b-o', label='Unicast')
    ax2.plot(node_counts, results['broadcast']['avg'], 'r-o', label='Broadcast')
    ax2.set_xscale('log', base=2)
    ax2.set_xticks(node_counts)
    ax2.set_xticklabels(node_counts)
    ax2.set_xlabel('Number of Nodes (log2 scale)')
    ax2.set_ylabel('Time per Message (time units)')
    ax2.set_title('Average Time per Message')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Create bar plots for comparison
    width = 0.35
    x = range(len(node_counts))
    
    # Total time comparison
    ax3.bar([i - width/2 for i in x], results['unicast']['total'], width, label='Unicast')
    ax3.bar([i + width/2 for i in x], results['broadcast']['total'], width, label='Broadcast')
    ax3.set_xticks(x)
    ax3.set_xticklabels(node_counts)
    ax3.set_xlabel('Number of Nodes')
    ax3.set_ylabel('Total Time (time units)')
    ax3.set_title('Total Time Comparison')
    ax3.legend()
    
    # Average time comparison
    ax4.bar([i - width/2 for i in x], results['unicast']['avg'], width, label='Unicast')
    ax4.bar([i + width/2 for i in x], results['broadcast']['avg'], width, label='Broadcast')
    ax4.set_xticks(x)
    ax4.set_xticklabels(node_counts)
    ax4.set_xlabel('Number of Nodes')
    ax4.set_ylabel('Time per Message (time units)')
    ax4.set_title('Average Time Comparison')
    ax4.legend()
    
    plt.tight_layout()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Save results
    plt.savefig('logs/switch_test_results.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    with open('logs/switch_test_results.txt', 'w') as f:
        f.write("Nodes\tUnicast_Total\tUnicast_Avg\tBroadcast_Total\tBroadcast_Avg\n")
        for i, n in enumerate(node_counts):
            f.write(f"{n}\t{results['unicast']['total'][i]:.2f}\t"
                   f"{results['unicast']['avg'][i]:.2f}\t"
                   f"{results['broadcast']['total'][i]:.2f}\t"
                   f"{results['broadcast']['avg'][i]:.2f}\n")

if __name__ == "__main__":
    main() 
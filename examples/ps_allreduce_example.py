import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
import matplotlib.pyplot as plt
from message import Message, MessageType
from node import Node, SwitchNode, EndNode
from topos.star import create_star_network
from collective.ps_allreduce import BroadcastPSAllReduce, UnicastPSAllReduce

def run_test(num_nodes: int, use_broadcast: bool, data_size: int = 1024*1024):
    """Run a single PS-AllReduce test"""
    env = simpy.Environment()
    done_event = env.event()  # Add completion event
    
    # Create network
    network = create_star_network(
        env=env,
        num_nodes=num_nodes + 1,
        bandwidth=100,
        latency=5,
        processing_delay=0.1
    )
    
    # Start node processes
    for node in network.nodes.values():
        env.process(node.receive())
    
    # Create and run PS-AllReduce
    ps_class = BroadcastPSAllReduce if use_broadcast else UnicastPSAllReduce
    ps_allreduce = ps_class(
        env=env,
        network=network,
        ps_node_id=0,
        data_size=data_size
    )
    
    # Run simulation
    start_time = env.now
    
    def ps_process():
        yield from ps_allreduce.run()
        done_event.succeed()  # Signal completion
        
    env.process(ps_process())
    env.run(until=done_event)  # Run until done_event is triggered
    end_time = env.now
    
    return end_time - start_time, network.nodes  # Return nodes for statistics

def main():
    node_counts = [4, 8, 16, 32]
    results = {'broadcast': [], 'unicast': []}
    
    # Run tests
    for num_nodes in node_counts:
        print(f"\nTesting with {num_nodes} nodes:")
        
        # Test broadcast version
        print("\nBroadcast version:")
        time_broadcast, nodes = run_test(num_nodes, True)
        results['broadcast'].append(time_broadcast)
        
        # Print message counts for broadcast
        print("\nBroadcast message counts:")
        for node in nodes.values():
            node_type = "PS" if node.node_id == 0 else "Worker"
            print(f"{node_type} {node.node_id} received {node.messages_received} messages")
        
        # Test unicast version
        print("\nUnicast version:")
        time_unicast, nodes = run_test(num_nodes, False)
        results['unicast'].append(time_unicast)
        
        # Print message counts for unicast
        print("\nUnicast message counts:")
        for node in nodes.values():
            node_type = "PS" if node.node_id == 0 else "Worker"
            print(f"{node_type} {node.node_id} received {node.messages_received} messages")
    
    # Plot results
    plt.figure(figsize=(10, 5))
    plt.plot(node_counts, results['broadcast'], 'b-o', label='Broadcast')
    plt.plot(node_counts, results['unicast'], 'r-o', label='Unicast')
    plt.xscale('log', base=2)
    plt.xticks(node_counts, node_counts)
    plt.xlabel('Number of Nodes (log2 scale)')
    plt.ylabel('Total Time (time units)')
    plt.title('PS-AllReduce Performance Comparison')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save results
    os.makedirs('logs', exist_ok=True)
    plt.savefig('logs/ps_allreduce_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    with open('logs/ps_allreduce_comparison.txt', 'w') as f:
        f.write("Nodes\tBroadcast\tUnicast\n")
        for i, n in enumerate(node_counts):
            f.write(f"{n}\t{results['broadcast'][i]:.2f}\t{results['unicast'][i]:.2f}\n")

if __name__ == "__main__":
    main() 
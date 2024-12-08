import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from channel import Channel
from node import RingNode

def create_ring_network(env: simpy.Environment, num_nodes: int):
    """Create ring network"""
    nodes = []
    channels = {}
    
    # Create nodes
    for i in range(num_nodes):
        node = RingNode(
            env=env,
            node_id=i,
            initial_data=0,
            processing_delay=0.1,
            total_nodes=num_nodes
        )
        nodes.append(node)
    
    # Create communication channels and connect nodes
    for i in range(num_nodes):
        next_node = (i + 1) % num_nodes
        # Create channel from current node to next node
        channel = Channel(
            env=env,
            bandwidth=100,  # 100Mbps
            latency=5,      # 5ms
            packet_loss_rate=0.05  # 5% packet loss rate
        )
        channels[(i, next_node)] = channel
        nodes[i].add_neighbor(next_node, nodes[next_node], channel)
    
    return nodes

def node_process(env: simpy.Environment, node: RingNode):
    """Main process for each node"""
    # Start message receiving process
    env.process(node.receive())
    
    if node.node_id == 0:  # Let node 0 initiate the message
        # Wait a bit to ensure all nodes are started
        yield env.timeout(1)
        print(f"Time {env.now:.2f}: Node 0 starts sending initial message")
        yield from node.send(1, "Initial message", MessageType.DATA)

def main():
    # Create simulation environment
    env = simpy.Environment()
    
    # Create ring network with 4 nodes
    num_nodes = 4
    nodes = create_ring_network(env, num_nodes)
    
    # Start processes for all nodes
    for node in nodes:
        env.process(node_process(env, node))
    
    # Run simulation
    print("Starting simulation...")
    env.run(until=20)  # Run for 20 time units
    
    # Print statistics
    print("\nStatistics:")
    for node in nodes:
        print(f"Node {node.node_id} received {node.messages_received} messages")

if __name__ == "__main__":
    main() 
import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from channel import Channel
from node import SimpleNode

def node_process(env: simpy.Environment, node: SimpleNode):
    """Main process for each node"""
    # Start message receiving process
    env.process(node.receive())
    
    if node.node_id == 0:  # Let node 0 initiate the message
        # Wait a bit to ensure all nodes are started
        yield env.timeout(1)
        print(f"Time {env.now:.2f}: Node 0 starts sending initial message")
        yield from node.send(1, "Hello, Node 1!", MessageType.DATA)

def main():
    # Create simulation environment
    env = simpy.Environment()

    # Create nodes
    nodes = []
    for i in range(2):  # Create 2 nodes
        node = SimpleNode(
            env=env,
            node_id=i,
            initial_data=0,
            processing_delay=0.1
        )
        nodes.append(node)

    # Create bidirectional communication channels and connect nodes
    channel_0_to_1 = Channel(env, bandwidth=100, latency=10, packet_loss_rate=0.1)
    channel_1_to_0 = Channel(env, bandwidth=100, latency=10, packet_loss_rate=0.1)

    # Add neighbor relationships with both node and channel information
    nodes[0].add_neighbor(1, nodes[1], channel_0_to_1)
    nodes[1].add_neighbor(0, nodes[0], channel_1_to_0)

    # Start node processes
    for node in nodes:
        env.process(node_process(env, node))

    # Run simulation
    print("Starting simulation...")
    env.run(until=10)  # Run for 10 time units

if __name__ == "__main__":
    main() 
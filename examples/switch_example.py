import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from channel import Channel
from node import Node, SwitchNode, EndNode

def create_star_network(env: simpy.Environment, num_nodes: int):
    """Create a star network with one switch in the center"""
    nodes = []
    channels = {}
    
    # Create switch node (ID: 0)
    switch = SwitchNode(
        env=env,
        node_id=0,
        initial_data=0,
        processing_delay=0.1
    )
    nodes.append(switch)
    
    # Create end nodes
    for i in range(1, num_nodes):
        node = EndNode(
            env=env,
            node_id=i,
            initial_data=0,
            processing_delay=0.1
        )
        nodes.append(node)
        
        # Create bidirectional channels between switch and node
        channel_to_node = Channel(
            env=env,
            bandwidth=100,  # 100Mbps
            latency=5,      # 5ms
            packet_loss_rate=0.05
        )
        channel_to_switch = Channel(
            env=env,
            bandwidth=100,
            latency=5,
            packet_loss_rate=0.05
        )
        
        # Connect switch and node
        switch.add_neighbor(i, node, channel_to_node)
        node.add_neighbor(0, switch, channel_to_switch)
        
    return nodes

def node_process(env: simpy.Environment, node: Node):
    """Main process for each node"""
    env.process(node.receive())
    
    if node.node_id == 1:  # Let node 1 send broadcast message
        yield env.timeout(1)
        print(f"Time {env.now:.2f}: Node 1 starts broadcasting message")
        yield from node.send(0, "Hello everyone!", MessageType.BROADCAST)
        
        # Send another broadcast after some time
        yield env.timeout(5)
        print(f"Time {env.now:.2f}: Node 1 starts broadcasting second message")
        yield from node.send(0, "Second broadcast!", MessageType.BROADCAST)

def main():
    # Create simulation environment
    env = simpy.Environment()
    
    # Create star network with 5 nodes (1 switch + 4 end nodes)
    num_nodes = 5
    nodes = create_star_network(env, num_nodes)
    
    # Start processes for all nodes
    for node in nodes:
        env.process(node_process(env, node))
    
    # Run simulation
    print("Starting simulation...")
    env.run(until=20)
    
    # Print statistics
    print("\nStatistics:")
    for node in nodes:
        node_type = "Switch" if isinstance(node, SwitchNode) else "Node"
        print(f"{node_type} {node.node_id} received {node.messages_received} messages")

if __name__ == "__main__":
    main() 
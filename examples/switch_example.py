import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simpy
from message import Message, MessageType
from node import Node, SwitchNode, EndNode
from topos.star import create_star_network

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
    nodes = create_star_network(
        env=env,
        num_nodes=5,
        bandwidth=100,      # 100Mbps
        latency=5,          # 5ms
        packet_loss_rate=0.05,
        processing_delay=0.1
    )
    
    # Start processes for all nodes
    for node in nodes:
        env.process(node_process(env, node))
    
    # Run simulation
    print("Starting simulation...")
    env.run(until=20)  # Run for 20 time units
    
    # Print statistics
    print("\nStatistics:")
    for node in nodes:
        node_type = "Switch" if isinstance(node, SwitchNode) else "Node"
        print(f"{node_type} {node.node_id} received {node.messages_received} messages")

if __name__ == "__main__":
    main() 
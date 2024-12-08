import simpy
from node import SwitchNode, EndNode
from channel import Channel

def create_star_network(env: simpy.Environment, num_nodes: int, 
                       bandwidth: float = 100,    # 100Mbps
                       latency: float = 5,        # 5ms
                       packet_loss_rate: float = 0.05,
                       processing_delay: float = 0.1):
    """Create a star network with one switch in the center
    
    Args:
        env: SimPy environment
        num_nodes: Total number of nodes (including switch)
        bandwidth: Channel bandwidth in Mbps
        latency: Channel latency in ms
        packet_loss_rate: Probability of packet loss
        processing_delay: Node processing delay in ms
        
    Returns:
        list: List of nodes where nodes[0] is the switch and others are end nodes
    """
    nodes = []
    
    # Create switch node (ID: 0)
    switch = SwitchNode(
        env=env,
        node_id=0,
        initial_data=0,
        processing_delay=processing_delay
    )
    nodes.append(switch)
    
    # Create end nodes
    for i in range(1, num_nodes):
        node = EndNode(
            env=env,
            node_id=i,
            initial_data=0,
            processing_delay=processing_delay
        )
        nodes.append(node)
        
        # Create bidirectional channels between switch and node
        channel_to_node = Channel(
            env=env,
            bandwidth=bandwidth,
            latency=latency,
            packet_loss_rate=packet_loss_rate
        )
        channel_to_switch = Channel(
            env=env,
            bandwidth=bandwidth,
            latency=latency,
            packet_loss_rate=packet_loss_rate
        )
        
        # Connect switch and node
        switch.add_neighbor(i, node, channel_to_node)
        node.add_neighbor(0, switch, channel_to_switch)
        
    return nodes 
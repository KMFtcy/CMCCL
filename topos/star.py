from network import generate_all_flows
from ns.switch.switch import SimplePacketSwitch
from ns.packet.sink import PacketSink
from ns.topos.utils import generate_fib
import networkx as nx
import simpy

def create_star_network(num_nodes: int, env: simpy.Environment):
    """Create a star network with one switch in the center
    
    Args:
        num_nodes: Total number of nodes (including switch)
        env: SimPy environment
        
    Returns
        Network: Network object
    """
    G = nx.Graph()
    # Create the central node
    G.add_node(0, type="switch")  # Central node is a switch
    # Create other nodes
    for i in range(1, num_nodes):
        G.add_node(i, type="host")  # Other nodes are hosts
        G.add_edge(0, i)  # Connect central node to other nodes
    
    hosts = set()
    for node_id in G.nodes():
        if G.nodes[node_id]["type"] == "host":
            hosts.add(node_id)

    all_flows = generate_all_flows(G, hosts)
    generate_fib(G, all_flows)
    
    # Add device attribute
    for node_id in G.nodes():
        node = G.nodes[node_id]
        node["device"] = SimplePacketSwitch(
            env, nports=num_nodes-1, port_rate=1e9, buffer_size=None, element_id=f"{node_id}"
        )
        node["device"].demux.fib = node["flow_to_port"]

    # Connect each node's ports to the next hop
    for node_id in G.nodes():
        node = G.nodes[node_id]
        for port_number, next_hop in node["port_to_nexthop"].items():
            node["device"].ports[port_number].out = G.nodes[next_hop]["device"]

    # Connect all flow destinations to a sink for statistics
    for flow_id, flow in all_flows.items():
        G.nodes[flow.dst]["device"].demux.ends[flow_id] = PacketSink(env, debug=True)

    # record send packet num in node attributes
    for node_id in G.nodes():
        G.nodes[node_id]["send_packet_num"] = 0

    # add all flows to the network
    G.all_flows = all_flows
    
    # # Print all nodes information in the fib graph
    # for node, data in G.nodes(data=True):
    #     print(f"Node: {node}, Data: {data}")
    # # Print device information of node 3
    # print(G.nodes[3]["device"].demux.ends)

    return G
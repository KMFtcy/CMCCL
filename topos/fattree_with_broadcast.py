import networkx as nx
import simpy
from switch import BroadcastSwitch
from ns.packet.sink import PacketSink
from ns.topos.utils import generate_fib
from network import generate_all_flows

def create_fattree_network_with_broadcast(k: int, env: simpy.Environment, debug: bool=False):
    """Create a k-ary FatTree network with broadcast switches
    
    Args:
        k: The k parameter of the FatTree (must be even)
        env: SimPy environment
        
    Returns:
        Network: Network object (nx.Graph)
    """
    if k % 2 != 0:
        raise ValueError("k must be even")
        
    G = nx.Graph()
    
    # Calculate the number of different switch types
    n_core = (k//2)**2
    n_aggr = k * k//2
    n_edge = k * k//2
    n_hosts = k**3//4
    
    # Add core switches (top layer)
    core_start = 0
    for i in range(n_core):
        G.add_node(i, type="switch", layer="core")
    
    # Add aggregation switches (middle layer)
    aggr_start = n_core
    for pod in range(k):
        for i in range(k//2):
            node_id = aggr_start + pod * (k//2) + i
            G.add_node(node_id, type="switch", layer="aggr")
    
    # Add edge switches (bottom layer)
    edge_start = aggr_start + n_aggr
    for pod in range(k):
        for i in range(k//2):
            node_id = edge_start + pod * (k//2) + i
            G.add_node(node_id, type="switch", layer="edge")
    
    # Add hosts
    host_start = edge_start + n_edge
    for pod in range(k):
        for switch in range(k//2):
            for host in range(k//2):
                host_id = host_start + pod * (k**2//4) + switch * (k//2) + host
                G.add_node(host_id, type="host", layer="host")
                # Connect host to edge switch
                edge_id = edge_start + pod * (k//2) + switch
                G.add_edge(host_id, edge_id)
    
    # Connect edge switches to aggregation switches
    for pod in range(k):
        for edge in range(k//2):
            edge_id = edge_start + pod * (k//2) + edge
            for aggr in range(k//2):
                aggr_id = aggr_start + pod * (k//2) + aggr
                G.add_edge(edge_id, aggr_id)
    
    # Connect aggregation switches to core switches
    for pod in range(k):
        for aggr in range(k//2):
            aggr_id = aggr_start + pod * (k//2) + aggr
            for j in range(k//2):
                core_id = aggr * (k//2) + j
                G.add_edge(aggr_id, core_id)
    
    # Get all hosts
    hosts = {n for n in G.nodes() if G.nodes[n]["type"] == "host"}
    
    # Generate flows and FIB
    all_flows = generate_all_flows(G, hosts)
    generate_fib(G, all_flows)
    
    # Add devices
    for node_id in G.nodes():
        node = G.nodes[node_id]
        # Calculate number of ports needed
        n_ports = len(list(G.neighbors(node_id)))
        
        # Create the BroadcastSwitch
        device = BroadcastSwitch(
            env, nports=n_ports, port_rate=1e9, buffer_size=None, node_id=str(node_id), debug=debug
        )
        device.is_host = (node["type"] == "host")
        device.nexthop_to_port = node["nexthop_to_port"]
        node["device"] = device
        node["device"].demux.fib = node["flow_to_port"]

    # Connect ports
    for node_id in G.nodes():
        node = G.nodes[node_id]
        for port_number, next_hop in node["port_to_nexthop"].items():
            node["device"].ports[port_number].out = G.nodes[next_hop]["device"]

    # Connect flow destinations to sinks
    for flow_id, flow in all_flows.items():
        G.nodes[flow.dst]["device"].demux.ends[flow_id] = PacketSink(env, debug=debug)

    # Record send packet num in node attributes
    for node_id in G.nodes():
        G.nodes[node_id]["send_packet_num"] = 0

    # Add all flows to the network
    G.all_flows = all_flows
    
    return G

# def generate_all_flows(G, hosts):
#     """Generate flows between all host pairs"""
#     all_flows = {}
#     flow_id = 0
    
#     # Generate flows between all host pairs
#     for src in hosts:
#         for dst in hosts:
#             if src != dst:
#                 all_flows[flow_id] = Flow(
#                     flow_id,
#                     src,
#                     dst,
#                     size=None,
#                     start_time=None,
#                     finish_time=None
#                 )
#                 # Use single shortest path
#                 all_flows[flow_id].path = nx.shortest_path(G, src, dst)
#                 flow_id += 1
    
#     return all_flows 
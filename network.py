from typing import Dict, Optional, Tuple
import simpy
from message import Message
from ns.flow.flow import Flow
from ns.packet.packet import Packet

from itertools import product
import networkx as nx

def generate_all_flows(
    G,
    hosts,
    size=None,
    start_time=None,
    finish_time=None,
    arrival_dist=None,
    size_dist=None,
):
    all_flows = dict()
    flow_id = 0
    
    # Generate all possible source-destination pairs
    for src, dst in product(sorted(hosts), repeat=2):
        if src == dst:
            continue
            
        all_flows[flow_id] = Flow(
            flow_id,
            src,
            dst,
            size=size,
            start_time=start_time,
            finish_time=finish_time,
            arrival_dist=arrival_dist,
            size_dist=size_dist,
        )
        
        # all_flows[flow_id].path = list(nx.all_shortest_paths(G, src, dst))[0]
        # print(f"nodes count is {G.number_of_nodes()}, finding path from {src} to {dst}")
        all_flows[flow_id].path = nx.shortest_path(G, src, dst)
        flow_id += 1
        
    return all_flows

def get_flow_by_src_dst(all_flows: Dict[int, Flow], src: int, dst: int) -> Optional[Tuple[int, Flow]]:
    """Select a flow based on source and destination"""
    for flow_id, flow in all_flows.items():
        if flow.src == src and flow.dst == dst:
            return flow_id, flow
    return None

def send(env: simpy.Environment, network: nx.Graph, src_id: int, dst_id: int, message: Message, data_size: int=1.5e9, is_broadcast: bool=False, latency: float=0.5):
    """Send a message from source to destination."""
    if dst_id == -1:
        flow_id = -1  # 广播包使用特殊flow_id
    else:
        all_flows = network.all_flows
        flow_info = get_flow_by_src_dst(all_flows, src_id, dst_id)
        if flow_info is None:
            print(f"No flow found from {src_id} to {dst_id}.")
            return
        flow_id, flow = flow_info

    # Create a packet
    packet = Packet(
        env.now,
        size=data_size,
        packet_id=network.nodes[src_id]["send_packet_num"],
        src=src_id,
        dst=dst_id,
        flow_id=flow_id,
    )

    packet.is_broadcast = is_broadcast
    if is_broadcast:
        packet.last_hop = src_id
        packet.history_hop = [src_id]

    # Increment the send packet num
    network.nodes[src_id]["send_packet_num"] += 1

    # Return the process so caller can wait for it
    return env.process(_send_packet(env, packet, network.nodes[src_id]["device"], latency))
def _send_packet(env: simpy.Environment, packet: Packet, device, latency: float=10):
    """Internal method to handle sending the packet."""
    yield env.timeout(latency)  # latency for every message
    device.put(packet)
    # print(f"Packet {packet.packet_id} sent from {packet.src} to {packet.dst}.")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topos.fattree_with_broadcast import create_fattree_network_with_broadcast as build
from collective.ring_allreduce import RingAllReduce
from collective.tree_allreduce import BinaryTreeAllReduce, BroadcastTreeAllReduce
from collective.ps_allreduce import PSAllReduce, BroadcastPSAllReduce
from collective.logger import set_log_file
import simpy
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import networkx as nx

def run_test(k, algorithm):
    """Run AllReduce test on k-ary FatTree"""
    # Set log file based on topology name and size
    num_hosts = (k ** 3) // 4  # number of hosts in fat-tree
    log_file = f"logs/fattree_{num_hosts}.log"
    set_log_file(log_file)
    
    env = simpy.Environment()
    network = build(env=env, k=k)
    hosts = sorted([n for n in network.nodes() if network.nodes[n]["type"] == "host"])
    
    # 打印FatTree拓扑信息
    print(f"\n=== FatTree Topology Info (k={k}) ===")
    print(f"Total nodes: {network.number_of_nodes()}")
    
    # 按层统计节点
    core_nodes = sorted([n for n in network.nodes() if network.nodes[n]["layer"] == "core"])
    aggr_nodes = sorted([n for n in network.nodes() if network.nodes[n]["layer"] == "aggr"])
    edge_nodes = sorted([n for n in network.nodes() if network.nodes[n]["layer"] == "edge"])
    host_nodes = sorted([n for n in network.nodes() if network.nodes[n]["layer"] == "host"])
    
    print("\n=== Layer Information ===")
    print(f"Core layer: {len(core_nodes)} nodes, IDs: {core_nodes}")
    print(f"Aggregation layer: {len(aggr_nodes)} nodes, IDs: {aggr_nodes}")
    print(f"Edge layer: {len(edge_nodes)} nodes, IDs: {edge_nodes}")
    print(f"Host layer: {len(host_nodes)} nodes, IDs: {host_nodes}")
    
    print("\n=== Node Connections ===")
    for layer_name, nodes in [("Core", core_nodes), ("Aggregation", aggr_nodes), 
                            ("Edge", edge_nodes), ("Host", host_nodes)]:
        print(f"\n{layer_name} layer connections:")
        for node in nodes:
            neighbors = sorted(list(network.neighbors(node)))
            print(f"  Node {node} -> {neighbors}")
    
    # 打印路由表示例（第一个主机的）
    if hosts:
        first_host = hosts[0]
        print(f"\nRouting table for host {first_host}:")
        print(f"nexthop_to_port: {network.nodes[first_host]['nexthop_to_port']}")
        print(f"port_to_nexthop: {network.nodes[first_host]['port_to_nexthop']}")
    
    print("\n=== Starting AllReduce Test ===")
    
    if algorithm == "ring":
        allreduce = RingAllReduce(env, network, hosts)
    elif algorithm == "binary_tree":
        allreduce = BinaryTreeAllReduce(env, network, hosts)
    elif algorithm == "broadcast_tree":
        allreduce = BroadcastTreeAllReduce(env, network, hosts)
    elif algorithm == "ps":
        allreduce = PSAllReduce(env, network, hosts)
    else:  # broadcast_ps
        allreduce = BroadcastPSAllReduce(env, network, hosts)
    
    start_time = env.now
    env.process(allreduce.reduce())
    env.run()
    end_time = env.now
    
    total_time = end_time - start_time
    print(f"Algorithm: {algorithm}, Total time: {total_time}")
    
    return total_time

# Test configurations
k_values = [2, 4, 6, 8]  # k must be even
algorithms = ["ring", "binary_tree", "broadcast_tree", "ps", "broadcast_ps"]
styles = {
    "ring": {"color": "blue", "marker": "o", "label": "Ring AllReduce"},
    "binary_tree": {"color": "red", "marker": "s", "label": "Binary Tree AllReduce"},
    "broadcast_tree": {"color": "green", "marker": "^", "label": "Broadcast Tree AllReduce"},
    "ps": {"color": "purple", "marker": "d", "label": "PS AllReduce"},
    "broadcast_ps": {"color": "orange", "marker": "v", "label": "Broadcast PS AllReduce"}
}

# Run tests and collect results
results = {alg: [] for alg in algorithms}
host_counts = [k**3//4 for k in k_values]  # Calculate number of hosts for each k

for k in k_values:
    for alg in algorithms:
        time = run_test(k, alg)
        results[alg].append(time)

# Plot results
plt.figure(figsize=(12, 8))
for alg in algorithms:
    plt.semilogy(host_counts, results[alg],
             color=styles[alg]["color"],
             marker=styles[alg]["marker"],
             label=styles[alg]["label"],
             linewidth=2,
             markersize=8)

plt.xlabel('Number of Hosts', fontsize=12)
plt.ylabel('Simulation Time (log scale)', fontsize=12)
plt.title('AllReduce Algorithms Performance on FatTree', fontsize=14)

# 设置y轴刻度
ax = plt.gca()
ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=20))
ax.yaxis.set_minor_locator(ticker.LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1))
ax.yaxis.set_tick_params(which='both', labelbottom=True)

# 设置网格
plt.grid(True, which='major', linestyle='-', alpha=0.7)
plt.grid(True, which='minor', linestyle=':', alpha=0.4)

plt.legend(fontsize=10, bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Save the plot
plt.savefig('logs/all_allreduce_on_fattree_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nResults have been saved to logs/all_allreduce_on_fattree_comparison.png") 
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topos.star_with_broadcast import create_star_network_with_broadcast as build
from collective.ring_allreduce import RingAllReduce
from collective.tree_allreduce import BinaryTreeAllReduce, BroadcastTreeAllReduce
from collective.ps_allreduce import PSAllReduce, BroadcastPSAllReduce
import simpy
import matplotlib.pyplot as plt
import os

def run_test(num_nodes, algorithm):
    """Run test for specified algorithm and number of nodes"""
    env = simpy.Environment()
    network = build(env=env, num_nodes=num_nodes)
    hosts = sorted([n for n in network.nodes() if network.nodes[n]["type"] == "host"])
    
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
    print(f"Algorithm: {algorithm}, Nodes: {num_nodes}, Total time: {total_time}")
    return total_time

# Test configurations
node_counts = [5, 9, 17, 33, 65, 129, 257]  # Including central switch
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

for nodes in node_counts:
    for alg in algorithms:
        time = run_test(nodes, alg)
        results[alg].append(time)

# Plot results
plt.figure(figsize=(12, 8))
for alg in algorithms:
    plt.semilogy(node_counts, results[alg], 
             color=styles[alg]["color"],
             marker=styles[alg]["marker"],
             label=styles[alg]["label"],
             linewidth=2,
             markersize=8)

plt.xlabel('Number of Nodes (including switch)', fontsize=12)
plt.ylabel('Simulation Time', fontsize=12)
plt.title('AllReduce Algorithms Performance Comparison', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=10, bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# Add minor gridlines
plt.grid(True, which='minor', linestyle=':', alpha=0.4)
plt.minorticks_on()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Save the plot
plt.savefig('logs/all_allreduce_on_star_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("Results have been saved to logs/all_allreduce_on_star_comparison.png")
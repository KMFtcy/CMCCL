from typing import List, Dict, Optional, Tuple
import simpy
from node import Node
from message import Message, MessageType

class Network:
    """Network class that manages message transmission between nodes"""
    def __init__(self, env: simpy.Environment, nodes: List[Node]):
        self.env = env
        self.nodes = {node.node_id: node for node in nodes}
        
    def find_path(self, source_id: int, target_id: int) -> Optional[List[int]]:
        """Find a path from source to target using BFS
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            
        Returns:
            List of node IDs representing the path, or None if no path exists
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
            
        # Use BFS to find shortest path
        queue = [(source_id, [source_id])]
        visited = {source_id}
        
        while queue:
            current_id, path = queue.pop(0)
            current_node = self.nodes[current_id]
            
            # Check all neighbors
            for neighbor_id in current_node.neighbors:
                if neighbor_id == target_id:
                    return path + [target_id]
                    
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
                    
        return None
        
    def transmit(self, source_id: int, target_id: int, data: any, msg_type: MessageType):
        """Transmit a message from source to target through the network"""
        path = self.find_path(source_id, target_id)
        if not path:
            print(f"No path found from Node {source_id} to Node {target_id}")
            return

        # Transmit message along the path
        for i in range(len(path) - 1):
            current_id = path[i]
            next_id = path[i + 1]
            
            # Wait for send to complete
            yield from self.nodes[current_id].send(next_id, data, msg_type)
            # Wait a bit to ensure message is processed
            yield self.env.timeout(self.nodes[next_id].processing_delay)
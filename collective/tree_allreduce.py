import simpy
from message import Message, MessageType
from network import send
import networkx as nx
from typing import List, Dict, Optional

class TreeAllReduce:
    """Tree AllReduce implementation"""
    def __init__(self, env: simpy.Environment, network: nx.Graph, workers: List[str], data_size: int = 1.5e9):
        self.env = env
        self.network = network
        self.workers = sorted(workers)  # Sort workers to ensure consistent order
        self.n_workers = len(workers)
        self.data_size = data_size
        self.tree = self._build_logical_tree()

    def _build_logical_tree(self) -> Dict[str, Dict[str, List[str]]]:
        """Build a logical tree structure for the workers
        Returns a dict with 'parent' and 'children' for each worker
        """
        tree = {worker: {'parent': None, 'children': []} for worker in self.workers}
        
        # Simple binary tree structure
        for i, worker in enumerate(self.workers):
            if i > 0:  # Skip root
                parent_idx = (i - 1) // 2
                parent = self.workers[parent_idx]
                tree[worker]['parent'] = parent
                tree[parent]['children'].append(worker)
        
        return tree

    def get_parent(self, worker_id: str) -> Optional[str]:
        """Get parent of a worker in the tree"""
        return self.tree[worker_id]['parent']

    def get_children(self, worker_id: str) -> List[str]:
        """Get children of a worker in the tree"""
        return self.tree[worker_id]['children']

    def is_root(self, worker_id: str) -> bool:
        """Check if worker is root of the tree"""
        return self.tree[worker_id]['parent'] is None

    def is_leaf(self, worker_id: str) -> bool:
        """Check if worker is leaf of the tree"""
        return len(self.tree[worker_id]['children']) == 0

    def reduce(self, worker_id: str):
        """Perform Tree AllReduce operation"""
        # Phase 1: Reduce (bottom-up)
        if not self.is_leaf(worker_id):
            # Wait for data from all children
            for child in self.get_children(worker_id):
                message = Message(
                    source_id=child,
                    target_id=worker_id,
                    data=f"reduce_from_{child}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                send(self.env, self.network, child, worker_id, message, data_size=self.data_size)
                yield self.env.timeout(1)  # Simulate computation time

        # Send to parent (except for root)
        if not self.is_root(worker_id):
            parent = self.get_parent(worker_id)
            message = Message(
                source_id=worker_id,
                target_id=parent,
                data=f"reduce_to_parent",
                msg_type=MessageType.REDUCE,
                timestamp=self.env.now
            )
            send(self.env, self.network, worker_id, parent, message, data_size=self.data_size)
            yield self.env.timeout(1)

        # Phase 2: Broadcast (top-down)
        if self.is_root(worker_id):
            # Root broadcasts to its children
            for child in self.get_children(worker_id):
                message = Message(
                    source_id=worker_id,
                    target_id=child,
                    data=f"broadcast_to_{child}",
                    msg_type=MessageType.BROADCAST,
                    timestamp=self.env.now
                )
                send(self.env, self.network, worker_id, child, message, data_size=self.data_size)
                yield self.env.timeout(1)
        else:
            # Non-root nodes wait for broadcast from parent and forward to children
            parent = self.get_parent(worker_id)
            message = Message(
                source_id=parent,
                target_id=worker_id,
                data=f"broadcast_from_parent",
                msg_type=MessageType.BROADCAST,
                timestamp=self.env.now
            )
            # Forward to children
            for child in self.get_children(worker_id):
                message = Message(
                    source_id=worker_id,
                    target_id=child,
                    data=f"broadcast_to_{child}",
                    msg_type=MessageType.BROADCAST,
                    timestamp=self.env.now
                )
                send(self.env, self.network, worker_id, child, message, data_size=self.data_size)
                yield self.env.timeout(1)

class BinaryTreeAllReduce(TreeAllReduce):
    """Binary Tree AllReduce implementation"""
    def _build_logical_tree(self) -> Dict[str, Dict[str, List[str]]]:
        """Build a binary tree structure"""
        tree = super()._build_logical_tree()
        # Ensure each non-leaf node has at most 2 children
        for worker in self.workers:
            if len(tree[worker]['children']) > 2:
                tree[worker]['children'] = tree[worker]['children'][:2]
        return tree 

class BroadcastTreeAllReduce(TreeAllReduce):
    """Tree AllReduce with broadcast capability for the broadcast phase"""
    def reduce(self, worker_id: str):
        """Perform Tree AllReduce operation with broadcast capability"""
        # Phase 1: Reduce (bottom-up) - Same as TreeAllReduce
        if not self.is_leaf(worker_id):
            # Wait for data from all children
            for child in self.get_children(worker_id):
                message = Message(
                    source_id=child,
                    target_id=worker_id,
                    data=f"reduce_from_{child}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                send(self.env, self.network, child, worker_id, message, data_size=self.data_size)
                yield self.env.timeout(1)  # Simulate computation time

        # Send to parent (except for root)
        if not self.is_root(worker_id):
            parent = self.get_parent(worker_id)
            message = Message(
                source_id=worker_id,
                target_id=parent,
                data=f"reduce_to_parent",
                msg_type=MessageType.REDUCE,
                timestamp=self.env.now
            )
            send(self.env, self.network, worker_id, parent, message, data_size=self.data_size)
            yield self.env.timeout(1)

        # Phase 2: Broadcast (using broadcast capability)
        if self.is_root(worker_id):
            # Root broadcasts to all workers using broadcast capability
            message = Message(
                source_id=worker_id,
                target_id=-1,  # Broadcast address
                data=f"broadcast_from_root",
                msg_type=MessageType.BROADCAST,
                timestamp=self.env.now
            )
            # Use broadcast capability
            send(self.env, self.network, worker_id, -1, message, 
                 data_size=self.data_size, is_broadcast=True)
            yield self.env.timeout(1)
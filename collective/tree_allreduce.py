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
        self.workers = sorted(workers)
        self.n_workers = len(workers)
        self.data_size = data_size
        self.tree = self._build_logical_tree()
        self.levels = self._get_tree_levels()
        # Create events for each level
        self.reduce_events = [env.event() for _ in range(len(self.levels))]
        self.broadcast_events = [env.event() for _ in range(len(self.levels))]

    def _build_logical_tree(self) -> Dict[str, Dict[str, List[str]]]:
        """Build a logical tree structure for the workers"""
        tree = {worker: {'parent': None, 'children': []} for worker in self.workers}
        
        for i, worker in enumerate(self.workers):
            if i > 0:  # Skip root
                parent_idx = (i - 1) // 2
                parent = self.workers[parent_idx]
                tree[worker]['parent'] = parent
                tree[parent]['children'].append(worker)
        
        return tree

    def _get_tree_levels(self) -> List[List[str]]:
        """Get nodes at each level of the tree"""
        levels = []
        if not self.workers:
            return levels
        
        current_level = [self.workers[0]]  # Root is first worker in sorted list
        while current_level:
            levels.append(current_level)
            next_level = []
            for node in current_level:
                next_level.extend(self.tree[node]['children'])
            current_level = next_level
        
        return levels

    def get_parent(self, worker_id: str) -> Optional[str]:
        return self.tree[worker_id]['parent']

    def reduce(self):
        """Perform Tree AllReduce operation"""
        # Phase 1: Reduce (bottom-up)
        for level_idx, level in enumerate(reversed(self.levels[1:])):  # Skip root level
            # All workers in this level send to their parents simultaneously
            send_processes = []
            for worker in level:
                parent = self.get_parent(worker)
                message = Message(
                    source_id=worker,
                    target_id=parent,
                    data=f"reduce_from_{worker}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                # Store the send process
                send_proc = send(self.env, self.network, worker, parent, message, data_size=self.data_size)
                send_processes.append(send_proc)
            yield self.env.all_of(send_processes)
            
        # Phase 2: Broadcast (top-down)
        for level_idx, level in enumerate(self.levels[:-1]):  # Skip leaf level
            send_processes = []
            for worker in level:
                children = self.tree[worker]['children']
                for child in children:
                    message = Message(
                        source_id=worker,
                        target_id=child,
                        data=f"broadcast_to_{child}",
                        msg_type=MessageType.BROADCAST,
                        timestamp=self.env.now
                    )
                    # Store the send process
                    send_proc = send(self.env, self.network, worker, child, message, data_size=self.data_size)
                    send_processes.append(send_proc)
            yield self.env.all_of(send_processes)

class BinaryTreeAllReduce(TreeAllReduce):
    """Binary Tree AllReduce implementation"""
    def _build_logical_tree(self) -> Dict[str, Dict[str, List[str]]]:
        tree = {worker: {'parent': None, 'children': []} for worker in self.workers}
        
        for i, worker in enumerate(self.workers):
            if i > 0:  # Skip root
                parent_idx = (i - 1) // 2
                parent = self.workers[parent_idx]
                tree[worker]['parent'] = parent
                if len(tree[parent]['children']) < 2:  # Ensure max 2 children
                    tree[parent]['children'].append(worker)
        
        return tree

class BroadcastTreeAllReduce(TreeAllReduce):
    """Tree AllReduce with broadcast capability"""
    def reduce(self):
        """Perform Tree AllReduce with broadcast capability"""
        # Phase 1: Reduce (bottom-up)
        for level_idx, level in enumerate(reversed(self.levels[1:])):
            send_processes = []
            for worker in level:
                parent = self.get_parent(worker)
                message = Message(
                    source_id=worker,
                    target_id=parent,
                    data=f"reduce_from_{worker}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                # Store the send process
                send_proc = send(self.env, self.network, worker, parent, message, data_size=self.data_size)
                send_processes.append(send_proc)
            yield self.env.all_of(send_processes)

        # Phase 2: Use broadcast capability
        root = self.levels[0][0]
        message = Message(
            source_id=root,
            target_id=-1,  # Broadcast address
            data="broadcast_from_root",
            msg_type=MessageType.BROADCAST,
            timestamp=self.env.now
        )
        # Just send the broadcast message without waiting
        yield self.env.all_of([send(self.env, self.network, root, -1, message, 
             data_size=self.data_size, is_broadcast=True)])
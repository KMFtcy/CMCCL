import simpy
from message import Message, MessageType
from network import send
import networkx as nx
from typing import List, Dict

class PSAllReduce:
    """Base class for Parameter Server AllReduce implementations"""
    def __init__(self, env: simpy.Environment, network: nx.Graph, workers: List[int], server_id: int, data_size: int = 1.5e6):
        self.env = env
        self.network = network
        self.workers = workers
        self.server_id = server_id
        self.data_size = data_size
        self.received_count = 0  # Count of received messages

    def reduce(self, worker_id: int, data_size: int = None):
        """Should be implemented by subclasses"""
        raise NotImplementedError

class UnicastPSAllReduce(PSAllReduce):
    """Parameter Server AllReduce using unicast messages"""
    def reduce(self, worker_id: int, data_size: int = None):
        """Perform reduce operation using unicast messages"""
        # Use provided data_size or default to self.data_size
        data_size = data_size if data_size is not None else self.data_size
        
        # Phase 1: Workers send values to server
        message = Message(
            source_id=worker_id,
            target_id=self.server_id,
            data="reduce",
            msg_type=MessageType.REDUCE,
            timestamp=self.env.now
        )
        send(self.env, self.network, worker_id, self.server_id, message, data_size=data_size)
        yield self.env.timeout(1)  # Simulate computation time

        # Server aggregates values
        self.received_count += 1
        
        # Wait for all workers to send their values
        if self.received_count == len(self.workers):
            # Phase 2: Server broadcasts result back to workers
            for w_id in self.workers:
                message = Message(
                    source_id=self.server_id,
                    target_id=w_id,
                    data="result",
                    msg_type=MessageType.BROADCAST,
                    timestamp=self.env.now
                )
                send(self.env, self.network, self.server_id, w_id, message, data_size=data_size)
                yield self.env.timeout(1)

class BroadcastPSAllReduce(PSAllReduce):
    """Parameter Server AllReduce using broadcast messages"""
    def reduce(self, worker_id: int, data_size: int = None):
        """Perform reduce operation using broadcast messages"""
        # Use provided data_size or default to self.data_size
        data_size = data_size if data_size is not None else self.data_size
        
        # Phase 1: Workers send values to server
        message = Message(
            source_id=worker_id,
            target_id=self.server_id,
            data="reduce",
            msg_type=MessageType.REDUCE,
            timestamp=self.env.now
        )
        send(self.env, self.network, worker_id, self.server_id, message, data_size=data_size)
        yield self.env.timeout(1)  # Simulate computation time

        # Server aggregates values
        self.received_count += 1
        
        # Wait for all workers to send their values
        if self.received_count == len(self.workers):
            # Phase 2: Server broadcasts result to all workers using a single broadcast message
            message = Message(
                source_id=self.server_id,
                target_id=-1,  # Broadcast address
                data="result",
                msg_type=MessageType.BROADCAST,
                timestamp=self.env.now
            )
            send(self.env, self.network, self.server_id, -1, message, 
                 data_size=data_size, is_broadcast=True)
            yield self.env.timeout(1)
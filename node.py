import simpy
from typing import List, Dict
from message import Message, MessageType
from channel import Channel

class Node:
    def __init__(self, env: simpy.Environment, node_id: int, 
                 initial_data: float, processing_delay: float):
        self.env = env
        self.node_id = node_id
        self.data = initial_data
        self.processing_delay = processing_delay
        self.neighbors: Dict[int, Node] = {}
        self.neighbor_channels: Dict[int, Channel] = {}
        self.received_messages: List[Message] = []
        self.running = True
        
    def add_neighbor(self, neighbor_id: int, neighbor_node, channel: Channel):
        self.neighbors[neighbor_id] = neighbor_node
        self.neighbor_channels[neighbor_id] = channel
        
    def send(self, target_id: int, data: float, msg_type: MessageType):
        """Returns a generator function for SimPy to process"""
        if target_id not in self.neighbors:
            raise ValueError(f"Node {target_id} is not a neighbor")
            
        message = Message(
            source_id=self.node_id,
            target_id=target_id,
            data=data,
            msg_type=msg_type,
            timestamp=self.env.now
        )
        
        channel = self.neighbor_channels[target_id]
        target_node = self.neighbors[target_id]
        yield from channel.transmit(message, target_node)
        
    def receive(self):
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                self.handle_message(message)
            yield self.env.timeout(0.001)
            
    def handle_message(self, message: Message):
        # To be implemented by specific algorithm classes
        pass 
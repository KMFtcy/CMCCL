import simpy
from typing import List, Dict
from message import Message, MessageType
from channel import Channel

class Node:
    """Base node class"""
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
        self.messages_received = 0  # Add counter to base class
        
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
        """Base receive method"""
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                # Count received messages
                self.messages_received += 1
                # Print message receipt
                print(f"Time {self.env.now:.2f}: Node {self.node_id} received {message.msg_type.value} from Node {message.source_id}: {message.data}")
            yield self.env.timeout(0.001)
class SwitchNode(Node):
    """Switch node that can broadcast messages to all connected nodes"""
    def receive(self):
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                # Count received messages
                self.messages_received += 1
                print(f"Time {self.env.now:.2f}: Switch {self.node_id} received {message.msg_type.value} from Node {message.source_id}: {message.data}")
                
                # Handle broadcast messages
                if message.msg_type == MessageType.BROADCAST:
                    # Broadcast to all neighbors except the source
                    for neighbor_id in self.neighbors:
                        if neighbor_id != message.source_id:
                            new_data = f"Broadcast from Node {message.source_id}: {message.data}"
                            self.env.process(self.send(neighbor_id, new_data, MessageType.BROADCAST))
            yield self.env.timeout(0.001)

class EndNode(Node):
    """End node that can send and receive broadcast messages"""
    def receive(self):
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                # Count received messages
                self.messages_received += 1
                print(f"Time {self.env.now:.2f}: Node {self.node_id} received {message.msg_type.value} from Node {message.source_id}: {message.data}")
            yield self.env.timeout(0.001)

class SimpleNode(Node):
    """Simple node implementation for demonstration"""
    def receive(self):
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                # Count received messages
                self.messages_received += 1
                print(f"Time {self.env.now:.2f}: Node {self.node_id} received data from Node {message.source_id}: {message.data}")
            yield self.env.timeout(0.001)

class RingNode(Node):
    """Node implementation for ring topology"""
    def __init__(self, env, node_id, initial_data, processing_delay, total_nodes):
        super().__init__(env, node_id, initial_data, processing_delay)
        self.total_nodes = total_nodes
        
    def receive(self):
        while self.running:
            if self.received_messages:
                message = self.received_messages.pop(0)
                # Simulate processing delay
                yield self.env.timeout(self.processing_delay)
                # Count received messages
                self.messages_received += 1
                print(f"Time {self.env.now:.2f}: Node {self.node_id} received data from Node {message.source_id}: {message.data}")
                
                # Pass message to next node
                next_node = (self.node_id + 1) % self.total_nodes
                new_data = f"Data from Node {self.node_id}_{self.messages_received}"
                self.env.process(self.send(next_node, new_data, MessageType.DATA))
            yield self.env.timeout(0.001)
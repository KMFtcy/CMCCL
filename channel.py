import simpy
import random
from typing import Optional
from message import Message

class Channel:
    def __init__(self, env: simpy.Environment, bandwidth: float, 
                 latency_dist: float, packet_loss_rate: float):
        self.env = env
        self.bandwidth = bandwidth  # Mbps
        self.latency_list = latency_dist      # ms
        self.packet_loss_rate = packet_loss_rate
        self.busy = simpy.Resource(env, capacity=1)
        
    def transmit(self, message: Message, target_node):
        """Returns a generator function for SimPy to process"""
        with self.busy.request() as req:
            yield req
            
            # Calculate transmission delay
            message_size = len(str(message.data).encode())
            transmission_time = message_size / (self.bandwidth * 1024 * 1024 / 8)
            
            # Simulate propagation delay
            yield self.env.timeout(self.latency_list() / 1000.0)
            
            # Simulate transmission delay
            yield self.env.timeout(transmission_time)
            
            # Simulate packet loss
            # if random.random() < self.packet_loss_rate:
            #     return None
            
            # Deliver message to target node
            target_node.received_messages.append(message)
            return message
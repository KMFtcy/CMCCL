import simpy
from typing import Dict, List
from network import Network
from message import Message, MessageType

class PSAllReduce:
    """Base class for Parameter Server based AllReduce implementations"""
    def __init__(self, env: simpy.Environment, network: Network, ps_node_id: int, data_size: int):
        self.env = env
        self.network = network
        self.ps_node_id = ps_node_id
        self.data_size = data_size
        self.worker_nodes = [
            node_id for node_id in network.nodes.keys() 
            if node_id != ps_node_id
        ]
        
    def gather(self) -> simpy.Event:
        """First phase: workers send data to PS"""
        print(f"Time {self.env.now:.2f}: Starting gather phase")
        for worker_id in self.worker_nodes:
            print(f"Time {self.env.now:.2f}: Worker {worker_id} sending data to PS")
            yield from self.network.transmit(
                source_id=worker_id,
                target_id=self.ps_node_id,
                data=self.data_size,
                msg_type=MessageType.DATA
            )
    
    def scatter(self) -> simpy.Event:
        """Second phase: PS distributes aggregated data to workers"""
        raise NotImplementedError("Scatter method must be implemented by subclasses")
    
    def run(self) -> simpy.Event:
        """Run the PS-AllReduce algorithm"""
        print(f"Time {self.env.now:.2f}: Starting PS-AllReduce with {len(self.worker_nodes)} workers")
        
        # First phase: gather
        yield from self.gather()
        
        # Second phase: scatter
        yield from self.scatter()
        
        print(f"Time {self.env.now:.2f}: PS-AllReduce completed")

class BroadcastPSAllReduce(PSAllReduce):
    """PS-AllReduce implementation using broadcast for scatter phase"""
    def scatter(self) -> simpy.Event:
        """Second phase: PS broadcasts aggregated data to all workers"""
        print(f"Time {self.env.now:.2f}: Starting broadcast scatter phase")
        aggregated_data = self.data_size * len(self.worker_nodes)
        
        print(f"Time {self.env.now:.2f}: PS broadcasting aggregated data to all workers")
        yield from self.network.transmit(
            source_id=self.ps_node_id,
            target_id=self.worker_nodes[0],  # Any worker will do as initial target
            data=aggregated_data,
            msg_type=MessageType.BROADCAST
        )

class UnicastPSAllReduce(PSAllReduce):
    """PS-AllReduce implementation using unicast for scatter phase"""
    def scatter(self) -> simpy.Event:
        """Second phase: PS sends aggregated data to each worker sequentially"""
        print(f"Time {self.env.now:.2f}: Starting unicast scatter phase")
        aggregated_data = self.data_size * len(self.worker_nodes)
        
        for worker_id in self.worker_nodes:
            print(f"Time {self.env.now:.2f}: PS sending aggregated data to Worker {worker_id}")
            yield from self.network.transmit(
                source_id=self.ps_node_id,
                target_id=worker_id,
                data=aggregated_data,
                msg_type=MessageType.DATA
            ) 
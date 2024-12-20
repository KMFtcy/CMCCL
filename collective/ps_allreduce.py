import simpy
from message import Message, MessageType
from network import send
import networkx as nx
from typing import List
import time
import logging
import json
from .logger import logger

class PSAllReduce:
    """Parameter Server AllReduce implementation"""
    def __init__(self, env: simpy.Environment, network: nx.Graph, workers: List[str], data_size: int = 1.5e9):
        self.env = env
        self.network = network
        self.workers = sorted(workers)  # 所有worker节点
        self.n_workers = len(workers)
        self.data_size = data_size
        self.ps_node = min(self.workers)  # 使用第一个worker作为参数服务器
        
    def reduce(self):
        """Perform Parameter Server AllReduce operation"""
        # Phase 1: Workers send to PS
        send_processes = []
        for worker in self.workers:
            if worker != self.ps_node:  # PS节点不需要发送给自己
                message = Message(
                    source_id=worker,
                    target_id=self.ps_node,
                    data=f"reduce_from_{worker}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                send_proc = send(self.env, self.network, worker, self.ps_node, message, data_size=self.data_size)
                send_processes.append(send_proc)
        
        # 等待所有worker发送完成
        if send_processes:
            # Record start time before yield
            yield_start_time = time.time()
            yield self.env.all_of(send_processes)
            # Record end time after yield
            yield_end_time = time.time()

            # Log time data
            logger.info(json.dumps({
                "algorithm": "ps_allreduce",
                "phase": "reduce",
                "step": 0,
                "yield_time_spent": yield_end_time - yield_start_time
            }))
            
        # Phase 2: PS broadcasts result to all workers
        broadcast_processes = []
        for worker in self.workers:
            if worker != self.ps_node:  # PS节点不需要发送给自己
                message = Message(
                    source_id=self.ps_node,
                    target_id=worker,
                    data=f"broadcast_to_{worker}",
                    msg_type=MessageType.BROADCAST,
                    timestamp=self.env.now
                )
                broadcast_proc = send(self.env, self.network, self.ps_node, worker, message, data_size=self.data_size)
                broadcast_processes.append(broadcast_proc)
                
        if broadcast_processes:
            # Record start time before yield
            yield_start_time = time.time()
            yield self.env.all_of(broadcast_processes)
            # Record end time after yield
            yield_end_time = time.time()

            # Log time data
            logger.info(json.dumps({
                "algorithm": "ps_allreduce",
                "phase": "broadcast",
                "step": 0,
                "yield_time_spent": yield_end_time - yield_start_time
            }))

class BroadcastPSAllReduce(PSAllReduce):
    """Parameter Server AllReduce with broadcast capability"""
    def reduce(self):
        """Perform Parameter Server AllReduce with broadcast capability"""
        # Phase 1: Workers send to PS (same as base class)
        send_processes = []
        for worker in self.workers:
            if worker != self.ps_node:
                message = Message(
                    source_id=worker,
                    target_id=self.ps_node,
                    data=f"reduce_from_{worker}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                send_proc = send(self.env, self.network, worker, self.ps_node, message, data_size=self.data_size)
                send_processes.append(send_proc)
        
        if send_processes:
            # Record start time before yield
            yield_start_time = time.time()
            yield self.env.all_of(send_processes)
            # Record end time after yield
            yield_end_time = time.time()

            # Log time data
            logger.info(json.dumps({
                "algorithm": "ps_allreduce_broadcast",
                "phase": "reduce",
                "step": 0,
                "yield_time_spent": yield_end_time - yield_start_time
            }))
            
        # Phase 2: PS broadcasts result using network broadcast capability
        message = Message(
            source_id=self.ps_node,
            target_id=-1,  # 广播地址
            data="broadcast_from_ps",
            msg_type=MessageType.BROADCAST,
            timestamp=self.env.now
        )
        # Record start time before yield
        yield_start_time = time.time()
        yield send(self.env, self.network, self.ps_node, -1, message, 
                  data_size=self.data_size, is_broadcast=True)
        # Record end time after yield
        yield_end_time = time.time()

        # Log time data
        logger.info(json.dumps({
            "algorithm": "ps_allreduce_broadcast",
            "phase": "broadcast",
            "step": 0,
            "yield_time_spent": yield_end_time - yield_start_time
        }))
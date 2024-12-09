import simpy
from message import Message, MessageType
from network import send
import networkx as nx
from typing import List, Dict

class RingAllReduce:
    """Ring AllReduce implementation"""
    def __init__(self, env: simpy.Environment, network: nx.Graph, workers: List[int], data_size: int = 1.5e9):
        self.env = env
        self.network = network
        self.workers = sorted(workers)
        self.n_workers = len(workers)
        self.data_size = data_size
        self.chunk_size = data_size // self.n_workers
        # Create events for synchronization
        self.scatter_reduce_events = [env.event() for _ in range(self.n_workers - 1)]
        self.allgather_events = [env.event() for _ in range(self.n_workers - 1)]

    def get_next_rank(self, rank: int) -> int:
        """Get the next rank in the ring"""
        idx = self.workers.index(rank)
        return self.workers[(idx + 1) % self.n_workers]

    def get_prev_rank(self, rank: int) -> int:
        """Get the previous rank in the ring"""
        idx = self.workers.index(rank)
        return self.workers[(idx - 1) % self.n_workers]

    def reduce(self):
        """Perform Ring AllReduce operation"""
        # Phase 1: Scatter-reduce
        scatter_reduce_start = self.env.now
        step_times = []

        for step in range(self.n_workers - 1):
            step_start = self.env.now
            print(f"Step {step} starting at {step_start}")
            # Each worker sends to its next neighbor
            send_processes = []
            for worker_id in self.workers:
                send_dst = self.get_next_rank(worker_id)
                message = Message(
                    source_id=worker_id,
                    target_id=send_dst,
                    data=f"scatter_reduce_step_{step}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                # Store the send process
                send_proc = send(self.env, self.network, worker_id, send_dst, message, data_size=self.chunk_size)
                send_processes.append(send_proc)

            # Wait for all sends to complete
            for proc in send_processes:
                yield proc

            # Last worker triggers the event for this step
            if worker_id == self.workers[-1]:
                self.scatter_reduce_events[step].succeed()
            # Wait for step completion
            yield self.scatter_reduce_events[step]
            
            step_end = self.env.now
            step_time = step_end - step_start
            print(f"Step {step} ending at {step_end}")
            step_times.append((f"Scatter-Reduce Step {step}", step_time))

        scatter_reduce_phase_time = self.env.now - scatter_reduce_start
        print("\nRing AllReduce Scatter-Reduce Phase Times:")
        for step_name, time in step_times:
            print(f"{step_name}: {time}")
        print(f"Total Scatter-Reduce Phase Time: {scatter_reduce_phase_time}")

        # Phase 2: Allgather
        allgather_start = self.env.now
        step_times = []

        for step in range(self.n_workers - 1):
            step_start = self.env.now
            print(f"Allgather Step {step} starting at {step_start}")
            # Each worker sends to its next neighbor
            send_processes = []
            for worker_id in self.workers:
                send_dst = self.get_next_rank(worker_id)
                message = Message(
                    source_id=worker_id,
                    target_id=send_dst,
                    data=f"allgather_step_{step}",
                    msg_type=MessageType.BROADCAST,
                    timestamp=self.env.now
                )
                # Store the send process
                send_proc = send(self.env, self.network, worker_id, send_dst, message, data_size=self.chunk_size)
                send_processes.append(send_proc)

            # Wait for all sends to complete
            for proc in send_processes:
                yield proc

            # Last worker triggers the event for this step
            if worker_id == self.workers[-1]:
                self.allgather_events[step].succeed()
            # Wait for step completion
            yield self.allgather_events[step]
            
            step_end = self.env.now
            step_time = step_end - step_start
            print(f"Allgather Step {step} ending at {step_end}")
            step_times.append((f"Allgather Step {step}", step_time))

        allgather_phase_time = self.env.now - allgather_start
        print("\nRing AllReduce Allgather Phase Times:")
        for step_name, time in step_times:
            print(f"{step_name}: {time}")
        print(f"Total Allgather Phase Time: {allgather_phase_time}")
        print(f"Total AllReduce Time: {allgather_phase_time + scatter_reduce_phase_time}\n")

class HierarchicalRingAllReduce(RingAllReduce):
    """Hierarchical Ring AllReduce implementation for FatTree topology"""
    def __init__(self, env: simpy.Environment, network: nx.Graph, workers: List[int], data_size: int = 1.5e9):
        super().__init__(env, network, workers, data_size)
        # Group workers by their pod (for FatTree topology)
        self.pods = self._group_workers_by_pod()
        # Create events for each phase
        self.intra_pod_reduce_events = {pod_id: env.event() for pod_id in self.pods}
        self.inter_pod_reduce_event = env.event()
        self.intra_pod_broadcast_events = {pod_id: env.event() for pod_id in self.pods}

    def _group_workers_by_pod(self) -> Dict[str, List[int]]:
        """Group workers by their pod in FatTree topology"""
        pods = {}
        for worker in self.workers:
            # Assuming worker IDs are in format "h{pod_id}_{host_id}"
            pod_id = worker.split('_')[0]
            if pod_id not in pods:
                pods[pod_id] = []
            pods[pod_id].append(worker)
        return pods

    def reduce(self, worker_id: int):
        """Perform Hierarchical Ring AllReduce operation"""
        pod_id = worker_id.split('_')[0]
        pod_workers = self.pods[pod_id]
        pod_size = len(pod_workers)
        chunk_size = self.data_size // (pod_size * self.n_workers)

        # Phase 1: Intra-pod reduce
        for step in range(pod_size - 1):
            send_dst = self.get_next_rank(worker_id)
            message = Message(
                source_id=worker_id,
                target_id=send_dst,
                data=f"intra_pod_reduce_step_{step}",
                msg_type=MessageType.REDUCE,
                timestamp=self.env.now
            )
            send(self.env, self.network, worker_id, send_dst, message, data_size=chunk_size)
            
            # Last worker in pod triggers the event
            if worker_id == pod_workers[-1]:
                self.intra_pod_reduce_events[pod_id].succeed()
            # Wait for pod completion
            yield self.intra_pod_reduce_events[pod_id]

        # Phase 2: Inter-pod reduce (only pod leaders participate)
        if worker_id == pod_workers[0]:  # Pod leader
            for step in range(len(self.pods) - 1):
                send_dst = self.get_next_rank(worker_id)
                message = Message(
                    source_id=worker_id,
                    target_id=send_dst,
                    data=f"inter_pod_reduce_step_{step}",
                    msg_type=MessageType.REDUCE,
                    timestamp=self.env.now
                )
                send(self.env, self.network, worker_id, send_dst, message, data_size=chunk_size)
            
            # Last pod leader triggers the event
            if worker_id == sorted(self.pods.keys())[-1]:
                self.inter_pod_reduce_event.succeed()
        # All workers wait for inter-pod reduce completion
        yield self.inter_pod_reduce_event

        # Phase 3: Broadcast within pods
        for step in range(pod_size - 1):
            send_dst = self.get_next_rank(worker_id)
            message = Message(
                source_id=worker_id,
                target_id=send_dst,
                data=f"intra_pod_broadcast_step_{step}",
                msg_type=MessageType.BROADCAST,
                timestamp=self.env.now
            )
            send(self.env, self.network, worker_id, send_dst, message, data_size=chunk_size)
            
            # Last worker in pod triggers the event
            if worker_id == pod_workers[-1]:
                self.intra_pod_broadcast_events[pod_id].succeed()
            # Wait for pod completion
            yield self.intra_pod_broadcast_events[pod_id] 
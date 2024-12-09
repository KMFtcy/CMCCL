from ns.switch.switch import SimplePacketSwitch
from ns.packet.packet import Packet
from ns.packet.sink import PacketSink
import copy
class BroadcastSwitch(SimplePacketSwitch):
    """Custom packet switch that overrides the put method to implement specific forwarding logic."""

    def __init__(self, env, nports: int, port_rate: float, buffer_size: int, node_id=None, nexthop_to_port=None, debug: bool = False):
        super().__init__(env, nports, port_rate, buffer_size, element_id=node_id, debug=debug)
        self.debug = debug
        self.node_id = node_id
        self.nexthop_to_port = nexthop_to_port if nexthop_to_port is not None else {}
        self.is_host = False  # 添加 is_host 属性

    def put(self, packet: Packet):
        """Sends a packet to this element with custom forwarding logic."""
        if getattr(packet, 'is_broadcast'):  # Check if the packet is a broadcast
            last_hop = packet.last_hop  # Get the last hop from the packet
            
            # host sink
            if self.is_host and int(last_hop) != int(self.node_id):
                self.forward_to_sink(packet)
                return
            
            if int(last_hop) == int(self.node_id):  # for source node, the last hop is itself
                last_hop_port = self.node_id
            else:
                # print(f"at node {self.node_id}, last_hop: {last_hop}, nexthop_to_port: {self.nexthop_to_port}")
                last_hop_port = self.nexthop_to_port[int(last_hop)]
            
            packet.last_hop = self.node_id

            # Forward to all connected devices except the port that leads to the last hop
            for port_num, port in enumerate(self.ports):
                # Only forward to connected ports (port.out is not None) and not the last hop port
                if port_num != int(last_hop_port) and port is not None and port.out is not None:
                    # print(f"forwarding packet {packet.packet_id} to port {port_num}")
                    # Forward the packet to the port, must deepcopy to avoid reference issue. Multiple will edit last hop on the same packet.
                    port.put(copy.deepcopy(packet)) 
        else:
            # Call the original put method for normal processing
            super().put(packet)

    def forward_to_sink(self, packet: Packet):
        """Forward the packet to a special sink."""
        ps = PacketSink(self.env, self.debug)
        ps.put(packet)
        # print(f"Forwarding packet {packet.packet_id} to sink from {self.node_id}.")
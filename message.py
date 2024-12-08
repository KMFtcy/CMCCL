from dataclasses import dataclass
from enum import Enum
from typing import Any

class MessageType(Enum):
    DATA = "DATA"
    CONTROL = "CONTROL"
    BROADCAST = "BROADCAST"
    REDUCE = "REDUCE"

@dataclass
class Message:
    source_id: int
    target_id: int
    data: Any
    msg_type: MessageType
    timestamp: float

    def __str__(self):
        return f"Message(from={self.source_id} to={self.target_id} type={self.msg_type.value})" 
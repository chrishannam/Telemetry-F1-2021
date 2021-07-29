import pickle
from pathlib import Path
from typing import Tuple, Dict

from packets import Packet


class PacketLoader:
    def __init__(self, path_to_packets: str = None):

        if not path_to_packets:
            self.path_to_packets = Path(__file__).parent

        self.packets: Dict[Tuple, Packet] = {}

    def fetch_packets(self):
        for packet in self.path_to_packets.glob(pattern='*.pickle'):
            with open(packet, 'rb') as raw_data:
                packet_data = pickle.load(raw_data)
                self.packets[f"{str(packet).replace('.pickle', '')}"] = packet_data
        return self.packets

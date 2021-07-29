from telemetry_f1_2021.example_packets.loader import PacketLoader


def test_packet_loader():
    pl = PacketLoader()
    packets = pl.fetch_packets()
    print(packets.keys())

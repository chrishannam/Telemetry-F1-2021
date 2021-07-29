import copy
import json
import pickle
from pathlib import Path

from telemetry_f1_2021.packets import HEADER_FIELD_TO_PACKET_TYPE

from telemetry_f1_2021.listener import TelemetryListener


def _get_listener():
    try:
        print('Starting listener on localhost:20777')
        return TelemetryListener()
    except OSError as exception:
        print(f'Unable to setup connection: {exception.args[1]}')
        print('Failed to open connector, stopping.')
        exit(127)


def main():
    listener = _get_listener()

    try:
        while True:
            packet = listener.get()
            print(packet)
    except KeyboardInterrupt:
        print('Stop the car, stop the car Checo.')
        print('Stop the car, stop at pit exit.')
        print('Just pull over to the side.')


def save_packets():
    samples = {}
    listener = _get_listener()
    packets_to_capture = copy.deepcopy(HEADER_FIELD_TO_PACKET_TYPE)

    # remove FinalClassification and LobbyInfo
    for k in [(2021, 1, 8), (2021, 1, 9)]:
        del HEADER_FIELD_TO_PACKET_TYPE[k]

    while len(samples) != len(list(HEADER_FIELD_TO_PACKET_TYPE)):
        packet = listener.get()

        key = (
            packet.m_header.m_packet_format,
            packet.m_header.m_packet_version,
            packet.m_header.m_packet_id,
        )

        if key in list(packets_to_capture):
            packet_type = HEADER_FIELD_TO_PACKET_TYPE[key].__name__
            samples[packet_type] = packet
            del packets_to_capture[key]

    root_dir = Path(__file__).parent

    for packet_name, packet in samples.items():
        with open(f'{root_dir}/example_packets/{packet_name}.pickle', 'wb') as fh:
            print(f'Saving packet: {root_dir}/example_packets/{packet_name}.pickle')
            pickle.dump(packet, fh, protocol=pickle.HIGHEST_PROTOCOL)

        with open(f'{root_dir}/example_packets/json/{packet_name}.json', 'w') as fh:
            json.dump(packet.to_dict(), fh, indent=2)

    print('Done!')


if __name__ == '__main__':
    main()

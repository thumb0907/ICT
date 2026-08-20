PACKET_START = 0xAA
PACKET_END = 0x55
PACKET_SIZE = 5


def calculate_crc8(data: bytes) -> int:
    crc = 0

    for value in data:
        crc ^= value

        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return crc


def build_packet(
    sequence: int,
    buttons: int,
) -> bytes:
    sequence &= 0xFF
    buttons &= 0xFF

    crc = calculate_crc8(
        bytes([sequence, buttons])
    )

    return bytes(
        [
            PACKET_START,
            sequence,
            buttons,
            crc,
            PACKET_END,
        ]
    )


def parse_packet(
    packet: bytes,
) -> tuple[int, int] | None:
    if len(packet) != PACKET_SIZE:
        return None

    if packet[0] != PACKET_START:
        return None

    if packet[4] != PACKET_END:
        return None

    sequence = packet[1]
    buttons = packet[2]
    received_crc = packet[3]

    expected_crc = calculate_crc8(
        bytes([sequence, buttons])
    )

    if received_crc != expected_crc:
        return None

    return sequence, buttons


class PacketParser:
    def __init__(self):
        self.buffer = bytearray()

    def feed(
        self,
        data: bytes,
    ) -> list[tuple[int, int]]:
        packets = []

        self.buffer.extend(data)

        while True:
            start_index = self.buffer.find(
                bytes([PACKET_START])
            )

            if start_index < 0:
                self.buffer.clear()
                break

            if start_index > 0:
                del self.buffer[:start_index]

            if len(self.buffer) < PACKET_SIZE:
                break

            candidate = bytes(
                self.buffer[:PACKET_SIZE]
            )

            parsed = parse_packet(candidate)

            if parsed is None:
                del self.buffer[0]
                continue

            packets.append(parsed)
            del self.buffer[:PACKET_SIZE]

        return packets
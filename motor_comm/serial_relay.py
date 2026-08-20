import argparse
import time

import serial

from packet_protocol import PacketParser
from packet_protocol import build_packet


BAUD_RATE = 115200


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validated situation STM to "
            "mobile STM serial relay"
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Situation STM COM port",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Mobile STM COM port",
    )

    args = parser.parse_args()

    print(f"Opening situation STM: {args.source}")
    print(f"Opening mobile STM: {args.target}")

    try:
        with serial.Serial(
            port=args.source,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
        ) as source_port, serial.Serial(
            port=args.target,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
            write_timeout=0.1,
        ) as target_port:

            source_port.reset_input_buffer()
            target_port.reset_output_buffer()

            packet_parser = PacketParser()

            raw_bytes = 0
            valid_packets = 0

            last_sequence = 0
            last_buttons = 0
            last_report_time = time.monotonic()

            print(
                f"Validated relay started: "
                f"{args.source} -> {args.target}"
            )
            print("Stop: Ctrl+C")

            try:
                while True:
                    read_size = source_port.in_waiting

                    if read_size == 0:
                        read_size = 1

                    data = source_port.read(read_size)

                    if data:
                        raw_bytes += len(data)

                        packets = packet_parser.feed(data)

                        for sequence, buttons in packets:
                            output_packet = build_packet(
                                sequence,
                                buttons,
                            )

                            target_port.write(output_packet)

                            valid_packets += 1
                            last_sequence = sequence
                            last_buttons = buttons

                    now = time.monotonic()

                    if now - last_report_time >= 1.0:
                        print(
                            f"Raw: {raw_bytes:3d} bytes/s | "
                            f"Valid: {valid_packets:2d} packets/s | "
                            f"Buttons: 0x{last_buttons:02X}"
                        )

                        raw_bytes = 0
                        valid_packets = 0
                        last_report_time = now

            except KeyboardInterrupt:
                print("\nRelay stop requested")

            finally:
                try:
                    stop_sequence = (
                        last_sequence + 1
                    ) & 0xFF

                    stop_packet = build_packet(
                        stop_sequence,
                        0,
                    )

                    target_port.write(stop_packet)
                    target_port.flush()

                    print("Stop packet transmitted")

                except serial.SerialException:
                    pass

    except serial.SerialException as error:
        print(f"Serial error: {error}")


if __name__ == "__main__":
    main()
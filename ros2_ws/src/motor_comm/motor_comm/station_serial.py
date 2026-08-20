import argparse
import time

import serial

from .packet_protocol import PacketParser


BAUD_RATE = 115200


class StationSerialReceiver:
    def __init__(self, port: str):
        self.serial_port = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0,
        )

        self.parser = PacketParser()
        self.serial_port.reset_input_buffer()

    def read_packets(
        self,
    ) -> list[tuple[int, int]]:
        read_size = self.serial_port.in_waiting

        if read_size == 0:
            return []

        data = self.serial_port.read(read_size)

        return self.parser.feed(data)

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ):
        self.close()


def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--port",
        required=True,
        help="Situation STM COM port",
    )

    args = argument_parser.parse_args()

    print(f"Opening situation STM: {args.port}")
    print("Stop: Ctrl+C")

    last_buttons = None

    try:
        with StationSerialReceiver(
            args.port
        ) as receiver:

            while True:
                packets = receiver.read_packets()

                for sequence, buttons in packets:
                    if buttons != last_buttons:
                        print(
                            f"Sequence: {sequence:3d} | "
                            f"Buttons: 0x{buttons:02X}"
                        )

                        last_buttons = buttons

                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStation reader stopped")

    except serial.SerialException as error:
        print(f"Serial error: {error}")


if __name__ == "__main__":
    main()
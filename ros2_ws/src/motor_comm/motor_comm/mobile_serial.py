import argparse
import time

import serial

from .packet_protocol import build_packet


BAUD_RATE = 115200
SEND_PERIOD_SECONDS = 0.05


class MobileSerialSender:
    def __init__(self, port: str):
        self.serial_port = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0,
            write_timeout=0.1,
        )

        self.sequence = 0
        self.serial_port.reset_output_buffer()

    def send_buttons(self, buttons: int):
        packet = build_packet(
            self.sequence,
            buttons,
        )

        self.serial_port.write(packet)

        self.sequence = (
            self.sequence + 1
        ) & 0xFF

    def send_stop(self, repeat: int = 3):
        for _ in range(repeat):
            self.send_buttons(0)
            time.sleep(0.01)

    def close(self):
        if not self.serial_port.is_open:
            return

        try:
            self.send_stop()
            self.serial_port.flush()

        except serial.SerialException:
            pass

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


def parse_buttons(value: str) -> int:
    buttons = int(value, 0)

    if not 0 <= buttons <= 0xFF:
        raise argparse.ArgumentTypeError(
            "buttons must be between 0x00 and 0xFF"
        )

    return buttons


def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--port",
        required=True,
        help="Mobile STM COM port",
    )

    argument_parser.add_argument(
        "--buttons",
        required=True,
        type=parse_buttons,
        help="Button bitmask, for example 0x01",
    )

    argument_parser.add_argument(
        "--duration",
        type=float,
        default=0.5,
        help="Command duration in seconds",
    )

    args = argument_parser.parse_args()

    if args.duration <= 0:
        argument_parser.error(
            "duration must be greater than zero"
        )

    print(f"Opening mobile STM: {args.port}")
    print(f"Buttons: 0x{args.buttons:02X}")
    print(f"Duration: {args.duration:.2f}s")

    try:
        with MobileSerialSender(
            args.port
        ) as sender:

            finish_time = (
                time.monotonic()
                + args.duration
            )

            while time.monotonic() < finish_time:
                sender.send_buttons(args.buttons)

                time.sleep(
                    SEND_PERIOD_SECONDS
                )

        print("Command complete and stop transmitted")

    except serial.SerialException as error:
        print(f"Serial error: {error}")


if __name__ == "__main__":
    main()
import argparse
import time

import serial

from mobile_serial import MobileSerialSender
from station_serial import StationSerialReceiver


SEND_PERIOD_SECONDS = 0.05
COMMAND_TIMEOUT_SECONDS = 0.2


def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--source",
        required=True,
        help="Situation STM COM port",
    )

    argument_parser.add_argument(
        "--target",
        required=True,
        help="Mobile STM COM port",
    )

    args = argument_parser.parse_args()

    print(f"Situation STM: {args.source}")
    print(f"Mobile STM: {args.target}")
    print("Stop: Ctrl+C")

    try:
        with StationSerialReceiver(
            args.source
        ) as receiver, MobileSerialSender(
            args.target
        ) as sender:

            latest_buttons = 0
            last_receive_time = 0.0
            next_send_time = time.monotonic()
            last_printed_buttons = None

            while True:
                now = time.monotonic()
                packets = receiver.read_packets()

                if packets:
                    _, latest_buttons = packets[-1]
                    last_receive_time = now

                link_ok = (
                    now - last_receive_time
                    < COMMAND_TIMEOUT_SECONDS
                )

                if link_ok:
                    output_buttons = latest_buttons
                else:
                    output_buttons = 0

                if now >= next_send_time:
                    sender.send_buttons(
                        output_buttons
                    )

                    next_send_time = (
                        now + SEND_PERIOD_SECONDS
                    )

                if output_buttons != last_printed_buttons:
                    print(
                        f"Link: "
                        f"{'OK' if link_ok else 'TIMEOUT'} | "
                        f"Buttons: 0x{output_buttons:02X}"
                    )

                    last_printed_buttons = (
                        output_buttons
                    )

                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nBridge stopped")

    except serial.SerialException as error:
        print(f"Serial error: {error}")


if __name__ == "__main__":
    main()
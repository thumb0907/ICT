import serial

import rclpy
from rclpy.node import Node

from std_msgs.msg import UInt8

from .station_serial import StationSerialReceiver


TOPIC_NAME = "/mobile_platform/button_state"
SERIAL_POLL_PERIOD_SECONDS = 0.005


class StationNode(Node):
    def __init__(self):
        super().__init__("station_node")

        self.declare_parameter(
            "port",
            "",
        )

        port = str(
            self.get_parameter("port").value
        )

        if not port:
            raise RuntimeError(
                "The 'port' parameter is required"
            )

        self.publisher = self.create_publisher(
            UInt8,
            TOPIC_NAME,
            1,
        )

        self.receiver = StationSerialReceiver(
            port
        )

        self.last_buttons = None

        self.timer = self.create_timer(
            SERIAL_POLL_PERIOD_SECONDS,
            self.poll_serial,
        )

        self.get_logger().info(
            f"Situation UART opened: {port}"
        )

        self.get_logger().info(
            f"Publishing to: {TOPIC_NAME}"
        )

    def poll_serial(self):
        packets = self.receiver.read_packets()

        if not packets:
            return

        sequence, buttons = packets[-1]

        message = UInt8()
        message.data = buttons

        self.publisher.publish(message)

        if buttons != self.last_buttons:
            self.get_logger().info(
                f"Sequence: {sequence} | "
                f"Buttons: 0x{buttons:02X}"
            )

            self.last_buttons = buttons

    def destroy_node(self):
        try:
            self.receiver.close()

        except (
            serial.SerialException,
            OSError,
            KeyboardInterrupt,
        ):
            pass

        return super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    node = None

    try:
        node = StationNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    except (
        serial.SerialException,
        RuntimeError,
    ) as error:
        print(f"Station node error: {error}")

    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
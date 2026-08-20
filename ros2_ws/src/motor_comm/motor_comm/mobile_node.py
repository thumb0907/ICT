import time

import serial

import rclpy
from rclpy.node import Node

from std_msgs.msg import UInt8

from .mobile_serial import MobileSerialSender


TOPIC_NAME = "/mobile_platform/button_state"

UART_SEND_PERIOD_SECONDS = 0.05
COMMAND_TIMEOUT_SECONDS = 0.2


class MobileNode(Node):
    def __init__(self):
        super().__init__("mobile_node")

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

        self.sender = MobileSerialSender(port)

        self.latest_buttons = 0
        self.last_message_time = None
        self.command_timed_out = True
        self.last_sent_buttons = None

        self.subscription = self.create_subscription(
            UInt8,
            TOPIC_NAME,
            self.receive_buttons,
            1,
        )

        self.timer = self.create_timer(
            UART_SEND_PERIOD_SECONDS,
            self.send_uart_command,
        )

        self.get_logger().info(
            f"Mobile UART opened: {port}"
        )

        self.get_logger().info(
            f"Subscribing to: {TOPIC_NAME}"
        )

    def receive_buttons(self, message):
        self.latest_buttons = int(message.data)
        self.last_message_time = time.monotonic()

    def send_uart_command(self):
        now = time.monotonic()

        timed_out = (
            self.last_message_time is None
            or now - self.last_message_time
            > COMMAND_TIMEOUT_SECONDS
        )

        if timed_out:
            buttons = 0
        else:
            buttons = self.latest_buttons

        if timed_out != self.command_timed_out:
            if timed_out:
                self.get_logger().warning(
                    "ROS command timeout: sending stop"
                )
            else:
                self.get_logger().info(
                    "ROS command stream connected"
                )

            self.command_timed_out = timed_out

        self.sender.send_buttons(buttons)

        if buttons != self.last_sent_buttons:
            self.get_logger().info(
                f"UART buttons: 0x{buttons:02X}"
            )

            self.last_sent_buttons = buttons

    def destroy_node(self):
        try:
            self.sender.close()

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
        node = MobileNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    except (
        serial.SerialException,
        RuntimeError,
    ) as error:
        print(f"Mobile node error: {error}")

    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
import rclpy
from rclpy.node import Node

from std_msgs.msg import UInt8


TOPIC_NAME = "/mobile_platform/button_state"
PUBLISH_PERIOD_SECONDS = 0.05


class StationNode(Node):
    def __init__(self):
        super().__init__("station_node")

        self.declare_parameter(
            "test_buttons",
            0,
        )

        self.publisher = self.create_publisher(
            UInt8,
            TOPIC_NAME,
            1,
        )

        self.timer = self.create_timer(
            PUBLISH_PERIOD_SECONDS,
            self.publish_command,
        )

        self.get_logger().info(
            f"Publishing test commands to {TOPIC_NAME}"
        )

    def publish_command(self):
        buttons = int(
            self.get_parameter(
                "test_buttons"
            ).value
        )

        buttons = max(
            0,
            min(255, buttons),
        )

        message = UInt8()
        message.data = buttons

        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)

    node = StationNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
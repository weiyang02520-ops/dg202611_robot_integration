"""Publish synthetic or file-backed RGB images for no-camera smoke tests.

Not a ZED source. Useful on Ubuntu103 when /dev/video* is missing.

Parameters:
  image_path / npy_path / fake_image_path: optional local RGB file
    (.jpg/.jpeg/.png via OpenCV, or HxWx3 .npy). Prefer a real bottle/cup
    photo for non-empty detections; solid-colour defaults often yield [].
"""

from __future__ import annotations

import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image

from vision_perception.fake_image_source import load_fake_rgb, resolve_fake_image_path


class FakeImagePublisherNode(Node):
    def __init__(self):
        super().__init__("vision_fake_image_publisher")
        self.declare_parameter("image_topic", "/dg/vision/webcam/image_raw")
        self.declare_parameter("frame_id", "fake_webcam_optical_frame")
        self.declare_parameter("frame_rate_hz", 5.0)
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 480)
        # Aliases: image_path (preferred), fake_image_path (launch), npy_path (legacy).
        self.declare_parameter("image_path", "")
        self.declare_parameter("fake_image_path", "")
        self.declare_parameter("npy_path", "")

        topic = str(self.get_parameter("image_topic").value)
        rate = float(self.get_parameter("frame_rate_hz").value)
        if rate <= 0:
            raise ValueError("frame_rate_hz must be > 0")
        self._frame_id = str(self.get_parameter("frame_id").value)

        path = resolve_fake_image_path(
            str(self.get_parameter("image_path").value),
            str(self.get_parameter("fake_image_path").value),
            str(self.get_parameter("npy_path").value),
        )
        self._rgb, note = load_fake_rgb(
            path,
            width=int(self.get_parameter("width").value),
            height=int(self.get_parameter("height").value),
        )
        if path:
            self.get_logger().warning(
                f"DEV fake RGB from {note} (NOT_ZED). "
                "Use a real bottle/cup photo for non-empty detections."
            )
        else:
            self.get_logger().warning(
                "DEV fake RGB colour blocks (NOT_ZED); detections often []. "
                "Pass fake_image_path:=/ABS/bottle.jpg for non-empty smoke."
            )

        self._pub = self.create_publisher(Image, topic, 10)
        self._timer = self.create_timer(1.0 / rate, self._tick)

    def _tick(self):
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.height = int(self._rgb.shape[0])
        msg.width = int(self._rgb.shape[1])
        msg.encoding = "rgb8"
        msg.is_bigendian = 0
        msg.step = int(msg.width * 3)
        msg.data = self._rgb.tobytes()
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = None
    exit_code = 0
    try:
        node = FakeImagePublisherNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"[vision_fake_image_publisher] FATAL: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

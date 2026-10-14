"""Publish synthetic or file-backed RGB images for no-camera smoke tests.

Not a ZED source. Useful on Ubuntu103 when /dev/video* is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image


class FakeImagePublisherNode(Node):
    def __init__(self):
        super().__init__("vision_fake_image_publisher")
        self.declare_parameter("image_topic", "/dg/vision/webcam/image_raw")
        self.declare_parameter("frame_id", "fake_webcam_optical_frame")
        self.declare_parameter("frame_rate_hz", 5.0)
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 480)
        self.declare_parameter("npy_path", "")

        topic = str(self.get_parameter("image_topic").value)
        rate = float(self.get_parameter("frame_rate_hz").value)
        if rate <= 0:
            raise ValueError("frame_rate_hz must be > 0")
        self._frame_id = str(self.get_parameter("frame_id").value)

        npy_path = str(self.get_parameter("npy_path").value).strip()
        if npy_path:
            array = np.load(npy_path)
            if array.ndim != 3 or array.shape[2] != 3:
                raise ValueError(f"npy_path must be HxWx3 RGB, got {array.shape}")
            self._rgb = np.ascontiguousarray(array, dtype=np.uint8)
            self.get_logger().info(f"fake image from {Path(npy_path).name}")
        else:
            width = int(self.get_parameter("width").value)
            height = int(self.get_parameter("height").value)
            self._rgb = np.zeros((height, width, 3), dtype=np.uint8)
            # Visible colour blocks so subscribers can confirm data flow.
            self._rgb[:, : width // 2, 0] = 200
            self._rgb[:, width // 2 :, 2] = 200
            self.get_logger().warning(
                "DEV fake RGB publisher (no camera file); not a ZED source"
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

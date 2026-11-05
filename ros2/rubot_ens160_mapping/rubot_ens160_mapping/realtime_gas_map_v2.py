#!/usr/bin/env python3
"""Mapa de gases V2: callbacks ligeros y actualización a 2 Hz."""

import math
import time
from collections import defaultdict, deque

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from ens160_interfaces.msg import ENS160Reading
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import Buffer, TransformListener, TransformException


class RealtimeGasMapV2(Node):

    def __init__(self):
        super().__init__('realtime_gas_map_v2')

        self.cell_size = 0.20
        self.eco2_min = 400.0
        self.eco2_max = 700.0
        self.window_seconds = 10.0

        self.cells = defaultdict(deque)
        self.pending_max = None

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer, self
        )

        self.sub = self.create_subscription(
            ENS160Reading,
            '/ens160/readings',
            self.sensor_callback,
            10
        )

        self.publisher = self.create_publisher(
            MarkerArray,
            '/gas_map_markers_v2',
            10
        )

        self.timer = self.create_timer(
            0.5,
            self.update_map
        )

        self.get_logger().info(
            'Gas Map V2 iniciado - actualización 2 Hz'
        )

    def sensor_callback(self, msg):
        """Solo recoge el máximo entre actualizaciones."""

        value = float(msg.eco2_ppm)

        if not math.isfinite(value):
            return

        if self.pending_max is None:
            self.pending_max = value
        else:
            self.pending_max = max(
                self.pending_max, value
            )

    def get_color(self, value):

        t = (value - self.eco2_min) / (
            self.eco2_max - self.eco2_min
        )
        t = max(0.0, min(1.0, t))

        if t < 0.5:
            r, g, b = 0.0, 2*t, 1-2*t
        else:
            r, g, b = 2*(t-0.5), 2*(1-t), 0.0

        return ColorRGBA(
            r=float(r),
            g=float(g),
            b=float(b),
            a=0.85
        )

    def update_map(self):

        now = time.monotonic()

        if self.pending_max is not None:

            try:
                tf = self.tf_buffer.lookup_transform(
                    'map', 'base_link', Time()
                )

                x = tf.transform.translation.x
                y = tf.transform.translation.y

                i = math.floor(x / self.cell_size)
                j = math.floor(y / self.cell_size)

                self.cells[(i, j)].append(
                    (now, self.pending_max)
                )

                self.pending_max = None

            except TransformException:
                pass

        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = (
            self.get_clock().now().to_msg()
        )

        marker.ns = 'gas_map_v2'
        marker.id = 0
        marker.type = Marker.CUBE_LIST
        marker.action = Marker.ADD

        marker.pose.orientation.w = 1.0
        marker.lifetime.sec = 2

        marker.scale.x = self.cell_size
        marker.scale.y = self.cell_size
        marker.scale.z = 0.02

        for (i, j), samples in list(self.cells.items()):

            while samples and (
                now - samples[0][0] > self.window_seconds
            ):
                samples.popleft()

            if not samples:
                del self.cells[(i, j)]
                continue

            value = max(v for _, v in samples)

            point = Point()
            point.x = (i + 0.5) * self.cell_size
            point.y = (j + 0.5) * self.cell_size
            point.z = 0.05

            marker.points.append(point)
            marker.colors.append(
                self.get_color(value)
            )

        self.publisher.publish(
            MarkerArray(markers=[marker])
        )


def main():
    rclpy.init()
    node = RealtimeGasMapV2()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""Mapa de eCO2 en tiempo real mediante medias por celda."""

import math
from collections import defaultdict

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from ens160_interfaces.msg import ENS160Reading
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import Buffer, TransformListener, TransformException


class RealtimeGasMap(Node):

    def __init__(self):
        super().__init__('realtime_gas_map')

        # Parámetros iniciales del experimento
        self.cell_size = 0.20
        self.eco2_min = 400.0
        self.eco2_max = 600.0

        # Cada celda almacena [suma_eCO2, numero_muestras]
        self.cells = defaultdict(lambda: [0.0, 0])

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.sub = self.create_subscription(
            ENS160Reading,
            '/ens160/readings',
            self.sensor_callback,
            10
        )

        self.publisher = self.create_publisher(
            MarkerArray,
            '/gas_map_markers',
            10
        )

        # Publicación del mapa dos veces por segundo
        self.timer = self.create_timer(0.5, self.publish_map)

        self.get_logger().info(
            'Mapa de gases iniciado: celdas de 0.20 m'
        )

    def sensor_callback(self, msg):
        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                Time()
            )
        except TransformException:
            return

        x = transform.transform.translation.x
        y = transform.transform.translation.y

        i = math.floor(x / self.cell_size)
        j = math.floor(y / self.cell_size)

        value = float(msg.eco2_ppm)

        if not math.isfinite(value):
            return

        self.cells[(i, j)][0] += value
        self.cells[(i, j)][1] += 1

    def get_color(self, value):
        # Escala inicial azul -> verde -> rojo
        t = (value - self.eco2_min) / (
            self.eco2_max - self.eco2_min
        )
        t = max(0.0, min(1.0, t))

        if t < 0.5:
            r = 0.0
            g = 2.0 * t
            b = 1.0 - 2.0 * t
        else:
            r = 2.0 * (t - 0.5)
            g = 2.0 * (1.0 - t)
            b = 0.0

        return ColorRGBA(
            r=float(r),
            g=float(g),
            b=float(b),
            a=0.85
        )

    def publish_map(self):
        marker = Marker()

        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'realtime_gas_map'
        marker.id = 0
        marker.type = Marker.CUBE_LIST
        marker.action = Marker.ADD

        marker.pose.orientation.w = 1.0

        marker.scale.x = self.cell_size
        marker.scale.y = self.cell_size
        marker.scale.z = 0.02

        for (i, j), (total, count) in self.cells.items():
            mean_eco2 = total / count

            point = Point()
            point.x = (i + 0.5) * self.cell_size
            point.y = (j + 0.5) * self.cell_size
            point.z = 0.05

            marker.points.append(point)
            marker.colors.append(self.get_color(mean_eco2))

        self.publisher.publish(MarkerArray(markers=[marker]))


def main(args=None):
    rclpy.init(args=args)
    node = RealtimeGasMap()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


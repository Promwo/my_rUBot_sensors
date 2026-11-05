#!/usr/bin/env python3
"""Mapa espacial acumulativo con maximo historico de eCO2."""

import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from ens160_interfaces.msg import ENS160Reading
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import Buffer, TransformListener, TransformException


class RealtimeGasMapV3(Node):

    def __init__(self):
        super().__init__('realtime_gas_map_v3')

        self.cell_size = 0.30
        self.eco2_min = 400.0
        self.eco2_max = 700.0

        # Diccionario: celda -> [suma_eCO2, muestras]
        self.cells = {}  # celda -> maximo historico

        # Lecturas pendientes entre actualizaciones
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
            '/gas_map_markers_v3',
            10
        )

        self.timer = self.create_timer(
            0.5,
            self.update_map
        )

        self.get_logger().info(
            'Gas Map V3 iniciado | mapa acumulativo | '
            'celda=0.30m | modo=MAX HISTORICO | escala=400-700ppm'
        )

    def sensor_callback(self, msg):
        """Recoge lecturas sin realizar consultas TF."""

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
        """Gradiente azul -> verde -> rojo."""

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

    def update_map(self):

        # Obtener posición del robot una vez por ciclo
        if self.pending_max is not None:

            try:
                tf = self.tf_buffer.lookup_transform(
                    'map',
                    'base_link',
                    Time()
                )

            except TransformException:
                tf = None

            if tf is not None:
                x = tf.transform.translation.x
                y = tf.transform.translation.y

                i = math.floor(x / self.cell_size)
                j = math.floor(y / self.cell_size)

                cell = (i, j)

                current_max = self.pending_max

                # Actualizar con la medicion mas reciente
                self.cells[cell] = current_max

                self.pending_max = None

        # Crear marcador acumulativo
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = (
            self.get_clock().now().to_msg()
        )

        marker.ns = 'gas_map_v3'
        marker.id = 0
        marker.type = Marker.CUBE_LIST
        marker.action = Marker.ADD

        marker.pose.orientation.w = 1.0

        marker.scale.x = self.cell_size
        marker.scale.y = self.cell_size
        marker.scale.z = 0.02

        # Representar todas las celdas acumuladas
        for (i, j), max_eco2 in self.cells.items():

            point = Point()
            point.x = (i + 0.5) * self.cell_size
            point.y = (j + 0.5) * self.cell_size
            point.z = 0.05

            marker.points.append(point)
            marker.colors.append(
                self.get_color(max_eco2)
            )

        self.publisher.publish(
            MarkerArray(markers=[marker])
        )


def main():
    rclpy.init()
    node = RealtimeGasMapV3()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

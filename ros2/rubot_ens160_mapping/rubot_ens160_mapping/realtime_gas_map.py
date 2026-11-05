
#!/usr/bin/env python3
"""Mapa de gases en tiempo real con máximo eCO2 de los últimos 10 segundos."""

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


class RealtimeGasMap(Node):

    def __init__(self):
        super().__init__('realtime_gas_map')

        # Configuración del mapa
        self.cell_size = 0.20
        self.eco2_min = 400.0
        self.eco2_max = 700.0
        self.window_seconds = 10.0

        # Cada celda contiene (tiempo, eCO2)
        self.cells = defaultdict(deque)

        # Transformaciones TF
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Suscriptor ENS160
        self.sub = self.create_subscription(
            ENS160Reading,
            '/ens160/readings',
            self.sensor_callback,
            10
        )

        # Publicador para RViz
        self.publisher = self.create_publisher(
            MarkerArray,
            '/gas_map_markers',
            10
        )

        # Actualizar dos veces por segundo
        self.timer = self.create_timer(
            0.5,
            self.publish_map
        )

        self.get_logger().info(
            'Realtime Gas Map iniciado | '
            'celda=0.20m | ventana=10s | '
            'modo=MAX | escala=400-700ppm'
        )

    def sensor_callback(self, msg):

        # Obtener posición del robot en el mapa
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

        # Calcular índice de celda
        i = math.floor(x / self.cell_size)
        j = math.floor(y / self.cell_size)

        # Leer eCO2
        value = float(msg.eco2_ppm)

        if not math.isfinite(value):
            return

        # Guardar muestra con tiempo de recepción
        self.cells[(i, j)].append(
            (time.monotonic(), value)
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

    def publish_map(self):

        now = time.monotonic()

        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'realtime_gas_map'
        marker.id = 0
        marker.type = Marker.CUBE_LIST
        marker.action = Marker.ADD

        # El marcador caduca si dejamos de publicarlo
        marker.lifetime.sec = 2

        marker.pose.orientation.w = 1.0

        marker.scale.x = self.cell_size
        marker.scale.y = self.cell_size
        marker.scale.z = 0.02

        # Procesar cada celda
        for (i, j), samples in list(self.cells.items()):

            # Eliminar muestras antiguas
            while samples and (
                now - samples[0][0] > self.window_seconds
            ):
                samples.popleft()

            # Eliminar celdas sin muestras recientes
            if not samples:
                del self.cells[(i, j)]
                continue

            # Máximo eCO2 de los últimos 10 segundos
            max_eco2 = max(
                value for _, value in samples
            )

            # Centro de la celda
            point = Point()
            point.x = (i + 0.5) * self.cell_size
            point.y = (j + 0.5) * self.cell_size
            point.z = 0.05

            marker.points.append(point)
            marker.colors.append(
                self.get_color(max_eco2)
            )

        # Publicar todas las celdas en RViz
        self.publisher.publish(
            MarkerArray(markers=[marker])
        )


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


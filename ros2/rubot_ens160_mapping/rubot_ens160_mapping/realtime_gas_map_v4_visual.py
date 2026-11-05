#!/usr/bin/env python3
"""Mapa de gases V4: celdas grises libres y eCO2 acumulativo."""

import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from nav_msgs.msg import OccupancyGrid
from ens160_interfaces.msg import ENS160Reading
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import Buffer, TransformListener, TransformException


class RealtimeGasMapV4(Node):

    def __init__(self):
        super().__init__('realtime_gas_map_v4_visual')

        # Configuracion
        self.cell_size = 0.30
        self.eco2_min = 400.0
        self.eco2_max = 700.0
        self.free_threshold = 20

        # Ultima medicion por celda
        self.cells = {}

        # Celdas libres descubiertas por Cartographer
        self.free_cells = set()
        self.latest_map = None

        # Lecturas pendientes
        self.pending_max = None

        # Transformaciones
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer, self
        )

        # Suscriptor a los sensores
        self.sensor_sub = self.create_subscription(
            ENS160Reading,
            '/ens160/readings',
            self.sensor_callback,
            10
        )

        # Suscriptor al mapa SLAM
        map_qos = QoSProfile(depth=1)
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            map_qos
        )

        # Publicador RViz
        self.publisher = self.create_publisher(
            MarkerArray,
            '/gas_map_markers_v4_visual',
            10
        )

        # Sensores y visualizacion: 2 Hz
        self.timer = self.create_timer(
            0.5,
            self.update_map
        )

        # Recalcular espacio libre cada 3 segundos
        self.grid_timer = self.create_timer(
            3.0,
            self.update_free_cells
        )

        self.get_logger().info(
            'V4 iniciada | celdas 30cm | '
            'gris=libre | color=eCO2'
        )

    def sensor_callback(self, msg):
        """Callback ligero, como en la V3."""

        value = float(msg.eco2_ppm)

        if not math.isfinite(value):
            return

        if self.pending_max is None:
            self.pending_max = value
        else:
            self.pending_max = max(
                self.pending_max, value
            )

    def map_callback(self, msg):
        """Guardar el ultimo mapa de Cartographer."""
        self.latest_map = msg

    def update_free_cells(self):
        """Construir celdas grises sobre espacio conocido y libre."""

        msg = self.latest_map

        if msg is None:
            return

        info = msg.info
        resolution = info.resolution
        width = info.width
        height = info.height

        if resolution <= 0 or width == 0 or height == 0:
            return

        origin = info.origin
        ox = origin.position.x
        oy = origin.position.y

        q = origin.orientation
        yaw = math.atan2(
            2 * (q.w * q.z + q.x * q.y),
            1 - 2 * (q.y * q.y + q.z * q.z)
        )

        co = math.cos(yaw)
        si = math.sin(yaw)

        # Esquinas del mapa en coordenadas globales
        corners = []
        for lx in (0, width * resolution):
            for ly in (0, height * resolution):
                corners.append((
                    ox + co * lx - si * ly,
                    oy + si * lx + co * ly
                ))

        imin = math.floor(
            min(x for x, y in corners) / self.cell_size
        )
        imax = math.ceil(
            max(x for x, y in corners) / self.cell_size
        )

        jmin = math.floor(
            min(y for x, y in corners) / self.cell_size
        )
        jmax = math.ceil(
            max(y for x, y in corners) / self.cell_size
        )

        # Evitar un calculo excesivo en mapas grandes
        total = (imax - imin) * (jmax - jmin)

        if total > 20000:
            self.get_logger().warn(
                'Mapa demasiado grande para la cuadricula V4.'
            )
            return

        free = set()
        data = msg.data

        # Comprobar 25 puntos dentro de cada celda
        samples = (0.1, 0.3, 0.5, 0.7, 0.9)

        for i in range(imin, imax):
            for j in range(jmin, jmax):

                valid = True

                for fx in samples:
                    if not valid:
                        break

                    for fy in samples:

                        x = (i + fx) * self.cell_size
                        y = (j + fy) * self.cell_size

                        # Coordenadas locales del OccupancyGrid
                        dx = x - ox
                        dy = y - oy

                        lx = co * dx + si * dy
                        ly = -si * dx + co * dy

                        mx = math.floor(lx / resolution)
                        my = math.floor(ly / resolution)

                        if not (
                            0 <= mx < width and
                            0 <= my < height
                        ):
                            valid = False
                            break

                        occupancy = data[my * width + mx]

                        # Desconocido u ocupado: no dibujar
                        if occupancy < 0 or occupancy > self.free_threshold:
                            valid = False
                            break

                if valid:
                    free.add((i, j))

        self.free_cells = free

    def get_color(self, value):
        """Gradiente azul -> verde -> rojo."""

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
            a=0.90
        )

    def update_map(self):
        """Actualizar mediciones y publicar toda la cuadricula."""

        # Obtener posicion si hay lecturas nuevas
        if self.pending_max is not None:

            try:
                tf = self.tf_buffer.lookup_transform(
                    'map',
                    'base_link',
                    Time()
                )

                x = tf.transform.translation.x
                y = tf.transform.translation.y

                i = math.floor(x / self.cell_size)
                j = math.floor(y / self.cell_size)

                # Como en la ultima V3:
                # sustituir por la medicion mas reciente
                self.cells[(i, j)] = self.pending_max

                self.pending_max = None

            except TransformException:
                pass


        # Dos marcadores independientes:
        # gris para zonas libres y color para eCO2.

        def make_marker(marker_id, namespace, alpha):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = namespace
            marker.id = marker_id
            marker.type = Marker.TRIANGLE_LIST
            marker.action = Marker.ADD

            marker.pose.orientation.w = 1.0

            # TRIANGLE_LIST usa vertices en metros.
            marker.scale.x = 1.0
            marker.scale.y = 1.0
            marker.scale.z = 1.0

            marker.color.a = alpha

            return marker

        gray_marker = make_marker(
            0, 'gas_v4_visual_gray', 0.35
        )

        gas_marker = make_marker(
            1, 'gas_v4_visual_eco2', 0.90
        )

        def add_square(marker, i, j, z, color):

            x0 = i * self.cell_size
            y0 = j * self.cell_size

            x1 = x0 + self.cell_size
            y1 = y0 + self.cell_size

            # Dos triangulos forman un cuadrado plano.
            vertices = [
                (x0, y0), (x1, y0), (x1, y1),
                (x0, y0), (x1, y1), (x0, y1)
            ]

            for x, y in vertices:
                marker.points.append(
                    Point(x=x, y=y, z=z)
                )

                marker.colors.append(
                    ColorRGBA(
                        r=color.r,
                        g=color.g,
                        b=color.b,
                        a=1.0
                    )
                )

        # Zonas libres sin mediciones: gris.
        gray = ColorRGBA(
            r=0.75, g=0.78, b=0.82, a=1.0
        )

        for i, j in self.free_cells:

            if (i, j) in self.cells:
                continue

            add_square(
                gray_marker, i, j, 0.04, gray
            )

        # Zonas medidas: color segun eCO2.
        for (i, j), eco2 in self.cells.items():

            color = self.get_color(eco2)

            add_square(
                gas_marker, i, j, 0.05, color
            )

        self.publisher.publish(
            MarkerArray(
                markers=[gray_marker, gas_marker]
            )
        )


def main():
    rclpy.init()
    node = RealtimeGasMapV4()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

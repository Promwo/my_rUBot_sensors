#!/usr/bin/env python3

"""
TFG - rUBot07

Mapa de gases V4 Visual con trayectoria del robot.

Funcionalidades:
- Conserva el mapa de gases V4 Visual original.
- Representa la trayectoria del robot.
- Utiliza el sistema de referencia 'map'.
- Actualiza la trayectoria cada 0.2 segundos.
- Añade puntos cuando el robot avanza al menos 5 cm.
- Publica la trayectoria en /robot_path_markers.

La V4 Visual original permanece sin modificaciones.
"""

import math

import rclpy
from rclpy.time import Time

from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray

from tf2_ros import TransformException

from realtime_gas_map_v4_visual import RealtimeGasMapV4


class RealtimeGasMapV4Path(RealtimeGasMapV4):

    def __init__(self):

        super().__init__()

        # -----------------------------------------
        # CONFIGURACIÓN DE LA TRAYECTORIA
        # -----------------------------------------

        # Distancia mínima entre puntos: 5 cm
        self.min_path_distance = 0.05

        # Altura de la línea sobre el mapa
        self.path_height = 0.08

        # Grosor de la línea: 2 cm
        self.path_width = 0.02

        # Lista de puntos recorridos
        self.path_points = []

        # -----------------------------------------
        # PUBLICADOR
        # -----------------------------------------

        self.path_publisher = self.create_publisher(
            MarkerArray,
            '/robot_path_markers',
            10
        )

        # -----------------------------------------
        # TEMPORIZADOR
        # -----------------------------------------

        # Actualizar cada 0.2 segundos
        self.path_timer = self.create_timer(
            0.2,
            self.update_path
        )

        self.get_logger().info(
            'V4 Visual con trayectoria iniciada correctamente.'
        )

    def update_path(self):

        # -----------------------------------------
        # OBTENER POSICIÓN DEL ROBOT EN MAP
        # -----------------------------------------

        try:

            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                Time()
            )

            x = transform.transform.translation.x
            y = transform.transform.translation.y

        except TransformException:

            return

        # Comprobar coordenadas
        if not math.isfinite(x) or not math.isfinite(y):
            return

        # -----------------------------------------
        # GUARDAR PUNTOS DE LA TRAYECTORIA
        # -----------------------------------------

        if len(self.path_points) == 0:

            # Primera posición
            self.path_points.append(
                Point(
                    x=x,
                    y=y,
                    z=self.path_height
                )
            )

        else:

            # Última posición almacenada
            last_point = self.path_points[-1]

            # Distancia desde el último punto
            distance = math.hypot(
                x - last_point.x,
                y - last_point.y
            )

            # Guardar solamente si avanzamos 5 cm
            if distance >= self.min_path_distance:

                self.path_points.append(
                    Point(
                        x=x,
                        y=y,
                        z=self.path_height
                    )
                )

        # -----------------------------------------
        # CREAR MARCADOR DE TRAYECTORIA
        # -----------------------------------------

        marker = Marker()

        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'robot_trajectory'
        marker.id = 0

        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD

        marker.pose.orientation.w = 1.0

        # Grosor de la línea
        marker.scale.x = self.path_width

        # Color amarillo
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 1.0

        # Trayectoria completa
        marker.points = self.path_points

        # El marcador permanece visible
        marker.lifetime.sec = 0
        marker.lifetime.nanosec = 0

        # -----------------------------------------
        # PUBLICAR
        # -----------------------------------------

        self.path_publisher.publish(
            MarkerArray(
                markers=[marker]
            )
        )


def main(args=None):

    rclpy.init(args=args)

    node = RealtimeGasMapV4Path()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':

    main()

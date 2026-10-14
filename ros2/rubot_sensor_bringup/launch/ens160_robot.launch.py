"""Launch the robust physical rUBot bringup together with the ENS160 array."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogError,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_model = LaunchConfiguration("robot_model")
    robot_port = LaunchConfiguration("robot_port")
    lidar_port = LaunchConfiguration("lidar_port")
    lidar_frame_id = LaunchConfiguration("lidar_frame_id")
    camera_device = LaunchConfiguration("camera_device")
    camera_width = LaunchConfiguration("camera_width")
    camera_height = LaunchConfiguration("camera_height")
    camera_pixel_format = LaunchConfiguration("camera_pixel_format")
    camera_output_encoding = LaunchConfiguration("camera_output_encoding")
    sensor_port = LaunchConfiguration("sensor_port")
    sensor_baud_rate = LaunchConfiguration("sensor_baud_rate")

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("my_robot_bringup"),
            "launch",
            "my_robot_bringup_robust_hw.launch.py",
        )),
        launch_arguments={
            "robot_model": robot_model,
            "mecanum_serial_port": robot_port,
            "rplidar_serial_port": lidar_port,
            "rplidar_frame_id": lidar_frame_id,
            "usb_video_device": camera_device,
            "camera_width": camera_width,
            "camera_height": camera_height,
            "camera_pixel_format": camera_pixel_format,
            "camera_output_encoding": camera_output_encoding,
        }.items(),
    )

    sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("ens160_air_quality_ros"),
            "launch",
            "air_quality.launch.py",
        )),
        launch_arguments={
            "port": sensor_port,
            "baud_rate": sensor_baud_rate,
        }.items(),
    )

    wait_for_sensor = ExecuteProcess(
        cmd=[
            "python3",
            os.path.join(
                get_package_share_directory("my_robot_bringup"),
                "scripts",
                "wait_for_devices.py",
            ),
            "--serial", sensor_port,
            "--timeout", "30",
        ],
        output="screen",
        name="wait_for_ens160_device",
    )

    def start_sensor_after_wait(event, context):
        del context
        if event.returncode != 0:
            return [
                LogError(msg="ENS160 device check failed; stopping bringup."),
                EmitEvent(event=Shutdown(reason="ENS160 device is not ready")),
            ]
        return [sensor_launch]

    start_sensor_when_ready = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_for_sensor,
            on_exit=start_sensor_after_wait,
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "robot_model", default_value="rubot_arm/my_simple_robot.urdf"
        ),
        DeclareLaunchArgument("robot_port", default_value="/dev/robot_arduino"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/robot_lidar"),
        DeclareLaunchArgument("lidar_frame_id", default_value="base_scan"),
        DeclareLaunchArgument("camera_device", default_value="/dev/robot_camera"),
        DeclareLaunchArgument("camera_width", default_value="640"),
        DeclareLaunchArgument("camera_height", default_value="480"),
        DeclareLaunchArgument("camera_pixel_format", default_value="YUYV"),
        DeclareLaunchArgument("camera_output_encoding", default_value="rgb8"),
        DeclareLaunchArgument("sensor_port", default_value="/dev/ens160"),
        DeclareLaunchArgument("sensor_baud_rate", default_value="9600"),
        robot_launch,
        start_sensor_when_ready,
        wait_for_sensor,
    ])

"""Launch the physical mecanum rUBot together with the ENS160 array."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory("my_robot_bringup"),
            "/launch/my_robot_bringup_hw.launch.py",
        ]),
        launch_arguments={
            "mecanum_serial_port": LaunchConfiguration("robot_port"),
            "rplidar_serial_port": LaunchConfiguration("lidar_port"),
        }.items(),
    )

    sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory("ens160_air_quality_ros"),
            "/launch/air_quality.launch.py",
        ]),
        launch_arguments={
            "port": LaunchConfiguration("sensor_port"),
            "baud_rate": LaunchConfiguration("sensor_baud_rate"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("robot_port", default_value="/dev/ttyACM0"),
        DeclareLaunchArgument("sensor_port", default_value="/dev/ens160"),
        DeclareLaunchArgument("sensor_baud_rate", default_value="9600"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
        robot_launch,
        sensor_launch,
    ])

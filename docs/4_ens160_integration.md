# ENS160 Integration

The initial hardware architecture is inherited from the previous
`ENS160_rUBot` project:

- Six ENS160 sensors.
- TCA9548A I2C multiplexer using channels 0 to 5.
- Arduino Nano 33 IoT.
- USB serial communication at 9600 baud.

The firmware and generic ROS 2 publisher are maintained in
`ENS160_air_quality`. This repository consumes the `/ens160/readings` topic and
adds robot and map context.

Before hardware operation, verify the physical board, sensor mounting
positions and electrical connections.

## Persistent serial device

Linux names such as `/dev/ttyACM0` and `/dev/ttyACM1` depend on connection
order. The ENS160 repository provides a serial-number-specific `udev` rule and
the authoritative installation procedure:

- [`ENS160_air_quality/docs/3_udev_rules.md`](https://github.com/manelpuig/ENS160_air_quality/blob/main/docs/3_udev_rules.md)
- [`99-ens160.rules.example`](https://github.com/manelpuig/ENS160_air_quality/blob/main/udev/99-ens160.rules.example)

After installing that rule, the sensor array is available as `/dev/ens160`.
The launch and configuration files in this repository use that persistent name
by default:

```bash
ros2 launch rubot_sensor_bringup ens160_robot.launch.py \
  sensor_port:=/dev/ens160
```

The robot controller and the ENS160 controller must use different USB device
aliases. A separate rule for the robot belongs in `my_rUBot_mecanum`.

# my_rUBot Sensors

Integration of environmental sensors with the mecanum rUBot using ROS 2.

This repository contains only the software that combines robot state,
navigation and sensor measurements. Robot drivers remain in
[`my_rUBot_mecanum`](https://github.com/manelpuig/my_rUBot_mecanum), while
sensor firmware and generic sensor drivers remain in their own repositories,
starting with
[`ENS160_air_quality`](https://github.com/manelpuig/ENS160_air_quality).

## Repository responsibilities

| Repository | Responsibility |
| --- | --- |
| `my_rUBot_mecanum` | Robot description, drivers, control and navigation |
| `ENS160_air_quality` | ENS160 firmware, standalone tools and ROS 2 driver |
| `my_rUBot_sensors` | Robot-sensor bringup, spatial logging and mapping |

## ROS 2 packages

| Package | Purpose |
| --- | --- |
| `rubot_sensor_bringup` | Launch and configure the robot and sensor stack |
| `rubot_ens160_mapping` | Associate ENS160 readings with robot poses and create spatial datasets |

The repository is designed to support additional sensors later without moving
their generic drivers into this project.

## Workspace layout

The three repositories are independent clones inside the same ROS 2 workspace:

```text
my_rUBot_sensor_ws/
└── src/
    ├── my_rUBot_mecanum/
    ├── ENS160_air_quality/
    └── my_rUBot_sensors/
```

See [Workspace setup](docs/2_workspace_setup.md) for installation and build
instructions. See [Development workflow](docs/3_development_workflow.md) for the
fork and pull-request workflow used by the supervisor and student.

## Project status

Initial package structure and documentation. The next development stage will
port and refactor the spatial logging and mapping functions from the previous
`ENS160_rUBot` project.

## Documentation

- [1. Architecture](docs/1_architecture.md)
- [2. Workspace setup](docs/2_workspace_setup.md)
- [3. Development workflow](docs/3_development_workflow.md)
- [4. ENS160 integration](docs/4_ens160_integration.md)
- [5. Mapping workflow](docs/5_mapping_workflow.md)
- [6. Experimental methodology](docs/6_experiments.md)

## License

Apache License 2.0. See [LICENSE](LICENSE).

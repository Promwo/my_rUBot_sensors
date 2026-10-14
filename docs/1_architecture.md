# Architecture

## Repository boundaries

`my_rUBot_sensors` integrates other projects without copying their source
code. Each repository remains independently versioned and synchronized.

```text
my_rUBot_mecanum ───────┐
                       ├── rubot_sensor_bringup
ENS160_air_quality ─────┘            │
                                     ▼
                           rubot_ens160_mapping
```

## ENS160 data flow

```text
ENS160 array
    │ I2C through TCA9548A
    ▼
Arduino Nano 33 IoT
    │ USB serial
    ▼
ens160_air_quality_ros
    │ /ens160/readings
    ▼
rubot_ens160_mapping
    ├── TF map → base_link
    ├── positioned measurements
    ├── CSV datasets
    └── PointCloud2 / heatmaps
```

The generic ENS160 node reads and publishes measurements without depending on
the robot. The integration package adds robot pose and map context.

## Design rules

- Do not duplicate robot or sensor drivers.
- Keep hardware ports, frames, topics and output paths configurable.
- Use timestamps when associating measurements with TF transforms.
- Do not store generated logs in Git by default.
- Keep small, documented example datasets for repeatable tests.

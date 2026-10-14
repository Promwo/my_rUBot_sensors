# Workspace Setup

These instructions target Ubuntu 22.04 and ROS 2 Humble.

## Supervisor workspace

```bash
mkdir -p ~/my_rUBot_sensor_ws/src
cd ~/my_rUBot_sensor_ws/src
git clone https://github.com/manelpuig/my_rUBot_mecanum.git
git clone https://github.com/manelpuig/ENS160_air_quality.git
git clone https://github.com/manelpuig/my_rUBot_sensors.git
```

## Student workspace

The student clones the supervisor repositories for the robot and generic
sensor driver, and their own fork for the integration project:

```bash
mkdir -p ~/my_rUBot_sensor_ws/src
cd ~/my_rUBot_sensor_ws/src
git clone https://github.com/manelpuig/my_rUBot_mecanum.git
git clone https://github.com/manelpuig/ENS160_air_quality.git
git clone https://github.com/PATRICK_GITHUB/my_rUBot_sensors.git
```

Replace `PATRICK_GITHUB` with the student's GitHub username.

## Install dependencies and build

```bash
cd ~/my_rUBot_sensor_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Check package discovery before building if necessary:

```bash
colcon list | grep -E 'ens160|rubot_sensor'
```

The workspace directory is not a Git repository. Run Git commands from the
individual repository directories under `src/`.

# Development Workflow

## Ownership of changes

| Change | Repository |
| --- | --- |
| Robot driver, URDF, control or navigation | `my_rUBot_mecanum` |
| ENS160 firmware, parser or generic ROS driver | `ENS160_air_quality` |
| Combined launch, pose association, logging or mapping | `my_rUBot_sensors` |

Do not copy a fix between repositories. Commit it where the responsible
component is maintained.

## Student fork

Patrick works in a fork of `my_rUBot_sensors`. In the local clone:

```bash
git remote -v
git remote add upstream https://github.com/manelpuig/my_rUBot_sensors.git
git fetch upstream
```

Expected remotes:

```text
origin    https://github.com/PATRICK_GITHUB/my_rUBot_sensors.git
upstream  https://github.com/manelpuig/my_rUBot_sensors.git
```

Before starting a feature:

```bash
git switch main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
git switch -c feature/descriptive-name
```

After testing:

```bash
git add <intended-files>
git diff --cached
git commit -m "Describe the completed change"
git push -u origin feature/descriptive-name
```

Patrick then opens a pull request from the feature branch to
`manelpuig/my_rUBot_sensors:main`. Changes required in either dependency use a
separate discussion or pull request in the corresponding repository.

## Updating the three repositories

Update each clean clone independently:

```bash
cd ~/my_rUBot_sensor_ws/src/my_rUBot_mecanum && git pull --ff-only
cd ~/my_rUBot_sensor_ws/src/ENS160_air_quality && git pull --ff-only
cd ~/my_rUBot_sensor_ws/src/my_rUBot_sensors && git pull --ff-only
```

Always inspect `git status` before pulling. Uncommitted changes are local to
the repository in which they were made.

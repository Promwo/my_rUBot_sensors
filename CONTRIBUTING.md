# Contributing

Use a dedicated branch for each change and open a pull request against
`manelpuig/my_rUBot_sensors`.

Before committing:

1. Build the affected packages with `colcon build --symlink-install`.
2. Run their tests with `colcon test`.
3. Review `git diff` and avoid committing generated measurements, `build/`,
   `install/` or `log/`.
4. Keep changes to robot drivers in `my_rUBot_mecanum` and generic ENS160
   changes in `ENS160_air_quality`.

Use concise commit messages such as:

```text
Add map-frame measurement logger
Parameterize ENS160 mapping launch
Document corridor experiment procedure
```

# Mapping Workflow

The intended processing stages are:

1. Read one typed ENS160 measurement from `/ens160/readings`.
2. Resolve the sensor pose in the `map` frame using TF.
3. Publish or record the positioned measurement.
4. Accumulate selected values for RViz visualization.
5. Generate an offline heatmap from a recorded dataset and occupancy map.

The previous project demonstrated CSV logging, a growing `PointCloud2` and
inverse-distance-weighted heatmaps. The new implementation will retain these
capabilities while removing hard-coded paths and separating online ROS nodes
from offline analysis tools.

Configuration must include:

- Input topic and sensor channel selection.
- Target and sensor frames.
- Output directory.
- eCO2 display range.
- Point-cloud history limit.
- Heatmap grid size and interpolation parameters.

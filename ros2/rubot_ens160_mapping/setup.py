from glob import glob
import os

from setuptools import find_packages, setup


package_name = "rubot_ens160_mapping"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Manel Puig",
    maintainer_email="manel.puig@ub.edu",
    description="Spatial logging and mapping for rUBot ENS160 measurements.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "csv_logger_co2cloud = rubot_ens160_mapping.csv_logger_co2cloud:main",
            "eco2_cloud = rubot_ens160_mapping.eco2_cloud:main",
        ],
    },
)

"""Install the independent perception package, offline CLI and assets."""

from glob import glob
import os

from setuptools import setup


PACKAGE_NAME = "vision_perception"

# Keep aligned with requirements-runtime.txt and runtime_deps.py.
# Install NumPy (<2) BEFORE OpenCV / onnxruntime to avoid _ARRAY_API breakage.
_RUNTIME_REQUIRES = [
    "numpy>=1.26.4,<2",
    "opencv-python-headless==4.10.0.84",
    "onnxruntime==1.20.1",
]


def _unique_data_files():
    """Build data_files with unique destinations.

    setuptools keeps only the *last* entry per destination directory. Splitting
    ``share/<pkg>`` across multiple tuples drops package.xml and breaks
    ament_prefix_path / ``ros2 pkg prefix`` after isolated colcon install.
    """
    share_pkg = [
        "package.xml",
        "README.md",
        "requirements-runtime.txt",
    ]
    entries = [
        # Marker required for ament index + ament_prefix_path hook generation.
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, share_pkg),
        ("share/" + PACKAGE_NAME + "/launch", sorted(glob("launch/*.launch.py"))),
        ("share/" + PACKAGE_NAME + "/config", sorted(glob("config/*"))),
        ("share/" + PACKAGE_NAME + "/examples", sorted(glob("examples/*"))),
    ]
    # Guard against accidental duplicate destinations in future edits.
    destinations = [dest for dest, _ in entries]
    if len(destinations) != len(set(destinations)):
        raise RuntimeError(
            f"duplicate data_files destinations in setup.py: {destinations}"
        )
    for dest, files in entries:
        for path in files:
            if not os.path.exists(path):
                raise FileNotFoundError(f"data_files missing path: {path}")
    return entries


setup(
    name=PACKAGE_NAME,
    version="0.1.3",
    packages=[PACKAGE_NAME],
    data_files=_unique_data_files(),
    install_requires=["setuptools", *_RUNTIME_REQUIRES],
    zip_safe=True,
    maintainer="liaojingwu20041031",
    maintainer_email="206929594+liaojingwu20041031@users.noreply.github.com",
    description="Independent manipulation-vision: skeleton, offline V1, optional v1_ros webcam.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "vision_perception_node = vision_perception.vision_node:main",
            "vision_offline_detect = vision_perception.offline_cli:main",
            "vision_webcam_publisher = vision_perception.webcam_publisher:main",
            "vision_fake_image_publisher = vision_perception.fake_image_publisher:main",
        ],
    },
)

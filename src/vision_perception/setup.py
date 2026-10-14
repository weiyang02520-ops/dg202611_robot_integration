"""Python package metadata for ament_cmake_python install.

Share assets and ament index / ament_prefix_path hooks are installed by
CMakeLists.txt via ament_package(). Do NOT install share/ paths from here —
setuptools data_files can clobber colcon/ament-generated hooks.
"""

from setuptools import setup


PACKAGE_NAME = "vision_perception"

# Keep aligned with requirements-runtime.txt and runtime_deps.py.
# Install NumPy (<2) BEFORE OpenCV / onnxruntime to avoid _ARRAY_API breakage.
_RUNTIME_REQUIRES = [
    "numpy>=1.26.4,<2",
    "opencv-python-headless==4.10.0.84",
    "onnxruntime==1.20.1",
]

setup(
    name=PACKAGE_NAME,
    version="0.1.4",
    packages=[PACKAGE_NAME],
    # Intentionally empty: CMake installs launch/config/examples/package.xml and
    # ament_package() creates ament_prefix_path hooks + ament index marker.
    data_files=[],
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

"""Install the independent perception package, offline CLI and assets."""

from glob import glob

from setuptools import setup


PACKAGE_NAME = "vision_perception"

setup(
    name=PACKAGE_NAME,
    version="0.1.1",
    packages=[PACKAGE_NAME],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml", "README.md"]),
        ("share/" + PACKAGE_NAME + "/launch", glob("launch/*.launch.py")),
        ("share/" + PACKAGE_NAME + "/config", glob("config/*")),
        ("share/" + PACKAGE_NAME + "/examples", glob("examples/*")),
    ],
    install_requires=["setuptools", "numpy"],
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

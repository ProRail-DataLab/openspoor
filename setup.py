from setuptools import setup, find_packages
from pathlib import Path

requirements = [
      "importlib_metadata",
      "geopandas",
      "pyyaml",
      "loguru",
      "requests",
      "rtree",
      "pyproj<3",
      "pandas",
      "shapely",
      "folium"
]

dev_packages = [
      "pytest",
]

setup(name='openspoor',
      version='0.1.7',
      description='Open source project to allow translations between different spoor referential systems',
      long_description=(Path(__file__).parent / "README.md").read_text(),
      long_description_content_type='text/markdown',
      install_requires=requirements,
      extras_require={"dev": dev_packages},
      packages=find_packages(include="openspoor*"),
      package_data={'openspoor': ['config.yaml']},
      include_package_data=True,
      zip_safe=False)

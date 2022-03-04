from setuptools import setup, find_packages

setup(name='openspoor',
      version='0.1.5',
      description='Open source project to allow translations between different spoor referential systems',
      install_requires=[
            "geopandas",
            "pyyaml",
            "loguru",
            "requests",
            "rtree",
            "pyproj==2.4.1"],
      packages=find_packages(),
      package_data={'openspoor': ['config.yaml']},
      include_package_data=True,
      zip_safe=False)

# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Install from PyPI

The easiest way to install OpenSpoor is from PyPI:

```bash
pip install openspoor
```

## Install from Source

For development or to get the latest features:

### Step 1: Clone the Repository

```bash
git clone https://github.com/ProRail-DataLab/openspoor.git
cd openspoor
```

### Step 2: Create Virtual Environment

Using uv (recommended):
```bash
uv venv --python=3.11
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

Using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

Using uv:
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

## Verify Installation

Test your installation by running:

```python
import openspoor
print(f"OpenSpoor version: {openspoor.__version__}")
```

Or run the test suite:

```bash
# If installed from source
uv run pytest --nbmake --nbmake-kernel=python3

# If installed via pip
pytest --nbmake --nbmake-kernel=python3
```

## Dependencies

OpenSpoor depends on several key packages:

- **geopandas**: Geographic data handling
- **folium**: Interactive map visualizations  
- **pandas**: Data manipulation
- **shapely**: Geometric operations
- **pyproj**: Coordinate transformations
- **requests**: HTTP requests for API access
- **pyyaml**: Configuration file handling

## Troubleshooting

### Common Issues

**GeoPandas Installation Issues**

GeoPandas can be tricky to install due to its native dependencies. If you encounter issues:

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev

# Using conda (alternative)
conda install geopandas
```

**Network Issues**

OpenSpoor requires internet access to query ProRail's map services. Ensure you have:

- Internet connectivity
- Access to `mapservices.prorail.nl`
- No firewall blocking the requests

**Missing Dependencies**

If you get import errors, try reinstalling with all dependencies:

```bash
pip install --upgrade --force-reinstall openspoor
```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/ProRail-DataLab/openspoor/issues)
2. Review the [troubleshooting guide](development/testing.md)
3. Open a new issue with detailed error information
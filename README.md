# Openspoor

![Openspoor Logo](https://www.radingspoor.nl/wp-content/uploads/Stoom/Modellen_van_Leden/7_Inch_modellen/Zandloc_Janny/51133945_533417650499237_1555124498724814848_n-960x500.jpg)

## Introduction

The **Openspoor** package provides an easy way to transform between different geographical and topological systems commonly used in the Dutch railway network. It prepares this data for analysis and visualization. The goal is to make Openspoor publicly available as an open-source package.

### Supported Transformations

**Input Data:**
- Point data

**Geographical Systems:**
- WGS84 (GPS coordinates)
- EPSG:28992 (Rijksdriehoek)

**Topological Systems:**
- Geocode and geocode kilometrering
- Spoortak and spoortak kilometrering (unavailable on switches)
- Spoortakken of different historical versions

## Installation

Openspoor can be installed using different package management methods. Before proceeding, ensure you have created a virtual environment.

### Step 1: Install package management tool [uv](https://docs.astral.sh/uv/)

These steps show how to install `uv` globally using `pipx`, for other installation methods see the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

#### Install `pipx` (if not already installed):
```sh
pip install --user pipx
pipx ensurepath
```

#### Install `uv` globally:
```sh
pipx install uv
```
### Step 2: Create a virtual environment

```sh
uv venv --python=3.11
source ./venv/bin/activate # linux/mac
.venv/Scripts/activate # windows
```
### Step 3: Install Openspoor dependencies

#### Using `uv`:
```sh
uv pip install openspoor
```

## Platform-Specific Installation Notes

### Mac (including M1 chips)
```sh
conda create -n [env_name] python=3.11
conda install -c conda-forge proj=7.0.0
conda install -c conda-forge pyproj=2.6.0
uv pip install openspoor
```
For non-M1 Mac users, `uv pip install openspoor` should suffice.

## Development

To contribute to Openspoor, follow these steps to set up a development environment.

### Step 1: Clone repository:
   ```sh
   git clone https://github.com/ProRail-DataLab/openspoor.git
   cd openspoor
   ```
### Step 2: Create virtual environment:

```sh
uv venv --python=3.11
source .venv/bin/activate # linux/mac
.venv/Script/activate # windows
```

### Step 3: Install dependencies

```sh
uv sync
```

### Step 4: Run tests to verify setup
```sh
uv run pytest --nbmake --nbmake-kernel=python3
```

### Step 5: install pre-commit hooks

Openspoor uses pre-commit hooks to enforce code quality. To install them:
```sh
pre-commit install
```

To run hooks manually on all files:
```sh
pre-commit run --all-files
```

### Step 6: generating documentation

Openspoor uses `pdoc` to generate documentation. To generate and serve documentation locally:
```sh
pdoc --http : openspoor
```

## Demonstration Notebook

A demonstration notebook is available in the `demo_notebook` folder, showcasing Openspoor's functionality.

## Dependencies

Openspoor relies on data and APIs from [mapservices.prorail.nl](https://mapservices.prorail.nl/). Be aware of possible issues such as:
- Changes in API endpoints
- Modifications in output data format

## Package Structure

### 1. Mapservices
Provides an interface to ProRail's map services API to retrieve railway topology data.
- **PUICMapservices**: General railway track and switch data, including Geocode and Spoortak information.
- **SpoortakMapservices**: Data for Spoortak identification and local kilometrering.

### 2. Transformers
Convert geographical and topological data.
- **TransformerCoordinatesToSpoor**: WGS84/EPSG:28992 → Spoortak, Geocode
- **TransformerGeocodeToCoordinates**: Geocode → WGS84/EPSG:28992
- **TransformerSpoorToCoordinates**: Spoortak → WGS84/EPSG:28992

### 3. Spoortakmodel
Provides historical railway topology to enable transformations on historical data.

### 4. Visualisations
Allows plotting railway-related data on maps. Supports pandas and geopandas dataframes containing points or linestrings.

## Release History

- **0.1.9**: Added spoortakmodel and visualization features.
- **0.1.0**: First stable release.
- **0.0.1**: Work in progress.

## Contributing
We welcome contributions! Follow these steps:

1. Fork the repository.
2. Set up the development environment. See the [Development](#development)    section for details.
3. Create a feature branch:
   ```sh
   git checkout -b feature/your-feature
   ```
4. Commit changes:
   ```sh
   git commit -am "Add your feature"
   ```
5. Push changes:
   ```sh
   git push origin feature/your-feature
   ```
6. Create a pull request and assign at least three reviewers.

Alternatively, contribute by working on open issues listed on the GitHub repository.

---

For further details, visit the [Openspoor GitHub repository](https://github.com/ProRail-DataLab/openspoor).

# Openspoor

![alt text](https://www.radingspoor.nl/images/Stoom/Modellen_van_Leden/7_Inch_modellen/Zandloc_Janny/51133945_533417650499237_1555124498724814848_n.jpg)

The openspoor package is intended to allow easy transformation between different geographical and topological systems 
commonly used in Dutch Railway and prepare this data for analysis and visualisations. Its goal is to be publicly available and function as an open source package.

Currently the openspoor package allows the following transformations:

**Type of input:**
- Point data

These transformations can be performed between the following systems:

**Geographical systems:**
- WGS84 coordinate system (commonly known as GPS coordinates)
- EPSG:28992 coordinate system (commonly known in the Netherlands as Rijksdriehoek)

**Topological systems:**
- Geocode and geocode kilometrering
- Spoortak and spoortak kilometrering (unavailable on switches)
- Spoortakken of different historical versions

## Getting Started

### Installation - usage

#### Windows
Openspoor is dependent on Fiona and GDAL, which are missing Windows dependencies on PyPi.

Use conda to install Fiona and GDAL:

- `conda install -c conda-forge Fiona GDAL`

- `pip install openspoor`

#### Linux

- `pip install openspoor`

#### Mac

- `conda create -n [env_name] python=3.8`
- `conda install -c conda-forge proj=7.0.0`
- `conda install -c conda-forge pyproj=2.6.0`
- `pip install openspoor`

The steps above involving conda(-forge) are necessary for Mac M1 chips (used since Nov 2020). In case your Mac does not
have a M1 chip, then `pip install openspoor` should suffice.

### Installation - development

#### Windows

Installation using anaconda
- Clone the "openspoor" repository
  - `git clone https://github.com/ProRail-DataLab/openspoor.git`
- create an environment:
  - `conda create -n openspoorenv python==3.8`
- activate the environment:
  - `conda activate openspoorenv`
- install dependencies:
  - `conda install -c conda-forge --file requirements.txt`
- In the root directory of the repository, execute the command:
  - `pip install -e .[dev]`
- In the root directory of the repository, execute the command:
  - `pytest --nbmake --nbmake-kernel=python3`
- If all the test succeed, the openspoor package is ready to use and you are on the right "track"!

#### Linux

Installation using anaconda

- Clone the "openspoor" repository
  - `git clone https://github.com/ProRail-DataLab/openspoor.git`
- create an environment in your preferred way in Python 3.8 and activate. For example:
  - `python3 -m venv venv`
  - `source ./venv/bin/activate`
- activate the environment:
  - `conda activate openspoorenv`
- update pip:
  - `pip install --upgrade pip`
- install dependencies:
  - `pip install -r requirements.txt`
- In the root directory of the repository, execute the command:
  - `pip install -e .[dev]`
- In the root directory of the repository, execute the command:
  - `pytest --nbmake --nbmake-kernel=python3`
- If all the test succeed, the openspoor package is ready to use and you are on the right "track"!

### Demonstration notebook

In the demo_notebook folder a notebook can be found that demonstrates the example usage of the openspoor package.

## Dependencies

The transformations available in the openspoor package rely completely on data and API's made available at 
https://mapservices.prorail.nl/. Be aware of this dependency and specifically of the following possible issues:

- The use of API's on mapservices.prorail.nl is changed
- The output data of the mapservices API's is changed (with added, removed or missing columns for instance)


## Structure

The openspoor package is split into 4 categories.

### Mapservices

The MapservicesData classes use mapservices.prorail.nl API's to retrieve the necessary data to perform transformations.
The essentially function as an interface with the topological systems used by ProRail.

- PUICMapservices provides general data about railway tracks (spoor) and switches (wissel and kruisingbenen). This 
contains information regarding Geocode, geocodekilometrering, but also Spoortak identificatie.
- SpoortakMapservices provides information about railway tracks concerning Spoortak identificatie and lokale 
kilometrering.

### Transformers

The various transformers use the geopandas dataframes obtained by MapservicesData objects to add additional geographical
or topological systems to a given geopandas input dataframe. The current transformers only function for geopandas 
dataframes containing Point data. The available transformers are:

- TransformerCoordinatesToSpoor: transforms WGS84 or EPSG:28992 coordinates to spoortak and lokale kilomtrering as well 
as geocode and geocode kilometrering.
- TransformerGeocodeToCoordinates: transforms geocode and geocode kilometrering to WGS84 or EPSG:28992 coordinates.
- TransformerSpoorToCoordinates: transforms spoortak and lokale kilometrering to WGS84 or EPSG:28992 coordinates.

### Spoortakmodel

mapservices.prorail.nl only provides current information about the topological systems used in Dutch
Railways. As the topological systems tend to change with time, due to changing infrastructure and naming conventions, 
the current topological system is not necessarily sufficient to provide transformations on historical data. We added 
historical topological systems as part of the functionality of this package in such a way that it
is available publicly. This enables users to also knwow where assets where in previous versions of the
track topology. 

### Visualisations

This part contains functionalities to plot locations on a map of the Netherlands.This currently supports pandas or geopandas dataframes with locations of either points or linestrings. 

## Release History

- <b>0.1.9</b>
  - Added spoortakmodel and visualisations
  - Updated readme  

- <b>0.1</b>
  - The first proper release
  - ADD: transform point data between geographical systems.
- <b>0.0.1</b>
  - Work in progress 

#### Contributing
The openspoor package stimulates every other person the contribute to the package. To do so:

- Fork it
- Create your feature branch (git checkout -b feature/fooBar)
- Commit your changes (git commit -am 'Add some fooBar')
- Push to the branch (git push origin feature/fooBar)
- Create a new Pull Request with 3 obligated reviewers from the developement team.

You could also contribute by working on one of the open Issues as noted on the GitHub page.
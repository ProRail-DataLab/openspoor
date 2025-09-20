# OpenSpoor

![OpenSpoor Logo](https://www.radingspoor.nl/wp-content/uploads/Stoom/Modellen_van_Leden/7_Inch_modellen/Zandloc_Janny/51133945_533417650499237_1555124498724814848_n-960x500.jpg)

OpenSpoor is an open source project that allows translations between different spoor referential systems used in the Dutch railway network. It provides tools for working with ProRail's geographic data, performing coordinate transformations, and visualizing railway infrastructure.

## Key Features

- **MapServices Integration**: Access ProRail's public map services for railway infrastructure data
- **Coordinate Transformations**: Convert between different coordinate systems (RD, GPS)
- **Interactive Visualizations**: Create interactive maps with railway tracks, stations, and infrastructure
- **Spoortak Models**: Work with track sections and railway network topology
- **Network Analysis**: Find shortest paths and analyze railway connectivity

## Quick Links

- [Installation](installation.md) - Get started with OpenSpoor
- [Quick Start](quickstart.md) - Basic usage examples
- [Demo Notebook](examples/demo-notebook.md) - Comprehensive examples
- [API Reference](api/index.md) - Detailed API documentation

## What You Can Do

### Visualize Railway Infrastructure
Create interactive maps showing tracks, stations, and other railway infrastructure with aerial photography overlays.

### Transform Coordinates
Convert between geocode-kilometer references and x,y coordinates in various coordinate systems.

### Analyze Railway Networks
Find shortest paths between locations and analyze railway connectivity.

### Access ProRail Data
Query ProRail's public map services to get up-to-date information about railway infrastructure.

## Getting Started

1. **Install OpenSpoor**: `pip install openspoor`
2. **Check out the [Quick Start](quickstart.md)** guide
3. **Explore the [Demo Notebook](examples/demo-notebook.md)** for comprehensive examples
4. **Read the [User Guide](user-guide/mapservices.md)** for detailed documentation

## Project Information

- **Version**: 0.3.2
- **License**: MIT
- **Python**: 3.10+
- **Repository**: [GitHub](https://github.com/ProRail-DataLab/openspoor)

## Dependencies

OpenSpoor relies on data and APIs from [mapservices.prorail.nl](https://mapservices.prorail.nl/). Be aware of possible issues such as:

- Changes in API endpoints
- Modifications in output data format

!!! warning "External Dependencies"
    This package depends on external data sources. API changes or data format modifications at ProRail may affect functionality.
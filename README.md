# Living Ice Sheet Temperature

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/developmentseed/living-ice-sheet-temperature/ci.yml?style=for-the-badge&link=https%3A%2F%2Fgithub.com%2Fdevelopmentseed%2Fliving-ice-sheet-temperature%2Factions%2Fworkflows%2Fci.yml)
![GitHub deployments](https://img.shields.io/github/deployments/developmentseed/living-ice-sheet-temperature/github-pages?style=for-the-badge&link=https%3A%2F%2Fdevelopmentseed.org%2Fliving-ice-sheet-temperature%2F)

Visualize, download, and process Antarctic ice sheet temperature data.
Resources:

- [Map-based frontend](https://developmentseed.org/living-ice-sheet-temperature/)
- [Source data on source.coop](https://source.coop/englacial/ice-sheet-temperature)
- [Python package documentation](https://developmentseed.org/living-ice-sheet-temperature/docs/)

## Processing data

You'll need [GDAL](https://gdal.org/en/stable/download.html#binaries) and [tippecanoe](https://github.com/felt/tippecanoe?tab=readme-ov-file#installation).
We use a simple [Makefile](./Makefile) to (re)generate data.

```sh
make
```

To force regeneration of all data:

```sh
make -B
```

If your default GDAL install doesn't have parquet reader support, you can customize the GDAL location:

```sh
GDAL=/path/to/parquet/enabed/gdal make
```

## Developing

First, clone the repository:

```sh
git clone https://github.com/developmentseed/living-ice-sheet-temperature
cd living-ice-sheet-temperature
```

To run the frontend locally, get [yarn](https://yarnpkg.com/getting-started/install), then:

```sh
cd frontend
yarn install
yarn dev
```

This will open the frontend at http://localhost:5174/living-ice-sheet-temperature/.

For backend processing, we have some light tests:

```sh
uv run pytest
```

To run all of our checks (linting, formatting, etc):

```sh
scripts/check
```

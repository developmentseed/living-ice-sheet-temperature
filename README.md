# Living Ice Sheet Temperature

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/developmentseed/living-ice-sheet-temperature/ci.yml?style=for-the-badge&link=https%3A%2F%2Fgithub.com%2Fdevelopmentseed%2Fliving-ice-sheet-temperature%2Factions%2Fworkflows%2Fci.yml)
![GitHub deployments](https://img.shields.io/github/deployments/developmentseed/living-ice-sheet-temperature/github-pages?style=for-the-badge&link=https%3A%2F%2Fdevelopmentseed.org%2Fliving-ice-sheet-temperature%2F)

Frontend application and backend processing for radar-derived ice temperature data in Antarctica.

## Usage

To run the frontend locally, get [yarn](https://yarnpkg.com/getting-started/install), then:

```sh
cd frontend
yarn install
yarn dev
```

This will open the frontend at http://localhost:5174/living-ice-sheet-temperature/.

We provide a command-line interface (CLI) for running data processing operations.
To see what commands are available, install [uv](https://docs.astral.sh/uv/getting-started/installation/) then:

```sh
uv run livist --help
```

### Generating data products

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

## Development

For backend processing, we have some light tests:

```sh
uv run pytest
```

To run all of our checks (linting, formatting, etc):

```sh
scripts/check
```

# Living Ice Sheet Temperature

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/elizadawson/living-ice-sheet-temperature/ci.yml?style=for-the-badge&link=https%3A%2F%2Fgithub.com%2Felizadawson%2Fliving-ice-sheet-temperature%2Factions%2Fworkflows%2Fci.yml)
![GitHub deployments](https://img.shields.io/github/deployments/elizadawson/living-ice-sheet-temperature/github-pages?style=for-the-badge&link=https://elizadawson.github.io/living-ice-sheet-temperature/[])

Visualize, download, and process Antarctic ice sheet temperature data.
Resources:

- [Map-based frontend](https://elizadawson.github.io/living-ice-sheet-temperature/)
- [Source data on source.coop](https://source.coop/englacial/ice-sheet-temperature)
- [Python package documentation](https://elizadawson.github.io/living-ice-sheet-temperature/docs/)

## Processing data

You'll need [GDAL](https://gdal.org/en/stable/download.html#binaries) and [tippecanoe](https://github.com/felt/tippecanoe?tab=readme-ov-file#installation).
To generate everything:

```sh
scripts/generate
```

## Uploading data

To upload, you first need the [AWS CLI](https://aws.amazon.com/cli/) and credentials from source.coop.
Go to https://source.coop/englacial/ice-sheet-temperature and click on the lock:

![Edit mode](./img/edit-mode.png)

This will give you the option to "View credentials":

![View credentials](./img/view-credentials.png)

Choose "Environment Variables" and then copy those `export` commands into your shell.
Then:

```sh
scripts/upload
```

## Developing

First, clone the repository:

```sh
git clone https://github.com/elizadawson/living-ice-sheet-temperature
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

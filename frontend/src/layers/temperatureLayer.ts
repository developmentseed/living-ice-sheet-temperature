import { COORDINATE_SYSTEM } from "@deck.gl/core";
import { TileLayer } from "@deck.gl/geo-layers";
import { GeoJsonLayer } from "@deck.gl/layers";
import { parse } from "@loaders.gl/core";
import { MVTLoader } from "@loaders.gl/mvt";
import { Feature } from "geojson";
import { PMTiles } from "pmtiles";
import proj4 from "proj4";
import { AntarcticTileset2D } from "../lib/AntarcticTileset2D";

const EPSG3031 =
  "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs";
const toEpsg3031 = proj4("EPSG:4326", EPSG3031);

type Rgba = [number, number, number, number];

const TEMP_MIN = 245;
const TEMP_MAX = 270;

const COLOR_STOPS: Rgba[] = [
  [49, 54, 149, 200],
  [69, 117, 180, 200],
  [116, 173, 209, 200],
  [244, 109, 67, 200],
  [215, 48, 39, 200],
  [165, 0, 38, 200],
];

function temperatureToColor(properties: Record<string, unknown>): Rgba {
  const temp = properties?.temperature as number | undefined;
  if (temp == null || isNaN(temp)) return [128, 128, 128, 180];
  const t = Math.max(0, Math.min(1, (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)));
  const scaled = t * (COLOR_STOPS.length - 1);
  const i = Math.min(Math.floor(scaled), COLOR_STOPS.length - 2);
  const f = scaled - i;
  const a = COLOR_STOPS[i];
  const b = COLOR_STOPS[i + 1];
  return [
    Math.round(a[0] + f * (b[0] - a[0])),
    Math.round(a[1] + f * (b[1] - a[1])),
    Math.round(a[2] + f * (b[2] - a[2])),
    Math.round(a[3] + f * (b[3] - a[3])),
  ];
}

function projectFeature(feature: Feature): Feature {
  const coords = (feature.geometry as { coordinates: number[] }).coordinates;
  const [x, y] = toEpsg3031.forward(coords);
  return {
    ...feature,
    geometry: { type: "Point" as const, coordinates: [x, y] },
  };
}

export function createTemperatureLayer(pmtilesSource: PMTiles) {
  return new TileLayer({
    id: "temperatures",
    TilesetClass: AntarcticTileset2D,
    minZoom: 0,
    maxZoom: 10,
    pickable: true,
    autoHighlight: true,

    getTileData: async (tile: {
      index: { x: number; y: number; z: number };
    }) => {
      const { x, y, z } = tile.index;
      const result = await pmtilesSource.getZxy(z, x, y);
      if (!result?.data) return null;

      const parsed = await parse(result.data, MVTLoader, {
        mvt: { coordinates: "wgs84", tileIndex: { x, y, z } },
      });

      const features = (Array.isArray(parsed) ? parsed : [parsed]) as Feature[];
      return features.map(projectFeature);
    },

    renderSubLayers: (props: { id: string; data: Feature[] | null }) => {
      if (!props.data?.length) return null;
      return new GeoJsonLayer({
        ...props,
        id: `${props.id}-geojson`,
        data: { type: "FeatureCollection" as const, features: props.data },
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        pointType: "circle",
        filled: true,
        stroked: true,
        getFillColor: (f: Feature) =>
          temperatureToColor(f.properties as Record<string, unknown>),
        getPointRadius: 6,
        getLineColor: [0, 0, 0, 10],
        getLineWidth: 1,
        lineWidthUnits: "pixels",
        pointRadiusUnits: "pixels",
        opacity: 0.7,
      });
    },
  });
}

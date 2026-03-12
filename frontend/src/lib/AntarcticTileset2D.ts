import { Viewport } from "@deck.gl/core";
import { _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import { tileToBBOX } from "@mapbox/tilebelt";
import proj4 from "proj4";

const EPSG3031 =
  "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs";
const toWgs84 = proj4(EPSG3031, "EPSG:4326");

type TileIndex = { x: number; y: number; z: number };

function lonToTileX(lon: number, z: number): number {
  return Math.floor(((lon + 180) / 360) * Math.pow(2, z));
}

function latToTileY(lat: number, z: number): number {
  const rad = (lat * Math.PI) / 180;
  return Math.floor(
    ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) *
      Math.pow(2, z),
  );
}

export class AntarcticTileset2D extends Tileset2D {
  getTileIndices({
    viewport,
    minZoom,
    maxZoom,
  }: {
    viewport: Viewport;
    minZoom?: number;
    maxZoom?: number;
    zRange: [number, number] | null;
    tileSize?: number;
  }): TileIndex[] {
    const [left, bottom, right, top] = viewport.getBounds();

    const corners = [
      [left, bottom],
      [right, bottom],
      [right, top],
      [left, top],
      [(left + right) / 2, (bottom + top) / 2],
      [left, (bottom + top) / 2],
      [right, (bottom + top) / 2],
      [(left + right) / 2, bottom],
      [(left + right) / 2, top],
    ];

    let minLon = Infinity;
    let maxLon = -Infinity;
    let minLat = Infinity;
    let maxLat = -Infinity;
    for (const [x, y] of corners) {
      const [lon, lat] = toWgs84.forward([x, y]);
      if (lon < minLon) minLon = lon;
      if (lon > maxLon) maxLon = lon;
      if (lat < minLat) minLat = lat;
      if (lat > maxLat) maxLat = lat;
    }

    minLat = Math.max(minLat, -85.05);
    maxLat = Math.min(maxLat, 85.05);

    if (maxLon - minLon > 180) {
      minLon = -180;
      maxLon = 180;
    }

    // Web mercator tile at zoom z covers ~40_075_017 * cos(lat) / 2^z meters.
    // At ~75°S (typical Antarctic data), cos(75°) ≈ 0.259, so ~10.4M / 2^z meters.
    // We want each tile to span ~512 screen pixels:
    //   10_400_000 / 2^z = 512 * 2^(-viewport.zoom)
    //   z = log2(10_400_000 / 512) + viewport.zoom ≈ 14.3 + viewport.zoom
    const z = Math.round(14.3 + viewport.zoom);
    const tileZoom = Math.max(minZoom ?? 0, Math.min(maxZoom ?? 10, z));

    const n = Math.pow(2, tileZoom);
    const xMin = Math.max(0, lonToTileX(minLon, tileZoom));
    const xMax = Math.min(n - 1, lonToTileX(maxLon, tileZoom));
    const yMin = Math.max(0, latToTileY(maxLat, tileZoom));
    const yMax = Math.min(n - 1, latToTileY(minLat, tileZoom));

    const tiles: TileIndex[] = [];
    for (let x = xMin; x <= xMax; x++) {
      for (let y = yMin; y <= yMax; y++) {
        tiles.push({ x, y, z: tileZoom });
      }
    }
    return tiles;
  }

  getTileId({ x, y, z }: TileIndex): string {
    return `${z}-${x}-${y}`;
  }

  getTileZoom({ z }: TileIndex): number {
    return z;
  }

  getParentIndex({ x, y, z }: TileIndex): TileIndex {
    if (z === 0) return { x: 0, y: 0, z: 0 };
    return { x: Math.floor(x / 2), y: Math.floor(y / 2), z: z - 1 };
  }

  isTileVisible(): boolean {
    return true;
  }

  getTileMetadata({ x, y, z }: TileIndex): Record<string, unknown> {
    const [west, south, east, north] = tileToBBOX([x, y, z]);
    return {
      bbox: { west, south, east, north },
    };
  }
}

import { useMemo } from "react";
import { Box, Circle, HStack, Text, VStack } from "@chakra-ui/react";
import { COORDINATE_SYSTEM } from "@deck.gl/core";
import { OrthographicView } from "@deck.gl/core";
import { GeoJsonLayer } from "@deck.gl/layers";
import { DeckGL } from "@deck.gl/react";
import { Feature, FeatureCollection, Point } from "geojson";
import proj4 from "proj4";
import { useBasemap, useBoreholes } from "../hooks/usePublic";

const EPSG3031 =
  "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs";

const project = proj4("EPSG:4326", EPSG3031);

const COLOR_TEMPERATURE: [number, number, number] = [49, 130, 206];
const COLOR_TEMPERATURE_CHEMISTRY: [number, number, number] = [56, 161, 105];
const COLOR_TEMPERATURE_GRAIN_SIZE: [number, number, number] = [214, 158, 46];
const COLOR_ALL: [number, number, number] = [229, 62, 62];

function rgbToHex([r, g, b]: [number, number, number]): string {
  return "#" + [r, g, b].map((c) => c.toString(16).padStart(2, "0")).join("");
}

function projectBoreholes(data: FeatureCollection): FeatureCollection {
  return {
    ...data,
    features: data.features.map((feature) => {
      const point = feature.geometry as Point;
      const [x, y] = project.forward(point.coordinates);
      return {
        ...feature,
        geometry: { ...point, coordinates: [x, y] },
      };
    }),
  };
}

function boreholeColor(feature: Feature): [number, number, number] {
  const { has_chemistry, has_grain_size } = feature.properties ?? {};
  if (has_chemistry && has_grain_size) return COLOR_ALL;
  if (has_chemistry) return COLOR_TEMPERATURE_CHEMISTRY;
  if (has_grain_size) return COLOR_TEMPERATURE_GRAIN_SIZE;
  return COLOR_TEMPERATURE;
}

const BASEMAP_CATEGORY_COLORS: Record<
  string,
  [number, number, number, number]
> = {
  "Ice shelf": [207, 225, 235, 255],
  "Ice tongue": [207, 225, 235, 255],
  Land: [240, 240, 240, 255],
  Rumple: [240, 240, 240, 255],
  Ocean: [163, 189, 209, 255],
};
const DEFAULT_BASEMAP_COLOR: [number, number, number, number] = [
  222, 220, 210, 255,
];

const VIEW = new OrthographicView({ id: "ortho", flipY: false });

const INITIAL_VIEW_STATE = {
  target: [0, 0, 0] as [number, number, number],
  zoom: -13.5,
  minZoom: -14,
  maxZoom: -4,
};

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <HStack gap="2">
      <Circle size="12px" bg={color} />
      <Text fontSize="xs">{label}</Text>
    </HStack>
  );
}

export default function Map() {
  const basemapResult = useBasemap();
  const boreholesResult = useBoreholes();

  const projectedBoreholes = useMemo(
    () =>
      boreholesResult.data ? projectBoreholes(boreholesResult.data) : null,
    [boreholesResult.data],
  );

  const layers = [
    basemapResult.data &&
      new GeoJsonLayer({
        id: "basemap",
        data: basemapResult.data,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        stroked: false,
        filled: true,
        getFillColor: (feature: Feature) => {
          const category = feature.properties?.Category ?? "";
          return BASEMAP_CATEGORY_COLORS[category] ?? DEFAULT_BASEMAP_COLOR;
        },
      }),
    projectedBoreholes &&
      new GeoJsonLayer({
        id: "boreholes",
        data: projectedBoreholes,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        pointType: "circle",
        filled: true,
        stroked: true,
        getFillColor: (feature: Feature) => [...boreholeColor(feature), 204],
        getLineColor: [255, 255, 255, 255],
        getLineWidth: 1,
        getPointRadius: 6,
        pointRadiusUnits: "pixels",
        lineWidthUnits: "pixels",
        lineWidthMinPixels: 1,
        pickable: true,
      }),
  ];

  return (
    <Box flex="1" position="relative">
      <DeckGL
        views={VIEW}
        initialViewState={INITIAL_VIEW_STATE}
        controller
        layers={layers}
        getTooltip={({ object }: { object?: Feature }) =>
          object?.properties?.name ?? null
        }
      />
      <VStack
        position="absolute"
        bottom="6"
        right="3"
        zIndex="1000"
        bg="white"
        p="3"
        borderRadius="md"
        shadow="md"
        gap="1"
        alignItems="flex-start"
      >
        <Text fontWeight="bold" fontSize="sm">
          Boreholes
        </Text>
        <LegendItem color={rgbToHex(COLOR_TEMPERATURE)} label="Temperature" />
        <LegendItem
          color={rgbToHex(COLOR_TEMPERATURE_CHEMISTRY)}
          label="Temperature + chemistry"
        />
        <LegendItem
          color={rgbToHex(COLOR_TEMPERATURE_GRAIN_SIZE)}
          label="Temperature + grain size"
        />
        <LegendItem color={rgbToHex(COLOR_ALL)} label="All three" />
      </VStack>
    </Box>
  );
}

import { useMemo, useState } from "react";
import {
  AbsoluteCenter,
  Box,
  Checkbox,
  Circle,
  HStack,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";
import { COORDINATE_SYSTEM } from "@deck.gl/core";
import { OrthographicView } from "@deck.gl/core";
import { GeoJsonLayer } from "@deck.gl/layers";
import { DeckGL } from "@deck.gl/react";
import { Feature, FeatureCollection, Point } from "geojson";
import { PMTiles } from "pmtiles";
import proj4 from "proj4";
import { useBasemap, useBoreholes } from "../hooks/usePublic";
import { createTemperatureLayer } from "../layers/temperatureLayer";

const EPSG3031 =
  "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs";

const project = proj4("EPSG:4326", EPSG3031);

type Rgb = [number, number, number];
type Rgba = [number, number, number, number];

const BOREHOLE_COLORS = {
  temperature: { hex: "#3182ce", rgb: [49, 130, 206] as Rgb },
  temperatureChemistry: { hex: "#38a169", rgb: [56, 161, 105] as Rgb },
  temperatureGrainSize: { hex: "#d69e2e", rgb: [214, 158, 46] as Rgb },
  all: { hex: "#e53e3e", rgb: [229, 62, 62] as Rgb },
};

const BASEMAP_CATEGORY_COLORS: Record<string, Rgba> = {
  "Ice shelf": [207, 225, 235, 255],
  "Ice tongue": [207, 225, 235, 255],
  Land: [240, 240, 240, 255],
  Rumple: [240, 240, 240, 255],
  Ocean: [163, 189, 209, 255],
};
const DEFAULT_BASEMAP_COLOR: Rgba = [222, 220, 210, 255];

const VIEW = new OrthographicView({ id: "ortho", flipY: false });

const INITIAL_VIEW_STATE = {
  target: [0, 0, 0] as [number, number, number],
  zoom: -13.5,
  minZoom: -14,
  maxZoom: -4,
};

export default function Map() {
  const basemapResult = useBasemap();
  const boreholesResult = useBoreholes();
  const [showTemperatures, setShowTemperatures] = useState(true);
  const [showBoreholes, setShowBoreholes] = useState(true);

  const pmtiles = useMemo(
    () =>
      new PMTiles(
        "https://data.source.coop/englacial/ice-sheet-temperature/temperature/temperature-pure-ice.pmtiles",
      ),
    [],
  );

  const projectedBoreholes = useMemo(
    () => (boreholesResult.data ? projectPoints(boreholesResult.data) : null),
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
    showTemperatures && createTemperatureLayer(pmtiles),
    showBoreholes &&
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
        getPointRadius: 8,
        pointRadiusUnits: "pixels",
        lineWidthUnits: "pixels",
        lineWidthMinPixels: 1,
        pickable: true,
        autoHighlight: true,
      }),
  ];

  if (basemapResult.isLoading)
    return (
      <AbsoluteCenter>
        <VStack>
          Loading Living Ice Sheet Temperature...
          <Spinner />
        </VStack>
      </AbsoluteCenter>
    );

  return (
    <Box flex="1" position="relative">
      <DeckGL
        views={VIEW}
        initialViewState={INITIAL_VIEW_STATE}
        controller
        layers={layers}
        getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
        getTooltip={({ object }: { object?: Feature }) => {
          if (!object?.properties) return null;
          if (object.properties.name) return object.properties.name;
          if (object.properties.temperature != null) {
            const celsius = (object.properties.temperature as number) - 273.15;
            return `${celsius.toFixed(1)} °C`;
          }
          return null;
        }}
      />
      <Legend
        showTemperatures={showTemperatures}
        onToggleTemperatures={() => setShowTemperatures((v) => !v)}
        showBoreholes={showBoreholes}
        onToggleBoreholes={() => setShowBoreholes((v) => !v)}
      />
    </Box>
  );
}

function Legend({
  showTemperatures,
  onToggleTemperatures,
  showBoreholes,
  onToggleBoreholes,
}: {
  showTemperatures: boolean;
  onToggleTemperatures: () => void;
  showBoreholes: boolean;
  onToggleBoreholes: () => void;
}) {
  return (
    <VStack
      position="absolute"
      bottom="6"
      right="3"
      zIndex="1000"
      bg="white"
      p="3"
      borderRadius="md"
      shadow="md"
      gap="2"
      alignItems="flex-start"
    >
      <Text fontWeight="bold" fontSize="sm">
        Layers
      </Text>
      <Checkbox.Root
        size="sm"
        checked={showTemperatures}
        onCheckedChange={onToggleTemperatures}
      >
        <Checkbox.HiddenInput />
        <Checkbox.Control />
        <Checkbox.Label>Temperatures</Checkbox.Label>
      </Checkbox.Root>
      <Checkbox.Root
        size="sm"
        checked={showBoreholes}
        onCheckedChange={onToggleBoreholes}
      >
        <Checkbox.HiddenInput />
        <Checkbox.Control />
        <Checkbox.Label>Boreholes</Checkbox.Label>
      </Checkbox.Root>
      <VStack gap="1" alignItems="flex-start" pl="6">
        <LegendItem
          color={BOREHOLE_COLORS.temperature.hex}
          label="Temperature"
        />
        <LegendItem
          color={BOREHOLE_COLORS.temperatureChemistry.hex}
          label="Temperature + chemistry"
        />
        <LegendItem
          color={BOREHOLE_COLORS.temperatureGrainSize.hex}
          label="Temperature + grain size"
        />
        <LegendItem color={BOREHOLE_COLORS.all.hex} label="All three" />
      </VStack>
    </VStack>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <HStack gap="2">
      <Circle size="12px" bg={color} />
      <Text fontSize="xs">{label}</Text>
    </HStack>
  );
}

function projectPoints(data: FeatureCollection): FeatureCollection {
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

function boreholeColor(feature: Feature): Rgb {
  const { has_chemistry, has_grain_size } = feature.properties ?? {};
  if (has_chemistry && has_grain_size) return BOREHOLE_COLORS.all.rgb;
  if (has_chemistry) return BOREHOLE_COLORS.temperatureChemistry.rgb;
  if (has_grain_size) return BOREHOLE_COLORS.temperatureGrainSize.rgb;
  return BOREHOLE_COLORS.temperature.rgb;
}

import { useMemo, useState } from "react";
import {
  AbsoluteCenter,
  Box,
  Checkbox,
  HStack,
  RadioGroup,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";
import { COORDINATE_SYSTEM } from "@deck.gl/core";
import { OrthographicView } from "@deck.gl/core";
import { GeoJsonLayer, IconLayer } from "@deck.gl/layers";
import { DeckGL } from "@deck.gl/react";
import { Feature, FeatureCollection, Point } from "geojson";
import { PMTiles } from "pmtiles";
import proj4 from "proj4";
import { useBasemap, useBasins, useBoreholes } from "../hooks/usePublic";
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

function createTriangleIcon(fill: Rgb): {
  url: string;
  width: number;
  height: number;
  anchorY: number;
} {
  const [r, g, b] = fill;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><polygon points="16,2 30,28 2,28" fill="rgb(${r},${g},${b})" fill-opacity="0.8" stroke="black" stroke-width="1"/></svg>`;
  return {
    url: `data:image/svg+xml;base64,${btoa(svg)}`,
    width: 32,
    height: 32,
    anchorY: 28,
  };
}

const BOREHOLE_ICONS = {
  temperature: createTriangleIcon(BOREHOLE_COLORS.temperature.rgb),
  temperatureChemistry: createTriangleIcon(
    BOREHOLE_COLORS.temperatureChemistry.rgb,
  ),
  temperatureGrainSize: createTriangleIcon(
    BOREHOLE_COLORS.temperatureGrainSize.rgb,
  ),
  all: createTriangleIcon(BOREHOLE_COLORS.all.rgb),
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
  const basinsResult = useBasins();
  const boreholesResult = useBoreholes();
  const [showTemperatures, setShowTemperatures] = useState(true);
  const [showBoreholes, setShowBoreholes] = useState(true);
  const [temperatureSource, setTemperatureSource] =
    useState<string>("pure-ice");

  const pmtilesSources = useMemo(
    () => ({
      "pure-ice": new PMTiles(
        "https://data.source.coop/englacial/ice-sheet-temperature/temperature/temperature-pure-ice.pmtiles",
      ),
      chemistry: new PMTiles(
        "https://data.source.coop/englacial/ice-sheet-temperature/temperature/temperature-chemistry.pmtiles",
      ),
    }),
    [],
  );

  const pmtiles = pmtilesSources[temperatureSource as keyof typeof pmtilesSources];

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
    basinsResult.data &&
      new GeoJsonLayer({
        id: "basins",
        data: basinsResult.data,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        stroked: true,
        filled: false,
        getLineColor: [255, 255, 255, 255],
        getLineWidth: 2,
        lineWidthUnits: "pixels",
      }),
    showTemperatures &&
      createTemperatureLayer(pmtiles, `temperatures-${temperatureSource}`),
    showBoreholes &&
      projectedBoreholes &&
      new IconLayer({
        id: "boreholes",
        data: projectedBoreholes.features,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        getPosition: (feature: Feature) =>
          (feature.geometry as Point).coordinates as [number, number],
        getIcon: (feature: Feature) => boreholeIcon(feature),
        getSize: 24,
        sizeUnits: "pixels",
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
        temperatureSource={temperatureSource}
        onTemperatureSourceChange={setTemperatureSource}
        showBoreholes={showBoreholes}
        onToggleBoreholes={() => setShowBoreholes((v) => !v)}
      />
    </Box>
  );
}

function Legend({
  showTemperatures,
  onToggleTemperatures,
  temperatureSource,
  onTemperatureSourceChange,
  showBoreholes,
  onToggleBoreholes,
}: {
  showTemperatures: boolean;
  onToggleTemperatures: () => void;
  temperatureSource: string;
  onTemperatureSourceChange: (value: string) => void;
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
      <RadioGroup.Root
        size="sm"
        value={temperatureSource}
        onValueChange={(e) => e.value && onTemperatureSourceChange(e.value)}
        pl="6"
      >
        <VStack gap="1" alignItems="flex-start">
          <RadioGroup.Item value="pure-ice">
            <RadioGroup.ItemHiddenInput />
            <RadioGroup.ItemIndicator />
            <RadioGroup.ItemText>Pure ice</RadioGroup.ItemText>
          </RadioGroup.Item>
          <RadioGroup.Item value="chemistry">
            <RadioGroup.ItemHiddenInput />
            <RadioGroup.ItemIndicator />
            <RadioGroup.ItemText>Chemistry</RadioGroup.ItemText>
          </RadioGroup.Item>
        </VStack>
      </RadioGroup.Root>
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
      <svg width="12" height="12" viewBox="0 0 12 12" style={{ flexShrink: 0 }}>
        <polygon points="6,1 11,11 1,11" fill={color} />
      </svg>
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

function boreholeIcon(feature: Feature) {
  const { has_chemistry, has_grain_size } = feature.properties ?? {};
  if (has_chemistry && has_grain_size) return BOREHOLE_ICONS.all;
  if (has_chemistry) return BOREHOLE_ICONS.temperatureChemistry;
  if (has_grain_size) return BOREHOLE_ICONS.temperatureGrainSize;
  return BOREHOLE_ICONS.temperature;
}

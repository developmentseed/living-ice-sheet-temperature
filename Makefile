GDAL ?= gdal
TEMPERATURE_URL := https://data.source.coop/englacial/ice-sheet-temperature/AttenuationRateData/depth-avg-attenuation-ASE.txt
S3_PREFIX := s3://us-west-2.opendata.source.coop/englacial/ice-sheet-temperature/temperature

ALL: frontend/public/boreholes.json data/temperature-pure-ice.parquet data/temperature-pure-ice.pmtiles

frontend/public/boreholes.json:
	uv run livist boreholes > $@

data/temperature-pure-ice.parquet data/temperature-pure-ice-wgs84.parquet:
	mkdir -p $(dir $@)
	uv run livist temperatures $(if $(findstring wgs84,$@),--to-wgs84) $(TEMPERATURE_URL) $@

data/temperature-pure-ice-wgs84.fgb: data/temperature-pure-ice-wgs84.parquet
	$(GDAL) vector convert $< $@

data/temperature-pure-ice.pmtiles: data/temperature-pure-ice-wgs84.fgb
	tippecanoe -zg -o $@ $<

sync: data/temperature-pure-ice.pmtiles data/temperature-pure-ice.parquet
	aws s3 cp data/temperature-pure-ice.parquet $(S3_PREFIX)/temperature-pure-ice.parquet
	aws s3 cp data/temperature-pure-ice.pmtiles $(S3_PREFIX)/temperature-pure-ice.pmtiles

.PRECIOUS: data/temperature-pure-ice-wgs84.fgb data/temperature-pure-ice-wgs84.parquet

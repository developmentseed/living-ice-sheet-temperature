from living_ice_temperature.models import Borehole


def test_boreholes() -> None:
    boreholes = Borehole.from_csv_href(
        "https://data.source.coop/englacial/ice-sheet-temperature/AntarcticaBoreholeData/BoreholeLocations.csv"
    )
    Borehole.to_feature_collection(boreholes)

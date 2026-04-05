import enum


class Region(str, enum.Enum):
    ANDALUCIA = "andalucia"
    ARAGON = "aragon"
    ASTURIAS = "asturias"
    BALEARES = "baleares"
    CANARIAS = "canarias"
    CANTABRIA = "cantabria"
    CASTILLA_LA_MANCHA = "castilla-la-mancha"
    CASTILLA_Y_LEON = "castilla-y-leon"
    CATALUNA = "cataluna"
    CEUTA = "ceuta"
    EXTREMADURA = "extremadura"
    GALICIA = "galicia"
    LA_RIOJA = "la-rioja"
    MADRID = "madrid"
    MELILLA = "melilla"
    MURCIA = "murcia"
    NAVARRA = "navarra"
    PAIS_VASCO = "pais-vasco"
    VALENCIA = "valencia"


# Bounding box aproximado de cada comunidad autónoma en WGS84
# (min_lon, min_lat, max_lon, max_lat)
REGION_BBOX: dict[Region, tuple[float, float, float, float]] = {
    Region.ANDALUCIA: (-7.53, 35.98, -1.63, 38.73),
    Region.ARAGON: (-2.16, 39.85, 0.77, 42.93),
    Region.ASTURIAS: (-7.19, 42.87, -4.51, 43.67),
    Region.BALEARES: (1.16, 38.64, 4.33, 40.09),
    Region.CANARIAS: (-18.22, 27.63, -13.41, 29.47),
    Region.CANTABRIA: (-4.84, 42.77, -3.10, 43.55),
    Region.CASTILLA_LA_MANCHA: (-5.41, 38.00, -0.92, 41.33),
    Region.CASTILLA_Y_LEON: (-7.11, 40.06, -1.64, 43.23),
    Region.CATALUNA: (0.16, 40.52, 3.33, 42.86),
    Region.CEUTA: (-5.39, 35.87, -5.27, 35.93),
    Region.EXTREMADURA: (-7.55, 37.94, -4.65, 40.49),
    Region.GALICIA: (-9.31, 41.81, -6.72, 43.79),
    Region.LA_RIOJA: (-3.47, 41.92, -1.67, 42.64),
    Region.MADRID: (-4.58, 39.88, -3.05, 41.17),
    Region.MELILLA: (-2.99, 35.26, -2.91, 35.35),
    Region.MURCIA: (-2.34, 37.36, -0.65, 38.77),
    Region.NAVARRA: (-2.49, 41.91, -0.73, 43.31),
    Region.PAIS_VASCO: (-3.45, 42.47, -1.72, 43.46),
    Region.VALENCIA: (-1.53, 37.84, 0.66, 40.79),
}


def region_to_bbox_string(region: Region) -> str:
    min_lon, min_lat, max_lon, max_lat = REGION_BBOX[region]
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"

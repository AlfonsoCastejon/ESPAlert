/** Deduce la comunidad autónoma de una geometría comparando con bounding boxes. */

// [min_lon, min_lat, max_lon, max_lat, nombre]
const REGIONES: [number, number, number, number, string][] = [
  [-2.99, 35.26, -2.91, 35.35, "Melilla"],
  [-5.39, 35.87, -5.27, 35.93, "Ceuta"],
  [-4.58, 39.88, -3.05, 41.17, "Madrid"],
  [-3.47, 41.92, -1.67, 42.64, "La Rioja"],
  [-4.84, 42.77, -3.10, 43.55, "Cantabria"],
  [-7.19, 42.87, -4.51, 43.67, "Asturias"],
  [-3.45, 42.47, -1.72, 43.46, "País Vasco"],
  [-2.49, 41.91, -0.73, 43.31, "Navarra"],
  [1.16, 38.64, 4.33, 40.09, "Baleares"],
  [-18.22, 27.63, -13.41, 29.47, "Canarias"],
  [-2.34, 37.36, -0.65, 38.77, "Murcia"],
  [-1.53, 37.84, 0.66, 40.79, "Comunidad Valenciana"],
  [0.16, 40.52, 3.33, 42.86, "Cataluña"],
  [-9.31, 41.81, -6.72, 43.79, "Galicia"],
  [-2.16, 39.85, 0.77, 42.93, "Aragón"],
  [-7.55, 37.94, -4.65, 40.49, "Extremadura"],
  [-7.53, 35.98, -1.63, 38.73, "Andalucía"],
  [-5.41, 38.00, -0.92, 41.33, "Castilla-La Mancha"],
  [-7.11, 40.06, -1.64, 43.23, "Castilla y León"],
];

/** Devuelve un punto representativo [lon, lat] de cualquier geometría GeoJSON. */
function puntoRepresentativo(geom: GeoJSON.Geometry): [number, number] | null {
  if (geom.type === "Point") {
    return geom.coordinates as [number, number];
  }
  let coords: number[][] = [];
  if (geom.type === "Polygon") {
    coords = geom.coordinates[0] as number[][];
  } else if (geom.type === "MultiPolygon") {
    coords = geom.coordinates[0]?.[0] as number[][];
  } else if (geom.type === "LineString") {
    coords = geom.coordinates as number[][];
  }
  if (!coords || coords.length === 0) return null;
  const suma = coords.reduce((a, c) => [a[0] + c[0], a[1] + c[1]], [0, 0]);
  return [suma[0] / coords.length, suma[1] / coords.length];
}

/**
 * Devuelve el nombre de la comunidad autónoma cuyo bounding box contiene la
 * geometría. Las regiones están ordenadas de menor a mayor área para que, ante
 * solapamiento de bounding boxes, gane la más específica.
 */
export function comunidadDe(geom: GeoJSON.Geometry | null): string | null {
  if (!geom) return null;
  const punto = puntoRepresentativo(geom);
  if (!punto) return null;
  const [lon, lat] = punto;
  for (const [minLon, minLat, maxLon, maxLat, nombre] of REGIONES) {
    if (lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat) {
      return nombre;
    }
  }
  return null;
}

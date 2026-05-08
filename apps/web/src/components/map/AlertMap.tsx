"use client";

/**
 * Mapa interactivo de España con capas de CCAA, provincias y alertas.
 * Usa MapLibre GL con teselas vectoriales de OpenFreeMap y GeoJSON de OpenDataSoft.
 */

import { useRef, useEffect, useState } from "react";
import { Info } from "lucide-react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import styles from "./AlertMap.module.scss";
import type { Alerta, ColorAlerta } from "@/types/alert";

const COLORES: Record<ColorAlerta, string> = {
  green: "hsl(122, 39%, 49%)",
  yellow: "hsl(54, 98%, 60%)",
  orange: "hsl(36, 100%, 50%)",
  red: "hsl(4, 90%, 58%)",
  purple: "hsl(265, 100%, 68%)",
};

const FUENTES: Record<string, string> = {
  aemet: "AEMET",
  ign: "IGN",
  dgt: "DGT",
  meteoalarm: "MeteoAlarm",
  meshtastic: "Mesh",
};

const CENTRO_ESPANA: [number, number] = [-3.5, 39.5];
const ZOOM_INICIAL = 5.5;

// Encuadre máximo: incluye Canarias (lng ~-18, lat ~28) y Ceuta/Melilla (lat ~35).
const BOUNDS_ESPANA: maplibregl.LngLatBoundsLike = [
  [-19, 27],
  [6, 45],
];

// Vista predefinida por CCAA/ciudad autónoma: clave = valor de REGIONES.
const VISTAS_REGION: Record<string, { center: [number, number]; zoom: number }> = {
  andalucia: { center: [-4.5, 37.5], zoom: 6.5 },
  aragon: { center: [-0.7, 41.5], zoom: 7 },
  asturias: { center: [-5.85, 43.3], zoom: 8 },
  baleares: { center: [2.7, 39.6], zoom: 8 },
  canarias: { center: [-15.6, 28.2], zoom: 7 },
  cantabria: { center: [-4.0, 43.2], zoom: 8.5 },
  "castilla-la-mancha": { center: [-3.0, 39.5], zoom: 6.5 },
  "castilla-y-leon": { center: [-4.7, 41.7], zoom: 6.5 },
  cataluna: { center: [1.5, 41.7], zoom: 7 },
  ceuta: { center: [-5.34, 35.89], zoom: 11 },
  extremadura: { center: [-6.0, 39.2], zoom: 7 },
  galicia: { center: [-7.9, 42.8], zoom: 7.5 },
  "la-rioja": { center: [-2.5, 42.3], zoom: 8.5 },
  madrid: { center: [-3.7, 40.4], zoom: 8 },
  melilla: { center: [-2.94, 35.29], zoom: 11 },
  murcia: { center: [-1.5, 38.0], zoom: 8 },
  navarra: { center: [-1.6, 42.7], zoom: 8 },
  "pais-vasco": { center: [-2.6, 43.0], zoom: 8 },
  valencia: { center: [-0.5, 39.5], zoom: 7 },
};

// Servidos desde /public — versiones simplificadas con mapshaper (~400 KB en
// total frente a ~11 MB del origen externo). Imperceptible al zoom usado.
const URL_CCAA = "/data/ccaa.geojson";
const URL_PROVINCIAS = "/data/provincias.geojson";

const ESTILO_MAPA: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    openmaptiles: {
      type: "vector",
      url: "https://tiles.openfreemap.org/planet",
    },
  },
  layers: [
    {
      id: "fondo",
      type: "background",
      paint: { "background-color": "hsl(0, 0%, 83%)" },
    },
    {
      id: "agua",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "water",
      paint: { "fill-color": "hsl(0, 0%, 94%)" },
    },
  ],
};

interface AlertMapProps {
  alertas: Alerta[];
  region?: string;
}

// Radio del desplazamiento en grados (~55 m). Suficiente para separarse a zoom
// máximo (12) sin falsear visiblemente la ubicación.
const OFFSET_DUPLICADOS = 0.003;

/** Aplica offset radial determinista a puntos duplicados del mismo lat/lon. */
function desplazarPunto(
  coords: [number, number],
  indice: number,
): [number, number] {
  if (indice === 0) return coords;
  const angulo = (indice * 2 * Math.PI) / 8;
  const radio = OFFSET_DUPLICADOS * Math.ceil(indice / 8);
  return [coords[0] + Math.cos(angulo) * radio, coords[1] + Math.sin(angulo) * radio];
}

/** Transforma el array de alertas en una FeatureCollection para MapLibre */
function construirGeoJSON(alertas: Alerta[]): GeoJSON.FeatureCollection {
  const ocurrencias = new Map<string, number>();

  return {
    type: "FeatureCollection",
    features: alertas
      .filter((a) => a.geometry)
      .map((a) => {
        let geometry = a.geometry!;
        if (geometry.type === "Point") {
          const [lon, lat] = geometry.coordinates as [number, number];
          const clave = `${lon.toFixed(6)},${lat.toFixed(6)}`;
          const indice = ocurrencias.get(clave) ?? 0;
          ocurrencias.set(clave, indice + 1);
          geometry = { type: "Point", coordinates: desplazarPunto([lon, lat], indice) };
        }

        return {
          type: "Feature" as const,
          properties: {
            id: a.id,
            color: COLORES[a.color] || COLORES.green,
            headline: a.headline,
            description: a.description || "",
            area_description: a.area_description || "",
            source: a.source,
          },
          geometry,
        };
      }),
  };
}

/** Añade o actualiza la fuente y capas de alertas en el mapa */
function actualizarAlertas(map: maplibregl.Map, geojson: GeoJSON.FeatureCollection) {
  const source = map.getSource("alertas") as maplibregl.GeoJSONSource | undefined;
  if (source) {
    source.setData(geojson);
    return;
  }

  map.addSource("alertas", { type: "geojson", data: geojson });

  map.addLayer(
    {
      id: "alertas-fill",
      type: "fill",
      source: "alertas",
      filter: ["==", "$type", "Polygon"],
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": 0.4,
      },
    },
    "ccaa-line"
  );

  map.addLayer(
    {
      id: "alertas-line",
      type: "line",
      source: "alertas",
      filter: ["==", "$type", "Polygon"],
      paint: {
        "line-color": ["get", "color"],
        "line-width": 2,
        "line-opacity": 0.8,
      },
    },
    "ccaa-line"
  );

  map.addLayer({
    id: "alertas-point",
    type: "circle",
    source: "alertas",
    filter: ["==", "$type", "Point"],
    paint: {
      "circle-radius": 6,
      "circle-color": ["get", "color"],
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "hsl(187, 31%, 11%)",
    },
  });

  // Popup al pulsar alerta (poligono o punto)
  for (const capa of ["alertas-fill", "alertas-point"]) {
    map.on("click", capa, (e) => {
      if (!e.features?.[0]) return;
      const props = e.features[0].properties;

      const fuente = FUENTES[props.source] || props.source;
      const area = props.area_description || "";
      const origen = area ? `${fuente} — ${area}` : fuente;

      const contenedor = document.createElement("div");
      contenedor.className = "popup-alerta";

      const titulo = document.createElement("strong");
      titulo.className = "popup-alerta__titulo";
      titulo.textContent = props.headline || "";
      contenedor.appendChild(titulo);

      if (props.description) {
        const desc = document.createElement("p");
        desc.className = "popup-alerta__descripcion";
        desc.textContent = props.description;
        contenedor.appendChild(desc);
      }

      const origenEl = document.createElement("span");
      origenEl.className = "popup-alerta__origen";
      origenEl.textContent = origen;
      contenedor.appendChild(origenEl);

      const popup = new maplibregl.Popup({ closeButton: true, maxWidth: "18rem", className: "popup-tema" })
        .setLngLat(e.lngLat)
        .setDOMContent(contenedor)
        .addTo(map);

      const el = popup.getElement()?.querySelector(".maplibregl-popup-content") as HTMLElement | null;
      if (el) {
        el.style.background = "";
      }
    });

    map.on("mouseenter", capa, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", capa, () => {
      map.getCanvas().style.cursor = "";
    });
  }
}

/** Carga los contornos de CCAA y provincias desde OpenDataSoft */
async function cargarCapasEspana(map: maplibregl.Map) {
  const [geoCcaa, geoProv] = await Promise.all([
    fetch(URL_CCAA).then((r) => r.json()),
    fetch(URL_PROVINCIAS).then((r) => r.json()),
  ]);

  map.addSource("ccaa", { type: "geojson", data: geoCcaa });
  map.addLayer({
    id: "ccaa-fill",
    type: "fill",
    source: "ccaa",
    paint: { "fill-color": "hsl(0, 0%, 83%)" },
  });
  map.addLayer({
    id: "ccaa-line",
    type: "line",
    source: "ccaa",
    paint: {
      "line-color": "hsl(0, 0%, 33%)",
      "line-width": 1.8,
    },
  });

  map.addSource("provincias", { type: "geojson", data: geoProv });
  map.addLayer({
    id: "provincias-line",
    type: "line",
    source: "provincias",
    minzoom: 6.5,
    paint: {
      "line-color": "hsl(0, 0%, 53%)",
      "line-width": 1,
    },
  });

  // Click en CCAA para hacer zoom y ver provincias
  map.on("click", "ccaa-fill", (e) => {
    if (!e.features?.[0]) return;
    const bbox = new maplibregl.LngLatBounds();
    const geom = e.features[0].geometry;

    if (geom.type === "Polygon") {
      for (const ring of geom.coordinates) {
        for (const coord of ring) bbox.extend(coord as [number, number]);
      }
    } else if (geom.type === "MultiPolygon") {
      for (const poly of geom.coordinates) {
        for (const ring of poly) {
          for (const coord of ring) bbox.extend(coord as [number, number]);
        }
      }
    }

    if (!bbox.isEmpty()) {
      // Calculamos el encuadre y forzamos zoom mínimo para ver provincias
      const camara = map.cameraForBounds(bbox, { padding: 40, maxZoom: 9 });
      const zoomFinal = Math.max(camara?.zoom ?? 7, 6.6);
      map.flyTo({ center: camara?.center ?? map.getCenter(), zoom: zoomFinal });
    }
  });

  map.on("mouseenter", "ccaa-fill", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "ccaa-fill", () => {
    map.getCanvas().style.cursor = "";
  });

  // Doble click para volver a la vista general
  map.on("dblclick", (e) => {
    e.preventDefault();
    map.flyTo({ center: CENTRO_ESPANA, zoom: ZOOM_INICIAL });
  });
}

export default function AlertMap({ alertas, region }: AlertMapProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<maplibregl.Map | null>(null);
  const listoRef = useRef(false);

  useEffect(() => {
    if (!contenedorRef.current || mapaRef.current) return;

    let cancelado = false;

    // Wrapper de requestIdleCallback con fallback a setTimeout (Safari).
    const enIdle = (cb: () => void, timeoutMs = 200) => {
      const w = window as Window & {
        requestIdleCallback?: (cb: () => void) => number;
      };
      if (typeof w.requestIdleCallback === "function") {
        w.requestIdleCallback(cb);
      } else {
        setTimeout(cb, timeoutMs);
      }
    };

    // Diferimos la construcción del mapa para que el TBT (Total Blocking Time)
    // no se dispare. La inicialización de MapLibre con WebGL bloquea el main
    // thread varios cientos de ms en móvil.
    const inicializar = () => {
      if (cancelado || !contenedorRef.current || mapaRef.current) return;

      const map = new maplibregl.Map({
        container: contenedorRef.current,
        style: ESTILO_MAPA,
        center: CENTRO_ESPANA,
        zoom: ZOOM_INICIAL,
        minZoom: 5,
        maxZoom: 12,
        maxBounds: BOUNDS_ESPANA,
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
      });

      map.addControl(
        new maplibregl.NavigationControl({ showCompass: false }),
        "bottom-right"
      );

      map.on("load", () => {
        listoRef.current = true;
        // Las capas de CCAA/provincias también se difieren a idle para no
        // competir con el primer render del mapa.
        enIdle(() => {
          cargarCapasEspana(map).catch(() => {});
        });
      });

      mapaRef.current = map;
    };

    enIdle(inicializar);

    return () => {
      cancelado = true;
      mapaRef.current?.remove();
      mapaRef.current = null;
      listoRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapaRef.current;
    if (!map) return;

    const geojson = construirGeoJSON(alertas);

    if (listoRef.current) {
      actualizarAlertas(map, geojson);
    } else {
      const intervalo = setInterval(() => {
        if (listoRef.current) {
          clearInterval(intervalo);
          actualizarAlertas(map, geojson);
        }
      }, 200);
      return () => clearInterval(intervalo);
    }
  }, [alertas]);

  // Vuela a la región seleccionada en el filtro lateral
  useEffect(() => {
    const map = mapaRef.current;
    if (!map) return;

    const aplicar = () => {
      if (!region) {
        map.flyTo({ center: CENTRO_ESPANA, zoom: ZOOM_INICIAL });
        return;
      }
      const vista = VISTAS_REGION[region];
      if (vista) {
        map.flyTo({ center: vista.center, zoom: vista.zoom });
      }
    };

    if (listoRef.current) {
      aplicar();
    } else {
      const intervalo = setInterval(() => {
        if (listoRef.current) {
          clearInterval(intervalo);
          aplicar();
        }
      }, 200);
      return () => clearInterval(intervalo);
    }
  }, [region]);

  return (
    <div className={styles.contenedor}>
      <div ref={contenedorRef} className={styles.mapa} />
      <Leyenda />
    </div>
  );
}

function Leyenda() {
  const [abierta, setAbierta] = useState(true);

  return (
    <div
      className={`${styles.leyenda} ${abierta ? "" : styles["leyenda--cerrada"]}`}
      role="region"
      aria-label="Leyenda del mapa"
    >
      <button
        type="button"
        className={styles.leyendaToggle}
        aria-expanded={abierta}
        aria-controls="mapa-leyenda-contenido"
        onClick={() => setAbierta((v) => !v)}
      >
        <Info size={16} aria-hidden="true" />
        <span>Leyenda</span>
      </button>

      {abierta && (
        <div id="mapa-leyenda-contenido" className={styles.leyendaContenido}>
          <p className={styles.leyendaTitulo}>Severidad</p>
          <ul className={styles.leyendaLista}>
            <li>
              <span className={styles.leyendaPunto} style={{ background: COLORES.red }} aria-hidden="true" />
              Rojo — Riesgo extremo
            </li>
            <li>
              <span className={styles.leyendaPunto} style={{ background: COLORES.orange }} aria-hidden="true" />
              Naranja — Riesgo importante
            </li>
            <li>
              <span className={styles.leyendaPunto} style={{ background: COLORES.yellow }} aria-hidden="true" />
              Amarillo — Riesgo moderado
            </li>
            <li>
              <span className={styles.leyendaPunto} style={{ background: COLORES.green }} aria-hidden="true" />
              Verde — Sin riesgo significativo
            </li>
            <li>
              <span className={styles.leyendaPunto} style={{ background: COLORES.purple }} aria-hidden="true" />
              Morado — Mensaje Meshtastic
            </li>
          </ul>
          <p className={styles.leyendaTitulo}>Forma</p>
          <ul className={styles.leyendaLista}>
            <li>
              <span className={styles.leyendaPunto} style={{ background: "var(--color-texto-medio)" }} aria-hidden="true" />
              Círculo — Ubicación puntual (mesh, accidente, sismo)
            </li>
            <li>
              <span className={styles.leyendaArea} aria-hidden="true" />
              Área coloreada — Zona afectada por aviso meteorológico
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

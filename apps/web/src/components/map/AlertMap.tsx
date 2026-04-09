"use client";

/**
 * Mapa interactivo de España con capas de CCAA, provincias y alertas.
 * Usa MapLibre GL con teselas vectoriales de OpenFreeMap y GeoJSON de OpenDataSoft.
 */

import { useRef, useEffect } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import styles from "./AlertMap.module.scss";
import type { Alerta, ColorAlerta } from "@/types/alert";

const COLORES: Record<ColorAlerta, string> = {
  green: "#4CAF50",
  yellow: "#FDD835",
  orange: "#FF9800",
  red: "#F44336",
  purple: "#A35DFF",
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

const BOUNDS_ESPANA: maplibregl.LngLatBoundsLike = [
  [-12, 34],
  [6, 45],
];

const URL_CCAA =
  "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-spain-comunidad-autonoma/exports/geojson?lang=es";
const URL_PROVINCIAS =
  "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-spain-provincia/exports/geojson?lang=es";

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
      paint: { "background-color": "#d4d4d4" },
    },
    {
      id: "agua",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "water",
      paint: { "fill-color": "#f0f0f0" },
    },
  ],
};

interface AlertMapProps {
  alertas: Alerta[];
}

/** Transforma el array de alertas en una FeatureCollection para MapLibre */
function construirGeoJSON(alertas: Alerta[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: alertas
      .filter((a) => a.geometry)
      .map((a) => ({
        type: "Feature" as const,
        properties: {
          id: a.id,
          color: COLORES[a.color] || COLORES.green,
          headline: a.headline,
          description: a.description || "",
          area_description: a.area_description || "",
          source: a.source,
        },
        geometry: a.geometry!,
      })),
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
      "circle-stroke-color": "#142426",
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

      const html = `
        <div class="popup-alerta">
          <strong class="popup-alerta__titulo">${props.headline}</strong>
          ${props.description ? `<p class="popup-alerta__descripcion">${props.description}</p>` : ""}
          <span class="popup-alerta__origen">${origen}</span>
        </div>
      `;

      const popup = new maplibregl.Popup({ closeButton: true, maxWidth: "18rem", className: "popup-tema" })
        .setLngLat(e.lngLat)
        .setHTML(html)
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
    paint: { "fill-color": "#d4d4d4" },
  });
  map.addLayer({
    id: "ccaa-line",
    type: "line",
    source: "ccaa",
    paint: {
      "line-color": "#555555",
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
      "line-color": "#888888",
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

    if (!bbox.isEmpty()) map.fitBounds(bbox, { padding: 40, maxZoom: 9 });
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

export default function AlertMap({ alertas }: AlertMapProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<maplibregl.Map | null>(null);
  const listoRef = useRef(false);

  useEffect(() => {
    if (!contenedorRef.current || mapaRef.current) return;

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

    map.on("load", async () => {
      await cargarCapasEspana(map);
      listoRef.current = true;
    });

    mapaRef.current = map;

    return () => {
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

  return (
    <div className={styles.contenedor}>
      <div ref={contenedorRef} className={styles.mapa} />
    </div>
  );
}

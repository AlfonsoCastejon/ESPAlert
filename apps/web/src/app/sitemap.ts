import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://espalert.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const ahora = new Date();
  const rutas = ["", "/alertas", "/prediccion", "/login", "/registro", "/privacidad", "/aviso-legal"];
  return rutas.map((ruta) => ({
    url: `${BASE_URL}${ruta}`,
    lastModified: ahora,
    changeFrequency: ruta === "/alertas" ? "hourly" : "weekly",
    priority: ruta === "" ? 1 : 0.7,
  }));
}

"""Endpoint de predicción meteorológica por municipio (AEMET OpenData)."""

import json
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path, Query, status

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["forecast"])

AEMET_BASE = "https://opendata.aemet.es/opendata/api"
MUNICIPIOS_URL = f"{AEMET_BASE}/maestro/municipios"
PREDICCION_DIARIA_URL = f"{AEMET_BASE}/prediccion/especifica/municipio/diaria"

# Caché en memoria del maestro de municipios (se carga una sola vez)
_cache_municipios: list[dict] | None = None


def _headers() -> dict:
    return {
        "api_key": settings.AEMET_API_KEY.get_secret_value(),
        "Accept": "application/json",
    }


async def _obtener_municipios() -> list[dict]:
    """Descarga y cachea el maestro de municipios de AEMET."""
    global _cache_municipios
    if _cache_municipios is not None:
        return _cache_municipios

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Paso 1: obtener URL de datos
        resp = await client.get(MUNICIPIOS_URL, headers=_headers())
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al consultar AEMET")

        payload = resp.json()
        datos_url = payload.get("datos")
        if not datos_url:
            raise HTTPException(status_code=502, detail="AEMET no devolvió URL de datos")

        # Paso 2: descargar datos reales (codificados en latin-1)
        data_resp = await client.get(datos_url)
        if data_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al descargar municipios")

        text = data_resp.content.decode("latin-1")
        municipios = json.loads(text)

    _cache_municipios = municipios
    logger.info(f"Maestro de municipios AEMET cacheado: {len(municipios)} entradas")
    return municipios


@router.get(
    "/municipios",
    summary="Buscar municipios por nombre",
    description="Devuelve municipios de AEMET que coincidan con el texto de búsqueda.",
)
async def buscar_municipios(
    q: Annotated[str, Query(min_length=2, description="Texto de búsqueda (mín. 2 caracteres)")],
):
    """Busca municipios en el maestro de AEMET filtrando por nombre."""
    municipios = await _obtener_municipios()

    texto = q.lower().strip()
    resultados = [
        {"codigo": m["id"].replace("id", ""), "nombre": m["nombre"].strip()}
        for m in municipios
        if texto in m.get("nombre", "").lower()
    ]
    return resultados[:20]


@router.get(
    "/{codigo_municipio}",
    summary="Predicción diaria por municipio",
    description="Devuelve la predicción meteorológica diaria de AEMET para un municipio.",
    responses={
        200: {"description": "Predicción diaria"},
        404: {"description": "Municipio no encontrado"},
        502: {"description": "Error de AEMET"},
    },
)
async def prediccion_municipio(
    codigo_municipio: Annotated[str, Path(pattern=r"^\d{5}$", description="Código INE del municipio (5 dígitos)")],
):
    """Obtiene la predicción diaria de AEMET para el municipio indicado."""
    url = f"{PREDICCION_DIARIA_URL}/{codigo_municipio}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Paso 1: pedir la URL de datos
        resp = await client.get(url, headers=_headers())
        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Municipio no encontrado en AEMET",
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al consultar AEMET")

        payload = resp.json()
        data_url = payload.get("datos")
        if not data_url:
            raise HTTPException(status_code=502, detail="AEMET no devolvió URL de datos")

        # Paso 2: descargar los datos reales (codificados en latin-1)
        data_resp = await client.get(data_url)
        if data_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al descargar datos de AEMET")

        text = data_resp.content.decode("latin-1")
        prediccion_raw = json.loads(text)

    if not prediccion_raw or not isinstance(prediccion_raw, list):
        raise HTTPException(status_code=502, detail="Formato de respuesta inesperado")

    pred = prediccion_raw[0]
    municipio_nombre = pred.get("nombre", codigo_municipio)
    provincia = pred.get("provincia", "")
    dias = pred.get("prediccion", {}).get("dia", [])

    resultado = {
        "municipio": municipio_nombre,
        "provincia": provincia,
        "elaborado": pred.get("elaborado", ""),
        "dias": [],
    }

    for dia in dias:
        fecha = dia.get("fecha", "")

        # Temperatura min/max
        temp = dia.get("temperatura", {})
        temp_max = temp.get("maxima")
        temp_min = temp.get("minima")

        # Probabilidad de precipitación (varios periodos)
        prob_precip = dia.get("probPrecipitacion", [])
        precip_periodos = []
        for pp in prob_precip:
            precip_periodos.append({
                "periodo": pp.get("periodo", ""),
                "valor": pp.get("value", 0),
            })

        # Estado del cielo (varios periodos)
        cielo = dia.get("estadoCielo", [])
        cielo_periodos = []
        for ec in cielo:
            cielo_periodos.append({
                "periodo": ec.get("periodo", ""),
                "valor": ec.get("value", ""),
                "descripcion": ec.get("descripcion", ""),
            })

        # Viento (varios periodos)
        viento = dia.get("viento", [])
        viento_periodos = []
        for v in viento:
            viento_periodos.append({
                "periodo": v.get("periodo", ""),
                "direccion": v.get("direccion", ""),
                "velocidad": v.get("velocidad", 0),
            })

        # Racha máxima
        racha = dia.get("rachaMax", [])
        racha_max = None
        for r in racha:
            val = r.get("value", "")
            if val:
                try:
                    racha_max = max(racha_max or 0, int(val))
                except ValueError:
                    pass

        # Sensación térmica min/max
        sens = dia.get("sensTermica", {})
        sens_max = sens.get("maxima")
        sens_min = sens.get("minima")

        # Humedad relativa min/max
        humedad = dia.get("humedadRelativa", {})
        humedad_max = humedad.get("maxima")
        humedad_min = humedad.get("minima")

        # Cota de nieve provincial (varios periodos)
        cota_nieve_raw = dia.get("cotaNieveProv", [])
        cota_nieve = []
        for cn in cota_nieve_raw:
            cota_nieve.append({
                "periodo": cn.get("periodo", ""),
                "valor": cn.get("value", ""),
            })

        # Índice UV
        uv = dia.get("uvMax")

        resultado["dias"].append({
            "fecha": fecha,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "sens_termica_max": sens_max,
            "sens_termica_min": sens_min,
            "humedad_max": humedad_max,
            "humedad_min": humedad_min,
            "prob_precipitacion": precip_periodos,
            "cota_nieve": cota_nieve,
            "estado_cielo": cielo_periodos,
            "viento": viento_periodos,
            "racha_max": racha_max,
            "uv_max": uv,
        })

    return resultado

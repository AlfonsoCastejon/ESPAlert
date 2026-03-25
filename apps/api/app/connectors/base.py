import abc
import logging
from typing import List, Any
import httpx

logger = logging.getLogger(__name__)

class BaseConnector(abc.ABC):
    """
    Clase base abstracta para todos los conectores de fuentes de alertas.
    """
    
    # Cliente HTTP asíncrono compartido (patrón Singleton perezoso)
    _client = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return cls._client

    async def fetch(self) -> List[Any]:
        """
        Método público para obtener la lista de alertas normalizadas.
        Implementa el manejo de errores global para evitar que fallen
        silenciosa o abruptamente otros procesos si hay caída de red.
        """
        try:
            return await self._fetch()
        except httpx.RequestError as exc:
            logger.error(f"Error de red al intentar conectar en {self.__class__.__name__}: {exc}")
            return []
        except Exception as exc:
            logger.exception(f"Error inesperado durante la extracción en {self.__class__.__name__}: {exc}")
            return []

    @abc.abstractmethod
    async def _fetch(self) -> List[Any]:
        """
        Método abstracto que deben implementar todos los conectores hijos.
        Aquí reside la lógica específica de HTTP (usando self.client) 
        y la normalización de la respuesta.
        """
        pass
        
    @classmethod
    async def close_client(cls):
        """Cierra el cliente HTTP compartido."""
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

"""Rate limiter compartido (slowapi) para proteger endpoints sensibles."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia global. Se importa desde routers y main.
# La key se obtiene de la IP remota (respeta X-Forwarded-For si Caddy lo pasa).
limiter = Limiter(key_func=get_remote_address)

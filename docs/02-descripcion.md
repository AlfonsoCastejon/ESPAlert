# 2. Descripción

## Funcionalidades principales

### Mapa de alertas en tiempo real

La página principal muestra un mapa de España (peninsular, Baleares, Canarias, Ceuta y Melilla) con MapLibre GL sobre tiles de OpenFreeMap. Las alertas activas se representan con marcadores cuyo color corresponde a su severidad (rojo para extrema, naranja para severa, amarillo para moderada y verde para menor). El mapa carga las capas de comunidades autónomas y provincias en un GeoJSON simplificado para mantener un peso aceptable y muestra una leyenda visual con la escala de severidad y la diferencia entre punto de localización y polígono de área afectada. Cuando el usuario elige una comunidad autónoma en el filtro lateral, el mapa hace `flyTo` automático a su encuadre, lo que evita tener que hacer scroll manual hasta Canarias o Baleares.

Las nuevas alertas llegan por dos vías: polling cada minuto al endpoint `/api/alerts` y un canal WebSocket `/ws` que empuja los cambios en cuanto los conectores los persisten.

### Listado con filtros y paginación

La ruta `/alertas` ofrece la vista de listado completo. Permite filtrar por fuente (AEMET, IGN, DGT, MeteoAlarm, Meshtastic), severidad y comunidad autónoma. El orden es configurable por fecha o severidad y se devuelve paginado (20 por página). Cada fila muestra título, fuente, área, severidad y fecha, y se expande al hacer clic para ver descripción, fecha de expiración y metadatos. Los usuarios autenticados pueden marcar favoritos y los administradores pueden eliminar alertas individualmente.

### Predicción meteorológica por municipio

`/prediccion` consume el endpoint `/api/forecast` que actúa de proxy autenticado contra AEMET OpenData. El usuario busca su municipio (mínimo dos caracteres, con debounce) y la API devuelve el detalle de la predicción diaria: temperaturas máximas y mínimas, sensación térmica, humedad, probabilidad de precipitación por tramos, estado del cielo, viento, racha máxima, cota de nieve provincial e índice UV.

### Registro, login y perfil

ESPAlert usa autenticación JWT en cookie httpOnly (nombre `espalert_session`). El registro valida la fortaleza de la contraseña en cliente (mínimo ocho caracteres, mayúscula, minúscula y número) y en servidor con Pydantic. Tras el login, el usuario accede a su perfil (`/perfil`), gestiona sus alertas favoritas, cambia su contraseña (`/perfil/cuenta`) o se suscribe a las notificaciones push.

### Notificaciones push web

El navegador suscribe el dispositivo al endpoint `/api/push/subscribe` con claves VAPID. El backend envía los avisos relevantes mediante `pywebpush` cuando entra una alerta nueva que cumple las preferencias del usuario.

### Conector Meshtastic bidireccional

ESPAlert opera un broker **Mosquitto propio** desplegado como servicio Docker en el mismo droplet, y un **nodo Meshtastic físico** que actúa de gateway entre la radio LoRa y MQTT.

**LoRa** es una modulación de radio de bajo consumo y largo alcance que opera en bandas libres ISM (868 MHz en Europa). Envía paquetes pequeños a varios kilómetros con throughput bajo (entre 0.3 y 50 kbps según el factor de spreading) y latencia alta. Adecuada para texto y telemetría, no para multimedia.

**Meshtastic** es un firmware abierto que monta sobre LoRa una capa mesh: cada nodo retransmite los paquetes de los demás sin servidor central. Aporta cifrado AES-256 por canal, app móvil oficial por Bluetooth y puente MQTT para enlazar la red con servicios TCP/IP. Las placas compatibles cuestan entre 20 y 60 €.

**Encaje con ESPAlert**: la web depende de internet. Una emergencia que tumbe la red móvil deja a los usuarios sin avisos justo cuando más útiles serían. La mesh local sigue funcionando porque no usa infraestructura. ESPAlert tiende el puente: el backend publica al broker las alertas críticas y el nodo gateway las retransmite por LoRa al resto de nodos al alcance.

- **Entrada (mesh → ESPAlert)**: el cliente `paho-mqtt` se suscribe al topic del nodo y persiste los mensajes que llegan por radio en la tabla `mesh_messages` con coordenadas, SNR y RSSI. Si el mensaje incluye texto, además se inserta como `Alert` con `source=meshtastic`, `severity=unknown` y geometría tomada de las coordenadas del nodo emisor o de su última posición conocida. Estas alertas mesh no pasan por validación de organismo oficial, así que se diferencian visualmente del resto: aparecen en color morado en el mapa y caducan automáticamente a los 7 días.
- **Salida (ESPAlert → mesh)**: cuando se inserta una alerta nueva con severidad `severe` o `extreme`, o cuando una existente escala a esos niveles, el backend publica un resumen al broker. El nodo gateway lo retransmite por LoRa al resto de nodos al alcance, llegando finalmente a los móviles emparejados por Bluetooth con la app oficial de Meshtastic.

Los administradores revisan los mensajes en `/admin/mesh` y pueden purgar el histórico.

### Panel de administración

`/admin` está protegido por el rol `admin`. Permite listar y cambiar el rol de usuarios, eliminar alertas y gestionar mensajes mesh. El control se hace en backend con la dependencia `get_current_admin`.

## Interfaz y experiencia de usuario

Tema claro y oscuro con persistencia en `localStorage`, alternable desde la cabecera. Diseño responsive con breakpoints móvil, tablet y escritorio. Banner de cookies con cumplimiento básico de accesibilidad y enlace a la política de privacidad. Cumplimiento WCAG AA: contraste adecuado, focus visible global, aria-labels en botones de iconos, skip-link "Saltar al contenido principal" y atributos `lang="es"`.

## Usuarios objetivo

- Ciudadano general que quiere ver de un vistazo si hay riesgos cerca.
- Personal voluntario o de guardia de protección civil interesado en una vista agregada.
- Radioaficionados y comunidad Meshtastic que quieren publicar o consumir avisos por mesh.
- Estudiantes y desarrolladores que quieren un proyecto de referencia con stack moderno.

## Casos de uso típicos

1. Visitante anónimo entra a la home y consulta si hay alertas activas en su comunidad.
2. Usuario registrado marca como favoritas las alertas de AEMET en Andalucía.
3. Usuario suscrito recibe un push cuando entra una alerta de severidad extrema.
4. Administrador detecta una alerta duplicada y la elimina.
5. Operador mesh envía un mensaje desde un nodo Meshtastic y aparece en el panel admin.

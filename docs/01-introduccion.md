# 1. Introducción, objetivos y antecedentes

## Origen de la idea

En España conviven varios organismos que emiten avisos de riesgo a la población: AEMET (meteorología), IGN (sismología y volcanes), DGT (incidencias de tráfico) y MeteoAlarm (paraguas europeo). Cada uno publica sus alertas por canales distintos: la app oficial de AEMET, el portal del IGN, los paneles informativos de la DGT o los feeds CAP de MeteoAlarm. No existe un panel ciudadano único que las agregue en tiempo real, las represente sobre un mapa común y permita filtrarlas por severidad, fuente o territorio.

La motivación personal del proyecto añade un segundo eje: el interés por las redes mesh de baja potencia tipo Meshtastic (LoRa). En zonas rurales o tras una emergencia que tumba la red móvil, la cobertura mesh sigue funcionando. ESPAlert nace como excusa para integrar ambos mundos: un agregador web moderno y un canal de respaldo radio que permita reenviar avisos breves cuando falla internet.

## Objetivos

- Agregar en una sola plataforma alertas de AEMET, IGN, DGT y MeteoAlarm con polling periódico.
- Mostrarlas en un mapa interactivo con leyenda por severidad y filtrado por comunidad autónoma.
- Permitir registro y favoritos de alertas para usuarios autenticados.
- Enviar notificaciones push web a los suscriptores.
- Recibir y publicar mensajes mesh a través de Meshtastic vía MQTT.
- Ofrecer un panel de administración para moderar alertas y mensajes.

## Antecedentes y comparativa

- **App AEMET**: oficial, pero limitada a meteorología y solo en móvil.
- **MeteoAlarm**: web europea, agrega avisos meteorológicos pero no incluye sismos, tráfico ni canal mesh.
- **Avisos del 112**: notificaciones puntuales por SMS o redes sociales, sin mapa unificado ni filtro.
- **Apps de terceros (Windguru, Windy, etc.)**: orientadas a aficionados a meteo, sin agregar fuentes oficiales.

ESPAlert se diferencia por agregar fuentes heterogéneas (meteo, sismo, tráfico, mesh) en una única vista, ser código abierto, gratuita y disponer de un canal radio independiente de internet a través de Meshtastic. El alcance es deliberadamente acotado: España peninsular, Baleares, Canarias, Ceuta y Melilla.

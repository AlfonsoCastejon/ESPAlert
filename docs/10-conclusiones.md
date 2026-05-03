# 10. Conclusiones

## Cumplimiento de objetivos

El proyecto partía con seis objetivos concretos. Repaso del estado real:

- **Agregar alertas multi-fuente en tiempo real.** Conseguido. AEMET, IGN, DGT y MeteoAlarm están integrados con conectores propios y polling cada 2-5 minutos. La normalización a un modelo común `Alert` permite tratarlas homogéneamente en la API y en la interfaz.
- **Mapa unificado de España.** Conseguido. MapLibre GL sobre OpenFreeMap, capas simplificadas de comunidades y provincias, marcadores por severidad, leyenda interactiva y saltos rápidos a archipiélagos y ciudades autónomas.
- **Notificaciones push web.** Conseguido. Suscripción VAPID desde el frontend, persistencia por usuario y envío con `pywebpush` desde un worker Celery cuando entra una alerta nueva.
- **Canal Meshtastic como respaldo.** Conseguido completamente. Hay un nodo LoRa físico operativo que actúa de gateway: reenvía a la red mesh por radio cualquier alerta severa o extrema publicada por el backend, y reenruta al broker los mensajes que recibe de otros nodos al alcance. El broker es un **Mosquitto propio** desplegado como servicio Docker, no un broker público, lo que mantiene los mensajes dentro de la infraestructura del proyecto.
- **Predicción por municipio.** Conseguido. Búsqueda con debounce y proxy autenticado contra AEMET con detalle diario completo.
- **Panel de administración.** Conseguido. Listado y cambio de rol de usuarios, eliminación de alertas y gestión de mensajes mesh, todo protegido por la dependencia `get_current_admin`.

Más allá de los objetivos iniciales, se incorporaron en el camino: cobertura de pruebas con `pytest-cov`, endurecimiento de seguridad (rate limit, headers, autenticación previa al `accept()` del WebSocket), accesibilidad con skip-link y `:focus-visible` global, SEO (sitemap dinámico, OpenGraph, Twitter Card, manifest PWA) y optimización de Lighthouse (de 64 a 93 en escritorio).

## Mejoras futuras

- **Ampliar la red de nodos mesh.** Actualmente hay un solo nodo gateway en el droplet. Captar voluntarios para desplegar nodos adicionales en provincias con peor cobertura móvil mejoraría la resiliencia del canal LoRa.
- **Aplicación móvil nativa** con notificaciones push fiables fuera del navegador. La opción más práctica es una capa Capacitor sobre el frontend actual, lo que reutilizaría el 90 por ciento del código.
- **Correlación de alertas** mediante machine learning ligero: detectar cuando varias fuentes notifican el mismo evento desde ángulos distintos (lluvia AEMET + corte DGT + sismo IGN) y agruparlas en una "incidencia" única.
- **Multilenguaje completo** (catalán, gallego, euskera, inglés). El backend ya prioriza español pero conserva idiomas secundarios; falta exponerlo en la interfaz con `next-intl`.
- **Exportación a GeoJSON y CSV** del listado filtrado, útil para protección civil y para uso académico.
- **Recuperación de contraseña por email** con SendGrid o el SMTP de Mailgun.
- **Internacionalización del CAP** para incorporar agencias de Portugal y del sur de Francia, pensando en regiones transfronterizas.

## Lecciones aprendidas

- **Desplegar pronto y desplegar a menudo.** Subir el proyecto al droplet desde la primera semana ahorra mucho dolor: detectas problemas de configuración, de Caddy, de variables de entorno y de DNS antes de que se acumulen. Si lo hubiera dejado para el final, la última semana habría sido caótica.
- **El peso real del frontend está en los recursos, no en el código.** El JavaScript del bundle era razonable; el problema era un GeoJSON de 11.6 MB. La lección: medir antes de optimizar y mirar la pestaña Network antes que el bundle analyzer.
- **Los tests automáticos en CI no se discuten.** En cuanto rompí dos veces seguidas algo en `main` por subir sin pasar pytest local, configurar el workflow de CI fue trivial y eliminó toda una clase de errores.
- **Seguridad por capas.** El primer prototipo no tenía rate limit, ni headers, ni autenticación en el WebSocket. Añadirlo en una sola tarde cuando ya estaba todo funcionando me dejó claro que es mucho más barato pensarlo desde el principio. Para futuros proyectos, cookie httpOnly, headers Caddy y limit en endpoints de auth son la base mínima.
- **Sprints de dos semanas con tablero kanban.** Dividir el trabajo en bloques de dos semanas con objetivos claros mantuvo el proyecto avanzando incluso cuando hubo semanas peores. GitHub Projects con campos de Sprint y Estimación es suficiente, no necesité Jira.
- **Pequeño y bien afinado, mejor que grande e incompleto.** En las primeras semanas hubo tentación de añadir todo (alertas sanitarias, sismicidad mundial, integraciones con Telegram). Recortar el alcance al núcleo y rematar bien lo que entraba dio mejor resultado que un proyecto más ambicioso a medio terminar.

## Reflexión técnica

Lo que **repetiría** sin dudar:

- **FastAPI async.** El ahorro de threads con cuatro APIs externas y el WebSocket es notable, y la documentación OpenAPI automática te regala medio criterio de la rúbrica.
- **PostgreSQL con PostGIS.** Filtrar por bounding box en BD con índice GIST es órdenes de magnitud más rápido que cualquier filtrado en memoria.
- **JWT en cookie httpOnly.** Mitiga XSS sin sacrificar usabilidad. Vale el coste de añadir `credentials: "include"` en cada fetch.
- **MapLibre con OpenFreeMap.** Cero coste, sin tokens, sin sustos de facturación.
- **Celery con Beat.** Polling separado de la API, fácil de escalar añadiendo workers.

Lo que **cambiaría**:

- **Next.js 16 era demasiado reciente.** Salió pocas semanas antes de empezar y trajo cambios incompatibles (`next lint` eliminado, requisitos nuevos en `metadata`). Habría sido más sensato fijarse a Next 15 LTS y migrar más adelante.
- **Quizá tRPC en lugar de REST tradicional.** El frontend y el backend están en el mismo monorepo, comparten esquemas Pydantic/Zod implícitamente y tendría sentido compartirlos explícitamente con tRPC. La OpenAPI cumple, pero tRPC eliminaría las discrepancias de tipos manuales.
- **Plantear el broker propio antes.** Al final el sistema corre con Mosquitto propio y canal privado, pero llegué ahí tras descartar la opción del broker público. Si lo planteo desde el día uno habría evitado rehacer la configuración del nodo y los topics.

## Trade-offs aceptados

- Cookie httpOnly frente a localStorage: gano seguridad, pierdo flexibilidad para clientes no-web.
- Polling cada 2-5 minutos frente a webhooks: AEMET no expone webhooks; el polling es la única opción y el coste de latencia es asumible para alertas meteorológicas.
- Mosquitto propio con canal privado frente a broker público: gano control, privacidad y soberanía sobre el transporte; pierdo la inmediatez de no tener que mantener un servicio extra. Asumido a cambio de no depender de infraestructura ajena.
- GeoJSON simplificado al 5 por ciento: gano 28× en tamaño, pierdo precisión de fronteras (irrelevante para una vista de severidad por región).
- Tests al 66 por ciento de cobertura: por encima del umbral típico del 60 por ciento que se pide en proyectos académicos, sin caer en tests de relleno solo para inflar el número.

ESPAlert termina siendo un proyecto pequeño en alcance pero coherente en ejecución: cumple todos los objetivos planteados, despliega de forma reproducible, está cubierto por pruebas y documentado para que cualquiera pueda continuarlo.

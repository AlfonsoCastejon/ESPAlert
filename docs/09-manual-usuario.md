# 9. Manual de usuario

Este manual recorre las funcionalidades principales desde el punto de vista de la persona que usa la aplicación.

## Pantallas principales

![Home con el mapa de España y leyenda](assets/home.png)

![Listado de alertas con filtros desplegados](assets/alertas.png)

![Predicción con resultados de un municipio](assets/prediccion.png)

![Formulario de registro](assets/formulario.png)

![Perfil con favoritos](assets/favoritos.png)

![Preferencias del usuario](assets/preferencia.png)

![Panel de administración](assets/panelAdmin.png)

## Flujos paso a paso

### Consultar alertas activas

1. Abre [https://espalert.app](https://espalert.app). No hace falta registro.
2. El mapa centra automáticamente la península. Para ver Canarias, Baleares o Ceuta y Melilla selecciona la comunidad autónoma en el filtro lateral: el mapa volará automáticamente a su encuadre.
3. Haz clic sobre cualquier marcador para ver el título, la severidad, la fecha de expiración y la fuente.
4. Para una vista en lista, pulsa "Ver alertas" en la cabecera o navega a `/alertas`.

### Registrarse y guardar favoritos

1. Pulsa "Registro" en la cabecera.
2. Introduce email y contraseña (mínimo ocho caracteres, mayúscula, minúscula y número). El indicador de fortaleza es orientativo.
3. Tras el registro, sesión iniciada automáticamente.
4. En el listado, haz clic en el icono de estrella de cualquier alerta para marcarla como favorita.
5. En `/perfil` puedes ver el conjunto completo de favoritos y abrirlos en el mapa.

### Activar notificaciones push

1. Inicia sesión.
2. Ve a `/perfil` y pulsa "Activar notificaciones".
3. El navegador pedirá permiso. Acepta.
4. A partir de ese momento, las nuevas alertas que cumplan tus preferencias generan un push.

Los push se reciben aunque la pestaña esté cerrada, siempre que el navegador esté abierto en segundo plano.

### Consultar predicción meteorológica

1. Ve a `/prediccion`.
2. Escribe al menos dos caracteres del municipio. La búsqueda es con debounce: espera medio segundo a que aparezcan sugerencias.
3. Selecciona uno y verás máximas, mínimas, sensación térmica, humedad, probabilidad de precipitación, viento, racha máxima, cota de nieve provincial e índice UV.

### Cambiar tema claro u oscuro

1. Pulsa el icono de sol o luna en la cabecera.
2. La preferencia se guarda en `localStorage` y se respeta entre sesiones.
3. Si tu sistema operativo está en modo oscuro, ESPAlert arranca en oscuro la primera vez.

### Cambiar contraseña

1. Inicia sesión y ve a `/perfil/cuenta`.
2. Introduce la contraseña actual y la nueva (con la misma fortaleza requerida).
3. Pulsa "Guardar". La cookie se mantiene válida.

## Preguntas frecuentes

- **No me llegan notificaciones push.** Comprueba en los ajustes del navegador que `espalert.app` tiene permiso de notificaciones. En Chrome: candado junto a la URL -> Notificaciones -> Permitir. Si has cambiado de equipo, tienes que volver a suscribirte.
- **No veo Canarias en el mapa.** El mapa arranca centrado en la península. Selecciona "Canarias" en el filtro de comunidad autónoma y el mapa volará automáticamente al archipiélago.
- **El listado no muestra alertas antiguas.** El mapa filtra por las últimas 24 horas y el listado activo solo muestra alertas no expiradas. El histórico expirado está disponible vía API (`GET /api/alerts/history`) y se purga a los 14 días.
- **He olvidado mi contraseña.** En esta versión no hay recuperación automática por email. Contacta con el administrador del servicio.
- **La aplicación no carga en mi navegador.** ESPAlert requiere un navegador moderno con soporte de service workers (Chrome 90+, Firefox 88+, Safari 16+, Edge 90+). En Internet Explorer no funciona.
- **¿Es de pago?** No. ESPAlert es gratuito y de código abierto.
- **¿Mis datos se comparten?** No. La cuenta se usa solo para guardar favoritos, preferencias y suscripciones push. No hay tracking publicitario. Detalles en `/privacidad`.

## Accesibilidad

- Skip-link al pulsar Tab al cargar: salta directamente al contenido principal.
- Foco visible con borde naranja en todos los elementos interactivos.
- Contraste WCAG AA en ambos temas.
- Navegación completa por teclado.
- Lector de pantalla: cada icono interactivo lleva `aria-label`.

Si encuentras un problema de accesibilidad, abre una incidencia en el [repositorio](https://github.com/alfonsocastejon/ESPAlert/issues).

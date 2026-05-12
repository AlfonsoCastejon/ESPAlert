// Service worker de ESPAlert. Solo se encarga de mostrar notificaciones push.

self.addEventListener("push", (event) => {
  let datos = { titulo: "ESPAlert", cuerpo: "Nueva alerta", url: "/" };
  try {
    if (event.data) datos = { ...datos, ...event.data.json() };
  } catch (_) {
    if (event.data) datos.cuerpo = event.data.text();
  }

  const opciones = {
    body: datos.cuerpo,
    icon: "/icon.png",
    badge: "/icon.png",
    data: { url: datos.url || "/" },
  };

  event.waitUntil(self.registration.showNotification(datos.titulo, opciones));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const destino = event.notification.data?.url || "/";
  event.waitUntil(
    clients.matchAll({ type: "window" }).then((ventanas) => {
      for (const v of ventanas) {
        if (v.url.includes(destino) && "focus" in v) return v.focus();
      }
      if (clients.openWindow) return clients.openWindow(destino);
    }),
  );
});

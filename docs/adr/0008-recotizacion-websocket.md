# ADR 0008: Recotización en Tiempo Real vía WebSockets
**Fecha:** 2026-05-30
**Autor:** Leonardo

## Contexto
Las casas de apuestas requieren que los usuarios vean las cuotas de los partidos en vivo (`LIVE`) actualizadas al milisegundo. Si dependiéramos de que el cliente (Navegador) haga _polling_ a la API cada cierto tiempo, sobrecargaríamos el servidor de peticiones HTTP en eventos muy populares, y el retardo podría causar pérdidas financieras.

## Opciones consideradas
### 1. Polling HTTP (AJAX)
- **Pros:** Fácil de implementar. No requiere infraestructura extra.
- **Contras:** Alto consumo de recursos en el servidor, latencia inherente y experiencia pobre para apuestas en vivo.

### 2. Server-Sent Events (SSE)
- **Pros:** Conexión unidireccional ligera y nativa de HTTP.
- **Contras:** Django no tiene soporte nativo asíncrono para broadcast masivo a través de SSE de forma tan madura como Channels.

### 3. WebSockets con Django Channels
- **Pros:** Conexión bidireccional de baja latencia. Broadcast eficiente a miles de usuarios utilizando Redis como backend de capas (Channel Layer). Perfecta integración con el ecosistema Django asíncrono.
- **Contras:** Aumenta la complejidad de despliegue (requiere ASGI y servidor Redis).

## Decisión
Se eligió utilizar **WebSockets con Django Channels**. Se implementó un consumidor asíncrono (`OddsConsumer`) que agrupa a los usuarios por el ID del evento (`odds_{event_id}`). Al conectarse, el usuario recibe un `odds_snapshot` inicial. Posteriormente, mediante _signals_ (`post_save`) emitidas por cambios en los Mercados, el servidor hace _broadcast_ de un payload `odds_update` que el frontend refleja dinámicamente animando las cuotas sin recargar la pantalla.

## Consecuencias
- Excelente experiencia de usuario (UI reactiva e inmediata).
- Desacoplamiento de la lógica de negocio; el backend solo emite el signal y Channels se encarga de propagarlo.
- Despliegue más complejo en producción.

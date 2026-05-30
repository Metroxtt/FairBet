# ADR 0006: Idempotencia en Endpoints Transaccionales
**Fecha:** 2026-05-30
**Autor:** Leonardo

## Contexto
Los usuarios interactúan con la plataforma web desde dispositivos móviles o conexiones inestables. Es común que un usuario presione el botón de "Apostar" múltiples veces si la red se cuelga, o que el cliente intente reintentar un request HTTP fallido. Esto podría resultar en cobros duplicados o apuestas repetidas indeseadas.

## Opciones consideradas
### 1. Bloqueo en el Frontend exclusivamente
- **Pros:** Fácil de implementar (deshabilitar el botón de submit).
- **Contras:** Inseguro. No protege contra reintentos automáticos de red o llamadas a la API de terceros.
### 2. Claves de Idempotencia (Idempotency Keys)
- **Pros:** Estándar de la industria financiera (ej. Stripe). El cliente envía un UUID único por cada intención de transacción. El backend rechaza o devuelve la respuesta exitosa cacheada si el UUID ya fue procesado.
- **Contras:** Requiere generar y enviar UUIDs desde el cliente y almacenar estos UUIDs en la base de datos de manera única.

## Decisión
Se implementó el patrón de **Idempotency Keys**. El frontend genera un UUID (`crypto.randomUUID()`) y lo envía en el payload al crear una apuesta (`/api/bets/place/`). A nivel de modelo, tanto `Bet` como `ComboBet` e incluso `LedgerEntry` poseen un campo `idempotency_key` con restricción `UNIQUE`. 

## Consecuencias
- La base de datos arrojará un error de integridad (o el endpoint devolverá 400/409) si se procesa el mismo request duplicado, protegiendo totalmente los fondos del usuario.
- El cliente debe tener la responsabilidad de generar el UUID en cada nueva intención de apuesta.

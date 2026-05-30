# ADR 0005: Concurrencia en la Billetera (select_for_update)
**Fecha:** 2026-05-30
**Autor:** Leonardo

## Contexto
En un sistema de apuestas, múltiples transacciones financieras pueden ocurrir simultáneamente (por ejemplo, el usuario deposita dinero mientras una apuesta se está liquidando, o realiza múltiples apuestas en ráfaga). Si leemos el saldo, calculamos el nuevo saldo y lo guardamos sin control de concurrencia, podemos sufrir condiciones de carrera que lleven a inconsistencias financieras (creación de dinero de la nada o pérdida de fondos).

## Opciones consideradas
### 1. Bloqueo a nivel de aplicación (Mutex / Redis)
- **Pros:** Desacoplado de la base de datos.
- **Contras:** Agrega una dependencia externa (Redis). Riesgo de bloqueos huérfanos si el proceso muere.
### 2. Bloqueo pesimista en base de datos (`select_for_update`)
- **Pros:** Aprovecha las garantías transaccionales de PostgreSQL. Simple de implementar en Django con `transaction.atomic()`. Garantiza que ninguna otra transacción modifique la fila hasta que la actual termine.
- **Contras:** Puede causar cuellos de botella si hay demasiada contención sobre una misma cuenta (ej. la cuenta de la Casa).

## Decisión
Se eligió utilizar el bloqueo pesimista mediante `select_for_update()` dentro de un bloque `transaction.atomic()` en la función `transfer` de la billetera. Además, siempre bloqueamos las cuentas ordenándolas por su ID (`account_ids = sorted([from_account.pk, to_account.pk])`) para prevenir _deadlocks_ clásicos en la base de datos.

## Consecuencias
- Las transacciones financieras están 100% protegidas contra condiciones de carrera.
- El rendimiento en la cuenta global de la casa podría verse afectado bajo altísima concurrencia, lo cual es aceptable para esta etapa del proyecto.

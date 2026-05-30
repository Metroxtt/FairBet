# ADR 0007: Máquina de Estados para Entidades de Apuestas
**Fecha:** 2026-05-30
**Autor:** Leonardo

## Contexto
Tanto los eventos deportivos como los tickets de apuestas tienen un ciclo de vida bien definido. Una apuesta nace pendiente, puede cerrarse prematuramente (cash-out), ganarse, perderse o anularse (cancelación del evento). Administrar estos estados con booleanos o condicionales complejos generaría código difícil de mantener.

## Opciones consideradas
### 1. Variables estáticas y booleanos (`is_winner`, `is_cancelled`)
- **Pros:** Fácil implementación inicial.
- **Contras:** Multiplica el esfuerzo en validaciones para que no existan combinaciones imposibles (ej. ganada y cancelada al mismo tiempo).

### 2. Implementación de Máquina de Estados basada en `TextChoices`
- **Pros:** Un solo campo `estado` que dicta el ciclo de vida del objeto. Se encapsula la lógica de transición en métodos del modelo (ej. `settle()`, `cash_out()`). Se integra de forma natural al ORM de Django.

## Decisión
Se implementó un patrón de máquina de estados utilizando `models.TextChoices`. 
Las apuestas (`Bet`, `ComboBet`) tienen estados: `PENDING`, `WON`, `LOST`, `CANCELLED`, `CASHED_OUT`.
Los eventos (`Event`) transicionan entre: `SCHEDULED`, `LIVE`, `SUSPENDED`, `FINISHED`, `CANCELLED`.
Se encapsuló la lógica de transición y el movimiento de dinero en el método `settle()` de las apuestas para asegurar que el cambio de estado sea atómico junto con las transacciones de billetera.

## Consecuencias
- La lógica de negocio está fuertemente encapsulada en el modelo (Fat Models).
- Si un evento se cancela, la apuesta puede ser transicionada directamente a `CANCELLED` y manejar el reembolso sin tocar código de las vistas.

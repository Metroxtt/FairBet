# ADR 0012: Arquitectura de Apuestas Combinadas (ComboBets)
**Fecha:** 2026-05-30
**Autor:** Leonardo

## Contexto
Los usuarios solicitaron la capacidad de apostar a múltiples eventos deportivos de manera combinada ("Parlay" o "ComboBet"). En este modelo, todas las selecciones deben ser ganadoras para que la apuesta pague, y la cuota total es la multiplicación de las cuotas de cada selección.

## Opciones consideradas
### 1. Extender el modelo `Bet` existente
- **Pros:** Una única tabla para todas las apuestas.
- **Contras:** Rompe la estructura lógica. Un `Bet` actual está atado a un solo `Event` y `Market`. Cambiarlo obligaría a migrar miles de filas y hacer relaciones Muchos a Muchos opcionales, generando un esquema sucio.

### 2. Modelos separados: `ComboBet` y `ComboLeg`
- **Pros:** Esquema limpio y fuertemente tipado. `ComboBet` actúa como la cabecera (maneja el monto, estado global y transferencias con la billetera) y se relaciona uno-a-muchos con `ComboLeg` (cada "pata" de la apuesta combinada).
- **Contras:** Lógica de liquidación separada y cálculo de GGR independiente.

## Decisión
Se decidió implementar los modelos `ComboBet` y `ComboLeg` en la aplicación de `betting`. 
La lógica de liquidación se realiza a través de un método `check_and_settle()` llamado cada vez que un evento asociado finaliza. El método verifica iterativamente cada "pata" (leg):
1. Si un solo `leg` se pierde, la combinada entera pasa a `LOST`.
2. Si un `leg` corresponde a un evento `CANCELLED`, se asume como _void_ (cuota = 1.0) para esa pata y la cuota total del ComboBet se recalcula dinámicamente.
3. Si todos los `legs` terminan y no hay perdidos, la combinada se marca como `WON` y se pagan las ganancias en base a la cuota recalculada.

## Consecuencias
- Al separar los modelos, las lógicas de liquidación son especializadas y menos propensas a errores de condiciones _if_ excesivas.
- Para los reportes administrativos (como el Gross Gaming Revenue), fue necesario recordar hacer consultas a ambas tablas (`Bet` y `ComboBet`) y sumarlas.

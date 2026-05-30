# Lecciones Aprendidas - Sprint Final (Leonardo)

En este último sprint logramos cerrar brechas críticas de FairBet, pasando de un simple MVP de apuestas directas a una plataforma más profesional con soporte de apuestas múltiples, control administrativo y protección robusta de concurrencia. Aquí algunas de las lecciones técnicas y organizacionales más valiosas:

## 1. Concurrencia en Sistemas Financieros
Inicialmente pensamos que usar las operaciones atómicas típicas bastaría para el movimiento de saldos. Sin embargo, en el contexto de billeteras que comparten una "Cuenta de la Casa", la probabilidad de condiciones de carrera es muy alta al liquidar eventos populares. Aprender a usar `select_for_update()` en Django junto con el ordenamiento de claves primarias antes de bloquear, fue un hallazgo fundamental para evitar bloqueos cruzados (*deadlocks*) en PostgreSQL y asegurar la integridad 100% de los fondos.

## 2. Idempotencia como Regla de Oro
Las integraciones con APIs transaccionales nos enseñaron que "todo lo que puede fallar en red, va a fallar". Al implementar las claves de idempotencia UUID, blindamos la plataforma contra los doble clicks del usuario o reintentos automáticos, pasando la responsabilidad al cliente y asegurando una barrera dura a nivel de base de datos. 

## 3. Máquinas de Estados para Manejar el Caos
En sistemas donde una entidad puede transicionar por múltiples lógicas (Ej: Apuestas que pasan de Pendientes a Canceladas con reembolso, o de Pendientes a Ganadas con pago), utilizar simples booleanos hubiera sido un desastre mantenible. La adopción de máquinas de estados vía `TextChoices` encapsuló toda la lógica de transición dentro de los métodos del modelo (`settle()`), lo cual hizo que implementar el Cash-Out o la liquidación de combinadas (ComboBets) fuera un proceso predecible y altamente testeable.

## 4. WebSockets y Rendimiento
Implementar Channels para empujar cuotas en tiempo real nos ahorró muchísimas llamadas HTTP y sobrecarga del servidor en comparación con el *polling* tradicional. Aprendimos a mandar payloads lo más ligeros posibles y aislar a los clientes usando Grupos (`odds_X`) por partido, lo cual escalaría de manera horizontal muy fácilmente con un backend de Redis.

## 5. Arquitectura de las ComboBets y Reportes (GGR)
El mayor desafío técnico en la segunda mitad fue no romper la lógica de las apuestas simples al incorporar combinadas. Creando los modelos paralelos `ComboBet` y `ComboLeg`, el esquema se mantuvo limpio. La gran lección aquí ocurrió en los reportes: **Siempre debes revisar todos tus flujos de ingresos al añadir un nuevo tipo de producto**. Inicialmente, el cálculo de Ingresos Brutos (GGR) omitió sumar el volumen de las ComboBets; nos dimos cuenta a tiempo de actualizar los reportes del dashboard del operador para que la contabilidad cuadrara perfectamente.

---
Conclusión: Construir FairBet me ha dado un contexto invaluable de cómo se entrelazan la ingeniería de software concurrente, el diseño de interfaces en tiempo real y la precisión contable de los sistemas transaccionales.

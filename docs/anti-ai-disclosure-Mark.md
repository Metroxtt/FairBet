# Anti-AI Disclosure — Mark

## Primera sesion (17-18 de Mayo del 2026)
- Inicializacion del proyecto FairBet Lab con Django.
- Configuracion Docker: Dockerfile multi-etapa, docker-compose con PostgreSQL y Redis.
- Apoyo de IA para:
  - Estructura basica del proyecto Django dentro del contenedor.
  - Comprension de prefijos Conventional Commits (chore:, feat:, fix:, test:).
  - Investigacion de librerias para testing: coverage, hypothesis.
  - Conexion a PostgreSQL desde Django con variables de entorno.

## Segunda sesion (19 de Mayo del 2026)
- Configuracion de infraestructura asincrona: Daphne, Redis channel layer, Celery.
- Apoyo de IA para:
  - Integracion de Django Channels con Daphne como servidor ASGI.
  - Configuracion de Celery con Redis como broker.
  - Diferencias entre WSGI y ASGI para el proyecto.

## Tercera sesion (25 de Mayo del 2026)
- Refactorizacion completa del proyecto en apps modulares: users, wallet, events, betting.
- Configuracion de DRF, JWT, Channels, Celery y variables de entorno.
- Apoyo de IA para:
  - Separacion del monolito en apps Django independientes.
  - Configuracion de SimpleJWT con email como USERNAME_FIELD.
  - Estructura de serializers, viewsets y routers para cada app.
  - Arquitectura de contabilidad de partida doble en wallet.

## Cuarta sesion (27-28 de Mayo del 2026)
- Testing exhaustivo del modulo betting:
  - Tests de maquina de estados del modelo Bet (SCHEDULED, PENDING, WON, LOST, CASHED_OUT).
  - Tests de validaciones de juego responsable en place_bet.
  - Tests de la tarea Celery settle_bets_for_event.
  - Validaciones de DNI, autoexclusion, limites de deposito.
- Correccion de bugs criticos en wallet: is_excluded, self-transfer, withdraw get_or_create.
- Implementacion de WithdrawSerializer y test_settings con SQLite.
- Migraciones de todas las apps unificadas.
- Apoyo de IA para:
  - Uso de Hypothesis para tests de invarianza contable (partida doble).
  - Implementacion de parametrize en tests de maquina de estados.
  - Monkeypatching de timezone.now para tests de cash-out.
  - Logica de settle() con contabilidad de partida doble.
  - Edge cases en transfer: monto cero, negativo, idempotencia, self account.
  - Correccion de errores en withdraw (permission_classes, refresh_from_db).
  - Estado SUSPENDED en eventos y seed de datos con Decimal.

## Quinta sesion (30 de Mayo del 2026)
- Feature: top jugadores reales de la semana en el dashboard.
- Validacion de monto minimo S/20 en depositos.
- Fix: reemplazar floatformat por stringformat para separador decimal invariante.
- Fix: sanitizar parseo de cuotas con parseFloat en bet slip.
- Fix: cambiar fondo inicial de CASA de S/ 1,000,000 a S/ 10,000.
- Toggle de visibilidad de contraseña en login y registro.
- Apoyo de IA para:
  - Consulta SQL de agregacion para leaderboard semanal.
  - Manejo de locales con formato de decimales invariante.
  - Parseo seguro de cuotas desde el DOM.

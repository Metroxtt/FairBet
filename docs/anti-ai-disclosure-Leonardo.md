# Anti-AI Disclosure — Leonardo

## Primera sesion (17-18 de Mayo del 2026)
- Configuracion del entorno Docker (Dockerfile, docker-compose, dependencias).
- Apoyo de IA para:
  - Estructura del Dockerfile para Django + PostgreSQL + Redis.
  - Correccion de errores en requirements.txt (typo "gunicor").
  - Comprension de Conventional Commits (prefijos chore:, feat:, fix:).
  - Manejo de ramas secundarias con git checkout -b.

## Segunda sesion (28 de Mayo del 2026)
- Implementacion de WebSockets para cuotas en tiempo real (Django Channels + Redis).
- Creacion de migraciones iniciales para todas las apps.
- Resolucion de bugs de Fase 0.
- Apoyo de IA para:
  - Configuracion del layer de Channels con Redis como backend.
  - Logica de broadcast de cuotas actualizadas a clientes conectados.
  - Consumer de WebSocket para eventos en vivo.

## Tercera sesion (29 de Mayo del 2026)
- Implementacion del core financiero: billetera, transacciones, ledger.
- Limites de deposito y correccion de tests de billetera.
- Sincronizacion en tiempo real de eventos.
- Integracion de layout principal, estilos base y ticket de apuestas.
- Panel de ranking en barra lateral.
- Apoyo de IA para:
  - Logica de cash-out y apuestas en vivo.
  - Verificacion de ledger (contabilidad partida doble).
  - Anti-fraude y controles de juego responsable.
  - Estilos UI/UX (dashboard, historial, perfil, billetera).
  - Procesamiento de depositos con AJAX y formato de decimales.
  - Correccion de errores de estado y calculo en apuestas.
  - Autenticacion por sesiones (cookies) en DRF.

## Cuarta sesion (30 de Mayo del 2026)
- Apuestas combinadas (combos): API y validaciones de cuotas.
- Soporte para multiples selecciones y renderizado dinamico de mercados.
- Gestion integral de eventos en el panel operador:
  - Creacion, edicion y eliminacion de eventos.
  - Transicion automatica de Programado a En Vivo.
  - Visualizacion de resultados para eventos finalizados.
- Correcciones UI: decimales, saldo, limites de billetera, pantalla negra en operador.
- Apoyo de IA para:
  - Logica de validacion de combos: seleccion multiple, cuota combinada.
  - Transicion automatica de estados segun fecha_hora.
  - Diseno del panel operador con pestañas y tabla de eventos.
  - Filtro de eventos por categoria en el panel operador.

# Anti-AI Disclosure — Edwar

## Primera sesion (27 de Mayo del 2026)
- Investigacion de aspectos legales y normativos para la billetera digital en Peru.
- Identificacion de requisitos: registro de movimientos, trazabilidad de transacciones,
  auditoria, control de operaciones, validacion de usuarios y juego responsable
  conforme a la Ley 31557.
- Implementacion del modulo de billetera (wallet):
  - Endpoint deposit con calculo de saldo basado en LedgerEntry (contabilidad de partida doble).
  - Endpoint withdraw con validacion de autoexcluido y footer legal.
  - Limite diario de deposito y validacion de daily_limit=0.
  - refresh_from_db tras deposit para saldo actualizado en tiempo real.
- Apoyo de IA para:
  - Conceptos de contabilidad de partida doble aplicados a billetera digital.
  - Normativa Peruana Ley 31557 para plataformas de apuestas deportivas.
  - Arquitectura LedgerEntry como registro inmutable de transacciones.
  - Correccion de bugs: import decimal faltante, permission_classes, bypass de daily_limit.
  - Edge cases de transfer: monto cero, negativo, idempotencia estricta, self account.
  - Tests de Hypothesis para invarianza contable.

## Segunda sesion (28 de Mayo del 2026)
- Integracion de ramas del equipo: merges de wallet-Edwar, betting-Mark, users-Raiza y events-Leonardo.
- Correccion de conflictos de merge en vistas y templates.
- Tests de wallet corregidos para ejecucion local.

## Tercera sesion (29 de Mayo del 2026)
- Separacion de roles: bloqueo de apuestas, depositos y retiros para administradores (staff).
- Implementacion de endpoints admin: admin_verify_kyc, admin_block_user, admin_unblock_user.
- Construccion de tabla de usuarios con acciones (KYC, bloquear, desbloquear) en el dashboard del operador.
- Validacion de DNI con algoritmo peruano (modulo 11, serie y digito verificador).
- Trigger de liquidacion automatica de apuestas al ingresar resultado.
- Apoyo de IA para:
  - Logica de verificacion de DNI con pesos [3,2,7,6,5,4,3,2] y tabla de verificacion.
  - Filtro de usuarios por estado en el dashboard admin.
  - Confirmacion previa a acciones de bloqueo/verificacion via JS.
  - Trigger SQL / señal Django para liquidacion automatica.

## Cuarta sesion (30 de Mayo del 2026)
- Landing page publica sin necesidad de autenticacion:
  - Eliminacion de @login_required en home_view.
  - Modal de autenticacion (login/register) con AJAX.
  - Topbar adaptable para usuarios anonimos ("Ingresar" button).
  - Home con bienvenida generica para no-autenticados.
  - Login/register en pagina completa ocultando topbar y sport-bar.
  - LOGOUT_REDIRECT_URL cambiado de /login/ a /.
- Login AJAX: login_view responde con JSON cuando X-Requested-With=XMLHttpRequest.
- Home view condicional: contexto solo para usuarios autenticados (account, bets, leaderboard).
- Fix: categoria al crear eventos (se guardaba siempre como 'futbol').
- Fix: filtro FINISHED usando enum Event.Estado en vez de string 'finished'.
- Estilos responsive para 900px, 600px y 400px.
- Badge de categoria dinamico en home.html y list.html ({{ event.get_categoria_display }}).
- Cuotas renderizadas desde el servidor en list.html (no solo via WebSocket).
- Validacion de telefono obligatorio: exactamente 9 digitos empezando con 9.
- ADRs 03 (double-entry ledger), 04 (Decimal precision), 09 (responsible gaming),
  10 (hash-chain audit), 11 (role separation).
- Apoyo de IA para:
  - Estructura de modal de autenticacion con pestañas login/register.
  - Manejo de tokens JWT en localStorage desde el modal.
  - Logica de showAuthModal() y gate en addToSlip() para redirigir a login.
  - Responsive design con media queries para 3 breakpoints.
  - Implementacion de add_event_view con categoria desde formulario.

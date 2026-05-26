# Plan de Trabajo - FairBet Lab (Casa de Apuestas)

---

## Estado Actual del Proyecto

| Componente | Estado |
|------------|--------|
| Docker + Compose (4 servicios) | ✅ Listo |
| PostgreSQL + Redis | ✅ Configurado |
| Daphne (ASGI) + Channels | ✅ Configurado |
| Celery (`config/celery.py`) | ✅ Creado |
| DRF + JWT + permisos | ✅ Configurado |
| `.env` con variables de entorno | ✅ Creado |
| `AUTH_USER_MODEL = users.User` | ✅ Configurado |
| WebSocket routing (`ws/events/{id}/`) | ✅ Configurado |
| `ALLOWED_HOSTS`, `LANGUAGE_CODE`, `TIME_ZONE` | ✅ Configurado |
| `src/config/urls.py` con rutas a cada app | ✅ Configurado |
| App `users/` con modelo User + DepositLimit | ✅ Creado (Raiza completa) |
| App `wallet/` con Account + LedgerEntry + transfer() | ✅ Creado (Edwar completa) |
| App `events/` con Event + Market + WebSocket consumer | ✅ Creado (Leonardo completa) |
| App `betting/` con Bet + settle() + Celery task | ✅ Creado (Mark completa) |

---

## Ramas de Trabajo (Cada uno en su rama)

Cada integrante trabaja en **su propia rama** a partir de `main`:

| Persona | Rama | App |
|---------|------|-----|
| **Raiza** | `feature/users` | `users/` |
| **Mark** | `feature/betting` | `betting/` |
| **Leonardo** | `feature/events` | `events/` |
| **Edwar** | `feature/wallet` | `wallet/` |

**Flujo:**
1. `git checkout -b feature/users` (cada uno desde `main`)
2. Trabajan solo en los archivos de **su app**
3. Commit con prefijo: `feat:`, `fix:`, `test:`, `docs:`
4. Al terminar el Sprint 1, hacen **Pull Request** a `main`
5. Se fusionan en orden: `wallet` → `users` → `events` → `betting`

**⚠️ Cada uno toca SOLO los archivos de su app.**
Los archivos compartidos (`settings.py`, `urls.py`, `asgi.py`, `celery.py`, `.env`, `requirements.txt`) ya están configurados y **no deben modificarse sin coordinar con el equipo**.

---

## 📦 Sprint 1 — Lo que cada uno debe hacer

### Raiza → Rama: `feature/users` — App: `users`

**Ya está creado:** `models.py` (User + DepositLimit), `serializers.py` (RegisterSerializer con validación DNI), `views.py` (RegisterView, UserProfileView, self_exclude), `admin.py`, `urls.py`, `tests.py`

**Lo que debes completar:**
1. ✅ Modelos ya listos — ejecuta `python manage.py makemigrations users && python manage.py migrate`
2. Revisa que la validación de DNI (módulo 11) en `serializers.py` funcione correctamente
3. Prueba los endpoints: `POST /api/users/register/`, `GET /api/users/me/`, `POST /api/users/self-exclude/`
4. Agrega más tests en `tests.py` (registro con DNI inválido, usuario menor de edad, etc.)
5. **No modifiques** `settings.py`, `urls.py` generales ni apps de otros

---

### Mark → Rama: `feature/betting` — App: `betting`

**Ya está creado:** `models.py` (Bet + ComboBet + ComboLeg + settle()), `serializers.py` (BetSerializer + PlaceBetSerializer), `views.py` (place_bet + BetHistoryView), `tasks.py` (settle_bets_for_event Celery task), `admin.py`, `urls.py`, `tests.py`

**Lo que debes completar:**
1. ✅ Modelos ya listos — ejecuta `python manage.py makemigrations betting && python manage.py migrate`
2. Prueba el endpoint `POST /api/bets/place/` con evento, mercado y selección válidos
3. Verifica que la máquina de estados funciona: `pending → won | lost | cancelled`
4. Prueba que `settle_bets_for_event` (Celery) liquida todas las apuestas de un evento
5. Agrega tests de la máquina de estados y la idempotencia

---

### Leonardo → Rama: `feature/events` — App: `events`

**Ya está creado:** `models.py` (Event + Market), `serializers.py`, `views.py` (EventViewSet + MarketViewSet), `consumers.py` (OddsConsumer WebSocket), `routing.py`, `admin.py`, `urls.py`, `tests.py`

**Lo que debes completar:**
1. ✅ Modelos ya listos — ejecuta `python manage.py makemigrations events && python manage.py migrate`
2. Crea **seeds de datos** con partidos del Mundial 2026 (Perú vs Brasil, Argentina vs Uruguay, etc.)
3. Prueba el WebSocket: conectarse a `ws://localhost:8000/ws/events/1/` y verificar que recibe las cuotas
4. Implementa `group_send` cuando se actualiza un market → que el WebSocket reciba la nueva cuota en tiempo real
5. Agrega filtros de búsqueda por equipo, estado del evento

---

### Edwar → Rama: `feature/wallet` — App: `wallet`

**Ya está creado:** `models.py` (Account + LedgerEntry + transfer()), `serializers.py`, `views.py` (BalanceView, deposit), `admin.py`, `urls.py`, `tests.py`

**Lo que debes completar:**
1. ✅ Modelos ya listos — ejecuta `python manage.py makemigrations wallet && python manage.py migrate`
2. Prueba la función `transfer()` con `select_for_update` — verifica que el bloqueo pesimista funciona
3. Agrega **tests con Hypothesis** para verificar la invarianza contable:
   - `sum(debits) == sum(credits)` siempre
   - `balance_after == previous_balance + credit - debit`
4. Integra con `DepositLimit` de Raiza: en `deposit()` valida que el monto no supere el límite
5. Prueba `GET /api/wallet/balance/`, `GET /api/wallet/transactions/`

---

## 📦 Sprint 2 (para después del Sprint 1)

| Persona | Nuevas tareas | Rama |
|---------|---------------|------|
| **Raiza** | Bonos promocionales (cuenta bono + rollover) + Antifraude (detección multi-cuenta por IP) | `feature/bonus` |
| **Mark** | Apuestas Combinadas (ComboBet endpoint) + Cash-Out | `feature/advanced-betting` |
| **Leonardo** | Apuestas In-Play (cuotas dinámicas, suspensión automática) + Mercados adicionales (Over/Under 2.5, BTTS, Hándicap Asiático) | `feature/inplay` |
| **Edwar** | Auditoría inmutable (AuditLog con SHA256) + Dashboard (GGR, exposición, CSV) | `feature/compliance` |

---

## Recordatorios Técnicos

- `Decimal(max_digits=18, decimal_places=4)` en **todos** los campos de dinero
- `select_for_update()` dentro de `transaction.atomic()` en toda transferencia
- `idempotency_key` UUID en cada movimiento de fondos
- `@database_sync_to_async` para consultas ORM dentro de consumers WebSocket
- `group_add` / `group_send` para WebSocket en tiempo real
- Footer obligatorio: *"Plataforma educativa con moneda virtual. No constituye una casa de apuestas."*
- Cobertura mínima 80% en `wallet` y `betting` (pytest + coverage)
- Property-based testing con Hypothesis para invarianzas financieras

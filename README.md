# FAIRBET LAB

Plataforma educativa de apuestas deportivas con moneda virtual. Creada como parte del curso de Ingeniería de Software de la Universidad Señor de Sipán.

Esto no es una casa de apuestas real. No se usa dinero de verdad. Es un simulador para aprender cómo funciona una plataforma de apuestas por dentro: desde la contabilidad de partida doble hasta las cuotas en tiempo real por WebSocket.

---

## Qué hace

- Registro de usuarios con verificación de identidad (KYC simulado)
- Billetera virtual con depósitos, retiros y contabilidad auditada
- Apuestas simples y combinadas a eventos deportivos
- Cuotas que se actualizan en vivo (WebSocket)
- Panel de operador para gestionar eventos, usuarios y verificar el ledger
- Límites de depósito, autoexclusión y juego responsable
- Roles separados: el staff no puede apostar

## Stack

- **Backend:** Django 5 + Django REST Framework + Channels
- **Base de datos:** PostgreSQL 16
- **Cache / WS:** Redis 7
- **Frontend:** HTML templates + CSS vanilla + JavaScript
- **Infra:** Docker, Daphne (ASGI), Celery
- **Testing:** unittest + coverage + hypothesis

## Cómo levantar

```bash
docker compose up --build
```

Esto levanta tres servicios:
- `fairbet_web` — la app Django (Daphne en ASGI)
- `postgres` — la base de datos
- `redis` — cache y WebSocket layer

Para crear un admin:

```bash
docker exec -it fairbet_web python manage.py createsuperuser
```

Para correr tests:

```bash
docker exec fairbet_web python manage.py test
```

## Apps

| App | Qué hace |
|-----|----------|
| `users` | Registro, login, KYC, autoexclusión, límites de depósito |
| `wallet` | Billetera con contabilidad de partida doble, ledger encadenado con SHA-256 |
| `events` | Eventos deportivos, mercados, cuotas, WebSocket en tiempo real |
| `betting` | Apuestas simples y combinadas, liquidación automática, cash-out |

## ADRs

En `docs/adr/` están las decisiones técnicas que fuimos tomando:
por qué partida doble, por qué TextChoices, cómo manejamos concurrencia,
por qué el staff no apuesta, etc.

## Bitácoras de uso de IA

En `docs/anti-ai-disclosure-*.md` cada miembro documentó cómo y cuándo
usó IA como apoyo (para investigar conceptos, corregir bugs, entender
librerías, etc.). Ningún código se generó automáticamente sin entenderlo.

## Equipo

| Miembro | Contribución principal |
|---------|----------------------|
| Leonardo | WebSocket, eventos, apuestas combinadas, operador dashboard, Docker inicial |
| Mark | Testing (hypothesis, cobertura), infraestructura (Celery, Channels, JWT), refactors |
| Raiza | Módulo users (modelos, vistas, templates, KYC, autoexclusión, ADRs) |
| Edwar | Wallet (partida doble, ledger hash), admin endpoints, landing page, rol staff, ADRs |

## Disclaimer

Esto es un proyecto educativo. No hay dinero real involucrado.
Todo es moneda virtual. Si tienes problemas con el juego, busca ayuda profesional.
Jugar con dinero real puede causar adicción y pérdidas económicas.

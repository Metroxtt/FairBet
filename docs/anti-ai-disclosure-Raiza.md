# Anti-AI Disclosure — Raiza
## Primera sesion (25 de Mayo del 2026)
- Implementacion de modelos, vistas, serializers, admin y tests de la app users.
- Apoyo de IA para:
  - Cooldown 24h para subir limites de deposito.
  - Validacion DNI (modulo 11 / algoritmo peruano).
  - Autoexclusion con plazos (7/30/90/indefinido).
  - Correccion de bugs en tests.
## Segunda sesion (27 de Mayo del 2026)
- Apoyo de IA para revision de codigo y checklist de mejoras.
- Implementacion de:
  - Permission IsNotAutoexcluido en users/permissions.py.
  - Validacion de autoexcluido no puede cambiar limites.
  - Read-only para campo estado en UserSerializer.
  - Validacion de no re-autoexcluirse si ya esta autoexcluido.
  - Tests adicionales: DNI invalido, autoexcluido no cambia limites,
    irreversibilidad de autoexclusion, estado read-only.
  - Mejora en create_user: conversion de fecha y creacion de DepositLimit.
  - ADRs documentando decisiones tecnicas.
## Tercera sesion (28 de Mayo del 2026)
- Revision conjunta con el equipo y ajustes finales:
  - Agregado campo is_active al modelo User (requerido por Django auth).
  - Agregado endpoint verify-kyc/ para completar el flujo KYC simulado.
  - Reemplazada logica de cooldown por campo cooldown_hasta separado.
  - Tests para verify-kyc y cooldown_hasta.
## Cuarta sesion (28 de Mayo del 2026)
- Implementacion de templates y frontend del modulo users.
- Apoyo de IA para:
  - Estructura base del template base.html con herencia de bloques.
  - Sidebar con navegacion y topbar con wallet-chip.
  - auth.js con helper apiFetch() para manejo de JWT.
  - login.html con integracion JWT y fallback POST tradicional.
  - register.html con validacion DNI peruano y edad minima en JS.
  - profile.html con badges de estado coloreados.
  - kyc_verify.html con condicionales por estado de cuenta.
  - deposit_limits.html con barras de progreso y cooldown timer.
  - self_exclude.html con selector de plazos y mensaje de juego responsable.
  - Correcciones post-revision: footer para no-auth, page_title como variable,
    names de URL unicos, method/action en formularios.
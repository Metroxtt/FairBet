# Anti-AI Disclosure — Raiza
## Primera sesion (27 de Mayo del 2026)
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